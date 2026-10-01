/*
 * Navigation structure for the Bismark AI application shell.
 * Defines the sidebar sections and items.
 */

export type NavItem = {
  label: string;
  href: string;
  icon: string;
};

export type NavSection = {
  title: string;
  items: NavItem[];
};

export type OrganizationRole = "owner" | "admin" | "member";

const adminNavigation: NavSection[] = [
  {
    title: "PRIMARY",
    items: [
      { label: "Overview", href: "/app", icon: "overview" },
      { label: "Ask Bismark", href: "/app/ask", icon: "ask" },
    ],
  },
  {
    title: "KNOWLEDGE",
    items: [
      { label: "Sources", href: "/app/sources", icon: "sources" },
      { label: "Documents", href: "/app/documents", icon: "documents" },
    ],
  },
  {
    title: "ACTIVITY",
    items: [
      {
        label: "Conversations",
        href: "/app/conversations",
        icon: "conversations",
      },
      { label: "Analytics", href: "/app/analytics", icon: "analytics" },
    ],
  },
  {
    title: "WORKSPACE",
    items: [
      { label: "Members", href: "/app/members", icon: "members" },
      { label: "Usage", href: "/app/usage", icon: "usage" },
      { label: "Settings", href: "/app/settings", icon: "settings" },
    ],
  },
];

const memberNavigation: NavSection[] = [
  {
    title: "PRIMARY",
    items: [
      { label: "Ask Bismark", href: "/app/ask", icon: "ask" },
      {
        label: "Conversations",
        href: "/app/conversations",
        icon: "conversations",
      },
    ],
  },
];

export function isTenantAdmin(
  role: OrganizationRole | null | undefined,
): boolean {
  return role === "owner" || role === "admin";
}

export function navigationForRole(
  role: OrganizationRole | null | undefined,
): NavSection[] {
  if (isTenantAdmin(role)) return adminNavigation;
  return role === "member" ? memberNavigation : [];
}

const adminOnlyRoutes = [
  "/app/sources",
  "/app/documents",
  "/app/members",
  "/app/analytics",
  "/app/usage",
  "/app/settings",
];

export function isAdminOnlyRoute(pathname: string): boolean {
  return (
    pathname === "/app" ||
    adminOnlyRoutes.some(
      (route) => pathname === route || pathname.startsWith(`${route}/`),
    )
  );
}

export function requiresWorkspace(pathname: string): boolean {
  return ["/app/ask", "/app/conversations"].some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
}
