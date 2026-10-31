import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.customer import CustomerResponse


class InvoiceCreate(BaseModel):
    customer_id: uuid.UUID
    subscription_id: uuid.UUID | None = None
    due_date: datetime
    subtotal: Decimal = Field(..., ge=Decimal("0.00"))
    tax_rate: Decimal = Field(default=Decimal("18.00"), ge=Decimal("0.00"))
    notes: str | None = None


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    subscription_id: uuid.UUID | None = None
    invoice_number: str
    status: str
    issue_date: datetime
    due_date: datetime
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    currency: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    customer: CustomerResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
