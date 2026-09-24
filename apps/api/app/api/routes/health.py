from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import Settings
from app.db.health import check_database

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(BaseModel):
    status: Literal["ready"] = "ready"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    return ReadyResponse()


@router.get("/ready/database", response_model=ReadyResponse)
def ready_database() -> ReadyResponse:
    if not check_database(Settings()):
        raise HTTPException(status_code=503, detail="database unavailable")
    return ReadyResponse()
