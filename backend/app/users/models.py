"""
User SQLAlchemy ORM model.
Supports both email/password and OAuth-based users.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum as SAEnum, DateTime, Index, Uuid
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    User model supporting dual auth (email/password + OAuth).

    Design decisions:
    - password_hash is nullable to support OAuth-only users
    - oauth_provider + oauth_id enable linking multiple OAuth providers
    - role defaults to 'user' for RBAC enforcement
    """
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    oauth_provider = Column(String(50), nullable=True)  # e.g., "google"
    oauth_id = Column(String(255), nullable=True)  # Provider's unique user ID
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    analysis_history = relationship("AnalysisHistory", back_populates="user", lazy="dynamic")
    refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="dynamic")

    # Composite index for OAuth lookup
    __table_args__ = (
        Index("ix_users_oauth", "oauth_provider", "oauth_id", unique=True),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
