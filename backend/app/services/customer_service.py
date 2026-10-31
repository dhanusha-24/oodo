import math
import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer, CustomerContact
from app.schemas.customer import (
    CustomerContactCreate,
    CustomerCreate,
    CustomerUpdate,
)


class CustomerService:
    """Business logic for Customer and Contact management with strict tenant isolation."""

    @staticmethod
    async def create_customer(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        payload: CustomerCreate,
    ) -> Customer:
        """Create a new customer account in the given tenant organization."""
        # Uniqueness check for external_id within tenant
        if payload.external_id:
            existing_stmt = select(Customer).where(
                Customer.tenant_id == tenant_id,
                Customer.external_id == payload.external_id,
            )
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Customer with external_id '{payload.external_id}' already exists in this tenant",
                )

        customer = Customer(
            tenant_id=tenant_id,
            name=payload.name,
            legal_name=payload.legal_name,
            email=payload.email,
            phone=payload.phone,
            billing_address_line1=payload.billing_address_line1,
            billing_address_line2=payload.billing_address_line2,
            billing_city=payload.billing_city,
            billing_state=payload.billing_state,
            billing_postal_code=payload.billing_postal_code,
            billing_country=payload.billing_country,
            tax_id=payload.tax_id,
            currency_preference=payload.currency_preference,
            payment_terms_days=payload.payment_terms_days,
            notes=payload.notes,
            external_id=payload.external_id,
        )

        if payload.contacts:
            for contact_data in payload.contacts:
                contact = CustomerContact(
                    name=contact_data.name,
                    email=contact_data.email,
                    phone=contact_data.phone,
                    role=contact_data.role,
                    is_primary=contact_data.is_primary,
                )
                customer.contacts.append(contact)

        db.add(customer)
        try:
            await db.commit()
            await db.refresh(customer)
        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer violates unique constraint in this tenant",
            ) from exc

        return customer

    @staticmethod
    async def get_customer(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Customer:
        """Retrieve a customer by ID with tenant isolation."""
        stmt = (
            select(Customer)
            .options(selectinload(Customer.contacts))
            .where(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
            )
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found",
            )
        return customer

    @staticmethod
    async def list_customers(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        page: int = 1,
        limit: int = 25,
        search: str | None = None,
        status_filter: str | None = None,
    ) -> tuple[Sequence[Customer], int, int]:
        """List customers scoped to tenant with server-side pagination and filters."""
        page = max(1, page)
        limit = max(1, min(limit, 100))

        conditions = [Customer.tenant_id == tenant_id]

        if status_filter:
            conditions.append(Customer.status == status_filter.strip())

        if search and search.strip():
            search_term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.email.ilike(search_term),
                )
            )

        # Count total
        count_stmt = select(func.count(Customer.id)).where(*conditions)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        total_pages = math.ceil(total / limit) if total > 0 else 0

        # Query items
        offset = (page - 1) * limit
        stmt = (
            select(Customer)
            .where(*conditions)
            .order_by(Customer.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = (await db.execute(stmt)).scalars().all()

        return items, total, total_pages

    @staticmethod
    async def update_customer(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        payload: CustomerUpdate,
    ) -> Customer:
        """Update customer attributes and increment optimistic version lock."""
        customer = await CustomerService.get_customer(db, tenant_id, customer_id)

        update_dict = payload.model_dump(exclude_unset=True)

        if "external_id" in update_dict and update_dict["external_id"] != customer.external_id:
            new_ext_id = update_dict["external_id"]
            if new_ext_id:
                existing_stmt = select(Customer).where(
                    Customer.tenant_id == tenant_id,
                    Customer.external_id == new_ext_id,
                    Customer.id != customer_id,
                )
                existing = (await db.execute(existing_stmt)).scalar_one_or_none()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Customer with external_id '{new_ext_id}' already exists in this tenant",
                    )

        for key, value in update_dict.items():
            setattr(customer, key, value)

        customer.version += 1

        try:
            await db.commit()
            await db.refresh(customer)
        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer update violates unique constraint in this tenant",
            ) from exc

        return customer

    @staticmethod
    async def add_contact(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        payload: CustomerContactCreate,
    ) -> CustomerContact:
        """Add a contact person to an existing tenant customer."""
        # Verify customer existence and tenancy
        await CustomerService.get_customer(db, tenant_id, customer_id)

        if payload.is_primary:
            # Demote any current primary contacts
            stmt = (
                update(CustomerContact)
                .where(CustomerContact.customer_id == customer_id)
                .values(is_primary=False)
            )
            await db.execute(stmt)

        contact = CustomerContact(
            customer_id=customer_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            role=payload.role,
            is_primary=payload.is_primary,
        )
        db.add(contact)
        await db.commit()
        await db.refresh(contact)

        return contact
