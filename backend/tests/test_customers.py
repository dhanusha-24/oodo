import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.auth import Membership, Tenant, User, UserRole
from app.models.base import Base


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
    # Tenant A
    tenant_a = Tenant(
        id=uuid.uuid4(),
        name="Apex Enterprise",
        timezone="Asia/Kolkata",
        base_currency="INR",
        settings_json={"default_payment_terms_days": 14, "invoice_numbering_prefix": "INV"},
    )
    # Tenant B
    tenant_b = Tenant(
        id=uuid.uuid4(),
        name="Beta Logistics",
        timezone="Asia/Kolkata",
        base_currency="INR",
        settings_json={"default_payment_terms_days": 30, "invoice_numbering_prefix": "BETA"},
    )
    test_session.add_all([tenant_a, tenant_b])

    pwd = hash_password("Password123!")

    # Users in Tenant A
    user_owner_a = User(
        id=uuid.uuid4(),
        email="owner_a@apex.io",
        password_hash=pwd,
        full_name="Owner A",
        is_active=True,
    )
    user_sales_a = User(
        id=uuid.uuid4(),
        email="sales_a@apex.io",
        password_hash=pwd,
        full_name="Sales A",
        is_active=True,
    )
    user_billing_a = User(
        id=uuid.uuid4(),
        email="billing_a@apex.io",
        password_hash=pwd,
        full_name="Billing A",
        is_active=True,
    )
    user_analyst_a = User(
        id=uuid.uuid4(),
        email="analyst_a@apex.io",
        password_hash=pwd,
        full_name="Analyst A",
        is_active=True,
    )

    # Users in Tenant B
    user_owner_b = User(
        id=uuid.uuid4(),
        email="owner_b@beta.io",
        password_hash=pwd,
        full_name="Owner B",
        is_active=True,
    )
    user_sales_b = User(
        id=uuid.uuid4(),
        email="sales_b@beta.io",
        password_hash=pwd,
        full_name="Sales B",
        is_active=True,
    )

    test_session.add_all(
        [
            user_owner_a,
            user_sales_a,
            user_billing_a,
            user_analyst_a,
            user_owner_b,
            user_sales_b,
        ]
    )
    await test_session.flush()

    memberships = [
        Membership(
            tenant_id=tenant_a.id,
            user_id=user_owner_a.id,
            role=UserRole.TENANT_OWNER,
            status="ACTIVE",
        ),
        Membership(
            tenant_id=tenant_a.id,
            user_id=user_sales_a.id,
            role=UserRole.SALES_MANAGER,
            status="ACTIVE",
        ),
        Membership(
            tenant_id=tenant_a.id,
            user_id=user_billing_a.id,
            role=UserRole.BILLING_MANAGER,
            status="ACTIVE",
        ),
        Membership(
            tenant_id=tenant_a.id, user_id=user_analyst_a.id, role=UserRole.ANALYST, status="ACTIVE"
        ),
        Membership(
            tenant_id=tenant_b.id,
            user_id=user_owner_b.id,
            role=UserRole.TENANT_OWNER,
            status="ACTIVE",
        ),
        Membership(
            tenant_id=tenant_b.id,
            user_id=user_sales_b.id,
            role=UserRole.SALES_MANAGER,
            status="ACTIVE",
        ),
    ]
    test_session.add_all(memberships)
    await test_session.commit()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "owner_a": user_owner_a,
        "sales_a": user_sales_a,
        "billing_a": user_billing_a,
        "analyst_a": user_analyst_a,
        "owner_b": user_owner_b,
        "sales_b": user_sales_b,
    }


async def login(client: AsyncClient, email: str, password: str = "Password123!"):
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp


