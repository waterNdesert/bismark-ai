from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.health import check_database
from app.db.session import create_database_engine, get_database_url
from app.main import app, create_app


def test_app_imports() -> None:
    assert isinstance(app, FastAPI)


def test_settings_default_environment() -> None:
    assert Settings().app_env == "development"


def test_database_settings_are_optional_until_database_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(
        supabase_url="https://project.supabase.co",
        supabase_anon_key=SecretStr("anon-test-key"),
        supabase_service_role_key=SecretStr("service-test-key"),
    )
    assert settings.database_url is None
    assert settings.supabase_service_role_key is not None
    assert settings.supabase_service_role_key.get_secret_value() == "service-test-key"


def test_database_url_uses_psycopg_driver_without_exposing_password() -> None:
    settings = Settings(
        database_url=SecretStr("postgresql://user:password@localhost/db")
    )
    assert (
        get_database_url(settings) == "postgresql+psycopg://user:password@localhost/db"
    )

    engine = create_database_engine(settings)
    assert engine.url.drivername == "postgresql+psycopg"
    assert engine.url.render_as_string(hide_password=True).endswith("@localhost/db")
    engine.dispose()


def test_database_health_helper_executes_select_one() -> None:
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    assert check_database(Settings(), engine) is True
    connection.execute.assert_called_once()
    engine.dispose.assert_not_called()


def test_database_health_helper_fails_closed() -> None:
    engine = MagicMock()
    engine.connect.side_effect = SQLAlchemyError("unavailable")
    assert check_database(Settings(), engine) is False


def test_database_readiness_returns_generic_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.api.routes.health.check_database", lambda settings: False)
    with TestClient(create_app(Settings())) as client:
        response = client.get("/ready/database")
    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}


@pytest.mark.parametrize("path,status", [("/health", "ok"), ("/ready", "ready")])
def test_health_routes(path: str, status: str) -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"status": status}


@pytest.mark.parametrize(
    "origin,allowed",
    [("http://localhost:3000", True), ("https://untrusted.example", False)],
)
def test_cors(origin: str, allowed: bool) -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.get("/health", headers={"Origin": origin})
    assert (response.headers.get("access-control-allow-origin") == origin) is allowed
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize(
    "origins", ["*", "https://*.example.com", "https://example.com/path"]
)
def test_unsafe_origins_rejected(origins: str) -> None:
    with pytest.raises(ValidationError):
        Settings(cors_origins=origins)


def test_settings_load_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "Configured API")
    monkeypatch.setenv("CORS_ORIGINS", "https://one.example,https://two.example")
    settings = Settings()
    assert settings.app_name == "Configured API"
    assert settings.allowed_origins == ["https://one.example", "https://two.example"]
