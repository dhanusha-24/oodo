import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.customer import CustomerResponse
from app.schemas.invoice import InvoiceResponse


class PaymentCreate(BaseModel):
    customer_id: uuid.UUID
    invoice_id: uuid.UUID | None = None
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    payment_method: str = Field(
        default="BANK_TRANSFER",
        pattern="^(RAZORPAY|BANK_TRANSFER|STRIPE|UPI|CASH)$",
    )
    reference_id: str | None = None
    notes: str | None = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    invoice_id: uuid.UUID | None = None
    payment_number: str
    amount: Decimal
    currency: str
    payment_method: str
    status: str
    reference_id: str | None = None
    paid_at: datetime
    notes: str | None = None
    created_at: datetime

    customer: CustomerResponse | None = None
    invoice: InvoiceResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    page_size: int
