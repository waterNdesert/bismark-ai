from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.auth.dependencies import current_user
from app.auth.verifier import Principal
from app.core.errors import ApiError
from app.db.models import Profile

router = APIRouter(prefix="/api/v1", tags=["current user"])


class ProfileResponse(BaseModel):
    id: UUID
    email: str
    display_name: str | None


def profile_response(
    request: Request,
    principal: Principal,
    initialize: bool,
) -> ProfileResponse:
    factory = cast(sessionmaker[Session] | None, request.app.state.session_factory)
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
