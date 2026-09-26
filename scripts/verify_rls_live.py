"""Locally verify tenant RLS with two existing Supabase Auth users.

Run from the repository root through scripts/run_with_env.py so the ignored
.env supplies the development Supabase configuration.
"""

from __future__ import annotations

import getpass
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from uuid import UUID

ROW_LIMIT = 1000
TIMEOUT_SECONDS = 20


class VerificationError(Exception):
    """An error safe to include in the concise verification report."""


def safe_auth_error_code(error: HTTPError) -> str | None:
    try:
        payload = json.loads(error.read(8192))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    for key in ("code", "error_code"):
        code = payload.get(key)
        if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", code):
            return code
    return None


@dataclass(frozen=True)
class UserSession:
    label: str
    user_id: str
    access_token: str


@dataclass
class TenantInventory:
    profile_rows: list[dict[str, Any]]
    organization_member_rows: list[dict[str, Any]]
    organization_rows: list[dict[str, Any]]
    workspace_rows: list[dict[str, Any]]
    workspace_member_rows: list[dict[str, Any]]

    @property
    def organization_ids(self) -> set[str]:
        return {row["organization_id"] for row in self.organization_member_rows}

    @property
    def workspace_ids(self) -> set[str]:
        return {row["id"] for row in self.workspace_rows}


def request_json(
    base_url: str,
    path: str,
    *,
    api_key: str,
    label: str,
    access_token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {access_token or api_key}",
        "Accept": "application/json",
        "X-Supabase-Api-Version": "2024-01-01",
    }
    body = None
    method = "GET"
    if payload is not None:
        headers["Content-Type"] = "application/json;charset=UTF-8"
        body = json.dumps(payload).encode("utf-8")
        method = "POST"

    request = Request(f"{base_url}{path}", data=body,
                      headers=headers, method=method)
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            content = response.read()
    except HTTPError as error:
        code = safe_auth_error_code(
            error) if "authentication" in label else None
        detail = f" (Supabase code: {code})" if code else ""
        raise VerificationError(
            f"{label} returned HTTP {error.code}{detail}") from None
    except (URLError, TimeoutError, OSError):
        raise VerificationError(f"{label} could not reach Supabase") from None

    try:
        return json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise VerificationError(
            f"{label} returned an invalid response") from None


def checked_uuid(value: Any, label: str) -> str:
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise VerificationError(
            f"{label} returned an invalid user or tenant ID") from None


def authenticate(base_url: str, api_key: str, label: str) -> UserSession:
    email = input(f"{label} email: ").strip()
    password = getpass.getpass(f"{label} password: ")
    if not email or not password:
        raise VerificationError(f"{label} credentials were not provided")

    response = request_json(
        base_url,
        "/auth/v1/token?grant_type=password",
        api_key=api_key,
        label=f"{label} authentication",
        payload={
            "email": email,
            "password": password,
            "gotrue_meta_security": {},
        },
    )
    del email, password

    if not isinstance(response, dict):
        raise VerificationError(
            f"{label} authentication returned an invalid response")
    access_token = response.get("access_token")
    user = response.get("user")
    if not isinstance(access_token, str) or not isinstance(user, dict):
        raise VerificationError(
            f"{label} authentication did not return a user session")
    user_id = checked_uuid(user.get("id"), f"{label} authentication")
    return UserSession(label, user_id, access_token)


def postgrest_rows(
    base_url: str,
    api_key: str,
    session: UserSession,
    table: str,
    columns: str,
    filters: dict[str, str],
) -> list[dict[str, Any]]:
    query = urlencode({"select": columns, **filters, "limit": str(ROW_LIMIT)})
    response = request_json(
        base_url,
        f"/rest/v1/{table}?{query}",
        api_key=api_key,
        access_token=session.access_token,
        label=f"{session.label} read from {table}",
    )
    if not isinstance(response, list) or any(not isinstance(row, dict) for row in response):
        raise VerificationError(
            f"{session.label} read from {table} returned invalid rows")
    if len(response) >= ROW_LIMIT:
        raise VerificationError(
            f"{session.label} read from {table} reached the safety row limit"
        )
    return response


