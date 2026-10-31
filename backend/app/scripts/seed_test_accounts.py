import asyncio
import uuid
from decimal import Decimal
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.auth import Membership, Tenant, User, UserRole
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.tenant_sequence import TenantSequence


async def seed_additional_accounts():
    async with AsyncSessionLocal() as db:
        # 1. Fetch primary tenant (Acme)
        stmt = select(Tenant).where(Tenant.name.like("%Acme%"))
        acme_tenant = (await db.execute(stmt)).scalars().first()
        if not acme_tenant:
            print("Acme tenant not found! Please run main seed first.")
            return

        password = "SecurePassword123!"
        hashed_pwd = hash_password(password)

        acme_roles = [
            ("billing@acme.com", "Priya Nair (Billing Manager)", UserRole.BILLING_MANAGER),
            ("sales@acme.com", "Vikram Patel (Sales Director)", UserRole.SALES_MANAGER),
            ("analyst@acme.com", "Ananya Deshmukh (Financial Analyst)", UserRole.ANALYST),
        ]

        for email, name, role in acme_roles:
            stmt_user = select(User).where(User.email == email)
            existing = (await db.execute(stmt_user)).scalar_one_or_none()
            if not existing:
                user = User(
                    id=uuid.uuid4(),
                    email=email,
                    full_name=name,
                    password_hash=hashed_pwd,
                    is_active=True,
                )
                db.add(user)
                await db.flush()

                mem = Membership(
                    id=uuid.uuid4(),
                    tenant_id=acme_tenant.id,
                    user_id=user.id,
                    role=role,
                    status="ACTIVE",
                )
                db.add(mem)
                print(f"Created Acme account: {email} ({role})")
            else:
                print(f"Account {email} already exists.")

        # 2. Second Tenant for Multi-Tenancy Demonstration: Starlight Digital
        starlight_email = "admin@starlight.io"
        stmt_starlight = select(Tenant).where(Tenant.name.like("%Starlight%"))
        starlight_tenant = (await db.execute(stmt_starlight)).scalars().first()

        if not starlight_tenant:
            print("Creating second tenant: Starlight Digital Technologies...")
            starlight_tenant = Tenant(
                id=uuid.uuid4(),
                name="Starlight Digital Technologies",
                timezone="Asia/Kolkata",
                base_currency="INR",
                settings_json={"tax_id": "27AAACS9999Z1Z1", "invoice_prefix": "STA"},
            )
            db.add(starlight_tenant)
            await db.flush()

            # Sequence
            for doc_type, prefix in [("customer", "CUST"), ("subscription", "SUB"), ("invoice", "INV"), ("payment", "PAY")]:
                seq = TenantSequence(
                    tenant_id=starlight_tenant.id,
                    document_type=doc_type,
                    fiscal_year="2026-27",
                    prefix=prefix,
                    next_value=1,
                )
                db.add(seq)

            # Starlight Admin
            user2 = User(
                id=uuid.uuid4(),
                email=starlight_email,
                full_name="Karan Oberoi (Starlight Admin)",
                password_hash=hashed_pwd,
                is_active=True,
            )
            db.add(user2)
            await db.flush()

            mem2 = Membership(
                id=uuid.uuid4(),
                tenant_id=starlight_tenant.id,
                user_id=user2.id,
                role=UserRole.TENANT_OWNER,
                status="ACTIVE",
            )
            db.add(mem2)

            # Add sample Plan & Customer to Starlight to demonstrate isolation
            plan = Plan(
                id=uuid.uuid4(),
                tenant_id=starlight_tenant.id,
                name="Starlight Pro",
                code="STAR-PRO",
                billing_interval="MONTHLY",
                price=Decimal("4999.00"),
                currency="INR",
                is_active=True,
            )
            db.add(plan)
            await db.flush()

            cust = Customer(
                id=uuid.uuid4(),
                tenant_id=starlight_tenant.id,
                name="Zephyr Media Labs",
                billing_city="Mumbai",
                billing_country="IN",
                currency_preference="INR",
                status="ACTIVE",
                outstanding_balance=Decimal("0.00"),
            )
            db.add(cust)
            await db.flush()

            sub = Subscription(
                id=uuid.uuid4(),
                tenant_id=starlight_tenant.id,
                customer_id=cust.id,
                plan_id=plan.id,
                subscription_number="SUB-STA-0001",
                status="ACTIVE",
                amount=plan.price,
                currency="INR",
                billing_interval="MONTHLY",
            )
            db.add(sub)
            print(f"Created Starlight tenant & owner: {starlight_email}")

        await db.commit()
        print("Test accounts seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_additional_accounts())
