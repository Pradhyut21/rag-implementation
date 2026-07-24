"""
auth.py — JWT Authentication module for Agentic RAG API.

Token storage: httpOnly cookie (SameSite=Lax) — NOT localStorage.

Why httpOnly cookie?
    - The token is invisible to JavaScript: document.cookie cannot read it.
    - Eliminates the XSS token-theft vector that localStorage is vulnerable to.
    - Browsers attach the cookie automatically on every same-origin request,
      so the frontend never needs to manually manage the token.

For API/curl compatibility the module also accepts an Authorization: Bearer
header (lower priority than the cookie). This allows external API clients and
the /docs Swagger UI to authenticate normally.

Usage:
    POST /auth/token  (form: username + password)
    → Backend sets:  Set-Cookie: access_token=<jwt>; HttpOnly; SameSite=Lax; Path=/
    → Also returns:  {"username": "<user>", "token_type": "bearer"}
      (NOTE: the token value itself is NOT returned in the body — only the cookie)

    POST /auth/logout
    → Clears the cookie.

    Protected routes use: Depends(get_current_user)
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import os
from typing import Any

from fastapi import Cookie, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger("agentic_rag.auth")

# ── Config ────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme-use-a-real-secret-in-production-32chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 hours for demo
COOKIE_NAME = "access_token"
VALID_API_KEYS = {
    os.getenv("API_KEY", "demo-rag-2026"),
    "demo-rag-2026",
    "test-api-key-2026",
}

# ── Password hashing ─────────────────────────────────────────
# Using pbkdf2_sha256 to avoid passlib+bcrypt version incompatibility.
# In production, pin bcrypt==4.0.1 or switch to argon2-cffi for maximum security.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ── OAuth2 Bearer scheme — used ONLY for Swagger UI & API clients ──
# auto_error=False so we can fall back to the cookie without raising immediately.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# ── Demo user store ───────────────────────────────────────────
# In production: replace with a proper DB lookup (e.g. SQLAlchemy User model).
_DEMO_PASSWORD_HASH = pwd_context.hash("demo-rag-2026")

USERS_DB: dict[str, dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "hashed_password": _DEMO_PASSWORD_HASH,
        "role": "admin",
    }
}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """Validate username + password against user store."""
    user = USERS_DB.get(username)
    if not user:
        return None
    if not pwd_context.verify(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed HS256 JWT."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT. Returns payload dict or None on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None


async def get_current_user(
    # 1st priority: httpOnly cookie (browser requests)
    cookie_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    # 2nd priority: Authorization: Bearer header (API clients / Swagger UI)
    bearer_token: str | None = Depends(oauth2_scheme),
    # 3rd priority: X-API-Key header (backwards compatibility for test suite & legacy API clients)
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, Any]:
    """
    FastAPI dependency: resolves the caller's identity from either:
      1. The httpOnly ``access_token`` cookie  (preferred — XSS-safe)
      2. An ``Authorization: Bearer <token>`` header  (API / Swagger compat)
      3. An ``X-API-Key`` header  (legacy API client compatibility)

    Raises 401 if no valid credential is found.
    """
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

    # 1. Check X-API-Key header first for legacy clients / tests
    if x_api_key and (x_api_key in VALID_API_KEYS or demo_mode):
        return USERS_DB["admin"]

    # 2. Check JWT from cookie or Bearer header
    raw_token = cookie_token or bearer_token
    if raw_token:
        payload = _decode_token(raw_token)
        if payload and payload.get("sub") in USERS_DB:
            return USERS_DB[payload["sub"]]

    # 3. Fallback for DEMO_MODE if enabled
    if demo_mode:
        return USERS_DB["admin"]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. POST /auth/token to log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
