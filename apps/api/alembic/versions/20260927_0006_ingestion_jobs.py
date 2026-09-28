"""Create the ingestion job metadata skeleton.

Revision ID: 20260927_0006
Revises: 20260927_0005
Create Date: 2026-09-27
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260927_0006"
down_revision = "20260927_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("document_id", postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_ingestion_jobs_status",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_ingestion_jobs_attempt_count_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "organization_id", "workspace_id"],
            [
                "documents.id",
                "documents.organization_id",
                "documents.workspace_id",
            ],
            name="fk_ingestion_jobs_document_tenant",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ingestion_jobs"),
    )
    op.create_index(
        "ix_ingestion_jobs_document_id", "ingestion_jobs", ["document_id"]
    )
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])
    op.create_index(
        "ix_ingestion_jobs_organization_workspace",
        "ingestion_jobs",
        ["organization_id", "workspace_id"],
    )
    op.create_index(
        "ix_ingestion_jobs_created_at", "ingestion_jobs", ["created_at"]
    )


def downgrade() -> None:
    op.drop_table("ingestion_jobs")
