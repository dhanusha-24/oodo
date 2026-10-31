import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.auth import Tenant


class TenantSequence(BaseModel):
    """Tenant sequence counter for deterministic document numbering (Invoices, Quotes, Credit Notes)."""

    __tablename__ = "tenant_sequences"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "document_type",
            "fiscal_year",
            name="uq_tenant_sequence_tenant_doc_fy",
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
    )
    fiscal_year: Mapped[str] = mapped_column(
        String(16),
        index=True,
        nullable=False,
    )
    next_value: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )
    prefix: Mapped[str] = mapped_column(
        String(16),
        default="INV",
        server_default="INV",
        nullable=False,
    )
    padding: Mapped[int] = mapped_column(
        Integer,
        default=6,
        server_default="6",
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id])
