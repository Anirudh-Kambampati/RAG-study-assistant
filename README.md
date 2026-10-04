# 📄 Metis (Hosted + Local Hybrid)

A **document-based AI assistant** that lets you upload files and chat with them using **Retrieval-Augmented Generation (RAG)**.

This project is built as a **production-style system** with:

* modular architecture
* pluggable LLM backends
* persistent chat sessions
* deployable infrastructure (no local model dependency required)

---

## 🎯 What This Solves

Traditional LLMs often hallucinate or provide generic answers.

This app:

* retrieves **relevant chunks from your document**
* uses them as **context for the LLM**
* ensures answers are **grounded, explainable, and reliable**

---

## 🧠 Core Concept: RAG

Retrieval-Augmented Generation works as follows:

1. Upload document
2. Split into chunks
3. Convert chunks → embeddings
4. Store in Qdrant (vector database)
5. On query:

   * retrieve relevant chunks (or the whole document, if it's short enough — see Key Design Decisions)
   * pass them to the LLM, numbered so it can cite them inline
   * generate a grounded, cited answer

> **Legacy note:** earlier versions of this project stored vectors in a local
> FAISS index per document instead of Qdrant. See [Legacy / Historical
> Code](#-legacy--historical-code) below.

---

## ✨ Features

* 📁 Upload documents (`PDF`, `DOCX`, `PPTX`, `TXT`)
* 💬 Chat-style interface (ChatGPT-like UX)
* 🧠 True Retrieval-Augmented Generation, with MMR-based retrieval for diverse, non-duplicate context
* 🔍🔤 Hybrid search — dense semantic vectors + BM25 sparse lexical matching, fused server-side in Qdrant (Reciprocal Rank Fusion), so exact terms (codes, names, numbers, formulas) surface even when they're semantically unremarkable
* 🎯 Qdrant search scoped per user and per document
* 📚 Inline citations — answers cite `[1]`, `[2]`, etc. back to the exact retrieved passage, with a hover card showing the source page/snippet (NotebookLM-style)
* 🎛️ Assistant Modes (Quick Answer, Tutor, Exam Prep, Research) and Grounding modes (strict-documents vs. documents + general knowledge)
* 🔐 Real multi-user accounts (email/password, hashed + salted, HttpOnly session cookies) — documents and chats are scoped per user
* 💾 Persistent chat history per document, stored in Postgres (Neon)
* ⚡ Hosted LLM support (Groq)
* 🪂 Fallback LLM support (OpenRouter)
* 🧩 Modular embedding + LLM backend
* 🌐 Deployable via Docker, with env-driven CORS and a `/health` endpoint for PaaS health checks

---

## 🏗️ Architecture

```
User
│
▼
Next.js Frontend (frontend/)
│
├── Landing Page (/)
├── Dashboard (/dashboard)
├── Chat Page (/chat/[docId])
├── Settings (/settings)
├── Login / Signup (/login, /signup)
│
▼
FastAPI Backend (api/)
│
├── POST   /auth/signup, /auth/login, /auth/logout, GET /auth/me
├── GET    /health                     # liveness probe, no dependencies
├── POST   /chats/{doc_id}             # upload + index
├── GET    /chats                      # list chats (scoped to the user)
├── DELETE /chats/{doc_id}             # delete chat (+ its vectors)
└── POST   /chats/{doc_id}/query       # RAG query, with inline citations
│
├──▶ Postgres (Neon) — users, sessions, documents, chats, messages
│
▼
Qdrant (one collection, filtered per user_id + doc_id)
   hybrid search: dense vector + BM25 sparse, fused via RRF
│
▼
Embedding Model (HuggingFace MiniLM, all-MiniLM-L6-v2)
│
▼
LLM Layer
   ├── Primary: Groq (openai/gpt-oss-120b)
   └── Fallback: OpenRouter (google/gemma-4-26b-a4b-it:free)
```

---

## ⚙️ Tech Stack

* **Frontend:** Next.js (React, TypeScript) — ChatGPT-style interface with sidebar (New Chat, history, Settings), light/dark theme, and adjustable retrieval depth
* **Backend:** FastAPI (Python)
* **Auth:** PBKDF2-hashed passwords, HttpOnly session cookies (`auth.py`)
* **Database:** Postgres (Neon) — users, sessions, documents, chats, messages; schema managed via Alembic
* **LLM:** Groq `openai/gpt-oss-120b` (primary), OpenRouter `google/gemma-4-26b-a4b-it:free` (fallback)
* **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`, run via `fastembed`'s ONNX runtime rather than PyTorch — same model/output, much lighter memory footprint
* **Vector DB:** Qdrant Cloud — one shared collection, isolated per user/document via payload filters; hybrid dense + BM25 sparse search (BM25 implemented in pure Python, no extra model/runtime), fused via RRF
* **Document Parsing:** PyPDF, Unstructured, Docx2txt
* **Deployment:** Docker (backend), standard Next.js build (frontend)

---

## 🚀 Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/rag-study-assistant.git
cd rag-study-assistant
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**Mac/Linux**

```bash
source .venv/bin/activate
```

---

### 3️⃣ Install Dependencies

Backend (Python):

```bash
pip install -r requirements.txt
```

Frontend (Node.js 18.18+ required):

```bash
cd frontend
npm install
cd ..
```

---

### 4️⃣ Configure Environment Variables

Create a `.env` file in the root directory (see `.env.example` for the full,
commented list). At minimum:

```env
LLM_BACKEND=hosted

# Groq (Primary LLM)
GROQ_API_KEY=your_groq_api_key

# OpenRouter (Fallback LLM)
OPENROUTER_API_KEY=your_openrouter_api_key

# Neon Postgres connection string (app + auth data)
DATABASE_URL=postgresql://user:password@host/db?sslmode=require

# Qdrant Cloud (vector storage/retrieval)
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key

# "production" makes the session cookie Secure (HTTPS-only); leave unset
# (or "development") for local http:// development.
ENV=development

# The deployed frontend's origin(s), comma-separated if more than one.
# Only needed in production — defaults to http://localhost:3000.
FRONTEND_URL=http://localhost:3000
```

**Required env vars at a glance:**

| Variable | Required | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | Primary LLM provider |
| `OPENROUTER_API_KEY` | Yes | Fallback LLM provider |
| `DATABASE_URL` | Yes | Neon Postgres connection string (users/chats/messages) |
| `QDRANT_URL` / `QDRANT_API_KEY` | Yes | Qdrant Cloud vector store |
| `ENV` | No (default `development`) | Set to `production` to mark the session cookie `Secure` |
| `FRONTEND_URL` | No (default `http://localhost:3000`) | Frontend origin(s) allowed by CORS in production |
| `LLM_BACKEND` | No (default `hosted`) | `hosted` (Groq) or `fallback` (OpenRouter directly) |

---

### 5️⃣ Run the Application

Start the backend (from the repo root):

```bash
uvicorn api.main:app --reload --reload-exclude frontend/* --reload-exclude data/*
```

uvicorn's `--reload` only *restarts* on `.py` changes by default, so
Next.js's constant writes under `frontend/.next/` don't trigger a reload —
but it still watches the *entire* repo root at the filesystem level to
decide that, which adds needless overhead on a tree that size. The
`--reload-exclude` flags cut that down to just the backend source.
`npm run dev:backend` / `dev:all` already have the full exclude list baked
in.

In a second terminal, start the frontend:

```bash
cd frontend
npm run dev
```

Open in browser:

```
http://localhost:3000
```

The Next.js dev server proxies `/api/*` requests to the backend (default `http://localhost:8000`, override with `BACKEND_URL`).

**Or, run both at once** from the repo root (requires the venv already
activated, and `npm install` run once at the repo root to fetch the small
`concurrently` dev dependency):

```bash
npm install      # first time only
npm run dev:all
```

This just wraps the same two commands above in one terminal — it isn't a
different way of running the app, only a shortcut.

---

## 🚢 Deployment

The backend ships with a `Dockerfile` pinned to Python 3.12.10 (the version
this project is developed and tested against — see `.python-version`).

**Build and run:**

```bash
docker build -t metis-backend .
docker run -p 8000:8000 --env-file .env -e PORT=8000 metis-backend
```

The container's `CMD` is the production equivalent of the dev command above,
bound to all interfaces and reading the port from the platform-provided
`$PORT` (falls back to `8000` locally):

```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

No `--reload` — this is the production entrypoint, not the dev one.

**Health check:** `GET /health` returns `200 {"status": "ok"}` and does no
database/vector-store/LLM work, so it's safe to point a PaaS's health check
at it directly.

**CORS / frontend origin:** in production, set `FRONTEND_URL` to your
deployed frontend's origin (e.g. `https://metis.example.com`; comma-separate
apex + `www` if you serve both) so the backend's CORS policy allows it. Left
unset, it only allows `http://localhost:3000` (the local dev frontend).

The frontend itself (`frontend/`) is a standard Next.js app (`npm run
build` / `npm run start`) and isn't part of this Dockerfile — deploy it
wherever you'd normally deploy a Next.js app, pointing its `BACKEND_URL` at
the deployed backend's URL.

This covers the deployment *mechanics*; it does not mean the app has
actually been deployed anywhere yet.

---

## 🧪 How It Works (Execution Flow)

1. User signs up / logs in (session cookie issued, document/chat access scoped to that user)
2. User uploads a document
3. Document is parsed and cleaned
4. Text is split into chunks
5. Chunks are embedded using MiniLM and upserted into Qdrant
6. User asks a question
7. If the document is small enough, every chunk is sent as context; otherwise the most relevant *and* diverse chunks are retrieved (MMR)
8. Context is sent to the LLM, each chunk numbered so it can be cited
9. LLM generates a grounded response with inline citations, shaped by the active Assistant Mode and Grounding mode

---

## 🧠 LLM Strategy

| Layer      | Model                                    | Purpose            |
| ---------- | ----------------------------------------- | ------------------ |
| Primary    | Groq `openai/gpt-oss-120b`                | Fast responses ⚡   |
| Fallback   | OpenRouter `google/gemma-4-26b-a4b-it:free` | Reliability 🪂     |
| Embeddings | MiniLM (`all-MiniLM-L6-v2`)                | Lightweight + fast |

---

## ⚡ Key Design Decisions

* **One shared Qdrant collection, not one index per document** — every chunk carries `user_id`/`doc_id` in its payload, and every read/write is filtered on both, so isolation is enforced by the query itself rather than by filesystem/collection boundaries
* **Small documents skip similarity search entirely** — below a chunk-count threshold, the whole document is sent as context instead of top-k retrieval, so broad questions ("summarize this") aren't limited to whatever happens to be nearest the query embedding
* **Hybrid search instead of a reranker** — dense + BM25 candidates are fused server-side in Qdrant (RRF), then MMR re-ranked for diversity. Gets most of the precision benefit of a dense+sparse+rerank pipeline without an external reranking API, its cost, or its latency
* **Citations are numbered at retrieval time, not guessed by the model** — retrieved chunks are labeled `[1]`, `[2]`, … before being handed to the LLM, and the frontend resolves those same numbers back to each source's page/snippet
* **Postgres is the source of truth for everything except vectors** — users, sessions, documents, chats, and messages all live in Neon; Qdrant only ever holds embeddings + chunk text/metadata
* **Modular LLM + embedding backend** — swapping providers means changing `llm/generator.py`, not the surrounding pipeline
* **Failover system for reliability** — Groq first, OpenRouter if it fails

---

## 🗂️ Project Structure

```
rag-project/
│
├── frontend/             # Next.js frontend (landing page + app)
│   ├── app/              # Pages: /, /dashboard, /chat/[docId], /settings, /login, /signup
│   ├── components/       # AppShell, Sidebar, AuthProvider, SettingsProvider
│   └── lib/              # API client + settings (theme, assistant mode, retrieval depth)
│
├── api/                  # FastAPI backend (HTTP layer)
│   ├── main.py           # Chats CRUD + RAG query endpoint + /health
│   └── routes_auth.py    # Signup/login/logout/me
│
├── auth.py               # Password hashing, session cookies
├── db.py                 # Postgres connection + schema
├── alembic/               # Schema migrations
├── loaders/              # Document loaders (PDF/DOCX/PPTX/TXT)
├── chunking/             # Text splitting logic
├── embeddings/           # Embedding model
├── vector_store/         # Qdrant client, upsert/search/delete, MMR re-ranking
├── llm/                  # LLM provider config + prompt assembly
│
├── Dockerfile             # Backend production image
├── requirements.txt
└── README.md
```

See [Legacy / Historical Code](#-legacy--historical-code) for files that
predate the current Postgres + Qdrant architecture and are no longer part of
the live app.

---

## 📜 Legacy / Historical Code

This project went through a few architectural generations. The following
are **not used by the live app** — kept only as history, not as something to
build on:

* **`chat_store.json`** — a flat-file chat log from before Postgres existed.
  Chat history now lives in the `messages` table (Neon). Safe to delete.
* **`scripts/migrate_legacy_data.py`** — a one-time, already-run script that
  imported that old `chat_store.json` + a local `faiss_index/` directory
  into the current schema. It isn't called by the app and isn't part of any
  startup path.
* **FAISS** — the original vector store (`vector_store/faiss_store.py`, one
  index per document, saved to local disk). Fully replaced by Qdrant; the
  module itself has been removed and `faiss-cpu` is no longer a dependency.
  If you see a `faiss_index/` directory locally, it's leftover data from
  before that migration, not something the app writes to anymore.

If you're reading older commit history or a fork predating the Qdrant
migration, assume anything describing FAISS, `chat_store.json`, or
per-document vector indexes is out of date relative to this README.

---

## ⚠️ Known Limitations

* Some PDFs may fail due to malformed structure (PyPDF limitation)
* Lightweight embeddings → slightly lower semantic accuracy
* Free-tier APIs may have rate limits
* No rate limiting yet on login/signup
* Schema is managed by both Alembic migrations and an idempotent `init_db()`
  startup check — they're kept in sync by hand today, not automatically

---

## 🚀 Future Improvements

* 🔁 Hybrid search (BM25 + vector)
* 🎯 Reranking models
* 🧠 Query rewriting
* 📁 File preview panel
* 🛡️ Rate limiting on auth endpoints
* 🗃️ Consolidate schema management onto Alembic alone

~~Multi-user support~~ and ~~source highlighting~~ are done — see Features above.

---

## 👤 Author

**Anirudh Kambampati**

---

## 📜 License

MIT License. See the [LICENSE](LICENSE) file for more information.
