import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TenantSettingsResponse(BaseModel):
    """Current tenant organization settings response."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: uuid.UUID
    tenant_name: str
    timezone: str
    currency: str
    default_payment_terms_days: int
    invoice_numbering_prefix: str
    invoice_prefix: str
    settings_json: dict[str, Any] = Field(default_factory=dict)


class TenantSettingsUpdate(BaseModel):
    """Payload to update tenant configuration settings."""

    timezone: str | None = None
    currency: str | None = Field(default=None, max_length=3)
    default_payment_terms_days: int | None = Field(default=None, ge=0, le=365)
    invoice_numbering_prefix: str | None = Field(default=None, max_length=16)
    invoice_prefix: str | None = Field(default=None, max_length=16)
