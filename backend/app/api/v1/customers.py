import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantUserContext, get_current_tenant_user, require_roles
from app.core.database import get_db
from app.models.auth import UserRole
from app.schemas.customer import (
    CustomerContactCreate,
    CustomerContactResponse,
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
    PaginatedCustomerResponse,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])

WRITE_ROLES = (
    UserRole.TENANT_OWNER,
    UserRole.SALES_MANAGER,
    UserRole.BILLING_MANAGER,
)


@router.get(
    "",
    response_model=PaginatedCustomerResponse,
    summary="List tenant customers with pagination and filtering",
)
async def list_customers(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(25, ge=1, description="Items per page (max 100)"),
    search: str | None = Query(None, description="Search term for name or email"),
    status: str | None = Query(None, description="Filter by status (ACTIVE, ARCHIVED)"),
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedCustomerResponse:
    """Retrieve paginated customers for the authenticated tenant."""
    if not ctx.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active tenant context is required",
        )

    capped_limit = min(limit, 100)
    items, total, total_pages = await CustomerService.list_customers(
        db=db,
        tenant_id=ctx.tenant.id,
        page=page,
        limit=capped_limit,
        search=search,
        status_filter=status,
    )

    return PaginatedCustomerResponse(
        items=[CustomerResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        limit=capped_limit,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
)
async def create_customer(
    payload: CustomerCreate,
    ctx: TenantUserContext = Depends(require_roles(*WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    """Create a new customer account in the active tenant organization."""
    if not ctx.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active tenant context is required",
        )

    customer = await CustomerService.create_customer(
        db=db,
        tenant_id=ctx.tenant.id,
        payload=payload,
    )
    return CustomerResponse.model_validate(customer)


@router.get(
    "/{customer_id}",
    response_model=CustomerDetailResponse,
    summary="Get customer details with contacts and balance",
)
async def get_customer(
    customer_id: uuid.UUID,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerDetailResponse:
    """Retrieve complete customer details including contacts and balance."""
    if not ctx.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active tenant context is required",
        )

    customer = await CustomerService.get_customer(
        db=db,
        tenant_id=ctx.tenant.id,
        customer_id=customer_id,
    )
    return CustomerDetailResponse.model_validate(customer)


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update customer attributes",
)
async def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    ctx: TenantUserContext = Depends(require_roles(*WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    """Update customer details with tenant scoping and optimistic version lock."""
    if not ctx.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active tenant context is required",
        )

    customer = await CustomerService.update_customer(
        db=db,
        tenant_id=ctx.tenant.id,
        customer_id=customer_id,
        payload=payload,
    )
    return CustomerResponse.model_validate(customer)


@router.post(
    "/{customer_id}/contacts",
    response_model=CustomerContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add contact person to customer",
)
async def add_customer_contact(
    customer_id: uuid.UUID,
    payload: CustomerContactCreate,
    ctx: TenantUserContext = Depends(require_roles(*WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> CustomerContactResponse:
    """Add a new contact person to an existing customer."""
    if not ctx.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active tenant context is required",
        )

    contact = await CustomerService.add_contact(
        db=db,
        tenant_id=ctx.tenant.id,
        customer_id=customer_id,
        payload=payload,
    )
    return CustomerContactResponse.model_validate(contact)
