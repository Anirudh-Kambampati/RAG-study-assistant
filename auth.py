"""
Authentication: password hashing + opaque session tokens, both stdlib-only
(hashlib/secrets) — no bcrypt/passlib/jose dependency needed.

Session model: on login/signup we mint a random 32-byte token, send it to
the browser as an httpOnly cookie, and store only its SHA-256 hash in the
`sessions` table (so a stolen DB dump can't be replayed as a live cookie).
Every request re-hashes the cookie value and looks up that hash — if it
matches an unexpired row, the request is authenticated as that row's user.
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import psycopg
from fastapi import Cookie, Depends, HTTPException, Response

from db import db_session

SESSION_COOKIE_NAME = "metis_session"
SESSION_TTL_DAYS = 30
# Only send the cookie over HTTPS when explicitly running in production —
# local dev over plain http would otherwise never receive it.
COOKIE_SECURE = os.getenv("ENV", "development") == "production"

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iterations, salt, hex_digest = encoded.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(digest.hex(), hex_digest)
    except (ValueError, AttributeError):
        return False


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(conn: psycopg.Connection, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=SESSION_TTL_DAYS)
    conn.execute(
        "INSERT INTO sessions (id, user_id, token_hash, created_at, expires_at) VALUES (%s, %s, %s, %s, %s)",
        (secrets.token_hex(16), user_id, _hash_token(token), now.isoformat(), expires.isoformat()),
    )
    return token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_TTL_DAYS * 24 * 3600,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def delete_session(conn: psycopg.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token_hash = %s", (_hash_token(token),))


def get_user_by_session_token(conn: psycopg.Connection, token: str) -> dict | None:
    row = conn.execute(
        """
        SELECT u.* FROM users u
        JOIN sessions s ON s.user_id = u.id
        WHERE s.token_hash = %s AND s.expires_at > %s
        """,
        (_hash_token(token), datetime.now(timezone.utc).isoformat()),
    ).fetchone()
    return row


def get_current_user(
    metis_session: str | None = Cookie(default=None),
    conn: psycopg.Connection = Depends(db_session),
) -> dict:
    """FastAPI dependency: 401s any request without a valid, unexpired session."""
    if not metis_session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = get_user_by_session_token(conn, metis_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return user


def get_optional_user(
    metis_session: str | None = Cookie(default=None),
    conn: psycopg.Connection = Depends(db_session),
) -> dict | None:
    if not metis_session:
        return None
    return get_user_by_session_token(conn, metis_session)
