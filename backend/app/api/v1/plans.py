import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantUserContext, get_current_tenant_user
from app.core.database import get_db
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("", response_model=list[PlanResponse])
async def list_plans(
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all plans for current tenant."""
    stmt = (
        select(Plan)
        .where(Plan.tenant_id == ctx.session.tenant_id)
        .order_by(Plan.price.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new plan for current tenant."""
    # Check duplicate code
    stmt = select(Plan).where(
        Plan.tenant_id == ctx.session.tenant_id,
        Plan.code == payload.code.upper(),
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Plan code '{payload.code}' already exists",
        )

    plan = Plan(
        tenant_id=ctx.session.tenant_id,
        name=payload.name,
        code=payload.code.upper(),
        description=payload.description,
        billing_interval=payload.billing_interval,
        price=payload.price,
        currency=payload.currency,
        trial_days=payload.trial_days,
        is_active=payload.is_active,
        features_list=payload.features_list,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get single plan by ID."""
    stmt = select(Plan).where(
        Plan.id == plan_id,
        Plan.tenant_id == ctx.session.tenant_id,
    )
    plan = (await db.execute(stmt)).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdate,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update plan details."""
    stmt = select(Plan).where(
        Plan.id == plan_id,
        Plan.tenant_id == ctx.session.tenant_id,
    )
    plan = (await db.execute(stmt)).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(plan, field, val)

    await db.commit()
    await db.refresh(plan)
    return plan
