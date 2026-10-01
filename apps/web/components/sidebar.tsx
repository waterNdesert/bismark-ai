"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navigationForRole } from "../lib/navigation";
import {
  OverviewIcon,
  AskIcon,
  SourcesIcon,
  DocumentsIcon,
  ConversationsIcon,
  MembersIcon,
  UsageIcon,
  SettingsIcon,
  AnalyticsIcon,
} from "./icons";
import { useTenant } from "./tenant-context";
import { AccountMenu } from "./account-menu";

const icons = {
  overview: OverviewIcon,
  ask: AskIcon,
  sources: SourcesIcon,
  documents: DocumentsIcon,
  conversations: ConversationsIcon,
  members: MembersIcon,
  usage: UsageIcon,
  settings: SettingsIcon,
  analytics: AnalyticsIcon,
};
export function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { organizationRole } = useTenant();
  const navigation = navigationForRole(organizationRole);
  return (
    <nav className="app-navigation" aria-label="Main">
      {navigation.map((section) => (
        <div className="nav-section" key={section.title}>
          <p>{section.title.toLowerCase()}</p>
          {section.items.map((item) => {
            const Icon = icons[item.icon as keyof typeof icons];
            const active =
              pathname === item.href ||
              (item.href !== "/app" && pathname.startsWith(item.href + "/"));
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                onClick={onNavigate}
              >
                <Icon />
                {item.label}
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}
export function WorkspaceControl() {
  const context = useTenant();
  if (context.loading || context.error) return null;
  const org = context.selectedOrganization;
  return (
    <div className="workspace-control tenant-controls">
      {context.organizations.length > 1 ? (
        <label>
          Organization
          <select
            aria-label="Organization"
            value={org?.id ?? ""}
            onChange={(event) => context.selectOrganization(event.target.value)}
          >
            <option value="">Select organization</option>
            {context.organizations.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <strong>{org?.name ?? "No organization access yet"}</strong>
      )}
      {org &&
        (org.workspaces.length > 1 ? (
          <label>
            Workspace
            <select
              aria-label="Workspace"
              value={context.selectedWorkspace?.id ?? ""}
              onChange={(event) => context.selectWorkspace(event.target.value)}
            >
              <option value="">Select workspace</option>
              {org.workspaces.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <span>
            {context.selectedWorkspace?.name ?? "No workspace access"}
          </span>
        ))}
    </div>
  );
}
export function Sidebar() {
  return (
    <aside className="desktop-sidebar">
      <Link className="app-brand" href="/app">
        <span className="brand-symbol" aria-hidden="true">
          B
        </span>
        Bismark AI
      </Link>
      <WorkspaceControl />
      <Navigation />
      <div className="sidebar-footer">
        <AccountMenu />
      </div>
    </aside>
  );
}
