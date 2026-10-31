from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def create_database_engine(
    url: str | None = None,
    echo: bool | None = None,
) -> AsyncEngine:
    """Create and configure an asynchronous SQLAlchemy engine."""
    database_url = url or settings.DATABASE_URL
    is_echo = echo if echo is not None else settings.is_development

    engine_kwargs: dict[str, Any] = {
        "echo": is_echo,
        "future": True,
    }

    # SQLite (used in lightweight unit tests) does not support connection pool sizing
    if not database_url.startswith("sqlite"):
        engine_kwargs.update(
            {
                "pool_pre_ping": True,
                "pool_size": 20,
                "max_overflow": 10,
            }
        )

    return create_async_engine(database_url, **engine_kwargs)


# Application-wide engine instance
engine: AsyncEngine = create_database_engine()


def get_async_session_maker(
    engine_instance: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Create a configured async sessionmaker bound to the given or default engine."""
    return async_sessionmaker(
        bind=engine_instance or engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# Default session factory bound to the application engine
AsyncSessionLocal: async_sessionmaker[AsyncSession] = get_async_session_maker(engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
