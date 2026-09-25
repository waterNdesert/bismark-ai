from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.verifier import AuthVerifier, Principal
from app.core.errors import ApiError

bearer = HTTPBearer(auto_error=False)


def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Principal:
    if credentials is None:
        raise ApiError(401, "AUTHENTICATION_REQUIRED", "Sign in to continue.")
    token = credentials.credentials
    if len(token) > 16384 or any(character.isspace() for character in token):
        raise ApiError(401, "TOKEN_INVALID", "Your session is invalid or expired.")
    verifier = cast(AuthVerifier | None, request.app.state.auth_verifier)
    if verifier is None:
        raise ApiError(503, "AUTH_UNAVAILABLE", "Sign-in verification is unavailable.")
    return verifier.verify(token)