@pytest.mark.asyncio
async def test_create_customer_success(client: AsyncClient, seed_data: dict):
    await login(client, "sales_a@apex.io")

    payload = {
        "name": "Acme Global Solutions",
        "legal_name": "Acme Global Solutions Private Limited",
        "email": "finance@acmeglobal.com",
        "phone": "+919876543210",
        "billing_address_line1": "Level 4, Tech Park",
        "billing_address_line2": "Whitefield",
        "billing_city": "Bengaluru",
        "billing_state": "Karnataka",
        "billing_postal_code": "560066",
        "billing_country": "IN",
        "tax_id": "29ABCDE1234F1Z5",
        "currency_preference": "INR",
        "payment_terms_days": 30,
        "notes": "Key enterprise account",
        "external_id": "EXT-ACME-001",
        "contacts": [
            {
                "name": "Jane Doe",
                "email": "jane@acmeglobal.com",
                "phone": "+919876543211",
                "role": "VP Procurement",
                "is_primary": True,
            }
        ],
    }

    response = await client.post("/api/v1/customers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Global Solutions"
    assert data["legal_name"] == "Acme Global Solutions Private Limited"
    assert data["email"] == "finance@acmeglobal.com"
    assert data["billing_country"] == "IN"
    assert data["currency_preference"] == "INR"
    assert data["payment_terms_days"] == 30
    assert data["status"] == "ACTIVE"
    assert data["external_id"] == "EXT-ACME-001"
    assert data["tenant_id"] == str(seed_data["tenant_a"].id)
    assert "id" in data


@pytest.mark.asyncio
async def test_address_and_input_validation(client: AsyncClient, seed_data: dict):
    await login(client, "sales_a@apex.io")

    # Invalid email
    res1 = await client.post(
        "/api/v1/customers",
        json={"name": "Test Customer", "email": "invalid-email"},
    )
    assert res1.status_code == 422

    # Invalid country code (not 2 chars)
    res2 = await client.post(
        "/api/v1/customers",
        json={"name": "Test Customer", "billing_country": "INDIA"},
    )
    assert res2.status_code == 422

    # Invalid name (empty)
    res3 = await client.post(
        "/api/v1/customers",
        json={"name": ""},
    )
    assert res3.status_code == 422

    # Negative payment terms
    res4 = await client.post(
        "/api/v1/customers",
        json={"name": "Test Customer", "payment_terms_days": -5},
    )
    assert res4.status_code == 422


@pytest.mark.asyncio
async def test_unique_external_id_per_tenant(client: AsyncClient, seed_data: dict):
    # 1. Tenant A creates customer with external_id 'EXT-UNIQ-100'
    await login(client, "sales_a@apex.io")
    res1 = await client.post(
        "/api/v1/customers",
        json={"name": "Tenant A Customer 1", "external_id": "EXT-UNIQ-100"},
    )
    assert res1.status_code == 201

    # 2. Tenant A tries to create another customer with the SAME external_id -> 409 Conflict
    res2 = await client.post(
        "/api/v1/customers",
        json={"name": "Tenant A Customer 2", "external_id": "EXT-UNIQ-100"},
    )
    assert res2.status_code == 409

    # 3. Tenant B creates customer with the SAME external_id 'EXT-UNIQ-100' -> 201 (Tenant scoped)
    await login(client, "sales_b@beta.io")
    res3 = await client.post(
        "/api/v1/customers",
        json={"name": "Tenant B Customer 1", "external_id": "EXT-UNIQ-100"},
    )
    assert res3.status_code == 201


@pytest.mark.asyncio
async def test_strict_tenant_isolation(client: AsyncClient, seed_data: dict):
    # Tenant A creates customer
    await login(client, "sales_a@apex.io")
    res_a = await client.post(
        "/api/v1/customers",
        json={"name": "Tenant A Confidential Customer", "external_id": "EXT-ISO-A"},
    )
    assert res_a.status_code == 201
    cust_a_id = res_a.json()["id"]

    # Tenant B tries to access customer A via GET -> 404
    await login(client, "sales_b@beta.io")
    get_res = await client.get(f"/api/v1/customers/{cust_a_id}")
    assert get_res.status_code == 404

    # Tenant B tries to update customer A via PATCH -> 404
    patch_res = await client.patch(
        f"/api/v1/customers/{cust_a_id}",
        json={"name": "Attempted Hack"},
    )
    assert patch_res.status_code == 404

    # Tenant B tries to add contact to customer A via POST -> 404
    contact_res = await client.post(
        f"/api/v1/customers/{cust_a_id}/contacts",
        json={"name": "Intruder", "email": "intruder@beta.io"},
    )
    assert contact_res.status_code == 404

    # Tenant B listing does not include Customer A
    list_res = await client.get("/api/v1/customers")
    assert list_res.status_code == 200
    ids_in_b = [item["id"] for item in list_res.json()["items"]]
    assert cust_a_id not in ids_in_b


@pytest.mark.asyncio
async def test_pagination_default_and_cap(client: AsyncClient, seed_data: dict):
    await login(client, "sales_a@apex.io")

    # Create 30 customers
    for i in range(30):
        res = await client.post(
            "/api/v1/customers",
            json={"name": f"Customer Batch {i:02d}", "external_id": f"BATCH-{i:02d}"},
        )
        assert res.status_code == 201

    # Default pagination: page=1, limit=25
    res_default = await client.get("/api/v1/customers")
    assert res_default.status_code == 200
    data_default = res_default.json()
    assert len(data_default["items"]) == 25
    assert data_default["total"] == 30
    assert data_default["page"] == 1
    assert data_default["limit"] == 25
    assert data_default["total_pages"] == 2

    # Second page
    res_page2 = await client.get("/api/v1/customers?page=2")
    assert res_page2.status_code == 200
    data_page2 = res_page2.json()
    assert len(data_page2["items"]) == 5

    # Request limit exceeding 100 should cap at 100
    res_cap = await client.get("/api/v1/customers?limit=150")
    assert res_cap.status_code == 200
    data_cap = res_cap.json()
    assert data_cap["limit"] == 100
    assert len(data_cap["items"]) == 30


@pytest.mark.asyncio
async def test_search_and_status_filter(client: AsyncClient, seed_data: dict):
    await login(client, "sales_a@apex.io")

    # Customer 1
    await client.post(
        "/api/v1/customers",
        json={"name": "Alpha Technologies", "email": "alpha@tech.com"},
    )
    # Customer 2
    await client.post(
        "/api/v1/customers",
        json={"name": "Omega Systems", "email": "info@omega.com"},
    )
    # Customer 3 (archived)
    c3 = await client.post(
        "/api/v1/customers",
        json={"name": "Zeta Corp", "email": "zeta@corp.com"},
    )
    c3_id = c3.json()["id"]
    await client.patch(f"/api/v1/customers/{c3_id}", json={"status": "ARCHIVED"})

    # Search by name
    res_search_name = await client.get("/api/v1/customers?search=Alpha")
    assert res_search_name.status_code == 200
    items = res_search_name.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Alpha Technologies"

    # Search by email
    res_search_email = await client.get("/api/v1/customers?search=omega.com")
    assert res_search_email.status_code == 200
    items_email = res_search_email.json()["items"]
    assert len(items_email) == 1
    assert items_email[0]["name"] == "Omega Systems"

    # Filter status ARCHIVED
    res_archived = await client.get("/api/v1/customers?status=ARCHIVED")
    assert res_archived.status_code == 200
    items_archived = res_archived.json()["items"]
    assert len(items_archived) == 1
    assert items_archived[0]["name"] == "Zeta Corp"

    # Filter status ACTIVE
    res_active = await client.get("/api/v1/customers?status=ACTIVE")
    assert res_active.status_code == 200
    items_active = res_active.json()["items"]
    names_active = [item["name"] for item in items_active]
    assert "Alpha Technologies" in names_active
    assert "Omega Systems" in names_active
    assert "Zeta Corp" not in names_active


@pytest.mark.asyncio
async def test_role_guard_enforcement(client: AsyncClient, seed_data: dict):
    # 1. Sales Manager can create customer -> 201
    await login(client, "sales_a@apex.io")
    r_sales = await client.post("/api/v1/customers", json={"name": "Cust Created By Sales"})
    assert r_sales.status_code == 201
    cust_id = r_sales.json()["id"]

    # 2. Billing Manager can create customer -> 201
    await login(client, "billing_a@apex.io")
    r_billing = await client.post("/api/v1/customers", json={"name": "Cust Created By Billing"})
    assert r_billing.status_code == 201

    # 3. Tenant Owner can create customer -> 201
    await login(client, "owner_a@apex.io")
    r_owner = await client.post("/api/v1/customers", json={"name": "Cust Created By Owner"})
    assert r_owner.status_code == 201

    # 4. Analyst CANNOT create customer -> 403 Forbidden
    await login(client, "analyst_a@apex.io")
    r_analyst_post = await client.post("/api/v1/customers", json={"name": "Forbidden Cust"})
    assert r_analyst_post.status_code == 403

    # 5. Analyst CANNOT edit customer -> 403 Forbidden
    r_analyst_patch = await client.patch(
        f"/api/v1/customers/{cust_id}", json={"name": "Hacked Name"}
    )
    assert r_analyst_patch.status_code == 403

    # 6. Analyst CANNOT add contact -> 403 Forbidden
    r_analyst_contact = await client.post(
        f"/api/v1/customers/{cust_id}/contacts",
        json={"name": "Forbidden Contact"},
    )
    assert r_analyst_contact.status_code == 403

    # 7. Analyst CAN read list and detail -> 200 OK
    r_analyst_list = await client.get("/api/v1/customers")
    assert r_analyst_list.status_code == 200

    r_analyst_detail = await client.get(f"/api/v1/customers/{cust_id}")
    assert r_analyst_detail.status_code == 200


@pytest.mark.asyncio
async def test_customer_detail_and_contacts(client: AsyncClient, seed_data: dict):
    await login(client, "sales_a@apex.io")

    # Create customer with initial contact
    create_res = await client.post(
        "/api/v1/customers",
        json={
            "name": "Acme Detailed",
            "contacts": [{"name": "Initial Contact", "email": "init@acme.com", "is_primary": True}],
        },
    )
    assert create_res.status_code == 201
    cust_id = create_res.json()["id"]

    # Add second contact via contacts endpoint
    contact_res = await client.post(
        f"/api/v1/customers/{cust_id}/contacts",
        json={
            "name": "Secondary Contact",
            "email": "sec@acme.com",
            "phone": "+919876543212",
            "role": "Billing Support",
            "is_primary": False,
        },
    )
    assert contact_res.status_code == 201
    contact_data = contact_res.json()
    assert contact_data["name"] == "Secondary Contact"
    assert contact_data["customer_id"] == cust_id

    # Get customer detail
    detail_res = await client.get(f"/api/v1/customers/{cust_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["name"] == "Acme Detailed"
    assert "contacts" in detail
    assert len(detail["contacts"]) == 2
    assert "outstanding_balance" in detail
    assert Decimal(str(detail["outstanding_balance"])) == Decimal("0.00")


@pytest.mark.asyncio
async def test_patch_customer_update(client: AsyncClient, seed_data: dict):
    await login(client, "sales_a@apex.io")

    res = await client.post(
        "/api/v1/customers",
        json={
            "name": "Original Name",
            "payment_terms_days": 14,
            "external_id": "EXT-ORIG",
        },
    )
    cust_id = res.json()["id"]
    version1 = res.json()["version"]

    # Update customer
    patch_res = await client.patch(
        f"/api/v1/customers/{cust_id}",
        json={
            "name": "Updated Name",
            "payment_terms_days": 45,
            "notes": "Updated notes",
        },
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["name"] == "Updated Name"
    assert updated["payment_terms_days"] == 45
    assert updated["notes"] == "Updated notes"
    assert updated["version"] > version1
