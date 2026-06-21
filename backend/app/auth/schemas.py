"""
Auth Pydantic schemas for login, registration, and token responses.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Email + password login."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    """User registration with email, password, and full name."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    """JWT token pair returned on successful auth."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class RefreshRequest(BaseModel):
    """Refresh token rotation request."""
    refresh_token: str


class GoogleAuthCallback(BaseModel):
    """Google OAuth callback data."""
    code: str
    state: Optional[str] = None
