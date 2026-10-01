from collections.abc import Iterator
from typing import cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import current_user
from app.auth.verifier import Principal
from app.core.errors import ApiError, api_error_handler
from app.users.routes import router

USER = UUID(int=1)
OTHER_USER = UUID(int=2)
ORG_A = UUID(int=10)
ORG_B = UUID(int=20)
ORG_C = UUID(int=30)
WORKSPACE_A1 = UUID(int=101)
WORKSPACE_A2 = UUID(int=102)
WORKSPACE_B1 = UUID(int=201)


@pytest.fixture
def context_client() -> Iterator[tuple[TestClient, Session]]:
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE organizations ("
            "id CHAR(32) PRIMARY KEY, name TEXT NOT NULL, "
            "created_at DATETIME NOT NULL, deleted_at DATETIME NULL)"
        ))
        connection.execute(text(
            "CREATE TABLE organization_members ("
            "organization_id CHAR(32) NOT NULL, user_id CHAR(32) NOT NULL, "
            "role TEXT NOT NULL, PRIMARY KEY (organization_id, user_id))"
        ))
        connection.execute(text(
            "CREATE TABLE workspaces ("
            "id CHAR(32) PRIMARY KEY, organization_id CHAR(32) NOT NULL, "
            "name TEXT NOT NULL, created_at DATETIME NOT NULL, "
            "deleted_at DATETIME NULL)"
        ))
        connection.execute(text(
            "CREATE TABLE workspace_members ("
            "organization_id CHAR(32) NOT NULL, workspace_id CHAR(32) NOT NULL, "
            "user_id CHAR(32) NOT NULL, role TEXT NOT NULL, "
            "PRIMARY KEY (organization_id, workspace_id, user_id))"
        ))

    session_factory = sessionmaker(bind=engine)
    with Session(engine) as session:
        app = FastAPI()
        app.add_exception_handler(ApiError, api_error_handler)
        app.include_router(router)
        app.state.session_factory = session_factory
        app.dependency_overrides[current_user] = lambda: Principal(
            id=USER, email="member@example.test", role="authenticated"
        )
        with TestClient(app) as client:
            yield client, session
    engine.dispose()


def add_organization(
    session: Session,
    organization_id: UUID,
    name: str,
    created_at: str,
    role: str,
    user_id: UUID = USER,
    deleted_at: str | None = None,
) -> None:
    session.execute(
        text("INSERT INTO organizations VALUES (:id, :name, :created, :deleted)"),
        {
            "id": organization_id.hex,
            "name": name,
            "created": created_at,
            "deleted": deleted_at,
        },
    )
    session.execute(
        text("INSERT INTO organization_members VALUES (:org, :user, :role)"),
        {
            "org": organization_id.hex,
            "user": user_id.hex,
            "role": role,
        },
    )
    session.commit()


def add_workspace(
    session: Session,
    organization_id: UUID,
    workspace_id: UUID,
    name: str,
    created_at: str,
    role: str,
    user_id: UUID = USER,
    deleted_at: str | None = None,
) -> None:
    session.execute(
        text("INSERT INTO workspaces VALUES (:id, :org, :name, :created, :deleted)"),
        {
            "id": workspace_id.hex,
            "org": organization_id.hex,
            "name": name,
            "created": created_at,
            "deleted": deleted_at,
        },
    )
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


def test_context_requires_authentication(
    context_client: tuple[TestClient, Session],
) -> None:
    client, _ = context_client
    cast(FastAPI, client.app).dependency_overrides.pop(current_user)
    response = client.get("/api/v1/me/context")
    assert response.status_code == 401


def test_context_returns_empty_organizations_for_user_without_memberships(
    context_client: tuple[TestClient, Session],
) -> None:
    client, _ = context_client
    response = client.get("/api/v1/me/context")
    assert response.status_code == 200
    assert response.json() == {"organizations": []}


@pytest.mark.parametrize("role", ["owner", "admin", "member"])
def test_context_returns_organization_role(
    context_client: tuple[TestClient, Session], role: str
) -> None:
    client, session = context_client
    add_organization(session, ORG_A, "Acme", "2026-01-01 00:00:00", role)
    response = client.get("/api/v1/me/context")
    assert response.status_code == 200
    assert response.json()["organizations"] == [
        {"id": str(ORG_A), "name": "Acme", "role": role, "workspaces": []}
    ]


def test_context_returns_only_current_users_organizations(
    context_client: tuple[TestClient, Session],
) -> None:
    client, session = context_client
    add_organization(session, ORG_A, "Mine", "2026-01-01 00:00:00", "member")
    add_organization(
        session, ORG_B, "Other user", "2026-01-02 00:00:00", "owner", OTHER_USER
    )
    response = client.get("/api/v1/me/context")
    assert [org["id"] for org in response.json()["organizations"]] == [
        str(ORG_A)]


