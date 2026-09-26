"""Enable tenancy RLS with read access and self-profile updates.

Revision ID: 20260925_0003
Revises: 20260924_0002

Membership-list policies require nonrecursive lookups. These two private,
boolean-only functions use auth.uid(), never a caller-supplied user ID.
Run as the existing table owner (or a BYPASSRLS migration role). row_security=off
fails with an error rather than recursing if that prerequisite is not satisfied.
Do not expose bismark_rls in the Supabase Data API schemas.
Downgrade removes access policies but deliberately leaves RLS enabled (deny all).
"""

from alembic import op

revision = "20260925_0003"
down_revision = "20260924_0002"
branch_labels = None
depends_on = None

TABLES = (
    "profiles",
    "organizations",
    "organization_members",
    "workspaces",
    "workspace_members",
)
POLICIES = (
    ("profiles", "profiles_read_self"),
    ("profiles", "profiles_update_self"),
    ("organizations", "organizations_read_member"),
    ("organization_members", "organization_members_read_member"),
    ("workspaces", "workspaces_read_org_member"),
    ("workspace_members", "workspace_members_read_member"),
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")

    # A dedicated schema prevents public RPC exposure and untrusted replacement.
    op.execute("CREATE SCHEMA bismark_rls")
    op.execute("REVOKE ALL ON SCHEMA bismark_rls FROM PUBLIC, anon, authenticated")
    op.execute("GRANT USAGE ON SCHEMA bismark_rls TO authenticated")
    op.execute("""
        CREATE FUNCTION bismark_rls.is_org_member(target_org uuid)
        RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = '' SET row_security = off
        AS $$
            SELECT auth.uid() IS NOT NULL AND EXISTS (
                SELECT 1 FROM public.organization_members AS membership
                WHERE membership.organization_id = target_org
                  AND membership.user_id = auth.uid()
                  AND membership.role IN ('owner', 'admin', 'member')
            )
        $$
    """)
    op.execute("""
        CREATE FUNCTION bismark_rls.is_workspace_member(
            target_org uuid, target_workspace uuid
        )
        RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = '' SET row_security = off
        AS $$
            SELECT auth.uid() IS NOT NULL AND EXISTS (
                SELECT 1 FROM public.workspace_members AS membership
                JOIN public.organization_members AS organization_membership
                                    ON organization_membership.organization_id
                                         = membership.organization_id
                 AND organization_membership.user_id = membership.user_id
                WHERE membership.organization_id = target_org
                  AND membership.workspace_id = target_workspace
                  AND membership.user_id = auth.uid()
                  AND membership.role IN ('admin', 'member')
                  AND organization_membership.role IN ('owner', 'admin', 'member')
            )
        $$
    """)
    for function in ("is_org_member(uuid)", "is_workspace_member(uuid, uuid)"):
        op.execute(f"REVOKE ALL ON FUNCTION bismark_rls.{function} FROM PUBLIC, anon")
        op.execute(f"GRANT EXECUTE ON FUNCTION bismark_rls.{function} TO authenticated")

    op.execute("""
        CREATE POLICY profiles_read_self ON public.profiles
        FOR SELECT TO authenticated
        USING (id = (SELECT auth.uid()))
    """)
    op.execute("""
        CREATE POLICY profiles_update_self ON public.profiles
        FOR UPDATE TO authenticated
        USING (id = (SELECT auth.uid()))
        WITH CHECK (id = (SELECT auth.uid()))
    """)
    op.execute("""
        CREATE POLICY organizations_read_member ON public.organizations
        FOR SELECT TO authenticated
        USING (bismark_rls.is_org_member(id))
    """)
    op.execute("""
        CREATE POLICY organization_members_read_member ON public.organization_members
        FOR SELECT TO authenticated
        USING (bismark_rls.is_org_member(organization_id))
    """)
    op.execute("""
        CREATE POLICY workspaces_read_org_member ON public.workspaces
        FOR SELECT TO authenticated
        USING (bismark_rls.is_org_member(organization_id))
    """)
    op.execute("""
        CREATE POLICY workspace_members_read_member ON public.workspace_members
        FOR SELECT TO authenticated
        USING (bismark_rls.is_workspace_member(organization_id, workspace_id))
    """)


def downgrade() -> None:
    for table, policy in reversed(POLICIES):
        op.execute(f"DROP POLICY {policy} ON public.{table}")
    op.execute("DROP FUNCTION bismark_rls.is_workspace_member(uuid, uuid)")
    op.execute("DROP FUNCTION bismark_rls.is_org_member(uuid)")
    op.execute("DROP SCHEMA bismark_rls")
    # Never reopen tenant tables by disabling RLS on rollback.
