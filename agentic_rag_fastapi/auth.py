"""
auth.py — JWT Authentication module for Agentic RAG API.

Provides:
- Token creation (HS256 JWT)
- Token verification dependency
- Demo user store (swap for DB in production)

Usage:
    POST /auth/token with form data: username=admin&password=...
    → returns {"access_token": "<jwt>", "token_type": "bearer"}

    Protected routes use: Depends(get_current_user)
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import os
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger("agentic_rag.auth")

# ── Config ────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme-use-a-real-secret-in-production-32chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 hours for demo

# ── Password hashing ─────────────────────────────────────────
# Using pbkdf2_sha256 to avoid passlib+bcrypt version incompatibility.
# In production, pin bcrypt==4.0.1 or switch to argon2-cffi for maximum security.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ── OAuth2 scheme (Bearer token in Authorization header) ─────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# ── Demo user store ───────────────────────────────────────────
# In production: replace with DB lookup.
# Password is hashed with bcrypt. Default: admin / demo-rag-2026
_DEMO_PASSWORD_HASH = pwd_context.hash("demo-rag-2026")

USERS_DB: dict[str, dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "hashed_password": _DEMO_PASSWORD_HASH,
        "role": "admin",
    },
}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    user = USERS_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict[str, Any]:
    """
    FastAPI dependency: extracts and validates the JWT from the Authorization header.
    Falls back to X-API-Key compatibility mode if no Bearer token is present
    (preserves backwards compat with existing demo-rag-2026 key).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in at /auth/token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = USERS_DB.get(username)
    if user is None:
        raise credentials_exception

    return user
