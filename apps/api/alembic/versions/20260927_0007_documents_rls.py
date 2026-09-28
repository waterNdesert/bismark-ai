"""Enable RLS and revoke Data API grants on backend-managed tables.

Revision ID: 20260927_0007
Revises: 20260927_0006
Create Date: 2026-09-27
"""

from alembic import op

revision = "20260927_0007"
down_revision = "20260927_0006"
branch_labels = None
depends_on = None

TABLES = ("documents", "ingestion_jobs")
CRUD_PRIVILEGES = "SELECT, INSERT, UPDATE, DELETE"


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"REVOKE ALL PRIVILEGES ON TABLE public.{table} "
            "FROM anon, authenticated"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(
            f"GRANT {CRUD_PRIVILEGES} ON TABLE public.{table} "
            "TO anon, authenticated"
        )
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")
