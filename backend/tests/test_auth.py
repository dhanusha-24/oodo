import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import (
    TenantUserContext,
    require_roles,
)
from app.core.database import get_db
from app.core.security import (
    generate_csrf_token,
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_csrf_token,
    verify_password,
)
from app.main import app
from app.models.auth import Membership, Tenant, User, UserRole
from app.models.base import Base


# Setup in-memory SQLite database for authentication tests
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
    # Create Tenant 1
    tenant1 = Tenant(
        id=uuid.uuid4(),
        name="Acme Corp",
        timezone="Asia/Kolkata",
        base_currency="INR",
        settings_json={"tax_inclusive": False},
    )
    # Create Tenant 2
    tenant2 = Tenant(
        id=uuid.uuid4(),
        name="Beta LLC",
        timezone="America/New_York",
        base_currency="USD",
        settings_json={},
    )
    test_session.add_all([tenant1, tenant2])

    # Create Owner User
    hashed_pwd = hash_password("SecurePassword123!")
    user_owner = User(
        id=uuid.uuid4(),
        email="owner@acme.com",
        password_hash=hashed_pwd,
        full_name="Alice Owner",
        is_active=True,
    )

    # Create Sales User
    user_sales = User(
        id=uuid.uuid4(),
        email="sales@acme.com",
        password_hash=hashed_pwd,
        full_name="Bob Sales",
        is_active=True,
    )

    # Create Inactive User
    user_inactive = User(
        id=uuid.uuid4(),
        email="inactive@acme.com",
        password_hash=hashed_pwd,
        full_name="Inactive User",
        is_active=False,
    )

    test_session.add_all([user_owner, user_sales, user_inactive])
    await test_session.flush()

    # Memberships: Alice is TENANT_OWNER in Acme Corp and ANALYST in Beta LLC
    m1 = Membership(
        tenant_id=tenant1.id,
        user_id=user_owner.id,
        role=UserRole.TENANT_OWNER,
        status="ACTIVE",
    )
    m2 = Membership(
        tenant_id=tenant2.id,
        user_id=user_owner.id,
        role=UserRole.ANALYST,
        status="ACTIVE",
    )
    # Bob is SALES_MANAGER in Acme Corp
    m3 = Membership(
        tenant_id=tenant1.id,
        user_id=user_sales.id,
        role=UserRole.SALES_MANAGER,
        status="ACTIVE",
    )

    test_session.add_all([m1, m2, m3])
    await test_session.commit()

    return {
        "tenant1": tenant1,
        "tenant2": tenant2,
        "user_owner": user_owner,
        "user_sales": user_sales,
        "user_inactive": user_inactive,
    }


# Unit tests for security utilities
def test_argon2_password_hashing():
    pwd = "CorrectHorseBatteryStaple!"
    hashed = hash_password(pwd)
    assert hashed.startswith("$argon2id$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_session_token_generation_and_hashing():
    raw_token = generate_session_token()
    assert len(raw_token) >= 32
    token_hash = hash_session_token(raw_token)
    assert len(token_hash) == 64  # SHA-256 hex string
    # Deterministic hashing
    assert hash_session_token(raw_token) == token_hash


def test_csrf_token_generation_and_verification():
    csrf_token = generate_csrf_token()
    assert len(csrf_token) >= 32
    assert verify_csrf_token(csrf_token, csrf_token) is True
    assert verify_csrf_token(csrf_token, "invalid_csrf_token") is False


# API Integration Tests
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seed_data: dict):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@acme.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["user"]["email"] == "owner@acme.com"
    assert data["user"]["full_name"] == "Alice Owner"
    assert data["active_tenant_id"] == str(seed_data["tenant1"].id)
    assert len(data["memberships"]) == 2
    assert "csrf_token" in data
    assert "session_token" in data

    # Check HttpOnly cookie set
    cookies = response.cookies
    assert "session_token" in cookies
    # Check CSRF header
    assert "X-CSRF-Token" in response.headers


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, seed_data: dict):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@acme.com",
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, seed_data: dict):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@acme.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient, seed_data: dict):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@acme.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_with_cookie_and_bearer(client: AsyncClient, seed_data: dict):
    # Login first
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@acme.com",
            "password": "SecurePassword123!",
        },
    )
    assert login_res.status_code == 200
    token = login_res.json()["session_token"]

    # Access /auth/me with Cookie
    client.cookies.set("session_token", token)
    me_res_cookie = await client.get("/api/v1/auth/me")
    assert me_res_cookie.status_code == 200
    me_data = me_res_cookie.json()
    assert me_data["user"]["email"] == "owner@acme.com"
    assert me_data["active_tenant"]["name"] == "Acme Corp"
    assert me_data["active_tenant"]["base_currency"] == "INR"

    # Access /auth/me with Bearer token
    client.cookies.clear()
    me_res_bearer = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res_bearer.status_code == 200
    assert me_res_bearer.json()["user"]["email"] == "owner@acme.com"


