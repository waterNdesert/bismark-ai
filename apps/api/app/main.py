import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker

from app.api.routes.health import router
from app.auth.verifier import SupabaseAuthVerifier
from app.core.config import Settings
from app.core.errors import ApiError, api_error_handler
from app.db.session import create_database_engine
from app.users.routes import router as users_router


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings if settings is not None else Settings()
    logging.basicConfig(level=config.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(config) if config.database_url else None
        application.state.session_factory = sessionmaker(engine) if engine else None
        with httpx.Client(timeout=5.0, follow_redirects=False) as client:
            application.state.auth_verifier = (
                SupabaseAuthVerifier(
                    config.supabase_url,
                    config.supabase_anon_key.get_secret_value(),
                    client,
                )
                if config.supabase_url and config.supabase_anon_key
                else None
            )
            try:
                yield
            finally:
                if engine:
                    engine.dispose()

    application = FastAPI(
        title=config.app_name, version=config.app_version, lifespan=lifespan
    )
    application.add_exception_handler(ApiError, api_error_handler)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Accept", "Content-Type", "Authorization"],
    )
    application.include_router(router)
    application.include_router(users_router)
    return application


app = create_app()
