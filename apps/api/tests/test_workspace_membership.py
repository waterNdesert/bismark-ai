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
from app.auth.verifier import Principal
from app.auth.workspaces import (
    WorkspaceRole,
    get_workspace_role,
    require_workspace_membership,
)
from app.core.errors import ApiError, api_error_handler

USER = UUID(int=1)
OTHER_USER = UUID(int=2)
ORG = UUID(int=10)
OTHER_ORG = UUID(int=20)
WORKSPACE = UUID(int=100)
OTHER_WORKSPACE = UUID(int=200)


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
                "CREATE TABLE workspace_members "
                "(organization_id CHAR(32), workspace_id CHAR(32), "
                "user_id CHAR(32), role VARCHAR(32))"
            )
        )
    with Session(engine) as session:
        yield session
    engine.dispose()


def add_member(
    session: Session,
    organization_id: UUID,
    workspace_id: UUID,
    user_id: UUID,
    role: str,
) -> None:
    session.execute(
        text("INSERT INTO workspace_members VALUES (:org, :workspace, :user, :role)"),
        {
            "org": organization_id.hex,
            "workspace": workspace_id.hex,
            "user": user_id.hex,
            "role": role,
        },
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

    @app.get("/organizations/{organization_id}/workspaces/{workspace_id}/check")
    def check(
        role: Annotated[WorkspaceRole, Depends(require_workspace_membership)],
    ) -> dict[str, str]:
        return {"role": role}

    with TestClient(app) as client:
        yield client


def route(organization_id: UUID = ORG, workspace_id: UUID = WORKSPACE) -> str:
    return f"/organizations/{organization_id}/workspaces/{workspace_id}/check"


@pytest.mark.parametrize("role", ["admin", "member"])
def test_workspace_roles_allowed(
    session: Session, client: TestClient, role: str
) -> None:
    add_member(session, ORG, WORKSPACE, USER, role)
    response = client.get(route())
    assert response.status_code == 200
    assert response.json() == {"role": role}


def test_authenticated_non_member_denied(client: TestClient) -> None:
    response = client.get(route())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "WORKSPACE_ACCESS_DENIED"
    assert response.json()["error"]["message"] == "Access denied."


def test_workspace_role_lookup(session: Session) -> None:
    add_member(session, ORG, WORKSPACE, USER, "admin")
    add_member(session, ORG, OTHER_WORKSPACE, USER, "member")
    assert get_workspace_role(session, ORG, WORKSPACE, USER) == "admin"
    assert get_workspace_role(session, ORG, OTHER_WORKSPACE, USER) == "member"
    assert get_workspace_role(session, ORG, WORKSPACE, OTHER_USER) is None


def test_wrong_organization_workspace_combination_denied(
    session: Session, client: TestClient
) -> None:
    add_member(session, ORG, WORKSPACE, USER, "admin")
    add_member(session, OTHER_ORG, OTHER_WORKSPACE, USER, "member")
    assert client.get(route()).status_code == 200
    response = client.get(route(OTHER_ORG, WORKSPACE))
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Access denied."
    assert client.get(route(ORG, OTHER_WORKSPACE)).status_code == 403


def test_no_cross_organization_membership_confusion(
    session: Session, client: TestClient
) -> None:
    add_member(session, ORG, WORKSPACE, USER, "admin")
    add_member(session, OTHER_ORG, OTHER_WORKSPACE, OTHER_USER, "admin")
    assert client.get(route()).status_code == 200
    response = client.get(route(OTHER_ORG, OTHER_WORKSPACE))
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Access denied."
