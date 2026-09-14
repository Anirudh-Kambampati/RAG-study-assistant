import re
import uuid
from datetime import datetime, timezone

import psycopg
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, field_validator

from auth import (
    create_session,
    delete_session,
    get_current_user,
    hash_password,
    set_session_cookie,
    clear_session_cookie,
    verify_password,
)
from db import db_session

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not (1 <= len(v) <= 100):
            raise ValueError("Name must be between 1 and 100 characters")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def password_strong_enough(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str


def _user_out(row: dict) -> UserOut:
    return UserOut(id=row["id"], name=row["name"], email=row["email"])


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(body: SignupRequest, response: Response, conn: psycopg.Connection = Depends(db_session)):
    existing = conn.execute("SELECT id FROM users WHERE email = %s", (body.email,)).fetchone()
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (id, name, email, password_hash, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, body.name, body.email, hash_password(body.password), now, now),
    )
    token = create_session(conn, user_id)
    set_session_cookie(response, token)
    return UserOut(id=user_id, name=body.name, email=body.email)


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, conn: psycopg.Connection = Depends(db_session)):
    email = body.email.strip().lower()
    row = conn.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_session(conn, row["id"])
    set_session_cookie(response, token)
    return _user_out(row)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    metis_session: str | None = Cookie(default=None),
    conn: psycopg.Connection = Depends(db_session),
):
    if metis_session:
        delete_session(conn, metis_session)
    clear_session_cookie(response)


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return _user_out(user)