@pytest.mark.asyncio
async def test_auth_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_switch_tenant(client: AsyncClient, seed_data: dict):
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@acme.com",
            "password": "SecurePassword123!",
        },
    )
    token = login_res.json()["session_token"]
    tenant2_id = str(seed_data["tenant2"].id)

    # Switch to Beta LLC
    switch_res = await client.post(
        "/api/v1/auth/switch-tenant",
        headers={"Authorization": f"Bearer {token}"},
        json={"tenant_id": tenant2_id},
    )
    assert switch_res.status_code == 200
    data = switch_res.json()
    assert data["active_tenant"]["id"] == tenant2_id
    assert data["active_tenant"]["name"] == "Beta LLC"
    assert data["membership"]["role"] == "ANALYST"

    # Verify /me now reflects Beta LLC
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["active_tenant"]["id"] == tenant2_id


@pytest.mark.asyncio
async def test_switch_tenant_unauthorized_tenant(client: AsyncClient, seed_data: dict):
    # Bob (sales@acme.com) only belongs to Tenant 1
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "sales@acme.com",
            "password": "SecurePassword123!",
        },
    )
    token = login_res.json()["session_token"]
    tenant2_id = str(seed_data["tenant2"].id)

    # Bob tries to switch to Beta LLC (where he is NOT a member)
    switch_res = await client.post(
        "/api/v1/auth/switch-tenant",
        headers={"Authorization": f"Bearer {token}"},
        json={"tenant_id": tenant2_id},
    )
    assert switch_res.status_code == 403


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, seed_data: dict):
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@acme.com",
            "password": "SecurePassword123!",
        },
    )
    token = login_res.json()["session_token"]

    # Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200

    # Token should now be revoked
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_role_guard_enforcement(
    client: AsyncClient, seed_data: dict, test_session: AsyncSession
):
    # Add a temporary test route to app to test require_roles
    from fastapi import Depends

    @app.get("/api/v1/test-owner-only")
    async def owner_only_route(
        ctx: TenantUserContext = Depends(require_roles(UserRole.TENANT_OWNER)),
    ):
        return {"status": "ok", "user": ctx.user.email}

    # Login as Bob (SALES_MANAGER, not TENANT_OWNER)
    sales_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "sales@acme.com",
            "password": "SecurePassword123!",
        },
    )
    sales_token = sales_login.json()["session_token"]

    # Bob tries to access owner route -> 403
    forbidden_res = await client.get(
        "/api/v1/test-owner-only",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert forbidden_res.status_code == 403

    # Login as Alice (TENANT_OWNER)
    owner_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@acme.com",
            "password": "SecurePassword123!",
        },
    )
    owner_token = owner_login.json()["session_token"]

    # Alice accesses owner route -> 200
    allowed_res = await client.get(
        "/api/v1/test-owner-only",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert allowed_res.status_code == 200
    assert allowed_res.json()["status"] == "ok"
