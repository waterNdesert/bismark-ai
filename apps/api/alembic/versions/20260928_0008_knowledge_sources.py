"""Create tenant-scoped knowledge sources.

Revision ID: 20260928_0008
Revises: 20260927_0007
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260928_0008"
down_revision = "20260927_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("connection_reference", sa.Text(), nullable=True),
        sa.Column("sync_status", sa.Text(), nullable=True),
        sa.Column("sync_cursor", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
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
            "length(btrim(name)) > 0",
            name="ck_knowledge_sources_name_not_blank",
        ),
        sa.CheckConstraint(
            "source_type IN ('manual_upload')",
            name="ck_knowledge_sources_source_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'disabled', 'error')",
            name="ck_knowledge_sources_status",
        ),
        sa.CheckConstraint(
            "sync_status IS NULL OR sync_status IN "
            "('idle', 'syncing', 'success', 'failed')",
            name="ck_knowledge_sources_sync_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "organization_id"],
            ["workspaces.id", "workspaces.organization_id"],
            name="fk_knowledge_sources_workspace_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["profiles.id"],
            name="fk_knowledge_sources_created_by",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_sources"),
    )
    op.create_index(
        "ix_knowledge_sources_organization_id",
        "knowledge_sources",
        ["organization_id"],
    )
    op.create_index(
        "ix_knowledge_sources_workspace_id",
        "knowledge_sources",
        ["workspace_id"],
    )
    op.create_index(
        "ix_knowledge_sources_created_by",
        "knowledge_sources",
        ["created_by"],
    )
    op.create_index(
        "ix_knowledge_sources_source_type",
        "knowledge_sources",
        ["source_type"],
    )
    op.create_index(
        "ix_knowledge_sources_status",
        "knowledge_sources",
        ["status"],
    )
    op.create_index(
        "ix_knowledge_sources_organization_workspace",
        "knowledge_sources",
        ["organization_id", "workspace_id"],
    )
    op.execute(
        "ALTER TABLE public.knowledge_sources ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        "REVOKE ALL PRIVILEGES ON TABLE public.knowledge_sources "
        "FROM anon, authenticated"
    )


def downgrade() -> None:
    op.drop_table("knowledge_sources")