def in_filter(values: set[str]) -> str:
    return f"in.({','.join(sorted(values))})"


def inventory_user(
    base_url: str, api_key: str, session: UserSession
) -> TenantInventory:
    profile_rows = postgrest_rows(
        base_url,
        api_key,
        session,
        "profiles",
        "id",
        {"id": f"eq.{session.user_id}"},
    )
    organization_member_rows = postgrest_rows(
        base_url,
        api_key,
        session,
        "organization_members",
        "organization_id,user_id",
        {"user_id": f"eq.{session.user_id}"},
    )
    organization_ids = {
        checked_uuid(row.get("organization_id"),
                     f"{session.label} memberships")
        for row in organization_member_rows
    }

    organization_rows: list[dict[str, Any]] = []
    workspace_rows: list[dict[str, Any]] = []
    if organization_ids:
        organization_rows = postgrest_rows(
            base_url,
            api_key,
            session,
            "organizations",
            "id",
            {"id": in_filter(organization_ids)},
        )
        workspace_rows = postgrest_rows(
            base_url,
            api_key,
            session,
            "workspaces",
            "id,organization_id",
            {"organization_id": in_filter(organization_ids)},
        )
        for row in workspace_rows:
            checked_uuid(row.get("id"), f"{session.label} workspaces")
            checked_uuid(row.get("organization_id"),
                         f"{session.label} workspaces")

    workspace_member_rows = postgrest_rows(
        base_url,
        api_key,
        session,
        "workspace_members",
        "organization_id,workspace_id,user_id",
        {"user_id": f"eq.{session.user_id}"},
    )
    return TenantInventory(
        profile_rows,
        organization_member_rows,
        organization_rows,
        workspace_rows,
        workspace_member_rows,
    )


def fixture_gaps(
    sessions: tuple[UserSession, UserSession],
    inventories: tuple[TenantInventory, TenantInventory],
) -> list[str]:
    gaps: list[str] = []
    for session, inventory in zip(sessions, inventories, strict=True):
        if len(inventory.profile_rows) != 1:
            gaps.append(
                f"{session.label} profiles row (expected 1 visible, got {len(inventory.profile_rows)})"
            )
        if not inventory.organization_member_rows:
            gaps.append(
                f"{session.label} organization_members row is not visible")
        organization_ids = inventory.organization_ids
        visible_organization_ids = {
            checked_uuid(row.get("id"), f"{session.label} organizations")
            for row in inventory.organization_rows
        }
        if organization_ids - visible_organization_ids:
            gaps.append(
                f"{session.label} organizations row for a membership is not visible")
        if not organization_ids:
            gaps.append(
                f"{session.label} workspaces cannot be inspected without a visible organization membership"
            )
        elif not inventory.workspace_rows:
            gaps.append(
                f"{session.label} workspaces row is not visible in its organization")
        if not inventory.workspace_member_rows:
            gaps.append(
                f"{session.label} workspace_members row is not visible")

        workspace_ids = inventory.workspace_ids
        for row in inventory.workspace_member_rows:
            workspace_id = checked_uuid(
                row.get("workspace_id"), f"{session.label} workspace memberships")
            organization_id = checked_uuid(
                row.get("organization_id"), f"{session.label} workspace memberships")
            if workspace_id not in workspace_ids or organization_id not in organization_ids:
                gaps.append(
                    f"{session.label} workspace_members row is outside its visible tenant")
                break

    first, second = inventories
    if first.organization_ids & second.organization_ids:
        gaps.append(
            "User A and User B need separate organizations for isolation checks")
    if first.workspace_ids & second.workspace_ids:
        gaps.append(
            "User A and User B need separate workspaces for isolation checks")
    if sessions[0].user_id == sessions[1].user_id:
        gaps.append("User A and User B must be distinct Auth users")
    return gaps


