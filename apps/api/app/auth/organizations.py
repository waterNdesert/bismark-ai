from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.auth.dependencies import current_user
from app.auth.verifier import Principal
from app.core.errors import ApiError
from app.db.models import OrganizationMember

OrganizationRole = Literal["owner", "admin", "member"]


def get_organization_role(
    session: Session, organization_id: UUID, user_id: UUID
) -> OrganizationRole | None:
    role = session.scalar(
        select(OrganizationMember.role).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
    )
    if role not in {"owner", "admin", "member"}:
        return None
    return cast(OrganizationRole, role)


def require_organization_membership(
    request: Request,
    organization_id: UUID,
    principal: Annotated[Principal, Depends(current_user)],
) -> OrganizationRole:
    """Require membership for the route's organization_id; return its scoped role."""
    factory = cast(sessionmaker[Session] | None, request.app.state.session_factory)
    if factory is None:
        raise ApiError(503, "DATABASE_UNAVAILABLE", "Access check is unavailable.")
    try:
        with factory() as session:
            role = get_organization_role(session, organization_id, principal.id)
    except SQLAlchemyError:
        raise ApiError(
            503, "DATABASE_UNAVAILABLE", "Access check is unavailable."
        ) from None
    if role is None:
        raise ApiError(403, "ORGANIZATION_ACCESS_DENIED", "Access denied.")
    return role
