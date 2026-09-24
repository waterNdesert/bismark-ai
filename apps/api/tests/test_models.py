from typing import Any, cast

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Table, UniqueConstraint

from app.db.base import Base
from app.db.models import (
    Organization,
    OrganizationMember,
    Profile,
    Workspace,
    WorkspaceMember,
)


def table_for(model: Any) -> Table:
    return cast(Table, model.__table__)


def test_phase_1b_tables_are_registered() -> None:
    assert set(Base.metadata.tables) >= {
        "profiles",
        "organizations",
        "organization_members",
        "workspaces",
        "workspace_members",
    }


def test_primary_keys_and_required_columns() -> None:
    for model in (
        Profile,
        Organization,
        OrganizationMember,
        Workspace,
        WorkspaceMember,
    ):
        table = table_for(model)
        assert len(table.primary_key.columns) == 1
        assert table.c.created_at.nullable is False
        assert table.c.updated_at.nullable is False

    assert table_for(Profile).c.id.nullable is False
    assert table_for(Organization).c.name.nullable is False
    assert table_for(Organization).c.slug.nullable is False
    assert table_for(OrganizationMember).c.organization_id.nullable is False
    assert table_for(Workspace).c.organization_id.nullable is False
    assert table_for(WorkspaceMember).c.organization_id.nullable is False


def test_unique_constraints_and_role_checks() -> None:
    assert {
        constraint.name
        for constraint in table_for(Organization).constraints
        if isinstance(constraint, UniqueConstraint)
    } == {"uq_organizations_slug"}
    assert {
        constraint.name
        for constraint in table_for(OrganizationMember).constraints
        if isinstance(constraint, UniqueConstraint)
    } == {"uq_organization_members_org_user"}
    assert {
        constraint.name
        for constraint in table_for(Workspace).constraints
        if isinstance(constraint, UniqueConstraint)
    } == {"uq_workspaces_org_slug", "uq_workspaces_id_org"}
    assert {
        constraint.name
        for constraint in table_for(WorkspaceMember).constraints
        if isinstance(constraint, UniqueConstraint)
    } == {"uq_workspace_members_workspace_user"}

    assert "ck_organization_members_role" in {
        constraint.name
        for constraint in table_for(OrganizationMember).constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert "ck_workspace_members_role" in {
        constraint.name
        for constraint in table_for(WorkspaceMember).constraints
        if isinstance(constraint, CheckConstraint)
    }


def test_auth_and_tenant_safe_foreign_keys() -> None:
    profile_fk = next(iter(table_for(Profile).foreign_keys))
    assert str(profile_fk.target_fullname) == "auth.users.id"

    workspace_member_fks = {
        tuple(foreign_key.column_keys): foreign_key
        for foreign_key in table_for(WorkspaceMember).foreign_key_constraints
        if isinstance(foreign_key, ForeignKeyConstraint)
    }
    assert ("workspace_id", "organization_id") in workspace_member_fks
    assert ("organization_id", "user_id") in workspace_member_fks
    assert [
        str(element.target_fullname)
        for element in workspace_member_fks[
            ("workspace_id", "organization_id")
        ].elements
    ] == ["workspaces.id", "workspaces.organization_id"]
    assert [
        str(element.target_fullname)
        for element in workspace_member_fks[("organization_id", "user_id")].elements
    ] == ["organization_members.organization_id", "organization_members.user_id"]


def test_expected_indexes_exist() -> None:
    assert {index.name for index in table_for(OrganizationMember).indexes} == {
        "ix_organization_members_user_org",
        "ix_organization_members_org_role",
    }
    assert {index.name for index in table_for(Workspace).indexes} == {
        "ix_workspaces_organization_created",
    }
    assert {index.name for index in table_for(WorkspaceMember).indexes} == {
        "ix_workspace_members_user_org",
        "ix_workspace_members_org_workspace",
        "ix_workspace_members_workspace_role",
    }
