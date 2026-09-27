"""Auth utilities for password hashing, JWT sessions, RBAC, and tenancy."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request

JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "careeros")
ACCESS_TOKEN_DAYS = int(os.environ.get("ACCESS_TOKEN_DAYS", "7"))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    user: dict,
    *,
    jwt_id: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> tuple[str, str, datetime]:
    """Create a signed JWT and return token, JWT id, and expiration."""
    jti = jwt_id or f"jwt_{uuid.uuid4().hex}"
    exp = expires_at or (utc_now() + timedelta(days=ACCESS_TOKEN_DAYS))
    payload = {
        "iss": JWT_ISSUER,
        "sub": user["user_id"],
        "jti": jti,
        "role": user.get("role"),
        "institution_id": user.get("institution_id"),
        "approved": bool(user.get("approved", False)),
        "iat": int(utc_now().timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), jti, exp


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(401, "Session expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, "Invalid session") from exc


def extract_auth_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.cookies.get("session_token")


async def get_session_user(request: Request):
    """Local import to avoid circular import with server.py."""
    from server import db

    token = extract_auth_token(request)
    if not token:
        raise HTTPException(401, "Not authenticated")

    claims: Optional[dict] = None
    session_query = {"session_token": token}
    if token.count(".") == 2:
        claims = decode_access_token(token)
        session_query = {"jwt_id": claims["jti"]}

    sess = await db.user_sessions.find_one(session_query, {"_id": 0})
    if not sess and not claims:
        raise HTTPException(401, "Invalid session")

    if sess:
        expires_at = sess["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < utc_now():
            raise HTTPException(401, "Session expired")

    user_id = claims["sub"] if claims else sess["user_id"]
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(401, "User not found")
    return user


def require_roles(*roles: str):
    async def _dep(user=Depends(get_session_user)):
        if user["role"] not in roles:
            raise HTTPException(403, f"Forbidden - requires {','.join(roles)}")
        if user["role"] not in ("super_admin",) and not user.get("approved", False):
            raise HTTPException(403, "Account pending approval")
        return user

    return _dep


def require_same_institution(target_institution_id: Optional[str], user: dict) -> None:
    if user["role"] == "super_admin":
        return
    if target_institution_id and target_institution_id != user.get("institution_id"):
        raise HTTPException(403, "Cross-institution access denied")
