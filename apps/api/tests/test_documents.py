import importlib.util
from io import StringIO
from pathlib import Path
from types import ModuleType

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Table, UniqueConstraint

from app.db.base import Base
from app.db.models import Document


def table_for(model: type[Document]) -> Table:
    return model.__table__


@pytest.fixture
def migration() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic/versions/20260926_0004_documents.py"
    )
    spec = importlib.util.spec_from_file_location("documents_migration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def tenant_key_migration() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic/versions/20260927_0005_documents_tenant_key.py"
    )
    spec = importlib.util.spec_from_file_location(
        "documents_tenant_key_migration", path)
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


def test_documents_table_is_registered_and_has_expected_columns() -> None:
    assert "documents" in Base.metadata.tables
    table = table_for(Document)
    assert list(table.columns.keys()) == [
        "id",
        "organization_id",
        "workspace_id",
        "source_id",
        "uploaded_by",
        "original_filename",
        "storage_bucket",
        "storage_path",
        "mime_type",
        "size_bytes",
        "status",
        "created_at",
        "updated_at",
        "deleted_at",
    ]
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert str(table.c.id.server_default.arg) == "gen_random_uuid()"


def test_documents_required_and_nullable_columns() -> None:
    table = table_for(Document)
    for column in (
        "id",
        "organization_id",
        "workspace_id",
        "uploaded_by",
        "original_filename",
        "storage_bucket",
        "storage_path",
        "status",
        "created_at",
        "updated_at",
    ):
        assert table.c[column].nullable is False
    for column in ("source_id", "mime_type", "size_bytes", "deleted_at"):
        assert table.c[column].nullable is True


def test_documents_has_restricting_tenant_and_uploader_foreign_keys() -> None:
    foreign_keys = {
        tuple(constraint.column_keys): constraint
        for constraint in table_for(Document).foreign_key_constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    tenant_fk = foreign_keys[("workspace_id", "organization_id")]
    assert [element.target_fullname for element in tenant_fk.elements] == [
        "workspaces.id",
        "workspaces.organization_id",
    ]
    assert tenant_fk.ondelete == "RESTRICT"

    uploader_fk = foreign_keys[("uploaded_by",)]
    assert [element.target_fullname for element in uploader_fk.elements] == [
        "profiles.id"
    ]
    assert uploader_fk.ondelete == "RESTRICT"


def test_documents_has_filename_bucket_path_and_status_checks() -> None:
    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in table_for(Document).constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert checks == {
        "ck_documents_original_filename_not_blank":
            "length(btrim(original_filename)) > 0",
        "ck_documents_storage_bucket":
            "storage_bucket = 'knowledge-documents'",
        "ck_documents_storage_path_not_blank": "length(btrim(storage_path)) > 0",
        "ck_documents_status":
            "status IN ('uploaded', 'processing', 'ready', 'failed')",
    }


def test_documents_has_unique_storage_path_and_expected_indexes() -> None:
    table = table_for(Document)
    unique_constraints = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert unique_constraints == {
        "uq_documents_storage_path",
        "uq_documents_id_organization_workspace",
    }
    tenant_unique = next(
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_documents_id_organization_workspace"
    )
    assert tuple(column.name for column in tenant_unique.columns) == (
        "id",
        "organization_id",
        "workspace_id",
    )
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert {index.name for index in table.indexes} == {
        "ix_documents_organization_id",
        "ix_documents_workspace_id",
        "ix_documents_uploaded_by",
        "ix_documents_status",
        "ix_documents_source_id",
        "ix_documents_organization_workspace",
    }


def test_documents_migration_creates_only_the_requested_table(
    migration: ModuleType,
) -> None:
    assert migration.revision == "20260926_0004"
    assert migration.down_revision == "20260925_0003"
    upgrade_sql = render(migration, "upgrade")
    assert upgrade_sql.count("CREATE TABLE documents") == 1
    assert "CREATE TABLE " not in upgrade_sql.replace(
        "CREATE TABLE documents", "")
    assert "ON DELETE RESTRICT" in upgrade_sql
    assert "storage_bucket = 'knowledge-documents'" in upgrade_sql
    downgrade_sql = render(migration, "downgrade")
    assert "DROP TABLE documents" in downgrade_sql
    assert downgrade_sql.count("DROP TABLE") == 1


def test_tenant_key_migration_only_adds_and_drops_the_constraint(
    tenant_key_migration: ModuleType,
) -> None:
    assert tenant_key_migration.revision == "20260927_0005"
    assert tenant_key_migration.down_revision == "20260926_0004"
    upgrade_sql = render(tenant_key_migration, "upgrade")
    assert upgrade_sql.count("ADD CONSTRAINT") == 1
    assert (
        "ALTER TABLE documents ADD CONSTRAINT "
        "uq_documents_id_organization_workspace UNIQUE "
        "(id, organization_id, workspace_id)"
    ) in upgrade_sql
    assert "CREATE TABLE" not in upgrade_sql
    downgrade_sql = render(tenant_key_migration, "downgrade")
    assert downgrade_sql.count("DROP CONSTRAINT") == 1
    assert (
        "ALTER TABLE documents DROP CONSTRAINT "
        "uq_documents_id_organization_workspace"
    ) in downgrade_sql
    assert "DROP TABLE" not in downgrade_sql
