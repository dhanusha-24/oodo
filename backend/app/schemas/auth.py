import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """User login credential payload."""

    email: EmailStr
    password: str = Field(..., min_length=1)
    tenant_id: uuid.UUID | None = None


class UserResponse(BaseModel):
    """Serialized user details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool


class TenantResponse(BaseModel):
    """Serialized tenant details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    timezone: str
    base_currency: str
    settings_json: dict[str, Any] = Field(default_factory=dict)


class MembershipResponse(BaseModel):
    """Serialized membership with tenant context."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: uuid.UUID
    tenant_name: str
    role: str
    status: str


class LoginResponse(BaseModel):
    """Successful authentication response."""

    user: UserResponse
    active_tenant_id: uuid.UUID | None = None
    memberships: list[MembershipResponse] = Field(default_factory=list)
    csrf_token: str
    session_token: str | None = None


class AuthMeResponse(BaseModel):
    """Authenticated user profile with active tenant context."""

    user: UserResponse
    active_tenant: TenantResponse | None = None
    membership: MembershipResponse | None = None
    memberships: list[MembershipResponse] = Field(default_factory=list)


class SwitchTenantRequest(BaseModel):
    """Payload to switch active tenant context."""

    tenant_id: uuid.UUID


class SwitchTenantResponse(BaseModel):
    """Confirmation of tenant context switch."""

    active_tenant: TenantResponse
    membership: MembershipResponse