def run_rls_checks(
    base_url: str,
    api_key: str,
    sessions: tuple[UserSession, UserSession],
    inventories: tuple[TenantInventory, TenantInventory],
    checks: list[tuple[str, bool]],
) -> None:
    for index, (session, other, inventory, other_inventory) in enumerate(
        zip(sessions, sessions[::-1], inventories,
            inventories[::-1], strict=True)
    ):
        own_profile = postgrest_rows(
            base_url,
            api_key,
            session,
            "profiles",
            "id",
            {"id": f"eq.{session.user_id}"},
        )
        foreign_profile = postgrest_rows(
            base_url,
            api_key,
            session,
            "profiles",
            "id",
            {"id": f"eq.{other.user_id}"},
        )
        checks.extend(
            [
                (f"User {session.label[-1]} reads own profile",
                 len(own_profile) == 1),
                (f"User {session.label[-1]} cannot read other profile",
                 not foreign_profile),
            ]
        )

        own_orgs = postgrest_rows(
            base_url,
            api_key,
            session,
            "organizations",
            "id",
            {"id": in_filter(inventory.organization_ids)},
        )
        foreign_orgs = postgrest_rows(
            base_url,
            api_key,
            session,
            "organizations",
            "id",
            {"id": in_filter(other_inventory.organization_ids)},
        )
        visible_org_ids = {row.get("id") for row in own_orgs}
        checks.extend(
            [
                (
                    f"User {session.label[-1]} reads own organization(s)",
                    visible_org_ids == inventory.organization_ids,
                ),
                (f"User {session.label[-1]} cannot read other organization(s)",
                 not foreign_orgs),
            ]
        )

        own_workspaces = postgrest_rows(
            base_url,
            api_key,
            session,
            "workspaces",
            "id,organization_id",
            {"id": in_filter(inventory.workspace_ids)},
        )
        foreign_workspaces = postgrest_rows(
            base_url,
            api_key,
            session,
            "workspaces",
            "id",
            {"id": in_filter(other_inventory.workspace_ids)},
        )
        visible_workspace_ids = {row.get("id") for row in own_workspaces}
        checks.extend(
            [
                (
                    f"User {session.label[-1]} reads authorized workspace(s)",
                    visible_workspace_ids == inventory.workspace_ids,
                ),
                (f"User {session.label[-1]} cannot read other workspace(s)",
                 not foreign_workspaces),
            ]
        )

        own_organization_members = postgrest_rows(
            base_url,
            api_key,
            session,
            "organization_members",
            "organization_id,user_id",
            {"organization_id": in_filter(inventory.organization_ids)},
        )
        other_organization_members = postgrest_rows(
            base_url,
            api_key,
            session,
            "organization_members",
            "organization_id,user_id",
            {"organization_id": in_filter(other_inventory.organization_ids)},
        )
        own_org_members_scoped = bool(own_organization_members) and all(
            row.get("organization_id") in inventory.organization_ids
            for row in own_organization_members
        ) and any(row.get("user_id") == session.user_id for row in own_organization_members)
        checks.extend(
            [
                (
                    f"User {session.label[-1]} reads own-tenant organization memberships",
                    own_org_members_scoped,
                ),
                (
                    f"User {session.label[-1]} cannot read other-tenant organization memberships",
                    not other_organization_members,
                ),
            ]
        )

        own_workspace_members = postgrest_rows(
            base_url,
            api_key,
            session,
            "workspace_members",
            "organization_id,workspace_id,user_id",
            {"workspace_id": in_filter(inventory.workspace_ids)},
        )
        other_workspace_members = postgrest_rows(
            base_url,
            api_key,
            session,
            "workspace_members",
            "organization_id,workspace_id,user_id",
            {"workspace_id": in_filter(other_inventory.workspace_ids)},
        )
        own_workspace_members_scoped = bool(own_workspace_members) and all(
            row.get("organization_id") in inventory.organization_ids
            and row.get("workspace_id") in inventory.workspace_ids
            for row in own_workspace_members
        ) and any(row.get("user_id") == session.user_id for row in own_workspace_members)
        checks.extend(
            [
                (
                    f"User {session.label[-1]} reads own-tenant workspace memberships",
                    own_workspace_members_scoped,
                ),
                (
                    f"User {session.label[-1]} cannot read other-tenant workspace memberships",
                    not other_workspace_members,
                ),
            ]
        )


