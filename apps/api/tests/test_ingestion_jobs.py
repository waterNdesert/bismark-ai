import importlib.util
from io import StringIO
from pathlib import Path
from types import ModuleType

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Table, UniqueConstraint

from app.db.base import Base
from app.db.models import IngestionJob


def table_for(model: type[IngestionJob]) -> Table:
    return model.__table__


@pytest.fixture
def migration() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic/versions/20260927_0006_ingestion_jobs.py"
    )
    spec = importlib.util.spec_from_file_location(
        "ingestion_jobs_migration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render(migration: ModuleType, action: str) -> str:
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context):
        getattr(migration, action)()
    return " ".join(output.getvalue().split())


def test_ingestion_jobs_table_is_registered_with_expected_columns() -> None:
    assert "ingestion_jobs" in Base.metadata.tables
    table = table_for(IngestionJob)
    assert list(table.columns.keys()) == [
        "id",
        "document_id",
        "organization_id",
        "workspace_id",
        "status",
        "attempt_count",
        "error_code",
        "error_message",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    ]
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert str(table.c.id.server_default.arg) == "gen_random_uuid()"
    assert str(table.c.status.server_default.arg) == "pending"
    assert str(table.c.attempt_count.server_default.arg) == "0"


def test_ingestion_jobs_nullability_matches_schema() -> None:
    table = table_for(IngestionJob)
    required = (
        "id",
        "document_id",
        "organization_id",
        "workspace_id",
        "status",
        "attempt_count",
        "created_at",
        "updated_at",
    )
    optional = ("error_code", "error_message", "started_at", "completed_at")
    assert all(table.c[column].nullable is False for column in required)
    assert all(table.c[column].nullable is True for column in optional)


def test_ingestion_job_document_fk_is_composite_and_restricts_delete() -> None:
    foreign_keys = [
        constraint
        for constraint in table_for(IngestionJob).foreign_key_constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert len(foreign_keys) == 1
    document_fk = foreign_keys[0]
    assert tuple(document_fk.column_keys) == (
        "document_id",
        "organization_id",
        "workspace_id",
    )
    assert [element.target_fullname for element in document_fk.elements] == [
        "documents.id",
        "documents.organization_id",
        "documents.workspace_id",
    ]
    assert document_fk.ondelete == "RESTRICT"


def test_ingestion_job_status_and_attempt_count_checks() -> None:
    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in table_for(IngestionJob).constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert checks == {
        "ck_ingestion_jobs_status":
            "status IN ('pending', 'processing', 'completed', 'failed')",
        "ck_ingestion_jobs_attempt_count_nonnegative": "attempt_count >= 0",
    }


def test_ingestion_jobs_indexes_and_no_unique_document_constraint() -> None:
    table = table_for(IngestionJob)
    unique_constraints = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert unique_constraints == set()
    assert {index.name for index in table.indexes} == {
        "ix_ingestion_jobs_document_id",
        "ix_ingestion_jobs_status",
        "ix_ingestion_jobs_organization_workspace",
        "ix_ingestion_jobs_created_at",
    }


def test_ingestion_jobs_migration_only_creates_and_drops_its_table(
    migration: ModuleType,
) -> None:
    assert migration.revision == "20260927_0006"
    assert migration.down_revision == "20260927_0005"
    upgrade_sql = render(migration, "upgrade")
    assert upgrade_sql.count("CREATE TABLE ingestion_jobs") == 1
    assert "CREATE TABLE " not in upgrade_sql.replace(
        "CREATE TABLE ingestion_jobs", ""
    )
    assert "FOREIGN KEY(document_id, organization_id, workspace_id)" in upgrade_sql
    assert "REFERENCES documents (id, organization_id, workspace_id)" in upgrade_sql
    assert "ON DELETE RESTRICT" in upgrade_sql
    downgrade_sql = render(migration, "downgrade")
    assert downgrade_sql.count("DROP TABLE") == 1
    assert "DROP TABLE ingestion_jobs" in downgrade_sql
