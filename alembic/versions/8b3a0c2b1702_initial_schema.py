"""initial schema

Revision ID: 8b3a0c2b1702
Revises:
Create Date: 2026-09-14 19:21:54.505440

Mirrors db.SCHEMA exactly (see db.py's module docstring for why this app
uses plain SQL migrations rather than ORM-model autogeneration): users,
sessions, documents, chats, messages, user_settings, with the same foreign
keys and indexes the application code already relies on.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8b3a0c2b1702'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE users (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE sessions (
            id              TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash      TEXT NOT NULL UNIQUE,
            created_at      TEXT NOT NULL,
            expires_at      TEXT NOT NULL
        )
    """)
    op.execute("CREATE INDEX idx_sessions_user ON sessions(user_id)")
    op.execute("CREATE INDEX idx_sessions_token_hash ON sessions(token_hash)")

    op.execute("""
        CREATE TABLE documents (
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
        )
    """)
    op.execute("CREATE INDEX idx_documents_user ON documents(user_id)")

    op.execute("""
        CREATE TABLE chats (
            id              TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            title           TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    op.execute("CREATE INDEX idx_chats_user ON chats(user_id)")
    op.execute("CREATE INDEX idx_chats_document ON chats(document_id)")

    op.execute("""
        CREATE TABLE messages (
            id              TEXT PRIMARY KEY,
            chat_id         TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
            role            TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content         TEXT NOT NULL,
            sources_json    TEXT,
            created_at      TEXT NOT NULL
        )
    """)
    op.execute("CREATE INDEX idx_messages_chat ON messages(chat_id)")

    op.execute("""
        CREATE TABLE user_settings (
            user_id         TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            settings_json   TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_settings")
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS chats")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TABLE IF EXISTS users")
