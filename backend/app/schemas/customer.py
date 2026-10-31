import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CustomerContactCreate(BaseModel):
    """Payload to create a contact person for a customer."""

    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    role: str | None = Field(default=None, max_length=100)
    is_primary: bool = False

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Contact name cannot be empty")
        return s


class CustomerContactResponse(BaseModel):
    """Serialized customer contact."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    name: str
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class CustomerCreate(BaseModel):
    """Payload to create a new customer account."""

    name: str = Field(..., min_length=1, max_length=200)
    legal_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)

    # Billing address
    billing_address_line1: str | None = Field(default=None, max_length=255)
    billing_address_line2: str | None = Field(default=None, max_length=255)
    billing_city: str | None = Field(default=None, max_length=100)
    billing_state: str | None = Field(default=None, max_length=100)
    billing_postal_code: str | None = Field(default=None, max_length=20)
    billing_country: str = Field(default="IN", min_length=2, max_length=2)

    # Financial & Commercial settings
    tax_id: str | None = Field(default=None, max_length=50)
    currency_preference: str = Field(default="INR", min_length=3, max_length=3)
    payment_terms_days: int = Field(default=14, ge=0, le=365)
    notes: str | None = None
    external_id: str | None = Field(default=None, max_length=100)
    contacts: list[CustomerContactCreate] = Field(default_factory=list)

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Customer name cannot be empty or whitespace")
        return s

    @field_validator("billing_country", mode="after")
    @classmethod
    def validate_country(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if len(v_upper) != 2 or not v_upper.isalpha():
            raise ValueError("billing_country must be a 2-letter ISO country code")
        return v_upper

    @field_validator("currency_preference", mode="after")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if len(v_upper) != 3 or not v_upper.isalpha():
            raise ValueError("currency_preference must be a 3-letter currency code")
        return v_upper

    @field_validator("external_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return v


class CustomerUpdate(BaseModel):
    """Payload to update an existing customer."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    legal_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)

    billing_address_line1: str | None = Field(default=None, max_length=255)
    billing_address_line2: str | None = Field(default=None, max_length=255)
    billing_city: str | None = Field(default=None, max_length=100)
    billing_state: str | None = Field(default=None, max_length=100)
    billing_postal_code: str | None = Field(default=None, max_length=20)
    billing_country: str | None = Field(default=None, min_length=2, max_length=2)

    tax_id: str | None = Field(default=None, max_length=50)
    currency_preference: str | None = Field(default=None, min_length=3, max_length=3)
    payment_terms_days: int | None = Field(default=None, ge=0, le=365)
    status: str | None = Field(default=None, pattern="^(ACTIVE|ARCHIVED)$")
    notes: str | None = None
    external_id: str | None = Field(default=None, max_length=100)

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("Customer name cannot be empty or whitespace")
        return s

    @field_validator("billing_country", mode="after")
    @classmethod
    def validate_country(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_upper = v.strip().upper()
        if len(v_upper) != 2 or not v_upper.isalpha():
            raise ValueError("billing_country must be a 2-letter ISO country code")
        return v_upper

    @field_validator("currency_preference", mode="after")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_upper = v.strip().upper()
        if len(v_upper) != 3 or not v_upper.isalpha():
            raise ValueError("currency_preference must be a 3-letter currency code")
        return v_upper

    @field_validator("external_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return v


class CustomerResponse(BaseModel):
    """Customer account response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    legal_name: str | None = None
    email: str | None = None
    phone: str | None = None

    billing_address_line1: str | None = None
    billing_address_line2: str | None = None
    billing_city: str | None = None
    billing_state: str | None = None
    billing_postal_code: str | None = None
    billing_country: str

    tax_id: str | None = None
    currency_preference: str
    payment_terms_days: int
    status: str
    notes: str | None = None
    external_id: str | None = None
    outstanding_balance: Decimal = Decimal("0.00")

    version: int
    created_at: datetime
    updated_at: datetime


class CustomerDetailResponse(CustomerResponse):
    """Customer account detail response including contacts."""

    contacts: list[CustomerContactResponse] = Field(default_factory=list)


class PaginatedCustomerResponse(BaseModel):
    """Server-side paginated customer response."""

    items: list[CustomerResponse]
    total: int
    page: int
    limit: int
    total_pages: int
