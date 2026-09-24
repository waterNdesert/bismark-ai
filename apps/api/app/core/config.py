from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_name: str = "Bismark AI"
    app_version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"

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
