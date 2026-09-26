import importlib.util
from io import StringIO
from pathlib import Path
from types import ModuleType

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.fixture
def migration() -> ModuleType:
    path = Path(__file__).parents[1] / "alembic/versions/20260925_0003_tenancy_rls.py"
    spec = importlib.util.spec_from_file_location("tenancy_rls", path)
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


def test_revision_and_five_tables_enabled(migration: ModuleType) -> None:
    assert migration.down_revision == "20260924_0002"
    sql = render(migration, "upgrade")
    assert sql.count("ENABLE ROW LEVEL SECURITY") == 5
    for table in (
        "profiles",
        "organizations",
        "organization_members",
        "workspaces",
        "workspace_members",
    ):
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE TABLE" not in sql
    assert "DROP CONSTRAINT" not in sql
    assert "FORCE ROW LEVEL SECURITY" not in sql
    assert "service_role" not in sql


def test_profile_update_cannot_change_identity(migration: ModuleType) -> None:
    sql = render(migration, "upgrade")
    assert "FOR SELECT TO authenticated USING (id = (SELECT auth.uid()))" in sql
    assert (
        "FOR UPDATE TO authenticated USING (id = (SELECT auth.uid())) "
        "WITH CHECK (id = (SELECT auth.uid()))"
    ) in sql


def test_no_administration_write_policies(migration: ModuleType) -> None:
    sql = render(migration, "upgrade")
    assert sql.count("CREATE POLICY") == 6
    assert sql.count("FOR SELECT TO authenticated") == 5
    assert sql.count("FOR UPDATE TO authenticated") == 1
    for forbidden in ("FOR ALL", "FOR INSERT", "FOR DELETE", "USING (true)"):
        assert forbidden not in sql


def test_organization_read_policies_share_scoped_check(migration: ModuleType) -> None:
    sql = render(migration, "upgrade")
    for table, column in (
        ("organizations", "id"),
        ("organization_members", "organization_id"),
        ("workspaces", "organization_id"),
    ):
        assert (
            f"ON public.{table} FOR SELECT TO authenticated "
            f"USING (bismark_rls.is_org_member({column}))"
        ) in sql
    assert "membership.organization_id = target_org" in sql
    assert sql.count("membership.user_id = auth.uid()") == 2


def test_workspace_check_requires_both_memberships_and_org_scope(
    migration: ModuleType,
) -> None:
    sql = render(migration, "upgrade")
    assert (
        "USING (bismark_rls.is_workspace_member(organization_id, workspace_id))" in sql
    )
    assert "membership.workspace_id = target_workspace" in sql
    assert "organization_membership.organization_id = membership.organization_id" in sql
    assert "organization_membership.user_id = membership.user_id" in sql
    assert "membership.role IN ('admin', 'member')" in sql


def test_nonrecursive_helpers_are_restricted(migration: ModuleType) -> None:
    sql = render(migration, "upgrade")
    assert (
        sql.count("SECURITY DEFINER SET search_path = '' SET row_security = off") == 2
    )
    assert sql.count("SELECT auth.uid() IS NOT NULL AND EXISTS") == 2
    assert "REVOKE ALL ON SCHEMA bismark_rls FROM PUBLIC, anon, authenticated" in sql
    assert "GRANT USAGE ON SCHEMA bismark_rls TO authenticated" in sql
    for signature in ("is_org_member(uuid)", "is_workspace_member(uuid, uuid)"):
        assert (
            f"REVOKE ALL ON FUNCTION bismark_rls.{signature} FROM PUBLIC, anon" in sql
        )
        assert (
            f"GRANT EXECUTE ON FUNCTION bismark_rls.{signature} TO authenticated" in sql
        )


def test_downgrade_removes_policies_but_keeps_fail_closed_rls(
    migration: ModuleType,
) -> None:
    sql = render(migration, "downgrade")
    assert sql.count("DROP POLICY") == 6
    assert sql.count("DROP FUNCTION") == 2
    assert "DROP SCHEMA bismark_rls" in sql
    assert "DISABLE ROW LEVEL SECURITY" not in sql
    assert "DROP TABLE" not in sql
