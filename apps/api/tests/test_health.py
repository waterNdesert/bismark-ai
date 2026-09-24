import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app, create_app


def test_app_imports() -> None:
    assert isinstance(app, FastAPI)


def test_settings_default_environment() -> None:
    assert Settings().app_env == "development"


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
