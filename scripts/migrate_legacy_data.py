"""
One-time, opt-in migration of the pre-auth JSON/file-based storage into the
new database + per-user file layout.

Before authentication existed, every chat lived in a single global
`chat_store.json` and every FAISS index lived in `faiss_index/<md5(doc_id)>`
with NO owner. This script does not run automatically (nothing at server
startup calls it) — you run it deliberately, once, after deciding who
should own that pre-existing data.

It is read-only with respect to the legacy files: `chat_store.json` and
`faiss_index/` are only ever *read* and *copied* from, never modified or
deleted. If it isn't run, that legacy data simply stays inert on disk
un-migrated and the app behaves as if it doesn't exist (a fresh account has
zero chats) — nothing is silently deleted either way.

Usage:
    python scripts/migrate_legacy_data.py --email you@example.com --name "Your Name" --password "at-least-8-chars"

Re-running is safe: documents already migrated (matched by slug for that
user) are skipped rather than duplicated.
"""

import argparse
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn, init_db  # noqa: E402
from auth import hash_password  # noqa: E402

CHAT_STORE = Path("chat_store.json")
LEGACY_FAISS_DIR = Path("faiss_index")
USER_DATA_ROOT = Path("data/users")


def _source_hash(doc_id: str) -> str:
    return hashlib.md5(doc_id.encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password", required=True, help="At least 8 characters")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    if not CHAT_STORE.exists():
        print(f"No {CHAT_STORE} found — nothing to migrate.")
        return

    legacy_chats = json.loads(CHAT_STORE.read_text())
    if not legacy_chats:
        print(f"{CHAT_STORE} is empty — nothing to migrate.")
        return

    init_db()

    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = %s", (args.email,)).fetchone()
        if row:
            user_id = row["id"]
            print(f"Using existing account {args.email} ({user_id}).")
        else:
            user_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO users (id, name, email, password_hash, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, args.name, args.email, hash_password(args.password), now, now),
            )
            print(f"Created account {args.email} ({user_id}).")

        migrated, skipped_existing, skipped_no_index = 0, 0, 0

        for doc_id, chat in legacy_chats.items():
            existing = conn.execute(
                "SELECT id FROM documents WHERE user_id = %s AND slug = %s", (user_id, doc_id)
            ).fetchone()
            if existing:
                skipped_existing += 1
                continue

            legacy_index_dir = LEGACY_FAISS_DIR / _source_hash(doc_id)
            if not legacy_index_dir.exists():
                print(f"  ! No FAISS index found for '{doc_id}' — importing chat history only (RAG needs a re-upload).")
                skipped_no_index += 1

            document_id = str(uuid.uuid4())
            doc_dir = USER_DATA_ROOT / user_id / "documents" / document_id
            index_dir = doc_dir / "index"
            if legacy_index_dir.exists():
                shutil.copytree(legacy_index_dir, index_dir)
            else:
                doc_dir.mkdir(parents=True, exist_ok=True)

            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO documents (id, user_id, slug, filename, content_type, size_bytes, file_path, index_dir, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NULL, NULL, '', %s, %s, %s)
                """,
                (document_id, user_id, doc_id, doc_id, str(index_dir), now, now),
            )
            chat_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO chats (id, user_id, document_id, title, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (chat_id, user_id, document_id, doc_id, now, now),
            )
            for msg in chat.get("messages", []):
                conn.execute(
                    "INSERT INTO messages (id, chat_id, role, content, sources_json, created_at) VALUES (%s, %s, %s, %s, NULL, %s)",
                    (str(uuid.uuid4()), chat_id, msg["role"], msg["content"], now),
                )
            migrated += 1
            print(f"  + migrated '{doc_id}'")

    print(
        f"\nDone. Migrated {migrated}, skipped {skipped_existing} already-migrated, "
        f"{skipped_no_index} missing their FAISS index.\n"
        f"{CHAT_STORE} and {LEGACY_FAISS_DIR}/ were not modified — safe to keep or remove manually."
    )


if __name__ == "__main__":
    main()
