from typing import Literal, Protocol
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from app.core.errors import ApiError


class Principal(BaseModel):
    id: UUID
    email: str
    role: Literal["authenticated"]
    is_anonymous: Literal[False] = False


class AuthVerifier(Protocol):
    def verify(self, token: str) -> Principal: ...


class SupabaseAuthVerifier:
    """Verify with the configured Auth server; never decode untrusted JWT claims."""

    def __init__(self, url: str, key: str, client: httpx.Client) -> None:
        self.url = url.rstrip("/") + "/auth/v1/user"
        self.key = key
        self.client = client

    def verify(self, token: str) -> Principal:
        try:
            response = self.client.get(
                self.url,
                headers={"apikey": self.key, "Authorization": f"Bearer {token}"},
            )
        except httpx.RequestError:
            raise ApiError(
                503, "AUTH_UNAVAILABLE", "Sign-in verification is unavailable."
            ) from None
        if response.status_code in (401, 403):
            raise ApiError(401, "TOKEN_INVALID", "Your session is invalid or expired.")
        if response.status_code != 200:
            raise ApiError(
                503, "AUTH_UNAVAILABLE", "Sign-in verification is unavailable."
            )
        try:
            return Principal.model_validate(response.json())
        except (ValueError, ValidationError):
            raise ApiError(
                401, "TOKEN_INVALID", "A valid user session is required."
            ) from None
