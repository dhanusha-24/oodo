import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models.auth import Membership, Tenant, User, UserRole
from app.models.base import Base
from app.models.customer import Customer, CustomerContact
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.tenant_sequence import TenantSequence


async def seed() -> None:
    print("Starting database seeding...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing_user = (
            await db.execute(select(User).where(User.email == "owner@acme.com"))
        ).scalar_one_or_none()

        if existing_user:
            print("Demo data already seeded! Skipping creation.")
            return

        print("Seeding Tenant and Users...")
        # 1. Tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Acme Cloud Technologies Pvt Ltd",
            timezone="Asia/Kolkata",
            base_currency="INR",
            settings_json={
                "tax_id": "29AABCA1234A1Z5",
                "invoice_prefix": "INV",
                "invoice_sequence_padding": 4,
                "portal_access_enabled": True,
            },
        )
        db.add(tenant)
        await db.flush()

        # Tenant Sequences
        for doc_type, prefix in [("customer", "CUST"), ("subscription", "SUB"), ("invoice", "INV"), ("payment", "PAY")]:
            seq = TenantSequence(
                tenant_id=tenant.id,
                document_type=doc_type,
                fiscal_year="2026-27",
                prefix=prefix,
                next_value=6,
            )
            db.add(seq)

        # 2. Owner User
        hashed_pwd = hash_password("SecurePassword123!")
        owner = User(
            id=uuid.uuid4(),
            email="owner@acme.com",
            full_name="Rajesh Sharma (Acme Admin)",
            password_hash=hashed_pwd,
            is_active=True,
        )
        db.add(owner)
        await db.flush()

        membership = Membership(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            user_id=owner.id,
            role=UserRole.TENANT_OWNER,
            status="ACTIVE",
        )
        db.add(membership)

        # 3. Plans
        print("Seeding Plans...")
        starter_plan = Plan(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Starter Plan",
            code="STARTER",
            description="Essential subscription tier for small tech teams & early startups",
            billing_interval="MONTHLY",
            price=Decimal("2999.00"),
            currency="INR",
            trial_days=14,
            is_active=True,
            features_list="5 Team Members, 10,000 API Requests/mo, Basic Reporting, Email Support",
        )
        pro_plan = Plan(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Professional Growth",
            code="PRO",
            description="Power tier with high limits, webhooks and priority SLA",
            billing_interval="MONTHLY",
            price=Decimal("9999.00"),
            currency="INR",
            trial_days=14,
            is_active=True,
            features_list="25 Team Members, 250,000 API Requests/mo, Custom Webhooks, Priority SLA Support, Audit Logs",
        )
        ent_plan = Plan(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Enterprise Cloud",
            code="ENTERPRISE",
            description="Full-scale enterprise infrastructure with dedicated compliance",
            billing_interval="ANNUAL",
            price=Decimal("299999.00"),
            currency="INR",
            trial_days=30,
            is_active=True,
            features_list="Unlimited Members, Dedicated Account Manager, Custom SSO & RBAC, 99.99% Uptime SLA, SOC2 Reports",
        )
        db.add_all([starter_plan, pro_plan, ent_plan])
        await db.flush()

        # 4. Customers
        print("Seeding Customers...")
        customers_data = [
            {
                "name": "Infosys Tech Solutions",
                "legal_name": "Infosys Technology Solutions Pvt Ltd",
                "email": "procurement@infosys-tech.com",
                "phone": "+91 98450 11223",
                "tax_id": "29AABCU9603R1ZM",
                "city": "Bangalore",
                "state": "Karnataka",
                "code": "560100",
                "address": "Electronic City Phase 1, Hosur Road",
                "plan": pro_plan,
                "status": "ACTIVE",
            },
            {
                "name": "Reliance Digital Ventures",
                "legal_name": "Reliance Digital Ventures Limited",
                "email": "billing@reliancedv.com",
                "phone": "+91 98200 44556",
                "tax_id": "27AABCR2418Q1ZP",
                "city": "Mumbai",
                "state": "Maharashtra",
                "code": "400051",
                "address": "Bandra-Kurla Complex (BKC)",
                "plan": ent_plan,
                "status": "ACTIVE",
            },
            {
                "name": "Tata Cloud Systems",
                "legal_name": "Tata Cloud & Enterprise Systems Ltd",
                "email": "finance@tatacloud.in",
                "phone": "+91 99300 77889",
                "tax_id": "27AAACT2727Q1ZW",
                "city": "Pune",
                "state": "Maharashtra",
                "code": "411057",
                "address": "Hinjawadi IT Park, Phase 2",
                "plan": pro_plan,
                "status": "ACTIVE",
            },
            {
                "name": "Zomato Logistics Tech",
                "legal_name": "Zomato Logistics Technologies Pvt Ltd",
                "email": "accounts@zomatologistics.com",
                "phone": "+91 99100 22334",
                "tax_id": "07AAACZ1234A1Z5",
                "city": "Gurugram",
                "state": "Haryana",
                "code": "122002",
                "address": "Cyber City, DLF Phase 2",
                "plan": starter_plan,
                "status": "ACTIVE",
            },
            {
                "name": "Swiggy Delivery Platform",
                "legal_name": "Bundl Technologies Pvt Ltd",
                "email": "invoices@swiggyplatform.in",
                "phone": "+91 98800 66778",
                "tax_id": "29AABCS5678B1Z2",
                "city": "Bangalore",
                "state": "Karnataka",
                "code": "560034",
                "address": "Koramangala 3rd Block",
                "plan": starter_plan,
                "status": "ACTIVE",
            },
        ]

        now = datetime.now(UTC)
        created_customers = []

        for c_idx, c_data in enumerate(customers_data, 1):
            cust = Customer(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=c_data["name"],
                legal_name=c_data["legal_name"],
                email=c_data["email"],
                phone=c_data["phone"],
                billing_address_line1=c_data["address"],
                billing_city=c_data["city"],
                billing_state=c_data["state"],
                billing_postal_code=c_data["code"],
                billing_country="IN",
                tax_id=c_data["tax_id"],
                currency_preference="INR",
                payment_terms_days=14,
                status=c_data["status"],
                external_id=f"EXT-CUST-{100 + c_idx}",
                outstanding_balance=Decimal("0.00"),
            )
            db.add(cust)
            await db.flush()

            # Add contact
            contact = CustomerContact(
                id=uuid.uuid4(),
                customer_id=cust.id,
                name=f"VP Tech - {c_data['name'].split()[0]}",
                email=c_data["email"],
                phone=c_data["phone"],
                role="Procurement Lead",
                is_primary=True,
            )
            db.add(contact)
            created_customers.append((cust, c_data["plan"]))

        # 5. Subscriptions, Invoices & Payments
        print("Seeding Subscriptions, Invoices and Payments...")
        sub_statuses = ["ACTIVE", "ACTIVE", "CONFIRMED", "ACTIVE", "QUOTATION"]

        for idx, ((cust, plan), sub_status) in enumerate(zip(created_customers, sub_statuses, strict=True), 1):
            start_date = now - timedelta(days=idx * 20)
            sub = Subscription(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                customer_id=cust.id,
                plan_id=plan.id,
                subscription_number=f"SUB-2026-000{idx}",
                status=sub_status,
                start_date=start_date,
                current_period_start=start_date,
                current_period_end=start_date + timedelta(days=30 if plan.billing_interval == "MONTHLY" else 365),
                amount=plan.price,
                currency=plan.currency,
                billing_interval=plan.billing_interval,
                auto_renew=True,
            )
            db.add(sub)
            await db.flush()

            # Generate Invoice for the first 4
            if idx <= 4:
                tax = (plan.price * Decimal("18.00")) / Decimal("100.00")
                tot = plan.price + tax

                inv_status = "PAID" if idx == 1 else ("PARTIALLY_PAID" if idx == 2 else ("OVERDUE" if idx == 3 else "ISSUED"))
                paid_amt = tot if inv_status == "PAID" else (tot / 2 if inv_status == "PARTIALLY_PAID" else Decimal("0.00"))
                bal = tot - paid_amt

                inv = Invoice(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    customer_id=cust.id,
                    subscription_id=sub.id,
                    invoice_number=f"INV-2026-27-000{idx}",
                    status=inv_status,
                    issue_date=start_date,
                    due_date=start_date + timedelta(days=14),
                    subtotal=plan.price,
                    tax_rate=Decimal("18.00"),
                    tax_amount=tax,
                    total_amount=tot,
                    amount_paid=paid_amt,
                    balance_due=bal,
                    currency="INR",
                    notes=f"Tax invoice for subscription {sub.subscription_number}",
                )
                db.add(inv)
                await db.flush()

                cust.outstanding_balance = bal

                # If any paid amount, record Payment
                if paid_amt > 0:
                    pay = Payment(
                        id=uuid.uuid4(),
                        tenant_id=tenant.id,
                        customer_id=cust.id,
                        invoice_id=inv.id,
                        payment_number=f"PAY-2026-000{idx}",
                        amount=paid_amt,
                        currency="INR",
                        payment_method="RAZORPAY" if idx == 1 else "BANK_TRANSFER",
                        status="SUCCESS",
                        reference_id=f"RZP_PAY_{1000 + idx}",
                        paid_at=start_date + timedelta(days=2),
                        notes=f"Payment for {inv.invoice_number}",
                    )
                    db.add(pay)

        await db.commit()
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
