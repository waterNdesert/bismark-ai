"""Add a tenant-referenceable knowledge source key.

Revision ID: 20260928_0009
Revises: 20260928_0008
Create Date: 2026-09-28
"""

from alembic import op

revision = "20260928_0009"
down_revision = "20260928_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_knowledge_sources_id_organization_workspace",
        "knowledge_sources",
        ["id", "organization_id", "workspace_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_knowledge_sources_id_organization_workspace",
        "knowledge_sources",
        type_="unique",
    )
