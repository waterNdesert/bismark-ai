"""Link documents to tenant-scoped knowledge sources.

Revision ID: 20260928_0010
Revises: 20260928_0009
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260928_0010"
down_revision = "20260928_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_source_tenant",
        "documents",
        "knowledge_sources",
        ["source_id", "organization_id", "workspace_id"],
        ["id", "organization_id", "workspace_id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_documents_source_id", "documents", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_source_id", table_name="documents")
    op.drop_constraint("fk_documents_source_tenant", "documents", type_="foreignkey")
    op.drop_column("documents", "source_id")
