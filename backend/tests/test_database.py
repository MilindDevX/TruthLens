from app.database import _normalize_db_url


def test_normalizes_neon_sslmode_for_asyncpg():
    url = (
        "postgresql://user:password@host.neon.tech/neondb?"
        "sslmode=require&channel_binding=require"
    )

    assert _normalize_db_url(url) == (
        "postgresql+asyncpg://user:password@host.neon.tech/neondb?ssl=require"
    )
