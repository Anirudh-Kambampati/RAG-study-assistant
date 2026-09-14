import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Response
from pydantic import BaseModel

load_dotenv()

from loaders.loader_factory import load_source
from chunking.text_splitter import split_documents
from embeddings.embedder import get_embedding_model
from vector_store.qdrant_store import delete_document, search_document, upsert_document_chunks
from llm.generator import get_llm, get_fallback_llm
from llm.prompts import assemble_prompt, build_history_text, sanitize_preferences
from db import db_session, init_db
from auth import get_current_user
from api.routes_auth import router as auth_router

app = FastAPI(title="Metis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    USER_DATA_ROOT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# User-scoped storage: every document's original uploaded file lives under
# data/users/<user_id>/documents/<document_id>/ — a user's rows in the
# `documents` table are the only thing that can produce a path under their
# own <user_id> directory, so there is no way to reach another user's files
# without already having bypassed the ownership-scoped SQL queries below.
# Chunk vectors themselves live in Qdrant (vector_store/qdrant_store.py),
# scoped by (user_id, doc_id) payload filters rather than by filesystem path.
# ---------------------------------------------------------------------------
USER_DATA_ROOT = Path("data/users")

SAFE_ID = re.compile(r"[^\w.\- ]")
MAX_CHUNK_PREVIEW = 1400
DEFAULT_RETRIEVAL_K = 6
MAX_RETRIEVAL_K = 16
# MMR casts a wider net than k before picking the final, diverse set — this
# keeps near-duplicate chunks (e.g. repeated section headers) from crowding
# out genuinely different passages.
MMR_FETCH_MULTIPLIER = 4
MMR_LAMBDA = 0.5


def document_dir(user_id: str, document_id: str) -> Path:
    return USER_DATA_ROOT / user_id / "documents" / document_id


def sanitize_doc_id(doc_id: str) -> str:
    clean = SAFE_ID.sub("_", doc_id).strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Invalid document name")
    return clean


def get_owned_chat(conn: psycopg.Connection, user_id: str, slug: str) -> dict:
    """Look up a chat by its URL slug, scoped to the authenticated user.

    This is the single choke point every chat/document-scoped endpoint goes
    through: the WHERE clause filters on user_id, so supplying another
    user's slug simply finds no row (404) instead of leaking their data —
    ownership is enforced by the query itself, not by a separate check the
    caller could forget.
    """
    row = conn.execute(
        """
        SELECT c.id AS chat_id, c.title, d.id AS document_id, d.slug,
               d.index_dir, d.file_path
        FROM chats c
        JOIN documents d ON d.id = c.document_id
        WHERE c.user_id = %s AND d.slug = %s
        """,
        (user_id, slug),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return row


def _row_messages(conn: psycopg.Connection, chat_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT role, content, sources_json FROM messages WHERE chat_id = %s ORDER BY created_at ASC",
        (chat_id,),
    ).fetchall()
    messages = []
    for r in rows:
        msg = {"role": r["role"], "content": r["content"]}
        if r["sources_json"]:
            msg["sources"] = json.loads(r["sources_json"])
        messages.append(msg)
    return messages


def _insert_message(conn: psycopg.Connection, chat_id: str, role: str, content: str, sources=None) -> None:
    conn.execute(
        "INSERT INTO messages (id, chat_id, role, content, sources_json, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (
            str(uuid.uuid4()),
            chat_id,
            role,
            content,
            json.dumps(sources) if sources else None,
            datetime.now(timezone.utc).isoformat(),
        ),
    )


class QuerySource(BaseModel):
    rank: int
    score: float | None = None
    page: int | None = None
    title: str | None = None
    snippet: str


class QueryResponse(BaseModel):
    role: str
    content: str
    sources: list[QuerySource] = []


class ChatRequest(BaseModel):
    query: str
    k: int | None = None
    style: str | None = None
    format: str | None = None
    # Assistant mode & grounding (independent dimensions; see llm/prompts.py)
    assistant_mode: str | None = None
    grounding_mode: str | None = None
    # Response behavior toggles
    explain_terms: bool | None = None
    give_examples: bool | None = None
    highlight_key_points: bool | None = None
    related_concepts: bool | None = None
    ask_clarifying_questions: bool | None = None


@app.get("/chats")
def list_chats(user: dict = Depends(get_current_user), conn: psycopg.Connection = Depends(db_session)):
    rows = conn.execute(
        "SELECT c.id AS chat_id, d.slug, d.index_dir FROM chats c JOIN documents d ON d.id = c.document_id WHERE c.user_id = %s",
        (user["id"],),
    ).fetchall()
    return {
        row["slug"]: {"messages": _row_messages(conn, row["chat_id"]), "index_dir": row["index_dir"]}
        for row in rows
    }


@app.post("/chats/{doc_id}")
def create_chat(
    doc_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(db_session),
):
    slug = sanitize_doc_id(doc_id)
    existing = conn.execute(
        "SELECT id FROM documents WHERE user_id = %s AND slug = %s", (user["id"], slug)
    ).fetchone()
    if existing is not None:
        raise HTTPException(status_code=409, detail="A chat already exists for this document")

    document_id = str(uuid.uuid4())
    doc_dir = document_dir(user["id"], document_id)
    doc_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.filename or "document").name
    suffix = Path(original_name).suffix
    data = file.file.read()
    file_path = doc_dir / f"original{suffix}"
    file_path.write_bytes(data)

    try:
        documents = load_source(str(file_path))
        chunks = split_documents(documents)
        # `index_dir` is kept only because the documents table still has a
        # NOT NULL column for it; retrieval no longer reads a FAISS index
        # from this path — vectors live in Qdrant, upserted below.
        index_dir = doc_dir / "index"
        upsert_document_chunks(user["id"], document_id, original_name, chunks)
    except Exception:
        shutil.rmtree(doc_dir, ignore_errors=True)
        # Defensive: never leave orphaned vectors behind if something after
        # a partially-successful upsert still fails.
        delete_document(user["id"], document_id)
        raise

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO documents (id, user_id, slug, filename, content_type, size_bytes, file_path, index_dir, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (document_id, user["id"], slug, original_name, file.content_type, len(data), str(file_path), str(index_dir), now, now),
    )
    chat_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO chats (id, user_id, document_id, title, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (chat_id, user["id"], document_id, slug, now, now),
    )
    return {"detail": "Chat created", "doc_id": slug}


