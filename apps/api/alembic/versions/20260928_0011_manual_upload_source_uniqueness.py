"""Enforce one non-deleted manual-upload source per workspace."""

from alembic import op
import sqlalchemy as sa

revision = "20260928_0011"
down_revision = "20260928_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_knowledge_sources_manual_upload_workspace",
        "knowledge_sources",
        ["organization_id", "workspace_id"],
        unique=True,
        postgresql_where=sa.text("source_type = 'manual_upload' AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_knowledge_sources_manual_upload_workspace",
        table_name="knowledge_sources",
    )
