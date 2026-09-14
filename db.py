"""
Metis's database layer.

Backed by Neon (managed Postgres), reached via the standard `DATABASE_URL`
env var — never hardcoded. Access stays raw SQL (via `psycopg`, the modern
Postgres driver) rather than an ORM: every call site elsewhere in this app
(`auth.py`, `api/main.py`, `api/routes_auth.py`, `scripts/migrate_legacy_data.py`)
already talks to this module through a handful of functions
(`init_db`, `get_conn`, `db_session`) and treats rows as dict-like objects,
which is exactly what `psycopg.rows.dict_row` gives us — so the swap from the
previous local-SQLite version of this module changed only this file's
internals (driver, placeholder style, connect target), not any call site's
behavior.

Schema changes are tracked with Alembic (see `alembic/`) rather than by
editing `SCHEMA` below — `SCHEMA` exists only as the idempotent bootstrap a
fresh dev database needs, and mirrors Alembic's initial revision.
"""

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      TEXT NOT NULL UNIQUE,
    created_at      TEXT NOT NULL,
    expires_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);

CREATE TABLE IF NOT EXISTS documents (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slug            TEXT NOT NULL,
    filename        TEXT NOT NULL,
    content_type    TEXT,
    size_bytes      INTEGER,
    file_path       TEXT NOT NULL,
    index_dir       TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    UNIQUE(user_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);

CREATE TABLE IF NOT EXISTS chats (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_id);
CREATE INDEX IF NOT EXISTS idx_chats_document ON chats(document_id);

CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    chat_id         TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content         TEXT NOT NULL,
    sources_json    TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id         TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    settings_json   TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
"""


def _connect() -> psycopg.Connection:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Point it at your Neon Postgres connection "
            "string (see .env.example) — e.g. "
            "postgresql://user:password@ep-xxxx.neon.tech/dbname?sslmode=require"
        )
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            # Split into individual statements: psycopg's extended query
            # protocol (used whenever a query might later take parameters)
            # doesn't allow multiple statements in one execute() call.
            for statement in filter(None, (s.strip() for s in SCHEMA.split(";"))):
                cur.execute(statement)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    """One connection per request; short-lived, so a plain open/close per
    call is simpler and safer than sharing a connection across threads."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def db_session() -> Iterator[psycopg.Connection]:
    """FastAPI dependency wrapper around get_conn()."""
    with get_conn() as conn:
        yield conn