@app.delete("/chats/{doc_id}")
def delete_chat(
    doc_id: str,
    user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(db_session),
):
    slug = sanitize_doc_id(doc_id)
    chat = get_owned_chat(conn, user["id"], slug)

    delete_document(user["id"], chat["document_id"])
    # ON DELETE CASCADE removes the chat + its messages along with the document row.
    conn.execute("DELETE FROM documents WHERE id = %s AND user_id = %s", (chat["document_id"], user["id"]))
    shutil.rmtree(document_dir(user["id"], chat["document_id"]), ignore_errors=True)
    return {"detail": "Chat deleted", "doc_id": slug}


@app.delete("/chats")
def delete_all_chats(user: dict = Depends(get_current_user), conn: psycopg.Connection = Depends(db_session)):
    rows = conn.execute("SELECT id FROM documents WHERE user_id = %s", (user["id"],)).fetchall()
    count = len(rows)
    for row in rows:
        delete_document(user["id"], row["id"])
        shutil.rmtree(document_dir(user["id"], row["id"]), ignore_errors=True)
    conn.execute("DELETE FROM documents WHERE user_id = %s", (user["id"],))
    return {"detail": "All conversations deleted", "count": count}


@app.post("/chats/{doc_id}/clear")
def clear_chat(
    doc_id: str,
    user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(db_session),
):
    slug = sanitize_doc_id(doc_id)
    chat = get_owned_chat(conn, user["id"], slug)
    conn.execute("DELETE FROM messages WHERE chat_id = %s", (chat["chat_id"],))
    return {"detail": "Conversation cleared", "doc_id": slug}


@app.get("/chats/{doc_id}/export")
def export_chat(
    doc_id: str,
    user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(db_session),
):
    slug = sanitize_doc_id(doc_id)
    chat = get_owned_chat(conn, user["id"], slug)
    messages = _row_messages(conn, chat["chat_id"])

    lines = [f"# Conversation: {slug}", ""]
    for msg in messages:
        role = "You" if msg["role"] == "user" else "Assistant"
        lines.append(f"## {role}")
        lines.append("")
        lines.append(msg["content"])
        lines.append("")
    markdown = "\n".join(lines)
    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{slug}.md"'},
    )


