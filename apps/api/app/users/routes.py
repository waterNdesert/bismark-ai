from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.auth.dependencies import current_user
from app.auth.verifier import Principal
from app.core.errors import ApiError
from app.db.models import (
    Organization,
    OrganizationMember,
    Profile,
    Workspace,
    WorkspaceMember,
)

router = APIRouter(prefix="/api/v1", tags=["current user"])


class ProfileResponse(BaseModel):
    id: UUID
    email: str
    display_name: str | None


class WorkspaceContextResponse(BaseModel):
    id: UUID
    name: str
    role: Literal["admin", "member"]


class OrganizationContextResponse(BaseModel):
    id: UUID
    name: str
    role: Literal["owner", "admin", "member"]
    workspaces: list[WorkspaceContextResponse]


class MeContextResponse(BaseModel):
    organizations: list[OrganizationContextResponse]


def profile_response(
    request: Request,
    principal: Principal,
    initialize: bool,
) -> ProfileResponse:
    factory = cast(sessionmaker[Session] | None,
                   request.app.state.session_factory)
    if factory is None:
        raise ApiError(
            503, "DATABASE_UNAVAILABLE", "Your profile is unavailable. Try again."
        )
    try:
        with factory() as session:
            if initialize:
                # Identity is verified before this call. Concurrent retries do not
                # overwrite existing profile fields or grant any memberships.
                session.execute(
                    insert(Profile)
                    .values(id=principal.id)
                    .on_conflict_do_nothing(index_elements=[Profile.id])
                )
                session.commit()
            profile = session.get(Profile, principal.id)
            if profile is None:
                raise ApiError(
                    404, "PROFILE_NOT_FOUND", "Initialize your profile first."
                )
            return ProfileResponse(
                id=profile.id,
                email=principal.email,
                display_name=profile.display_name,
            )
    except SQLAlchemyError:
        raise ApiError(
            503, "DATABASE_UNAVAILABLE", "Your profile is unavailable. Try again."
        ) from None


@router.get("/me", response_model=ProfileResponse)
def me(
    request: Request,
    response: Response,
    principal: Annotated[Principal, Depends(current_user)],
) -> ProfileResponse:
    response.headers["Cache-Control"] = "no-store"
    return profile_response(request, principal, initialize=False)


@router.post("/me", response_model=ProfileResponse)
def initialize_me(
    request: Request,
    response: Response,
    principal: Annotated[Principal, Depends(current_user)],
) -> ProfileResponse:
    response.headers["Cache-Control"] = "no-store"
    return profile_response(request, principal, initialize=True)


@router.get("/me/context", response_model=MeContextResponse)
def me_context(
    request: Request,
    response: Response,
    principal: Annotated[Principal, Depends(current_user)],
) -> MeContextResponse:
    response.headers["Cache-Control"] = "no-store"
    factory = cast(sessionmaker[Session] | None,
                   request.app.state.session_factory)
    if factory is None:
        raise ApiError(503, "DATABASE_UNAVAILABLE",
                       "Tenant context is unavailable.")

    statement = (
        select(
            Organization.id,
            Organization.name,
            OrganizationMember.role,
            Workspace.id,
            Workspace.name,
            WorkspaceMember.role,
        )
        .join(
            OrganizationMember,
            OrganizationMember.organization_id == Organization.id,
        )
        .outerjoin(
            WorkspaceMember,
            and_(
                WorkspaceMember.organization_id == Organization.id,
                WorkspaceMember.user_id == principal.id,
            ),
        )
        .outerjoin(
            Workspace,
            and_(
                Workspace.id == WorkspaceMember.workspace_id,
                Workspace.organization_id == Organization.id,
                Workspace.deleted_at.is_(None),
            ),
        )
        .where(
            OrganizationMember.user_id == principal.id,
            Organization.deleted_at.is_(None),
        )
        .order_by(
            Organization.created_at,
            Organization.id,
            Workspace.created_at,
            Workspace.id,
        )
    )

    try:
        with factory() as session:
            rows = session.execute(statement).all()
    except SQLAlchemyError:
        raise ApiError(
            503, "DATABASE_UNAVAILABLE", "Tenant context is unavailable."
        ) from None

    organizations: dict[UUID, OrganizationContextResponse] = {}
    for (
        organization_id,
        organization_name,
        organization_role,
        workspace_id,
        workspace_name,
        workspace_role,
    ) in rows:
        if organization_id not in organizations:
            organizations[organization_id] = OrganizationContextResponse(
                id=organization_id,
                name=organization_name,
                role=organization_role,
                workspaces=[],
            )
        if workspace_id is not None:
            organizations[organization_id].workspaces.append(
                WorkspaceContextResponse(
                    id=workspace_id,
                    name=workspace_name,
                    role=workspace_role,
                )
            )

    return MeContextResponse(organizations=list(organizations.values()))
