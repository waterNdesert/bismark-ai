from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_env: Literal["development", "test",
                     "staging", "production"] = "development"
    app_name: str = "Bismark AI"
    app_version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO",
                       "WARNING", "ERROR", "CRITICAL"] = "INFO"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    supabase_url: str | None = None
    supabase_anon_key: SecretStr | None = None
    supabase_service_role_key: SecretStr | None = None
    supabase_storage_bucket: str = "knowledge-documents"
    max_upload_size_mb: int = Field(default=50, gt=0)
    allowed_upload_mime_types: str = (
        "application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "text/plain,text/markdown,text/html"
    )
    database_url: SecretStr | None = None
    db_pool_size: int = 10
    db_max_overflow: int = 10
    db_pool_timeout_seconds: int = 30

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, value: str | None) -> str | None:
        if not value:
            return None
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("SUPABASE_URL must be an HTTPS origin")
        return value.rstrip("/")

    @field_validator("frontend_url", "cors_origins")
    @classmethod
    def validate_origins(cls, value: str) -> str:
        for origin in value.split(","):
            parsed = urlsplit(origin.strip())
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                raise ValueError(
                    "Use explicit HTTP(S) origins without paths or credentials"
                )
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def allowed_upload_mime_type_set(self) -> frozenset[str]:
        return frozenset(
            mime_type.strip().lower()
            for mime_type in self.allowed_upload_mime_types.split(",")
            if mime_type.strip()
        )
