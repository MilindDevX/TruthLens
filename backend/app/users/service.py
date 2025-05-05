"""
User CRUD service layer.
Routers call this service — never the DB directly.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.users.models import User, UserRole
from app.users.schemas import UserCreate
from app.auth.service import hash_password


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Look up a user by primary key."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_oauth(db: AsyncSession, provider: str, oauth_id: str) -> User | None:
    """Look up a user by OAuth provider and ID."""
    result = await db.execute(
        select(User).where(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id,
        )
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user with hashed password.
    Raises ValueError if email already exists.
    """
    existing = await get_user_by_email(db, user_data.email)
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.USER,
    )
    db.add(user)
    await db.flush()  # Get the generated ID without committing
    return user


async def create_oauth_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    provider: str,
    oauth_id: str,
) -> User:
    """
    Create a user from OAuth login.
    If a user with the same email already exists, link the OAuth provider.
    """
    existing = await get_user_by_email(db, email)
    if existing:
        # Link OAuth to existing account
        existing.oauth_provider = provider
        existing.oauth_id = oauth_id
        await db.flush()
        return existing

    user = User(
        email=email,
        full_name=full_name,
        role=UserRole.USER,
        oauth_provider=provider,
        oauth_id=oauth_id,
        password_hash=None,  # OAuth users have no password
    )
    db.add(user)
    await db.flush()
    return user
