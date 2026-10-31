import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.invoice import Invoice


class Payment(TenantScopedModel):
    """Payment record received from customer and allocated to an invoice."""

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "payment_number", name="uq_payments_tenant_number"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    payment_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        server_default="INR",
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(
        String(32),
        default="BANK_TRANSFER",
        server_default="BANK_TRANSFER",
        nullable=False,
    )  # RAZORPAY, BANK_TRANSFER, STRIPE, UPI, CASH
    status: Mapped[str] = mapped_column(
        String(32),
        default="SUCCESS",
        server_default="SUCCESS",
        nullable=False,
        index=True,
    )  # SUCCESS, PENDING, FAILED

    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", lazy="selectin")
    invoice: Mapped["Invoice | None"] = relationship("Invoice", back_populates="payments", lazy="selectin")
