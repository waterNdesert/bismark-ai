"""Create the initial multi-tenant schema foundation.

Revision ID: 20260924_0002
Revises: 20260924_0001
Create Date: 2026-09-24
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260924_0002"
down_revision = "20260924_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id"], ["auth.users.id"], name="fk_profiles_user", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_profiles"),
    )

    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(btrim(name)) > 0", name="ck_organizations_name_not_blank"
        ),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="ck_organizations_slug_format"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_organizations"),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )

    op.create_table(
        "organization_members",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('owner', 'admin', 'member')", name="ck_organization_members_role"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_members_organization",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["profiles.id"],
            name="fk_organization_members_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_organization_members"),
        sa.UniqueConstraint(
            "organization_id", "user_id", name="uq_organization_members_org_user"
        ),
    )
    op.create_index(
        "ix_organization_members_user_org",
        "organization_members",
        ["user_id", "organization_id"],
    )
    op.create_index(
        "ix_organization_members_org_role",
        "organization_members",
        ["organization_id", "role"],
    )

    op.create_table(
        "workspaces",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(btrim(name)) > 0", name="ck_workspaces_name_not_blank"
        ),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="ck_workspaces_slug_format"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_workspaces_organization",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_workspaces"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_workspaces_org_slug"),
        sa.UniqueConstraint("id", "organization_id", name="uq_workspaces_id_org"),
    )
    op.create_index(
        "ix_workspaces_organization_created",
        "workspaces",
        ["organization_id", "created_at"],
    )

    op.create_table(
        "workspace_members",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'member')", name="ck_workspace_members_role"
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "organization_id"],
            ["workspaces.id", "workspaces.organization_id"],
            name="fk_workspace_members_workspace_org",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["organization_members.organization_id", "organization_members.user_id"],
            name="fk_workspace_members_organization_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_workspace_members"),
        sa.UniqueConstraint(
            "workspace_id", "user_id", name="uq_workspace_members_workspace_user"
        ),
    )
    op.create_index(
        "ix_workspace_members_user_org",
        "workspace_members",
        ["user_id", "organization_id"],
    )
    op.create_index(
        "ix_workspace_members_org_workspace",
        "workspace_members",
        ["organization_id", "workspace_id"],
    )
    op.create_index(
        "ix_workspace_members_workspace_role",
        "workspace_members",
        ["workspace_id", "role"],
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_members_workspace_role", table_name="workspace_members")
    op.drop_index("ix_workspace_members_org_workspace", table_name="workspace_members")
    op.drop_index("ix_workspace_members_user_org", table_name="workspace_members")
    op.drop_table("workspace_members")
    op.drop_index("ix_workspaces_organization_created", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_index("ix_organization_members_org_role", table_name="organization_members")
    op.drop_index("ix_organization_members_user_org", table_name="organization_members")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    op.drop_table("profiles")
