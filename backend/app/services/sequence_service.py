import asyncio
import uuid
from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import Tenant
from app.models.tenant_sequence import TenantSequence

DEFAULT_PREFIXES: dict[str, str] = {
    "INVOICE": "INV",
    "QUOTE": "QT",
    "CREDIT_NOTE": "CN",
}


class SequenceService:
    """Atomic tenant document sequence numbering service with row-level locking."""

    _locks: ClassVar[dict[tuple[uuid.UUID, str, str], asyncio.Lock]] = {}
    _global_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    @staticmethod
    def calculate_fiscal_year(dt: datetime | None = None) -> str:
        """Calculate fiscal year (Apr-Mar) string e.g. '2026-27'."""
        if dt is None:
            dt = datetime.now(UTC)
        year = dt.year
        if dt.month >= 4:
            start_year = year
            end_year_short = (year + 1) % 100
        else:
            start_year = year - 1
            end_year_short = year % 100
        return f"{start_year}-{end_year_short:02d}"

    @classmethod
    async def get_next_number(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        doc_type: str,
        fiscal_year: str | None = None,
        auto_commit: bool = True,
        prefix: str | None = None,
        padding: int | None = None,
    ) -> str:
        """Atomically generate the next sequential document number using SELECT FOR UPDATE."""
        normalized_doc = doc_type.strip().upper()
        if fiscal_year is None:
            fiscal_year = cls.calculate_fiscal_year()
        else:
            fiscal_year = fiscal_year.strip()

        # In-process lock keyed by (tenant_id, doc_type, fiscal_year) to serialize
        # concurrent coroutines in the same event loop (critical for SQLite & worker concurrency)
        async with cls._global_lock:
            lock_key = (tenant_id, normalized_doc, fiscal_year)
            if lock_key not in cls._locks:
                cls._locks[lock_key] = asyncio.Lock()
            lock = cls._locks[lock_key]

        async with lock:
            stmt = (
                select(TenantSequence)
                .where(
                    TenantSequence.tenant_id == tenant_id,
                    TenantSequence.document_type == normalized_doc,
                    TenantSequence.fiscal_year == fiscal_year,
                )
                .with_for_update()
            )
            result = await db.execute(stmt)
            seq = result.scalar_one_or_none()

            if seq is None:
                # Determine default prefix and padding
                resolved_prefix = prefix
                if resolved_prefix is None:
                    # Check tenant settings if available
                    tenant = await db.get(Tenant, tenant_id)
                    if tenant and tenant.settings_json and normalized_doc == "INVOICE":
                        resolved_prefix = tenant.settings_json.get(
                            "invoice_numbering_prefix"
                        ) or tenant.settings_json.get("invoice_prefix")
                if not resolved_prefix:
                    resolved_prefix = DEFAULT_PREFIXES.get(
                        normalized_doc, normalized_doc[:3].upper()
                    )

                resolved_padding = padding if padding is not None else 6

                try:
                    async with db.begin_nested():
                        seq = TenantSequence(
                            tenant_id=tenant_id,
                            document_type=normalized_doc,
                            fiscal_year=fiscal_year,
                            next_value=1,
                            prefix=resolved_prefix,
                            padding=resolved_padding,
                        )
                        db.add(seq)
                        await db.flush()
                except IntegrityError:
                    # Another concurrent transaction inserted the record
                    result = await db.execute(stmt)
                    seq = result.scalar_one()

            allocated_number = seq.next_value
            seq.next_value += 1

            if auto_commit:
                await db.commit()
            else:
                await db.flush()

            return f"{seq.prefix}-{seq.fiscal_year}-{allocated_number:0{seq.padding}d}"
