from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings


def get_database_url(settings: Settings) -> str:
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required for database operations")

    database_url = settings.database_url.get_secret_value()
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return database_url


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(
        get_database_url(settings),
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
    )


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
    return sessionmaker(
        bind=create_database_engine(settings),
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )
