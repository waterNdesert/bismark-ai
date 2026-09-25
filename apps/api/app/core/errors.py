import json
import logging
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status = status
        self.code = code
        self.message = message


async def api_error_handler(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, ApiError)
    request_id = str(uuid4())
    logger.warning(
        json.dumps(
            {
                "event": "api_error",
                "code": error.code,
                "request_id": request_id,
                "status": error.status,
            }
        )
    )
    headers = {"X-Request-ID": request_id, "Cache-Control": "no-store"}
    if error.status == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        status_code=error.status,
        headers=headers,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": None,
                "request_id": request_id,
            }
        },
    )
