import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.customer import CustomerResponse
from app.schemas.plan import PlanResponse


class SubscriptionCreate(BaseModel):
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    start_date: datetime | None = None
    billing_interval: str = Field(default="MONTHLY", pattern="^(MONTHLY|ANNUAL)$")
    amount: Decimal | None = None
    auto_renew: bool = True
    initial_status: str = Field(default="ACTIVE", pattern="^(DRAFT|QUOTATION|CONFIRMED|ACTIVE)$")


class SubscriptionStatusTransition(BaseModel):
    target_status: str = Field(
        ...,
        pattern="^(DRAFT|QUOTATION|CONFIRMED|ACTIVE|PAUSED|CANCELLED|CLOSED)$",
    )
    reason: str | None = None


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    subscription_number: str
    status: str
    start_date: datetime
    end_date: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    amount: Decimal
    currency: str
    billing_interval: str
    auto_renew: bool
    cancellation_reason: str | None = None
    quotation_approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    customer: CustomerResponse | None = None
    plan: PlanResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionListResponse(BaseModel):
    items: list[SubscriptionResponse]
    total: int
    page: int
    page_size: int
