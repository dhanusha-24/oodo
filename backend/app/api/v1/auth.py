import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import (
    TenantUserContext,
    get_current_tenant_user,
    get_current_user_and_session,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
    SESSION_DURATION_SECONDS,
    cache_session_in_redis,
    generate_csrf_token,
    generate_session_token,
    hash_session_token,
    invalidate_cached_session_in_redis,
    verify_password,
)
from app.models.auth import AuditLog, Membership, Tenant, User, UserSession
from app.schemas.auth import (
    AuthMeResponse,
    LoginRequest,
    LoginResponse,
    MembershipResponse,
    SwitchTenantRequest,
    SwitchTenantResponse,
    TenantResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and create session",
)
async def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Verify user credentials, generate session, set HttpOnly cookie and CSRF token."""
    # Look up user by normalized lowercase email
    stmt = (
        select(User)
        .where(func.lower(User.email) == payload.email.lower().strip())
        .options(selectinload(User.memberships).selectinload(Membership.tenant))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Resolve active memberships
    active_memberships = [m for m in user.memberships if m.status == "ACTIVE"]

    # Select active tenant
    active_tenant_id: uuid.UUID | None = None
    if payload.tenant_id:
        matching = next((m for m in active_memberships if m.tenant_id == payload.tenant_id), None)
        if not matching:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not an active member of the specified tenant",
            )
        active_tenant_id = matching.tenant_id
    elif active_memberships:
        active_tenant_id = active_memberships[0].tenant_id

    # Generate session tokens
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    csrf_token = generate_csrf_token()
    expires_at = datetime.now(UTC) + timedelta(seconds=SESSION_DURATION_SECONDS)

    # Persist session to database
    user_session = UserSession(
        id=uuid.uuid4(),
        session_token_hash=token_hash,
        user_id=user.id,
        tenant_id=active_tenant_id,
        expires_at=expires_at,
    )
    db.add(user_session)

    # Cache in Redis with database fallback
    await cache_session_in_redis(
        token_hash=token_hash,
        session_data={
            "session_id": str(user_session.id),
            "user_id": str(user.id),
            "tenant_id": str(active_tenant_id) if active_tenant_id else None,
            "expires_at": expires_at.isoformat(),
        },
        ttl_seconds=SESSION_DURATION_SECONDS,
    )

    # Write audit log
    client_ip = request.client.host if request.client else None
    audit = AuditLog(
        id=uuid.uuid4(),
        tenant_id=active_tenant_id,
        actor_user_id=user.id,
        entity_type="UserSession",
        entity_id=str(user_session.id),
        action="LOGIN",
        new_values={"tenant_id": str(active_tenant_id) if active_tenant_id else None},
        ip_address=client_ip,
        occurred_at=datetime.now(UTC),
    )
    db.add(audit)
    await db.commit()

    # Set HttpOnly session cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        max_age=SESSION_DURATION_SECONDS,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )

    # Set CSRF cookie and response header
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        max_age=SESSION_DURATION_SECONDS,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )
    response.headers[CSRF_HEADER_NAME] = csrf_token

    membership_dtos = [
        MembershipResponse(
            tenant_id=m.tenant_id,
            tenant_name=m.tenant.name if m.tenant else "Unknown Tenant",
            role=m.role,
            status=m.status,
        )
        for m in active_memberships
    ]

    return LoginResponse(
        user=UserResponse.model_validate(user),
        active_tenant_id=active_tenant_id,
        memberships=membership_dtos,
        csrf_token=csrf_token,
        session_token=raw_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke active user session",
)
async def logout(
    response: Response,
    request: Request,
    current: tuple[User, UserSession] = Depends(get_current_user_and_session),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revoke session record, clear cache, and delete session cookies."""
    user, session_record = current

    # Delete session record from database
    await db.delete(session_record)

    # Invalidate Redis cache
    await invalidate_cached_session_in_redis(session_record.session_token_hash)

    # Write audit log
    client_ip = request.client.host if request.client else None
    audit = AuditLog(
        id=uuid.uuid4(),
        tenant_id=session_record.tenant_id,
        actor_user_id=user.id,
        entity_type="UserSession",
        entity_id=str(session_record.id),
        action="LOGOUT",
        ip_address=client_ip,
        occurred_at=datetime.now(UTC),
    )
    db.add(audit)
    await db.commit()

    # Clear cookies
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")

    return {"detail": "Successfully logged out"}