def test_context_returns_only_explicit_workspace_memberships(
    context_client: tuple[TestClient, Session],
) -> None:
    client, session = context_client
    add_organization(session, ORG_A, "Acme", "2026-01-01 00:00:00", "owner")
    add_workspace(
        session, ORG_A, WORKSPACE_A1, "Engineering", "2026-01-02 00:00:00", "admin"
    )
    response = client.get("/api/v1/me/context")
    assert response.json()["organizations"][0]["workspaces"] == [
        {"id": str(WORKSPACE_A1), "name": "Engineering", "role": "admin"}
    ]


def test_organization_admin_without_workspace_row_gets_no_workspaces(
    context_client: tuple[TestClient, Session],
) -> None:
    client, session = context_client
    add_organization(session, ORG_A, "Acme", "2026-01-01 00:00:00", "admin")
    session.execute(text(
        "INSERT INTO workspaces VALUES (:id, :org, :name, :created, NULL)"
    ), {
        "id": WORKSPACE_A1.hex,
        "org": ORG_A.hex,
        "name": "Restricted",
        "created": "2026-01-02 00:00:00",
    })
    session.commit()
    response = client.get("/api/v1/me/context")
    assert response.json()["organizations"][0]["workspaces"] == []


def test_context_never_returns_workspace_from_another_organization(
    context_client: tuple[TestClient, Session],
) -> None:
    client, session = context_client
    add_organization(session, ORG_A, "Acme", "2026-01-01 00:00:00", "member")
    add_organization(session, ORG_B, "Other", "2026-01-01 00:00:00", "member")
    add_workspace(
        session, ORG_B, WORKSPACE_B1, "Other workspace", "2026-01-02 00:00:00",
        "member",
    )
    response = client.get("/api/v1/me/context")
    orgs = response.json()["organizations"]
    acme = next(org for org in orgs if org["id"] == str(ORG_A))
    assert acme["workspaces"] == []


def test_context_never_returns_another_users_workspace_membership(
    context_client: tuple[TestClient, Session],
) -> None:
    client, session = context_client
    add_organization(session, ORG_A, "Acme", "2026-01-01 00:00:00", "member")
    session.execute(text(
        "INSERT INTO workspaces VALUES (:id, :org, :name, :created, NULL)"
    ), {
        "id": WORKSPACE_A1.hex,
        "org": ORG_A.hex,
        "name": "Private to another user",
        "created": "2026-01-02 00:00:00",
    })
    session.execute(text(
        "INSERT INTO workspace_members VALUES (:org, :workspace, :user, :role)"
    ), {
        "org": ORG_A.hex,
        "workspace": WORKSPACE_A1.hex,
        "user": OTHER_USER.hex,
        "role": "member",
    })
    session.commit()
    response = client.get("/api/v1/me/context")
    assert response.json()["organizations"][0]["workspaces"] == []


def test_context_excludes_soft_deleted_organizations_and_workspaces(
    context_client: tuple[TestClient, Session],
) -> None:
    client, session = context_client
    add_organization(
        session, ORG_A, "Deleted org", "2026-01-01 00:00:00", "member",
        deleted_at="2026-02-01 00:00:00",
    )
    add_organization(session, ORG_B, "Active org",
                     "2026-01-02 00:00:00", "member")
    add_workspace(
        session, ORG_B, WORKSPACE_B1, "Deleted workspace", "2026-01-03 00:00:00",
        "member", deleted_at="2026-02-01 00:00:00",
    )
    response = client.get("/api/v1/me/context")
    assert [org["id"] for org in response.json()["organizations"]] == [
        str(ORG_B)]
    assert response.json()["organizations"][0]["workspaces"] == []


def test_context_ordering_and_response_fields_are_deterministic(
    context_client: tuple[TestClient, Session],
) -> None:
    client, session = context_client
    add_organization(session, ORG_B, "Later org",
                     "2026-02-01 00:00:00", "member")
    add_organization(session, ORG_A, "Earlier org",
                     "2026-01-01 00:00:00", "owner")
    add_workspace(
        session, ORG_A, WORKSPACE_A2, "Later workspace", "2026-02-02 00:00:00", "member"
    )
    add_workspace(
        session,
        ORG_A,
        WORKSPACE_A1,
        "Earlier workspace",
        "2026-01-02 00:00:00",
        "admin",
    )
    response = client.get("/api/v1/me/context")
    payload = response.json()
    assert [org["id"]
            for org in payload["organizations"]] == [str(ORG_A), str(ORG_B)]
    assert [
        workspace["id"] for workspace in payload["organizations"][0]["workspaces"]
    ] == [str(WORKSPACE_A1), str(WORKSPACE_A2)]
    assert set(payload) == {"organizations"}
    assert set(payload["organizations"][0]) == {
        "id", "name", "role", "workspaces"}
    assert set(payload["organizations"][0]["workspaces"][0]) == {
        "id", "name", "role"}
