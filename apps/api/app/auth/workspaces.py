from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.auth.dependencies import current_user
from app.auth.verifier import Principal
from app.core.errors import ApiError
from app.db.models import WorkspaceMember

WorkspaceRole = Literal["admin", "member"]


def get_workspace_role(
    session: Session, organization_id: UUID, workspace_id: UUID, user_id: UUID
) -> WorkspaceRole | None:
    # Existing composite FKs enforce workspace ownership and organization membership.
    role = session.scalar(
        select(WorkspaceMember.role).where(
            WorkspaceMember.organization_id == organization_id,
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    if role not in {"admin", "member"}:
        return None
    return cast(WorkspaceRole, role)


def require_workspace_membership(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(current_user)],
) -> WorkspaceRole:
    """Require membership in the route's organization/workspace; return its role."""
    factory = cast(sessionmaker[Session] | None, request.app.state.session_factory)
    if factory is None:
        raise ApiError(503, "DATABASE_UNAVAILABLE", "Access check is unavailable.")
    try:
        with factory() as session:
            role = get_workspace_role(
                session, organization_id, workspace_id, principal.id
            )
    except SQLAlchemyError:
        raise ApiError(
            503, "DATABASE_UNAVAILABLE", "Access check is unavailable."
        ) from None
    if role is None:
        raise ApiError(403, "WORKSPACE_ACCESS_DENIED", "Access denied.")
    return role
