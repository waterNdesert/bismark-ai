from collections.abc import Iterator
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app.auth.verifier import Principal, SupabaseAuthVerifier
from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import Profile
from app.main import create_app

USER_A = UUID("10000000-0000-0000-0000-000000000001")
USER_B = UUID("20000000-0000-0000-0000-000000000002")


def user_payload(user_id: UUID = USER_A) -> dict[str, object]:
    return {"id": str(user_id), "email": "user@example.test", "role": "authenticated"}


@pytest.mark.parametrize("status", [401, 403])
@pytest.mark.parametrize(
    "token", ["expired.jwt", "tampered.jwt", "foreign-project.jwt"]
)
def test_auth_server_rejects_invalid_tokens(status: int, token: str) -> None:
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status, json={"msg": "private details"})
        )
    ) as client:
        verifier = SupabaseAuthVerifier("https://project.supabase.co", "public", client)
        with pytest.raises(ApiError) as result:
            verifier.verify(token)
    assert result.value.status == 401
    assert result.value.code == "TOKEN_INVALID"
    assert "private" not in result.value.message


def test_verification_uses_fixed_project_and_bearer_not_client_identity() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://project.supabase.co/auth/v1/user"
        assert request.headers["Authorization"] == "Bearer session-token"
        assert request.headers["apikey"] == "public"
        return httpx.Response(200, json=user_payload())

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        principal = SupabaseAuthVerifier(
            "https://project.supabase.co", "public", client
        ).verify("session-token")
    assert principal.id == USER_A


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {**user_payload(), "id": "not-a-uuid"},
        {**user_payload(), "role": "service_role"},
        {**user_payload(), "is_anonymous": True},
    ],
)
def test_non_user_principals_rejected(payload: dict[str, object]) -> None:
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        with pytest.raises(ApiError) as result:
            SupabaseAuthVerifier(
                "https://project.supabase.co", "public", client
            ).verify("token")
    assert result.value.status == 401


@pytest.mark.parametrize("status", [302, 429, 500, 503])
def test_provider_failure_does_not_authenticate(status: int) -> None:
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(status))
    ) as client:
        with pytest.raises(ApiError) as result:
            SupabaseAuthVerifier(
                "https://project.supabase.co", "public", client
            ).verify("token")
    assert result.value.status == 503


def test_provider_timeout_fails_closed() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("sensitive network detail")

    with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(ApiError) as result:
            SupabaseAuthVerifier(
                "https://project.supabase.co", "public", client
            ).verify("token")
    assert result.value.code == "AUTH_UNAVAILABLE"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(
        create_app(
            Settings(
                database_url=None,
                supabase_url=None,
                supabase_anon_key=None,
            )
        )
    ) as test_client:
        yield test_client


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize(
    "headers", [{}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer"}]
)
def test_missing_auth_never_opens_database(
    client: TestClient,
    method: str,
    headers: dict[str, str],
) -> None:
    response = client.request(method, "/api/v1/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]


def test_unconfigured_auth_is_unavailable(client: TestClient) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer token"})
    assert response.status_code == 503


@pytest.mark.parametrize("user_id", [USER_A, USER_B])
def test_profile_scopes_reads_and_bootstrap_to_verified_user(
    client: TestClient,
    user_id: UUID,
) -> None:
    verifier = MagicMock()
    verifier.verify.return_value = Principal.model_validate(user_payload(user_id))
    cast(FastAPI, client.app).state.auth_verifier = verifier
    factory = MagicMock()
    session = factory.return_value.__enter__.return_value
    session.get.return_value = Profile(id=user_id, display_name="Existing name")
    cast(FastAPI, client.app).state.session_factory = factory
    headers = {"Authorization": "Bearer token", "X-User-ID": str(USER_B)}
    for _ in range(2):
        response = client.post("/api/v1/me", headers=headers, json={"id": str(USER_B)})
        assert response.status_code == 200
        assert response.json()["id"] == str(user_id)
        assert response.json()["display_name"] == "Existing name"
        session.get.assert_called_with(Profile, user_id)
        statement = session.execute.call_args.args[0].compile(
            dialect=postgresql.dialect()  # type: ignore[no-untyped-call]
        )
        assert statement.params["id"] == user_id
        assert "ON CONFLICT (id) DO NOTHING" in str(statement)
    session.reset_mock()
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    session.execute.assert_not_called()
    session.commit.assert_not_called()


def test_profile_missing_and_database_failure_are_safe(client: TestClient) -> None:
    verifier = MagicMock()
    verifier.verify.return_value = Principal.model_validate(user_payload())
    cast(FastAPI, client.app).state.auth_verifier = verifier
    factory = MagicMock()
    session = factory.return_value.__enter__.return_value
    cast(FastAPI, client.app).state.session_factory = factory
    session.get.return_value = None
    headers = {"Authorization": "Bearer token"}
    assert client.get("/api/v1/me", headers=headers).status_code == 404
    session.get.side_effect = SQLAlchemyError("postgresql://secret")
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 503
    assert "secret" not in response.text


def test_cors_allows_auth_only_from_configured_origin(client: TestClient) -> None:
    for origin, expected in [
        ("http://localhost:3000", 200),
        ("https://attacker.test", 400),
    ]:
        response = client.options(
            "/api/v1/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert response.status_code == expected


def test_invalid_token_cannot_touch_profiles(client: TestClient) -> None:
    verifier = MagicMock()
    verifier.verify.side_effect = ApiError(401, "TOKEN_INVALID", "Invalid session.")
    factory = MagicMock()
    cast(FastAPI, client.app).state.auth_verifier = verifier
    cast(FastAPI, client.app).state.session_factory = factory
    response = client.post("/api/v1/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    factory.assert_not_called()


@pytest.mark.parametrize(
    "value",
    [
        "http://project.test",
        "https://user:pass@project.test",
        "https://project.test/path",
    ],
)
def test_unsafe_supabase_configuration_rejected(value: str) -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(supabase_url=value)