def print_report(
    authentication: str,
    fixture_state: str,
    checks: list[tuple[str, bool]],
    missing: list[str],
    security_concern: str,
) -> None:
    passed = sum(result for _, result in checks)
    failed = len(checks) - passed
    failed_names = [name for name, result in checks if not result]
    check_result = f"{passed} passed, {failed} failed"
    if failed_names:
        check_result += "; failures: " + ", ".join(failed_names)
    checks_performed = (
        "profile, organization, workspace, and both membership tables for both users"
        if checks
        else "none"
    )
    print("Script created: scripts/verify_rls_live.py")
    print(f"Authentication result: {authentication}")
    print(f"Existing fixture state: {fixture_state}")
    print(f"RLS checks performed: {checks_performed}")
    print(f"Passed/failed checks: {check_result}")
    print("Missing fixtures: " + ("; ".join(missing) if missing else "none"))
    print(f"Security concern: {security_concern}")


def main() -> int:
    authentication = "not attempted"
    fixture_state = "not inspected"
    checks: list[tuple[str, bool]] = []
    missing: list[str] = []
    security_concern = "none"

    try:
        if sys.argv[1:] not in ([], ["--user-a-sign-in-only"]):
            raise VerificationError("unsupported command-line option")
        user_a_only = sys.argv[1:] == ["--user-a-sign-in-only"]
        if os.environ.get("APP_ENV", "").strip().lower() != "development":
            raise VerificationError(
                "set APP_ENV=development before running this local-only script")
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise VerificationError(
                "an interactive terminal is required for hidden password prompts")

        configured_url = os.environ.get("SUPABASE_URL", "").strip()
        api_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
        parsed_url = urlsplit(configured_url)
        if (
            parsed_url.scheme != "https"
            or not parsed_url.hostname
            or parsed_url.username
            or parsed_url.password
            or parsed_url.path not in {"", "/"}
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise VerificationError(
                "SUPABASE_URL must be a valid HTTPS project origin")
        if not api_key:
            raise VerificationError("SUPABASE_ANON_KEY is required")
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        confirmation = input(
            "Type DEVELOPMENT to confirm this is a development Supabase project: "
        )
        if confirmation != "DEVELOPMENT":
            raise VerificationError(
                "development-project confirmation did not match")

        user_a = authenticate(base_url, api_key, "User A")
        authentication = "User A authenticated"
        if user_a_only:
            fixture_state = "not inspected (User A sign-in-only mode)"
            print_report(
                authentication,
                fixture_state,
                checks,
                missing,
                "none; no tenant requests were made",
            )
            return 0

        authentication = "User A authenticated; User B pending"
        user_b = authenticate(base_url, api_key, "User B")
        authentication = "both legitimate Auth users authenticated"
        sessions = (user_a, user_b)

        inventories = (
            inventory_user(base_url, api_key, user_a),
            inventory_user(base_url, api_key, user_b),
        )
        missing = fixture_gaps(sessions, inventories)
        if missing:
            fixture_state = "incomplete or not visible through user-scoped RLS"
            print_report(
                authentication,
                fixture_state,
                checks,
                missing,
                "none; stopped before policy assertions and made no writes",
            )
            return 2

        fixture_state = "complete; isolated tenant rows visible to both users"
        run_rls_checks(base_url, api_key, sessions, inventories, checks)
        if any(not result for _, result in checks):
            security_concern = "one or more tenant-isolation assertions failed"
        print_report(authentication, fixture_state,
                     checks, missing, security_concern)
        return 1 if security_concern != "none" else 0
    except VerificationError as error:
        if str(error).startswith("User A authentication"):
            authentication = "User A sign-in failed"
        security_concern = str(error)
        print_report(authentication, fixture_state,
                     checks, missing, security_concern)
        return 2
    except KeyboardInterrupt:
        print_report(
            authentication,
            fixture_state,
            checks,
            missing,
            "verification interrupted; no application data was written",
        )
        return 130
    except Exception as error:
        print_report(
            authentication,
            fixture_state,
            checks,
            missing,
            f"stopped after unexpected error ({type(error).__name__}); details suppressed",
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
