import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import TenantUserContext, get_current_tenant_user
from app.core.database import get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentListResponse, PaymentResponse
from app.services.sequence_service import SequenceService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    customer_id: uuid.UUID | None = None,
    invoice_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List payments with pagination."""
    tenant_id = ctx.session.tenant_id
    stmt = (
        select(Payment)
        .options(selectinload(Payment.customer), selectinload(Payment.invoice))
        .where(Payment.tenant_id == tenant_id)
    )

    if customer_id:
        stmt = stmt.where(Payment.customer_id == customer_id)
    if invoice_id:
        stmt = stmt.where(Payment.invoice_id == invoice_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(Payment.paid_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    results = (await db.execute(stmt)).scalars().all()

    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payload: PaymentCreate,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Record customer payment and allocate to invoice if provided."""
    tenant_id = ctx.session.tenant_id

    customer = await db.get(Customer, payload.customer_id)
    if not customer or customer.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    invoice: Invoice | None = None
    if payload.invoice_id:
        invoice = await db.get(Invoice, payload.invoice_id)
        if not invoice or invoice.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    try:
        pay_number = await SequenceService.get_next_number(db, tenant_id, "payment")
    except Exception:
        count = (
            await db.execute(
                select(func.count(Payment.id)).where(Payment.tenant_id == tenant_id)
            )
        ).scalar_one()
        pay_number = f"PAY-{count + 1:05d}"

    payment = Payment(
        tenant_id=tenant_id,
        customer_id=payload.customer_id,
        invoice_id=payload.invoice_id,
        payment_number=pay_number,
        amount=payload.amount,
        currency=customer.currency_preference or "INR",
        payment_method=payload.payment_method,
        status="SUCCESS",
        reference_id=payload.reference_id or f"TXN-{uuid.uuid4().hex[:8].upper()}",
        paid_at=datetime.now(UTC),
        notes=payload.notes,
    )
    db.add(payment)

    # Adjust invoice balance
    if invoice:
        invoice.amount_paid += payload.amount
        invoice.balance_due = max(Decimal("0.00"), invoice.balance_due - payload.amount)
        if invoice.balance_due <= Decimal("0.00"):
            invoice.status = "PAID"
        else:
            invoice.status = "PARTIALLY_PAID"

    # Adjust customer outstanding balance
    customer.outstanding_balance = max(
        Decimal("0.00"), customer.outstanding_balance - payload.amount
    )

    await db.commit()
    await db.refresh(payment)

    stmt = (
        select(Payment)
        .options(selectinload(Payment.customer), selectinload(Payment.invoice))
        .where(Payment.id == payment.id)
    )
    return (await db.execute(stmt)).scalar_one()
