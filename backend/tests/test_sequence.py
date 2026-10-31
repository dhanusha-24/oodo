import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.auth import Membership, Tenant, User, UserRole
from app.models.base import Base
from app.services.sequence_service import SequenceService


@pytest.fixture
async def test_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_engine_maker():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        connect_args={"timeout": 30.0},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    yield engine, session_maker

    await engine.dispose()


@pytest.fixture
async def client(test_session: AsyncSession):
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def seed_data(test_session: AsyncSession):
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Apex Enterprise",
        timezone="Asia/Kolkata",
        base_currency="INR",
        settings_json={"default_payment_terms_days": 14, "invoice_numbering_prefix": "INV"},
    )
    test_session.add(tenant)

    pwd = hash_password("Password123!")
    user_owner = User(
        id=uuid.uuid4(),
        email="owner@apex.io",
        password_hash=pwd,
        full_name="Owner User",
        is_active=True,
    )
    user_sales = User(
        id=uuid.uuid4(),
        email="sales@apex.io",
        password_hash=pwd,
        full_name="Sales User",
        is_active=True,
    )
    user_analyst = User(
        id=uuid.uuid4(),
        email="analyst@apex.io",
        password_hash=pwd,
        full_name="Analyst User",
        is_active=True,
    )
    test_session.add_all([user_owner, user_sales, user_analyst])
    await test_session.flush()

    m_owner = Membership(
        tenant_id=tenant.id,
        user_id=user_owner.id,
        role=UserRole.TENANT_OWNER,
        status="ACTIVE",
    )
    m_sales = Membership(
        tenant_id=tenant.id,
        user_id=user_sales.id,
        role=UserRole.SALES_MANAGER,
        status="ACTIVE",
    )
    m_analyst = Membership(
        tenant_id=tenant.id,
        user_id=user_analyst.id,
        role=UserRole.ANALYST,
        status="ACTIVE",
    )
    test_session.add_all([m_owner, m_sales, m_analyst])
    await test_session.commit()

    return {
        "tenant": tenant,
        "user_owner": user_owner,
        "user_sales": user_sales,
        "user_analyst": user_analyst,
    }


