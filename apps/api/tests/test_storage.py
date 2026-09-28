import json
from uuid import UUID

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.storage.errors import StorageError
from app.storage.paths import build_storage_path
from app.storage.service import SupabaseStorageService
from app.storage.setup_bucket import create_private_bucket

ORGANIZATION_ID = UUID("11111111-1111-4111-8111-111111111111")
WORKSPACE_ID = UUID("22222222-2222-4222-8222-222222222222")
DOCUMENT_ID = UUID("33333333-3333-4333-8333-333333333333")
SERVICE_KEY = "server-only-storage-key"


def test_storage_path_contains_all_tenant_ids() -> None:
    path = build_storage_path(
        ORGANIZATION_ID,
        WORKSPACE_ID,
        DOCUMENT_ID,
        "report.pdf",
    )

    assert path == (
        "organizations/11111111-1111-4111-8111-111111111111"
        "/workspaces/22222222-2222-4222-8222-222222222222"
        "/documents/33333333-3333-4333-8333-333333333333/report.pdf"
    )


def test_storage_path_sanitizes_filename_and_traversal() -> None:
    path = build_storage_path(
        ORGANIZATION_ID,
        WORKSPACE_ID,
        DOCUMENT_ID,
        "../../private\\report final.pdf",
    )

    assert path.endswith("/private_report_final.pdf")
    assert ".." not in path
    assert "\\" not in path


def test_storage_path_flattens_absolute_filenames() -> None:
    for filename in ("/etc/passwd", r"C:\Users\report.pdf"):
        path = build_storage_path(
            ORGANIZATION_ID,
            WORKSPACE_ID,
            DOCUMENT_ID,
            filename,
        )
        safe_filename = path.rsplit("/", maxsplit=1)[-1]

        assert not path.startswith("/")
        assert "/" not in safe_filename
        assert "\\" not in safe_filename


@pytest.mark.parametrize("filename", ["", ".", "..", "folder/", "C:\\"])
def test_storage_path_rejects_empty_filename(filename: str) -> None:
    with pytest.raises(ValueError, match="filename"):
        build_storage_path(ORGANIZATION_ID, WORKSPACE_ID,
                           DOCUMENT_ID, filename)


def test_storage_path_rejects_invalid_tenant_ids() -> None:
    with pytest.raises(ValueError, match="organization_id"):
        build_storage_path("../../tenant", WORKSPACE_ID,
                           DOCUMENT_ID, "report.pdf")


def test_storage_bucket_defaults_to_knowledge_documents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SUPABASE_STORAGE_BUCKET", raising=False)

    assert Settings().supabase_storage_bucket == "knowledge-documents"


def test_setup_creates_only_a_private_configured_bucket() -> None:
    settings = Settings(
        supabase_url="https://project.supabase.co",
        supabase_service_role_key=SecretStr(SERVICE_KEY),
    )
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(404)
        return httpx.Response(200, json={"name": "knowledge-documents"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        create_private_bucket(settings, client)

    assert [request.method for request in requests] == ["GET", "POST"]
    create_request = requests[1]
    assert create_request.url.path == "/storage/v1/bucket"
    assert json.loads(create_request.content) == {
        "id": "knowledge-documents",
        "name": "knowledge-documents",
        "public": False,
    }
    assert create_request.headers["Authorization"] == f"Bearer {SERVICE_KEY}"


def test_setup_refuses_existing_public_bucket() -> None:
    settings = Settings(
        supabase_url="https://project.supabase.co",
        supabase_service_role_key=SecretStr(SERVICE_KEY),
    )

    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"public": True})
        )
    ) as client:
        with pytest.raises(StorageError, match="must be private"):
            create_private_bucket(settings, client)


def test_storage_service_upload_download_delete_use_private_backend_api() -> None:
    settings = Settings(
        supabase_url="https://project.supabase.co",
        supabase_service_role_key=SecretStr(SERVICE_KEY),
    )
    object_path = build_storage_path(
        ORGANIZATION_ID,
        WORKSPACE_ID,
        DOCUMENT_ID,
        "report.pdf",
    )
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(200, content=b"document bytes")
        return httpx.Response(200, json={"Key": object_path})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        storage = SupabaseStorageService(settings, client)
        storage.upload(object_path, b"document bytes", "application/pdf")
        assert storage.download(object_path) == b"document bytes"
        storage.delete(object_path)

    assert [request.method for request in requests] == [
        "POST", "GET", "DELETE"]
    assert all(
        request.headers["Authorization"] == f"Bearer {SERVICE_KEY}"
        for request in requests
    )
    object_endpoint = f"/storage/v1/object/knowledge-documents/{object_path}"
    assert requests[0].url.path == object_endpoint
    assert requests[1].url.path == (
        f"/storage/v1/object/authenticated/knowledge-documents/{object_path}"
    )
    assert requests[0].headers["x-upsert"] == "false"
    assert requests[2].url.path.endswith("/object/knowledge-documents")
    assert json.loads(requests[2].content) == {"prefixes": [object_path]}


def test_storage_error_does_not_leak_credentials_or_response_body() -> None:
    settings = Settings(
        supabase_url="https://project.supabase.co",
        supabase_service_role_key=SecretStr(SERVICE_KEY),
    )
    storage_path = build_storage_path(
        ORGANIZATION_ID,
        WORKSPACE_ID,
        DOCUMENT_ID,
        "report.pdf",
    )

    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(500, text=SERVICE_KEY)
        )
    ) as client:
        storage = SupabaseStorageService(settings, client)
        with pytest.raises(StorageError) as error:
            storage.download(storage_path)

    assert SERVICE_KEY not in str(error.value)
