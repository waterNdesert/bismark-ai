from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import current_user
from app.auth.organizations import (
    OrganizationRole,
    get_organization_role,
    require_organization_membership,
)
from app.auth.verifier import Principal
from app.core.errors import ApiError, api_error_handler

USER = UUID(int=1)
OTHER_USER = UUID(int=2)
ORG = UUID(int=10)
OTHER_ORG = UUID(int=20)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE organization_members "
                "(organization_id CHAR(32), user_id CHAR(32), role VARCHAR(32))"
            )
        )
    with Session(engine) as session:
        yield session
    engine.dispose()


def add_member(
    session: Session, organization_id: UUID, user_id: UUID, role: str
) -> None:
    session.execute(
        text("INSERT INTO organization_members VALUES (:org, :user, :role)"),
        {"org": organization_id.hex, "user": user_id.hex, "role": role},
    )
    session.commit()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app = FastAPI()
    app.state.session_factory = sessionmaker(bind=session.get_bind())
    app.add_exception_handler(ApiError, api_error_handler)

    def authenticated_user() -> Principal:
        return Principal(id=USER, email="member@example.test", role="authenticated")

    app.dependency_overrides[current_user] = authenticated_user

    @app.get("/organizations/{organization_id}/check")
    def check(
        role: Annotated[OrganizationRole, Depends(require_organization_membership)],
    ) -> dict[str, str]:
        return {"role": role}

    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize("role", ["member", "owner", "admin"])
def test_member_roles_allowed(session: Session, client: TestClient, role: str) -> None:
    add_member(session, ORG, USER, role)
    response = client.get(f"/organizations/{ORG}/check")
    assert response.status_code == 200
    assert response.json() == {"role": role}


def test_authenticated_non_member_denied(client: TestClient) -> None:
    response = client.get(f"/organizations/{ORG}/check")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ORGANIZATION_ACCESS_DENIED"
    assert response.json()["error"]["message"] == "Access denied."


def test_role_lookup(session: Session) -> None:
    add_member(session, ORG, USER, "owner")
    add_member(session, OTHER_ORG, USER, "member")
    assert get_organization_role(session, ORG, USER) == "owner"
    assert get_organization_role(session, OTHER_ORG, USER) == "member"
    assert get_organization_role(session, ORG, OTHER_USER) is None


def test_membership_cannot_cross_organizations(
    session: Session,
    client: TestClient,
) -> None:
    add_member(session, ORG, USER, "owner")
    add_member(session, OTHER_ORG, OTHER_USER, "admin")
    assert client.get(f"/organizations/{ORG}/check").status_code == 200
    response = client.get(f"/organizations/{OTHER_ORG}/check")
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Access denied."
