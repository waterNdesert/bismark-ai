"""Add a tenant-referenceable document key.

Revision ID: 20260927_0005
Revises: 20260926_0004
Create Date: 2026-09-27
"""

from alembic import op

revision = "20260927_0005"
down_revision = "20260926_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_documents_id_organization_workspace",
        "documents",
        ["id", "organization_id", "workspace_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_documents_id_organization_workspace",
        "documents",
        type_="unique",
    )
