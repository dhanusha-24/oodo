import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PlanBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: str | None = None
    billing_interval: str = Field(default="MONTHLY", pattern="^(MONTHLY|ANNUAL)$")
    price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = Field(default="INR", min_length=3, max_length=3)
    trial_days: int = Field(default=0, ge=0)
    is_active: bool = True
    features_list: str | None = None


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    trial_days: int | None = None
    is_active: bool | None = None
    features_list: str | None = None


class PlanResponse(PlanBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