def test_fiscal_year_calculation():
    # April starts new FY
    apr = datetime(2026, 4, 1, 0, 0, 0, tzinfo=UTC)
    assert SequenceService.calculate_fiscal_year(apr) == "2026-27"

    # October middle of FY
    oct_dt = datetime(2026, 10, 31, 12, 0, 0, tzinfo=UTC)
    assert SequenceService.calculate_fiscal_year(oct_dt) == "2026-27"

    # December end of calendar year
    dec = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
    assert SequenceService.calculate_fiscal_year(dec) == "2026-27"

    # January belongs to same FY
    jan = datetime(2027, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert SequenceService.calculate_fiscal_year(jan) == "2026-27"

    # March belongs to same FY
    mar = datetime(2027, 3, 31, 23, 59, 59, tzinfo=UTC)
    assert SequenceService.calculate_fiscal_year(mar) == "2026-27"

    # Prior March belongs to previous FY
    prior_mar = datetime(2026, 3, 31, 23, 59, 59, tzinfo=UTC)
    assert SequenceService.calculate_fiscal_year(prior_mar) == "2025-26"


@pytest.mark.asyncio
async def test_sequential_generation(test_session: AsyncSession, seed_data: dict):
    tenant = seed_data["tenant"]

    # 1. Generate 3 invoice sequence numbers sequentially
    inv1 = await SequenceService.get_next_number(test_session, tenant.id, "INVOICE", "2026-27")
    inv2 = await SequenceService.get_next_number(test_session, tenant.id, "INVOICE", "2026-27")
    inv3 = await SequenceService.get_next_number(test_session, tenant.id, "INVOICE", "2026-27")

    assert inv1 == "INV-2026-27-000001"
    assert inv2 == "INV-2026-27-000002"
    assert inv3 == "INV-2026-27-000003"

    # 2. Quotes and Credit Notes should have independent counters
    qt1 = await SequenceService.get_next_number(test_session, tenant.id, "QUOTE", "2026-27")
    cn1 = await SequenceService.get_next_number(test_session, tenant.id, "CREDIT_NOTE", "2026-27")

    assert qt1 == "QT-2026-27-000001"
    assert cn1 == "CN-2026-27-000001"

    # 3. Next invoice continues from 000004
    inv4 = await SequenceService.get_next_number(test_session, tenant.id, "INVOICE", "2026-27")
    assert inv4 == "INV-2026-27-000004"


@pytest.mark.asyncio
async def test_concurrency_sequence_generation(test_engine_maker):
    import asyncio

    _engine, session_maker = test_engine_maker

    # Seed a tenant in the database
    t_id = uuid.uuid4()
    async with session_maker() as session:
        tenant = Tenant(
            id=t_id,
            name="Concurrent Tenant",
            timezone="Asia/Kolkata",
            base_currency="INR",
            settings_json={},
        )
        session.add(tenant)
        await session.commit()

    total_tasks = 25

    async def generate_worker(worker_idx: int) -> str:
        async with session_maker() as session:
            return await SequenceService.get_next_number(session, t_id, "INVOICE", "2026-27")

    # Run 25 parallel coroutines concurrently
    results = await asyncio.gather(*(generate_worker(i) for i in range(total_tasks)))

    # Verify count and uniqueness
    assert len(results) == total_tasks
    assert len(set(results)) == total_tasks, (
        "Duplicate sequence numbers detected under concurrency!"
    )

    # Verify exact continuous sequential progression 1..25
    expected = [f"INV-2026-27-{i:06d}" for i in range(1, total_tasks + 1)]
    assert sorted(results) == expected


@pytest.mark.asyncio
async def test_get_settings_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_settings_authenticated(client: AsyncClient, seed_data: dict):
    # Log in as owner
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@apex.io", "password": "Password123!"},
    )
    assert login_res.status_code == 200

    # Get settings
    response = await client.get("/api/v1/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "Asia/Kolkata"
    assert data["currency"] == "INR"
    assert data["default_payment_terms_days"] == 14
    assert data["invoice_numbering_prefix"] == "INV"


@pytest.mark.asyncio
async def test_patch_settings_role_guard(client: AsyncClient, seed_data: dict):
    # 1. Sales Manager should be forbidden (403)
    login_sales = await client.post(
        "/api/v1/auth/login",
        json={"email": "sales@apex.io", "password": "Password123!"},
    )
    assert login_sales.status_code == 200

    sales_patch = await client.patch(
        "/api/v1/settings",
        json={"default_payment_terms_days": 30},
    )
    assert sales_patch.status_code == 403

    # 2. Analyst should be forbidden (403)
    login_analyst = await client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@apex.io", "password": "Password123!"},
    )
    assert login_analyst.status_code == 200

    analyst_patch = await client.patch(
        "/api/v1/settings",
        json={"default_payment_terms_days": 30},
    )
    assert analyst_patch.status_code == 403

    # 3. Tenant Owner should succeed (200)
    login_owner = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@apex.io", "password": "Password123!"},
    )
    assert login_owner.status_code == 200

    owner_patch = await client.patch(
        "/api/v1/settings",
        json={
            "timezone": "America/New_York",
            "currency": "USD",
            "default_payment_terms_days": 30,
            "invoice_numbering_prefix": "APEX-INV",
        },
    )
    assert owner_patch.status_code == 200
    updated_data = owner_patch.json()
    assert updated_data["timezone"] == "America/New_York"
    assert updated_data["currency"] == "USD"
    assert updated_data["default_payment_terms_days"] == 30
    assert updated_data["invoice_numbering_prefix"] == "APEX-INV"


@pytest.mark.asyncio
async def test_patch_settings_updates_subsequent_sequence(
    client: AsyncClient, test_session: AsyncSession, seed_data: dict
):
    tenant = seed_data["tenant"]

    # Log in as owner
    await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@apex.io", "password": "Password123!"},
    )

    # Update invoice prefix to BILL
    patch_res = await client.patch(
        "/api/v1/settings",
        json={"invoice_numbering_prefix": "BILL"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["invoice_numbering_prefix"] == "BILL"

    # Generate next number - should use updated prefix BILL
    next_num = await SequenceService.get_next_number(test_session, tenant.id, "INVOICE", "2026-27")
    assert next_num.startswith("BILL-2026-27-000001")
