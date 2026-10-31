import uuid
from datetime import datetime

import pytest
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import Settings, get_settings
from app.core.database import (
    create_database_engine,
    get_async_session_maker,
    get_db,
)
from app.models.base import Base, BaseModel, TenantScopedModel


# Concrete test models for testing the abstract base classes
class SampleItem(BaseModel):
    __tablename__ = "test_items"

    name: Mapped[str] = mapped_column(String(50), nullable=False)


class SampleTenantItem(TenantScopedModel):
    __tablename__ = "test_tenant_items"

    title: Mapped[str] = mapped_column(String(50), nullable=False)


def test_settings_loading():
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.APP_ENV in ["development", "test", "production"]
    assert "postgresql+psycopg" in settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL
    assert settings.REDIS_URL.startswith("redis://")
    assert settings.SESSION_SECRET is not None
    assert settings.AI_TIMEOUT_SECONDS == 15
    assert settings.AI_MAX_REQUESTS_PER_USER_PER_DAY == 20


def test_base_model_attributes():
    item = SampleItem(name="Test Item")
    assert item.name == "Test Item"
    assert hasattr(item, "id")
    assert hasattr(item, "created_at")
    assert hasattr(item, "updated_at")

    # Verify column definitions on SampleItem
    table = SampleItem.__table__
    assert "id" in table.c
    assert table.c.id.primary_key is True
    assert "created_at" in table.c
    assert table.c.created_at.nullable is False
    assert "updated_at" in table.c
    assert table.c.updated_at.nullable is False


def test_tenant_scoped_model_attributes():
    tenant_id = uuid.uuid4()
    item = SampleTenantItem(title="Tenant Resource", tenant_id=tenant_id)
    assert item.title == "Tenant Resource"
    assert item.tenant_id == tenant_id

    # Verify column definitions on SampleTenantItem
    table = SampleTenantItem.__table__
    assert "id" in table.c
    assert "tenant_id" in table.c
    assert table.c.tenant_id.nullable is False
    assert table.c.tenant_id.index is True
    assert "version" in table.c
    assert table.c.version.nullable is False
    assert table.c.version.default.arg == 1 or table.c.version.server_default is not None


@pytest.mark.asyncio
async def test_async_database_lifecycle():
    # Use SQLite in-memory for testing the async database operations
    engine = create_database_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = get_async_session_maker(engine)
    async with session_maker() as session:
        t_id = uuid.uuid4()
        item = SampleTenantItem(title="Saved Item", tenant_id=t_id)
        session.add(item)
        await session.commit()
        await session.refresh(item)

        assert item.id is not None
        assert isinstance(item.id, uuid.UUID)
        assert item.tenant_id == t_id
        assert item.version == 1
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)

        # Query back
        stmt = select(SampleTenantItem).where(SampleTenantItem.tenant_id == t_id)
        result = await session.execute(stmt)
        queried = result.scalar_one()
        assert queried.title == "Saved Item"

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_db_generator():
    db_gen = get_db()
    session = await anext(db_gen)
    assert isinstance(session, AsyncSession)
    try:
        await anext(db_gen)
    except StopAsyncIteration:
        pass


@pytest.mark.asyncio
async def test_alembic_configuration_and_check():
    import os

    from alembic.config import Config

    from alembic import command

    ini_path = "backend/alembic.ini" if os.path.exists("backend/alembic.ini") else "alembic.ini"
    assert os.path.exists(ini_path), f"alembic.ini not found at {ini_path}"

    test_db = "test_alembic_check.db"
    db_url = f"sqlite+aiosqlite:///{test_db}"

    test_engine = create_database_engine(db_url)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await test_engine.dispose()

    try:
        cfg = Config(ini_path)
        cfg.set_main_option("sqlalchemy.url", db_url)
        # Verify alembic check runs cleanly and detects target_metadata matches database
        command.check(cfg)
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)
