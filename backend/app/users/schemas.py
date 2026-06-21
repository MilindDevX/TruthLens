"""
User Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Minimum 8 characters")
    full_name: str = Field(min_length=1, max_length=255)


class UserResponse(BaseModel):
    """Public user profile response. Never exposes password_hash."""
    id: UUID
    email: str
    full_name: str
    role: str
    oauth_provider: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for profile updates."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