@app.post("/chats/{doc_id}/query")
def query_chat(
    doc_id: str,
    body: ChatRequest,
    user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(db_session),
):
    slug = sanitize_doc_id(doc_id)
    chat = get_owned_chat(conn, user["id"], slug)

    history_text = build_history_text(_row_messages(conn, chat["chat_id"]))
    _insert_message(conn, chat["chat_id"], "user", body.query)

    k = body.k if body.k is not None else DEFAULT_RETRIEVAL_K
    k = max(1, min(k, MAX_RETRIEVAL_K))

    query_embedding = get_embedding_model().embed_query(body.query)
    results = search_document(
        user["id"],
        chat["document_id"],
        query_embedding,
        k=k,
        fetch_k=max(k * MMR_FETCH_MULTIPLIER, 20),
        lambda_mult=MMR_LAMBDA,
    )
    docs = [doc for doc, _score in results]
    # Each chunk is labeled with its 1-based rank ("[1]", "[2]", ...) so the
    # model can cite it inline — this numbering must stay in lockstep with
    # `sources` below, since the frontend resolves "[n]" against sources[n-1].
    context = "\n\n".join(f"[{i + 1}] {d.page_content[:MAX_CHUNK_PREVIEW]}" for i, d in enumerate(docs))

    sources = [
        QuerySource(
            rank=i + 1,
            score=float(score) if score is not None else None,
            page=(doc.metadata.get("page") + 1) if isinstance(doc.metadata.get("page"), int) else None,
            title=chat["title"],
            snippet=doc.page_content[:300].replace("\n", " ").strip(),
        )
        for i, (doc, score) in enumerate(results)
    ]

    prefs = sanitize_preferences(
        assistant_mode=body.assistant_mode,
        grounding_mode=body.grounding_mode,
        style=body.style,
        format=body.format,
        explain_terms=body.explain_terms,
        give_examples=body.give_examples,
        highlight_key_points=body.highlight_key_points,
        related_concepts=body.related_concepts,
        ask_clarifying_questions=body.ask_clarifying_questions,
    )
    prompt = assemble_prompt(prefs, context, history_text, body.query)

    try:
        response = get_llm().invoke(prompt)
    except Exception as primary_err:
        print(f"Primary LLM failed: {primary_err}")
        try:
            response = get_fallback_llm().invoke(prompt)
        except Exception as fallback_err:
            print(f"Fallback LLM failed: {fallback_err}")
            raise HTTPException(
                status_code=502,
                detail="I couldn't generate an answer right now. Please try again.",
            )

    assistant_text = response.content if hasattr(response, "content") else str(response)
    sources_payload = [s.model_dump() for s in sources]
    _insert_message(conn, chat["chat_id"], "assistant", assistant_text, sources_payload)

    return QueryResponse(role="assistant", content=assistant_text, sources=sources)


# ---------------------------------------------------------------------------
# Settings: the frontend's Settings object is stored opaquely (as JSON) per
# user. Validation of its shape stays client-side (lib/settings.ts already
# sanitizes it on load) — the backend's job here is only to scope it to the
# authenticated user, not to re-validate application-level preferences.
# ---------------------------------------------------------------------------
@app.get("/settings")
def get_settings(user: dict = Depends(get_current_user), conn: psycopg.Connection = Depends(db_session)):
    row = conn.execute("SELECT settings_json FROM user_settings WHERE user_id = %s", (user["id"],)).fetchone()
    return json.loads(row["settings_json"]) if row else {}


@app.put("/settings")
def put_settings(
    body: dict,
    user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(db_session),
):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO user_settings (user_id, settings_json, updated_at) VALUES (%s, %s, %s)
        ON CONFLICT(user_id) DO UPDATE SET settings_json = excluded.settings_json, updated_at = excluded.updated_at
        """,
        (user["id"], json.dumps(body), now),
    )
    return {"detail": "Settings saved"}
