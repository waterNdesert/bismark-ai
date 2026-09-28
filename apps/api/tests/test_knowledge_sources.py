import importlib.util
from io import StringIO
from pathlib import Path
from types import ModuleType

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Table, UniqueConstraint

from app.db.base import Base
from app.db.models import KnowledgeSource


def table_for(model: type[KnowledgeSource]) -> Table:
    return model.__table__


@pytest.fixture
def migration() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic/versions/20260928_0008_knowledge_sources.py"
    )
    spec = importlib.util.spec_from_file_location(
        "knowledge_sources_migration", path)
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


def test_knowledge_sources_table_columns_defaults_and_nullability() -> None:
    assert "knowledge_sources" in Base.metadata.tables
    table = table_for(KnowledgeSource)
    assert list(table.columns.keys()) == [
        "id",
        "organization_id",
        "workspace_id",
        "created_by",
        "source_type",
        "name",
        "status",
        "connection_reference",
        "sync_status",
        "sync_cursor",
        "last_sync_at",
        "last_sync_error",
        "created_at",
        "updated_at",
        "deleted_at",
    ]
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert str(table.c.id.server_default.arg) == "gen_random_uuid()"
    assert str(table.c.status.server_default.arg) == "active"
    for column in (
        "id", "organization_id", "workspace_id", "created_by", "source_type",
        "name", "status", "created_at", "updated_at",
    ):
        assert table.c[column].nullable is False
    for column in (
        "connection_reference", "sync_status", "sync_cursor", "last_sync_at",
        "last_sync_error", "deleted_at",
    ):
        assert table.c[column].nullable is True


def test_knowledge_sources_tenant_and_creator_fks_are_restrictive() -> None:
    foreign_keys = {
        tuple(constraint.column_keys): constraint
        for constraint in table_for(KnowledgeSource).foreign_key_constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    tenant_fk = foreign_keys[("workspace_id", "organization_id")]
    assert [element.target_fullname for element in tenant_fk.elements] == [
        "workspaces.id", "workspaces.organization_id"
    ]
    assert tenant_fk.ondelete == "RESTRICT"
    creator_fk = foreign_keys[("created_by",)]
    assert [element.target_fullname for element in creator_fk.elements] == [
        "profiles.id"
    ]
    assert creator_fk.ondelete == "RESTRICT"


def test_knowledge_sources_checks_match_v1_values() -> None:
    checks = {
        constraint.name: " ".join(str(constraint.sqltext).split())
        for constraint in table_for(KnowledgeSource).constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert checks == {
        "ck_knowledge_sources_name_not_blank": "length(btrim(name)) > 0",
        "ck_knowledge_sources_source_type": "source_type IN ('manual_upload')",
        "ck_knowledge_sources_status": "status IN ('active', 'disabled', 'error')",
        "ck_knowledge_sources_sync_status": "sync_status IS NULL OR sync_status IN ('idle', 'syncing', 'success', 'failed')",
    }


def test_knowledge_sources_expected_indexes() -> None:
    assert {index.name for index in table_for(KnowledgeSource).indexes} == {
        "uq_knowledge_sources_manual_upload_workspace",
        "ix_knowledge_sources_organization_id",
        "ix_knowledge_sources_workspace_id",
        "ix_knowledge_sources_created_by",
        "ix_knowledge_sources_source_type",
        "ix_knowledge_sources_status",
        "ix_knowledge_sources_organization_workspace",
    }


def test_knowledge_sources_migration_creates_one_private_backend_table(
    migration: ModuleType,
) -> None:
    assert migration.revision == "20260928_0008"
    assert migration.down_revision == "20260927_0007"
    upgrade_sql = render(migration, "upgrade")
    assert upgrade_sql.count("CREATE TABLE knowledge_sources") == 1
    assert "CREATE TABLE " not in upgrade_sql.replace(
        "CREATE TABLE knowledge_sources", "")
    assert "ENABLE ROW LEVEL SECURITY" in upgrade_sql
    assert "FORCE ROW LEVEL SECURITY" not in upgrade_sql
    assert "REVOKE ALL PRIVILEGES ON TABLE public.knowledge_sources FROM anon, authenticated" in upgrade_sql
    assert "CREATE POLICY" not in upgrade_sql
    assert upgrade_sql.count("CREATE INDEX") == 6
    downgrade_sql = render(migration, "downgrade")
    assert downgrade_sql.count("DROP TABLE") == 1
    assert "DROP TABLE knowledge_sources" in downgrade_sql


def test_knowledge_sources_tenant_reference_key_preserves_primary_key() -> None:
    table = table_for(KnowledgeSource)
    unique_keys = {
        constraint.name: tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert unique_keys == {
        "uq_knowledge_sources_id_organization_workspace": (
            "id", "organization_id", "workspace_id"
        ),
    }
    assert tuple(table.primary_key.columns.keys()) == ("id",)


def test_knowledge_sources_tenant_key_migration_changes_only_constraint() -> None:
    path = (
        Path(__file__).parents[1]
        / "alembic/versions/20260928_0009_knowledge_sources_tenant_key.py"
    )
    spec = importlib.util.spec_from_file_location("knowledge_source_key", path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "20260928_0009"
    assert migration.down_revision == "20260928_0008"
    assert render(migration, "upgrade") == (
        "ALTER TABLE knowledge_sources ADD CONSTRAINT "
        "uq_knowledge_sources_id_organization_workspace "
        "UNIQUE (id, organization_id, workspace_id);"
    )
    assert render(migration, "downgrade") == (
        "ALTER TABLE knowledge_sources DROP CONSTRAINT "
        "uq_knowledge_sources_id_organization_workspace;"
    )
