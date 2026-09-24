"""Enable pgvector for future embedding columns.

Revision ID: 20260924_0001
Revises:
Create Date: 2026-09-24
"""

from alembic import op

revision = "20260924_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Keep the shared extension in place; application tables are not present yet.
    pass
