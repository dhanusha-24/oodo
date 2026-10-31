from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.api.deps import TenantUserContext, get_current_tenant_user, require_roles
from app.core.database import get_db
from app.models.auth import Tenant, UserRole
from app.models.tenant_sequence import TenantSequence
from app.schemas.settings import TenantSettingsResponse, TenantSettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


def _build_settings_response(tenant: Tenant) -> TenantSettingsResponse:
    settings = tenant.settings_json or {}
    invoice_prefix = (
        settings.get("invoice_numbering_prefix") or settings.get("invoice_prefix") or "INV"
    )
    terms_days = settings.get("default_payment_terms_days", 14)
    return TenantSettingsResponse(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        timezone=tenant.timezone,
        currency=tenant.base_currency,
        default_payment_terms_days=terms_days,
        invoice_numbering_prefix=invoice_prefix,
        invoice_prefix=invoice_prefix,
        settings_json=settings,
    )


@router.get(
    "",
    response_model=TenantSettingsResponse,
    summary="Get tenant settings",
)
async def get_tenant_settings(
    ctx: TenantUserContext = Depends(get_current_tenant_user),
) -> TenantSettingsResponse:
    """Retrieve settings for the current active tenant organization."""
    if not ctx.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active tenant context is required",
        )
    return _build_settings_response(ctx.tenant)


@router.patch(
    "",
    response_model=TenantSettingsResponse,
    summary="Update tenant settings",
)
async def update_tenant_settings(
    payload: TenantSettingsUpdate,
    ctx: TenantUserContext = Depends(require_roles(UserRole.TENANT_OWNER, UserRole.PLATFORM_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> TenantSettingsResponse:
    """Update settings for the current active tenant organization."""
    if not ctx.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active tenant context is required",
        )

    tenant = ctx.tenant

    if payload.timezone is not None:
        tenant.timezone = payload.timezone

    if payload.currency is not None:
        tenant.base_currency = payload.currency.upper()

    settings_dict = dict(tenant.settings_json or {})

    if payload.default_payment_terms_days is not None:
        settings_dict["default_payment_terms_days"] = payload.default_payment_terms_days

    prefix_to_set = payload.invoice_numbering_prefix or payload.invoice_prefix
    if prefix_to_set is not None:
        settings_dict["invoice_numbering_prefix"] = prefix_to_set
        settings_dict["invoice_prefix"] = prefix_to_set

        # Update existing sequences for INVOICE if present
        stmt = (
            update(TenantSequence)
            .where(
                TenantSequence.tenant_id == tenant.id,
                TenantSequence.document_type == "INVOICE",
            )
            .values(prefix=prefix_to_set)
        )
        await db.execute(stmt)

    tenant.settings_json = settings_dict
    flag_modified(tenant, "settings_json")

    await db.commit()
    await db.refresh(tenant)

    return _build_settings_response(tenant)
