"""
Auth service: JWT creation/verification, password hashing, refresh token management.

Security design:
- Access tokens: 15-minute expiry, stateless JWT
- Refresh tokens: 7-day expiry, stored as SHA-256 hash in DB
- Refresh token rotation: old token revoked on each refresh
- Reuse detection: if a rotated-out token is reused, revoke ALL tokens for that user
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import settings
from app.auth.models import RefreshToken

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, role: str) -> str:
    """
    Create a short-lived JWT access token.

    Payload contains user_id (sub) and role for RBAC.
    Expiry: 15 minutes (configurable).
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    Raises JWTError on invalid/expired tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise JWTError("Invalid token type")
        return payload
    except JWTError:
        raise


def _hash_token(token: str) -> str:
    """SHA-256 hash a refresh token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token() -> str:
    """Generate a cryptographically secure refresh token."""
    return secrets.token_urlsafe(64)


async def create_refresh_token_record(
    db: AsyncSession,
    user_id: uuid.UUID,
    device_info: Optional[str] = None,
) -> str:
    """
    Generate a new refresh token and store its hash in DB.

    Returns the raw token (to be sent to client once, never stored server-side).
    """
    raw_token = generate_refresh_token()
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    record = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        device_info=device_info,
        expires_at=expires_at,
    )
    db.add(record)
    await db.flush()

    return raw_token


async def rotate_refresh_token(
    db: AsyncSession,
    raw_old_token: str,
    device_info: Optional[str] = None,
) -> tuple[str, uuid.UUID]:
    """
    Rotate a refresh token: revoke the old one and issue a new one.

    Implements reuse detection:
    - If the incoming token hash matches a REVOKED token, that means
      an attacker is replaying a stolen token. We revoke ALL tokens
      for that user (token family compromise).

    Returns: (new_raw_token, user_id)
    Raises: ValueError on invalid/expired/revoked token
    """
    old_hash = _hash_token(raw_old_token)

    # Look up the token by hash
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == old_hash)
    )
    token_record = result.scalar_one_or_none()

    if token_record is None:
        raise ValueError("Invalid refresh token")

    # REUSE DETECTION: if this token was already revoked, it's been replayed
    if token_record.revoked:
        # Compromise detected — revoke ALL tokens for this user
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == token_record.user_id)
            .values(revoked=True, reuse_detected=True)
        )
        await db.flush()
        raise ValueError("Refresh token reuse detected. All sessions revoked for security.")

    if token_record.is_expired():
        raise ValueError("Refresh token expired")

    # Revoke the old token
    token_record.revoked = True
    await db.flush()

    # Issue a new token
    new_raw_token = await create_refresh_token_record(
        db, token_record.user_id, device_info
    )

    return new_raw_token, token_record.user_id


async def revoke_all_user_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Revoke all refresh tokens for a user (e.g., on password change or logout-all)."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .values(revoked=True)
    )
    await db.flush()