@router.get(
    "/me",
    response_model=AuthMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user and active tenant context",
)
async def get_me(
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> AuthMeResponse:
    """Return profile details, active tenant, and all memberships for authenticated user."""
    # Query user's memberships with tenant details
    stmt = (
        select(Membership)
        .where(
            Membership.user_id == ctx.user.id,
            Membership.status == "ACTIVE",
        )
        .options(selectinload(Membership.tenant))
    )
    res = await db.execute(stmt)
    memberships = res.scalars().all()

    membership_dtos = [
        MembershipResponse(
            tenant_id=m.tenant_id,
            tenant_name=m.tenant.name if m.tenant else "Unknown Tenant",
            role=m.role,
            status=m.status,
        )
        for m in memberships
    ]

    active_membership_dto = None
    if ctx.membership:
        tenant_name = ctx.tenant.name if ctx.tenant else "Unknown Tenant"
        active_membership_dto = MembershipResponse(
            tenant_id=ctx.membership.tenant_id,
            tenant_name=tenant_name,
            role=ctx.membership.role,
            status=ctx.membership.status,
        )

    active_tenant_dto = None
    if ctx.tenant:
        active_tenant_dto = TenantResponse.model_validate(ctx.tenant)

    return AuthMeResponse(
        user=UserResponse.model_validate(ctx.user),
        active_tenant=active_tenant_dto,
        membership=active_membership_dto,
        memberships=membership_dtos,
    )


@router.post(
    "/switch-tenant",
    response_model=SwitchTenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Switch active tenant organization for current session",
)
async def switch_tenant(
    payload: SwitchTenantRequest,
    request: Request,
    current: tuple[User, UserSession] = Depends(get_current_user_and_session),
    db: AsyncSession = Depends(get_db),
) -> SwitchTenantResponse:
    """Switch active tenant context for the current session to another authorized tenant."""
    user, session_record = current

    # Verify user has active membership in target tenant
    stmt = (
        select(Membership)
        .where(
            Membership.user_id == user.id,
            Membership.tenant_id == payload.tenant_id,
            Membership.status == "ACTIVE",
        )
        .options(selectinload(Membership.tenant))
    )
    res = await db.execute(stmt)
    target_membership = res.scalar_one_or_none()

    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an active member of the specified tenant",
        )

    # Fetch tenant
    target_tenant = target_membership.tenant
    if not target_tenant:
        target_tenant = await db.get(Tenant, payload.tenant_id)
        if not target_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

    # Update session
    session_record.tenant_id = target_tenant.id

    # Update cache
    await cache_session_in_redis(
        token_hash=session_record.session_token_hash,
        session_data={
            "session_id": str(session_record.id),
            "user_id": str(user.id),
            "tenant_id": str(target_tenant.id),
            "expires_at": session_record.expires_at.isoformat(),
        },
        ttl_seconds=SESSION_DURATION_SECONDS,
    )

    # Write audit log
    client_ip = request.client.host if request.client else None
    audit = AuditLog(
        id=uuid.uuid4(),
        tenant_id=target_tenant.id,
        actor_user_id=user.id,
        entity_type="UserSession",
        entity_id=str(session_record.id),
        action="SWITCH_TENANT",
        new_values={"tenant_id": str(target_tenant.id)},
        ip_address=client_ip,
        occurred_at=datetime.now(UTC),
    )
    db.add(audit)
    await db.commit()

    return SwitchTenantResponse(
        active_tenant=TenantResponse.model_validate(target_tenant),
        membership=MembershipResponse(
            tenant_id=target_membership.tenant_id,
            tenant_name=target_tenant.name,
            role=target_membership.role,
            status=target_membership.status,
        ),
    )
