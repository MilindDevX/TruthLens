"""
Refresh token SQLAlchemy model.

Security features per approved review:
- Token stored as SHA-256 hash only (never plaintext)
- Device fingerprint for binding
- Reuse detection flag for token family compromise
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.database import Base


class RefreshToken(Base):
    """
    Refresh token model with security hardening.

    Key design decisions:
    - token_hash: We never store the raw token, only its SHA-256 hash.
      The raw token is returned to the client once, then forgotten.
    - device_info: Combines user-agent + IP for token binding. If a
      refresh request comes from a different device, we flag it.
    - reuse_detected: If a previously-rotated token is presented again,
      this flags the entire token family as compromised and revokes all.
    """
    __tablename__ = "refresh_tokens"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hex = 64 chars
    device_info = Column(String(512), nullable=True)  # user-agent + IP fingerprint
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    reuse_detected = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")

    def is_expired(self) -> bool:
        """Check if this token has expired (handles naive/aware datetime from SQLite)."""
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

    def is_valid(self) -> bool:
        """Token is valid only if not expired, not revoked, and no reuse detected."""
        return not self.is_expired() and not self.revoked and not self.reuse_detected

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"
