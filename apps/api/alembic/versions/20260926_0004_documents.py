"""Create tenant-scoped document metadata.

Revision ID: 20260926_0004
Revises: 20260925_0003
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260926_0004"
down_revision = "20260925_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
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
        sa.Column("uploaded_by", postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("storage_bucket", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'uploaded'"),
            nullable=False,
        ),
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
            "length(btrim(original_filename)) > 0",
            name="ck_documents_original_filename_not_blank",
        ),
        sa.CheckConstraint(
            "storage_bucket = 'knowledge-documents'",
            name="ck_documents_storage_bucket",
        ),
        sa.CheckConstraint(
            "length(btrim(storage_path)) > 0",
            name="ck_documents_storage_path_not_blank",
        ),
        sa.CheckConstraint(
            "status IN ('uploaded', 'processing', 'ready', 'failed')",
            name="ck_documents_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "organization_id"],
            ["workspaces.id", "workspaces.organization_id"],
            name="fk_documents_workspace_org",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["profiles.id"],
            name="fk_documents_uploaded_by",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
        sa.UniqueConstraint("storage_path", name="uq_documents_storage_path"),
    )
    op.create_index(
        "ix_documents_organization_id", "documents", ["organization_id"]
    )
    op.create_index("ix_documents_workspace_id", "documents", ["workspace_id"])
    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index(
        "ix_documents_organization_workspace",
        "documents",
        ["organization_id", "workspace_id"],
    )


def downgrade() -> None:
    op.drop_table("documents")
