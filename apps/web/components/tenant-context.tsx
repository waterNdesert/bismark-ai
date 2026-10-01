"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { apiUrl } from "../lib/auth";
import {
  isAdminOnlyRoute,
  isTenantAdmin,
  requiresWorkspace,
} from "../lib/navigation";
import { useAccessToken } from "./app-session";

type Workspace = { id: string; name: string; role: "admin" | "member" };
type Organization = {
  id: string;
  name: string;
  role: "owner" | "admin" | "member";
  workspaces: Workspace[];
};
function useTenantState() {
  const token = useAccessToken();
  const [result, setResult] = useState<{
    token: string;
    organizations: Organization[];
  } | null>(null);
  const [failure, setFailure] = useState<{
    token: string;
    message: string;
  } | null>(null);
  const [selection, setSelection] = useState({
    organization: "",
    workspace: "",
  });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const response = await fetch(`${apiUrl()}/api/v1/me/context`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
          redirect: "error",
          signal: AbortSignal.any([
            controller.signal,
            AbortSignal.timeout(10000),
          ]),
        });
        if (!response.ok)
          throw new Error(
            response.status === 401
              ? "Your session could not be verified. Sign out and sign in again."
              : "We couldn’t load your workspace access. Try again.",
          );
        const data = (await response.json()) as {
          organizations: Organization[];
        };
        if (!Array.isArray(data.organizations))
          throw new Error("Invalid context");
        if (controller.signal.aborted) return;
        setSelection((previous) => {
          const org =
            data.organizations.find(
              (item) => item.id === previous.organization,
            ) ??
            (data.organizations.length === 1 ? data.organizations[0] : null);
          const workspace =
            org?.workspaces.find((item) => item.id === previous.workspace) ??
            (org?.workspaces.length === 1 ? org.workspaces[0] : null);
          return {
            organization: org?.id ?? "",
            workspace: workspace?.id ?? "",
          };
        });
        setResult({ token, organizations: data.organizations });
      } catch (error) {
        if (!controller.signal.aborted)
          setFailure({
            token,
            message:
              error instanceof Error && error.message.startsWith("Your session")
                ? error.message
                : "We couldn’t load your workspace access. Try again.",
          });
      }
    })();
    return () => controller.abort();
  }, [token, revision]);
  const organizations = result?.token === token ? result.organizations : [];
  const selectedOrganization =
    organizations.find((item) => item.id === selection.organization) ?? null;
  const selectedWorkspace =
    selectedOrganization?.workspaces.find(
      (item) => item.id === selection.workspace,
    ) ?? null;
  const error = failure?.token === token ? failure.message : null;
  return {
    organizations,
    selectedOrganization,
    selectedWorkspace,
    organizationRole: selectedOrganization?.role ?? null,
    workspaceRole: selectedWorkspace?.role ?? null,
    loading: !error && result?.token !== token,
    error,
    selectOrganization(id: string) {
      const org = organizations.find((item) => item.id === id);
      setSelection({
        organization: org?.id ?? "",
        workspace: org?.workspaces.length === 1 ? org.workspaces[0].id : "",
      });
    },
    selectWorkspace(id: string) {
      setSelection((previous) => ({
        ...previous,
        workspace: selectedOrganization?.workspaces.some(
          (item) => item.id === id,
        )
          ? id
          : "",
      }));
    },
    refreshContext() {
      setResult(null);
      setFailure(null);
      setRevision((value) => value + 1);
    },
  };
}
const TenantContext = createContext<ReturnType<typeof useTenantState> | null>(
  null,
);
export function TenantProvider({ children }: { children: ReactNode }) {
  return <TenantContext value={useTenantState()}>{children}</TenantContext>;
}
export function useTenant() {
  const context = useContext(TenantContext);
  if (!context) throw new Error("TenantProvider is required");
  return context;
}
export function TenantGate({ children }: { children: ReactNode }) {
  const context = useTenant();
  const pathname = usePathname();
  const router = useRouter();
  const accountRoute =
    pathname === "/app/account" || pathname.startsWith("/app/account/");
  const memberDeniedRoute =
    context.organizationRole === "member" && isAdminOnlyRoute(pathname);
  useEffect(() => {
    if (memberDeniedRoute) router.replace("/app/ask");
  }, [memberDeniedRoute, router]);

  if (accountRoute) return children;
  if (context.loading) return <p role="status">Loading workspace access…</p>;
  if (context.error)
    return (
      <div role="alert">
        <p>{context.error}</p>
        <button onClick={context.refreshContext}>Retry workspace access</button>
      </div>
    );
  if (memberDeniedRoute)
    return (
      <section className="session-gate">
        <p role="status">Opening Ask Bismark…</p>
      </section>
    );

  const message = !context.organizations.length
    ? "No organization access yet"
    : !context.selectedOrganization
      ? "Select an organization"
      : requiresWorkspace(pathname) &&
          !context.selectedOrganization.workspaces.length
        ? "No workspace access"
        : requiresWorkspace(pathname) && !context.selectedWorkspace
          ? "Select a workspace"
          : null;
  if (message) {
    return (
      <section className="session-gate">
        <h1>{message}</h1>
        <p>
          {!context.organizations.length
            ? "Your account is signed in, but no organization memberships are available yet."
            : !context.selectedOrganization
              ? "Choose an organization using the navigation controls."
              : !context.selectedOrganization.workspaces.length
                ? "You have no explicit workspace membership for this organization."
                : "Choose an accessible workspace using the navigation controls."}
        </p>
      </section>
    );
  }
  if (isAdminOnlyRoute(pathname) && !isTenantAdmin(context.organizationRole)) {
    return (
      <section className="session-gate">
        <p role="status">Checking tenant access…</p>
      </section>
    );
  }
  return children;
}
