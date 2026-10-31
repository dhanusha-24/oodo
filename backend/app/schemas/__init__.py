"""Pydantic schemas module."""

from app.schemas.analytics import DashboardSummaryResponse, MonthlyTrend
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MembershipResponse,
    SwitchTenantRequest,
    TenantResponse,
    UserResponse,
)
from app.schemas.customer import (
    CustomerContactCreate,
    CustomerContactResponse,
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
    PaginatedCustomerResponse,
)
from app.schemas.invoice import InvoiceCreate, InvoiceListResponse, InvoiceResponse
from app.schemas.payment import PaymentCreate, PaymentListResponse, PaymentResponse
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.schemas.settings import TenantSettingsResponse, TenantSettingsUpdate
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionListResponse,
    SubscriptionResponse,
    SubscriptionStatusTransition,
)

__all__ = [
    "CustomerContactCreate",
    "CustomerContactResponse",
    "CustomerCreate",
    "CustomerDetailResponse",
    "CustomerResponse",
    "CustomerUpdate",
    "DashboardSummaryResponse",
    "InvoiceCreate",
    "InvoiceListResponse",
    "InvoiceResponse",
    "LoginRequest",
    "LoginResponse",
    "MembershipResponse",
    "MonthlyTrend",
    "PaginatedCustomerResponse",
    "PaymentCreate",
    "PaymentListResponse",
    "PaymentResponse",
    "PlanCreate",
    "PlanResponse",
    "PlanUpdate",
    "SubscriptionCreate",
    "SubscriptionListResponse",
    "SubscriptionResponse",
    "SubscriptionStatusTransition",
    "SwitchTenantRequest",
    "TenantResponse",
    "TenantSettingsResponse",
    "TenantSettingsUpdate",
    "UserResponse",
]
