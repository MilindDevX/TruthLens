"""
Async SQLAlchemy database engine and session management.
Provides session dependency for FastAPI routes.

Supports both PostgreSQL (production) and SQLite (development):
- PostgreSQL: uses asyncpg driver with connection pooling
- SQLite: uses aiosqlite driver, no pooling
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


# Detect database type for engine configuration
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Engine kwargs differ by database type
_engine_kwargs = {}
if not _is_sqlite:
    # PostgreSQL: connection pooling (configurable)
    _engine_kwargs = {
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_pre_ping": True,
    }
else:
    # SQLite: no pooling, enable WAL mode via connect_args
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
    }

# Async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    **_engine_kwargs,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields an async database session.
    Automatically closes the session after the request.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables. Used at application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose engine connections. Used at application shutdown."""
    await engine.dispose()
