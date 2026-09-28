import importlib.util
from io import StringIO
from pathlib import Path
from types import ModuleType

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations

TABLES = ("documents", "ingestion_jobs")
PRIVILEGES = "SELECT, INSERT, UPDATE, DELETE"


@pytest.fixture
def migration() -> ModuleType:
    path = (
        Path(__file__).parents[1]
        / "alembic/versions/20260927_0007_documents_rls.py"
    )
    spec = importlib.util.spec_from_file_location(
        "documents_rls_migration", path)
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


def test_revision_and_rls_are_enabled_only_for_documents_tables(
    migration: ModuleType,
) -> None:
    assert migration.revision == "20260927_0007"
    assert migration.down_revision == "20260927_0006"
    sql = render(migration, "upgrade")
    assert sql.count("ENABLE ROW LEVEL SECURITY") == 2
    for table in TABLES:
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY" in sql
    assert "FORCE ROW LEVEL SECURITY" not in sql
    assert "CREATE TABLE" not in sql


def test_migration_revokes_all_privileges_from_anon_and_authenticated(
    migration: ModuleType,
) -> None:
    sql = render(migration, "upgrade")
    for table in TABLES:
        assert (
            f"REVOKE ALL PRIVILEGES ON TABLE public.{table} "
            "FROM anon, authenticated"
        ) in sql
    assert sql.count("REVOKE ALL PRIVILEGES") == 2


def test_migration_creates_no_rls_policies(migration: ModuleType) -> None:
    sql = render(migration, "upgrade")
    assert "CREATE POLICY" not in sql
    assert "DROP POLICY" not in sql


def test_upgrade_touches_only_the_two_documents_tables(
    migration: ModuleType,
) -> None:
    sql = render(migration, "upgrade")
    assert sql.count("ALTER TABLE") == 2
    assert sql.count("REVOKE ALL PRIVILEGES") == 2
    for table in TABLES:
        assert f"public.{table}" in sql
    assert "public.profiles" not in sql
    assert "public.workspaces" not in sql


def test_downgrade_restores_rls_and_original_crud_grants(
    migration: ModuleType,
) -> None:
    sql = render(migration, "downgrade")
    for table in TABLES:
        assert f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY" in sql
        assert (
            f"GRANT {PRIVILEGES} ON TABLE public.{table} TO anon, authenticated"
        ) in sql
    assert sql.count("DISABLE ROW LEVEL SECURITY") == 2
    assert sql.count("GRANT SELECT, INSERT, UPDATE, DELETE") == 2
    assert "CREATE TABLE" not in sql
    assert "DROP TABLE" not in sql
