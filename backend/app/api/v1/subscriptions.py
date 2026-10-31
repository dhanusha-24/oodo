import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import TenantUserContext, get_current_tenant_user
from app.core.database import get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionListResponse,
    SubscriptionResponse,
    SubscriptionStatusTransition,
)
from app.services.sequence_service import SequenceService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    status_filter: str | None = Query(None, alias="status"),
    customer_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List subscriptions with pagination and status filters."""
    tenant_id = ctx.session.tenant_id
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.customer), selectinload(Subscription.plan))
        .where(Subscription.tenant_id == tenant_id)
    )

    if status_filter:
        stmt = stmt.where(Subscription.status == status_filter.upper())
    if customer_id:
        stmt = stmt.where(Subscription.customer_id == customer_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(Subscription.created_at.desc())
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


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a subscription."""
    tenant_id = ctx.session.tenant_id

    # Verify customer
    customer = await db.get(Customer, payload.customer_id)
    if not customer or customer.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # Verify plan
    plan = await db.get(Plan, payload.plan_id)
    if not plan or plan.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # Generate sequence
    try:
        sub_number = await SequenceService.get_next_number(db, tenant_id, "subscription")
    except Exception:
        count = (
            await db.execute(
                select(func.count(Subscription.id)).where(Subscription.tenant_id == tenant_id)
            )
        ).scalar_one()
        sub_number = f"SUB-{count + 1:05d}"

    now = datetime.now(UTC)
    start = payload.start_date or now
    days = 365 if payload.billing_interval == "ANNUAL" else 30
    period_end = start + timedelta(days=days)

    amount = payload.amount if payload.amount is not None else plan.price

    sub = Subscription(
        tenant_id=tenant_id,
        customer_id=payload.customer_id,
        plan_id=payload.plan_id,
        subscription_number=sub_number,
        status=payload.initial_status,
        start_date=start,
        current_period_start=start,
        current_period_end=period_end,
        amount=amount,
        currency=plan.currency,
        billing_interval=payload.billing_interval,
        auto_renew=payload.auto_renew,
    )
    db.add(sub)
    await db.flush()

    # If activated immediately, create initial invoice
    if payload.initial_status == "ACTIVE":
        try:
            inv_number = await SequenceService.get_next_number(db, tenant_id, "invoice")
        except Exception:
            inv_number = f"INV-{uuid.uuid4().hex[:6].upper()}"

        tax_amt = (amount * 18) / 100
        total_amt = amount + tax_amt

        inv = Invoice(
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            subscription_id=sub.id,
            invoice_number=inv_number,
            status="ISSUED",
            issue_date=now,
            due_date=now + timedelta(days=customer.payment_terms_days or 14),
            subtotal=amount,
            tax_rate=18,
            tax_amount=tax_amt,
            total_amount=total_amt,
            amount_paid=0,
            balance_due=total_amt,
            currency=plan.currency,
            notes=f"Subscription invoice for {plan.name} ({sub_number})",
        )
        db.add(inv)
        customer.outstanding_balance += total_amt

    await db.commit()
    await db.refresh(sub)
    # Reload relationships
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.customer), selectinload(Subscription.plan))
        .where(Subscription.id == sub.id)
    )
    return (await db.execute(stmt)).scalar_one()


@router.get("/{sub_id}", response_model=SubscriptionResponse)
async def get_subscription(
    sub_id: uuid.UUID,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get subscription by ID."""
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.customer), selectinload(Subscription.plan))
        .where(
            Subscription.id == sub_id,
            Subscription.tenant_id == ctx.session.tenant_id,
        )
    )
    sub = (await db.execute(stmt)).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.post("/{sub_id}/transition", response_model=SubscriptionResponse)
async def transition_subscription_status(
    sub_id: uuid.UUID,
    payload: SubscriptionStatusTransition,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Transition subscription through lifecycle states."""
    tenant_id = ctx.session.tenant_id
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.customer), selectinload(Subscription.plan))
        .where(
            Subscription.id == sub_id,
            Subscription.tenant_id == tenant_id,
        )
    )
    sub = (await db.execute(stmt)).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    old_status = sub.status
    target = payload.target_status.upper()

    now = datetime.now(UTC)
    if target == "CONFIRMED" and old_status == "QUOTATION":
        sub.quotation_approved_at = now
    elif target == "CANCELLED":
        sub.cancellation_reason = payload.reason or "Cancelled by user"
        sub.end_date = now

    sub.status = target
    await db.commit()
    await db.refresh(sub)
    return sub
