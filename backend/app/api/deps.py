from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    SESSION_COOKIE_NAME,
    hash_session_token,
)
from app.models.auth import Membership, Tenant, User, UserRole, UserSession


@dataclass
class TenantUserContext:
    """Security context holding authenticated user, active tenant, and active membership."""

    user: User
    session: UserSession
    tenant: Tenant | None
    membership: Membership | None


async def get_current_user_and_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> tuple[User, UserSession]:
    """Resolve current user and session from HttpOnly cookie or Bearer token header."""
    raw_token: str | None = None

    # 1. Try HttpOnly session cookie
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)

    # 2. Fall back to Authorization Bearer header
    if not raw_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header.removeprefix("Bearer ").strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
        )

    token_hash = hash_session_token(raw_token)

    # Query active session from database
    stmt = select(UserSession).where(UserSession.session_token_hash == token_hash)
    result = await db.execute(stmt)
    session_record = result.scalar_one_or_none()

    if not session_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    # Check expiration
    now = datetime.now(UTC)
    expires_at = session_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= now:
        await db.delete(session_record)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired",
        )

    # Fetch user
    user = await db.get(User, session_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or disabled",
        )

    return user, session_record


async def get_current_tenant_user(
    current: tuple[User, UserSession] = Depends(get_current_user_and_session),
    db: AsyncSession = Depends(get_db),
) -> TenantUserContext:
    """Resolve active tenant context and membership for the authenticated user session."""
    user, session_record = current

    # If active tenant is already established on the session
    if session_record.tenant_id:
        stmt = select(Membership).where(
            Membership.tenant_id == session_record.tenant_id,
            Membership.user_id == user.id,
            Membership.status == "ACTIVE",
        )
        membership_res = await db.execute(stmt)
        membership = membership_res.scalar_one_or_none()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active membership in tenant",
            )

        tenant = await db.get(Tenant, session_record.tenant_id)
        return TenantUserContext(
            user=user,
            session=session_record,
            tenant=tenant,
            membership=membership,
        )

    # No tenant on session: attempt to select user's first active membership
    stmt = (
        select(Membership)
        .where(
            Membership.user_id == user.id,
            Membership.status == "ACTIVE",
        )
        .order_by(Membership.created_at.asc())
    )
    memberships = (await db.execute(stmt)).scalars().all()

    if memberships:
        active_membership = memberships[0]
        session_record.tenant_id = active_membership.tenant_id
        await db.commit()

        tenant = await db.get(Tenant, active_membership.tenant_id)
        return TenantUserContext(
            user=user,
            session=session_record,
            tenant=tenant,
            membership=active_membership,
        )

    # Check for platform admin without tenant membership
    admin_stmt = select(Membership).where(
        Membership.user_id == user.id,
        Membership.role == UserRole.PLATFORM_ADMIN,
    )
    admin_membership = (await db.execute(admin_stmt)).scalar_one_or_none()
    if admin_membership:
        return TenantUserContext(
            user=user,
            session=session_record,
            tenant=None,
            membership=admin_membership,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No active tenant membership found",
    )


def require_roles(*allowed_roles: str | UserRole) -> Callable[..., TenantUserContext]:
    """Dependency factory checking user membership role against permitted roles."""
    roles_set = {str(r) for r in allowed_roles}

    async def role_checker(
        ctx: TenantUserContext = Depends(get_current_tenant_user),
    ) -> TenantUserContext:
        user_role = ctx.membership.role if ctx.membership else None
        if not user_role or (user_role not in roles_set and user_role != UserRole.PLATFORM_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient permissions",
            )
        return ctx

    return role_checker
