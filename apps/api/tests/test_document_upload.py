from collections.abc import Iterator
from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.auth.dependencies import current_user
from app.auth.organizations import require_organization_membership
from app.auth.verifier import Principal
from app.auth.workspaces import require_workspace_membership
from app.core.config import Settings
from app.core.errors import ApiError, api_error_handler
from app.documents.routes import router
from app.storage.errors import StorageError

USER_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
ORGANIZATION_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
WORKSPACE_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")


class FakeSession:
    def __init__(self, *, fail_commit: bool = False) -> None:
        self.document: Any = None
        self.fail_commit = fail_commit
        self.committed = False
        self.rolled_back = False

    def begin_nested(self):
        return nullcontext()

    def scalar(self, statement: Any) -> None:
        return None

    def add(self, document: Any) -> None:
        from app.db.models import Document

        if isinstance(document, Document):
            self.document = document

    def flush(self) -> None:
        now = datetime.now(timezone.utc)
        if self.document is not None:
            self.document.created_at = now
            self.document.updated_at = now

    def commit(self) -> None:
        if self.fail_commit:
            raise SQLAlchemyError("database secret detail")
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakeSessionFactory:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    def __call__(self) -> "FakeSessionFactory":
        return self

    def __enter__(self) -> FakeSession:
        return self.session

    def __exit__(self, *_: object) -> None:
        return None


class FakeStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, str]] = []
        self.deletes: list[str] = []
        self.fail_upload = False
        self.fail_delete = False

    def upload(self, storage_path: str, content: bytes, mime_type: str) -> None:
        if self.fail_upload:
            raise StorageError("private storage failure")
        self.uploads.append((storage_path, content, mime_type))

    def delete(self, storage_path: str) -> None:
        if self.fail_delete:
            raise StorageError("private cleanup failure")
        self.deletes.append(storage_path)


def build_client(
    *, fail_commit: bool = False, authenticate: bool = True
) -> tuple[TestClient, FakeSession, FakeStorage]:
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    app.include_router(router)
    session = FakeSession(fail_commit=fail_commit)
    storage = FakeStorage()
    app.state.session_factory = FakeSessionFactory(session)
    app.state.storage_service = storage
    app.state.settings = Settings()

    if authenticate:
        app.dependency_overrides[current_user] = lambda: Principal(
            id=USER_ID, email="member@example.test", role="authenticated"
        )
    app.dependency_overrides[require_organization_membership] = lambda: "member"
    app.dependency_overrides[require_workspace_membership] = lambda: "member"
    return TestClient(app), session, storage


def upload(client: TestClient, *, filename: str = "report.txt", mime: str = "text/plain"):
    return client.post(
        f"/api/v1/organizations/{ORGANIZATION_ID}/workspaces/{WORKSPACE_ID}/documents",
        files={"file": (filename, b"document body", mime)},
    )


def test_success_upload_saves_tenant_row_and_safe_response() -> None:
    client, session, storage = build_client()
    response = upload(client, filename="../quarterly report.txt")

    assert response.status_code == 201
    assert session.committed
    assert session.document.organization_id == ORGANIZATION_ID
    assert session.document.workspace_id == WORKSPACE_ID
    assert session.document.uploaded_by == USER_ID
    assert session.document.original_filename == "../quarterly report.txt"
    assert session.document.storage_bucket == "knowledge-documents"
    assert session.document.status == "uploaded"
    assert session.document.size_bytes == len(b"document body")
    assert len(storage.uploads) == 1
    storage_path, _, _ = storage.uploads[0]
    assert storage_path.startswith(
        f"organizations/{ORGANIZATION_ID}/workspaces/{WORKSPACE_ID}/documents/"
    )
    assert ".." not in storage_path
    assert set(response.json()) == {
        "id",
        "organization_id",
        "workspace_id",
        "original_filename",
        "mime_type",
        "size_bytes",
        "status",
        "created_at",
    }
    assert "storage_path" not in response.text
    assert "service" not in response.text.lower()


def test_upload_requires_authentication() -> None:
    client, _, _ = build_client(authenticate=False)
    response = upload(client)
    assert response.status_code == 401


def test_organization_non_member_is_forbidden() -> None:
    client, _, _ = build_client()

    def deny() -> None:
        raise ApiError(403, "ORGANIZATION_ACCESS_DENIED", "Access denied.")

    client.app.dependency_overrides[require_organization_membership] = deny
    response = upload(client)
    assert response.status_code == 403


def test_workspace_non_member_is_forbidden() -> None:
    client, _, _ = build_client()

    def deny() -> None:
        raise ApiError(403, "WORKSPACE_ACCESS_DENIED", "Access denied.")

    client.app.dependency_overrides[require_workspace_membership] = deny
    response = upload(client)
    assert response.status_code == 403


def test_empty_filename_is_rejected() -> None:
    client, session, storage = build_client()
    response = upload(client, filename="")
    assert response.status_code == 400
    assert session.document is None
    assert not storage.uploads


def test_unsupported_mime_type_is_rejected() -> None:
    client, session, storage = build_client()
    response = upload(client, mime="application/x-executable")
    assert response.status_code == 400
    assert session.document is None
    assert not storage.uploads


def test_storage_failure_does_not_create_document_row() -> None:
    client, session, storage = build_client()
    storage.fail_upload = True

    response = upload(client)

    assert response.status_code == 502
    assert session.document is None
    assert not session.committed
    assert "private storage failure" not in response.text


def test_database_failure_triggers_storage_cleanup() -> None:
    client, session, storage = build_client(fail_commit=True)

    response = upload(client)

    assert response.status_code == 500
    assert session.rolled_back
    assert storage.uploads
    assert storage.deletes == [storage.uploads[0][0]]
    assert "database secret detail" not in response.text


def test_invalid_mime_metadata_is_rejected() -> None:
    client, session, storage = build_client()
    response = upload(client, mime="not-a-content-type")
    assert response.status_code == 400
    assert session.document is None
    assert not storage.uploads
