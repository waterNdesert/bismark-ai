from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.session import create_database_engine


def check_database(settings: Settings, engine: Engine | None = None) -> bool:
    owned_engine = engine is None
    database_engine = engine or create_database_engine(settings)
    try:
        with database_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except (RuntimeError, SQLAlchemyError):
        return False
    finally:
        if owned_engine:
            database_engine.dispose()


if __name__ == "__main__":
    if not check_database(Settings()):
        raise SystemExit("database check failed")
    print("database check passed")
