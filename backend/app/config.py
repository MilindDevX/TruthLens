"""
Application configuration using Pydantic BaseSettings.
All secrets loaded from environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Central configuration for TruthLens X backend.
    Values are loaded from environment variables, with defaults for development.
    """

    # ─── Application ───
    APP_NAME: str = "TruthLens X"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="'development' or 'production'")
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # ─── Database ───
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./truthlens_dev.db",
        description="Async database connection string (SQLite for dev, PostgreSQL for prod)"
    )
    DATABASE_URL_SYNC: str = Field(
        default="sqlite:///./truthlens_dev.db",
        description="Sync connection string (for Alembic)"
    )

    # ─── JWT Auth ───
    JWT_SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND",
        description="Secret key for JWT encoding. Generate with: openssl rand -hex 32"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── Google OAuth ───
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ─── Rate Limiting ───
    RATE_LIMIT_PER_MINUTE: int = 60

    # ─── File Upload ───
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_FORMATS: list[str] = ["image/jpeg", "image/png", "image/webp"]
    MAX_TEXT_WORDS: int = 5000
    MAX_TEXT_CHARS: int = 30000

    # ─── ML Models ───
    MODELS_DIR: str = Field(
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models"),
        description="Root directory for versioned model storage"
    )
    ACTIVE_TEXT_MODEL_VERSION: str = "v1.0.0"
    ACTIVE_IMAGE_MODEL_VERSION: str = "v1.0.0"

    # ─── Logging ───
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ─── Database Pool (PostgreSQL only) ───
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ─── CORS ───
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton instance
settings = Settings()
