"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navigation } from "../lib/navigation";
import {
  OverviewIcon,
  AskIcon,
  SourcesIcon,
  DocumentsIcon,
  ConversationsIcon,
  MembersIcon,
  UsageIcon,
  SettingsIcon,
  ChevronDownIcon,
} from "./icons";
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
};
export function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
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
  return (
    <div className="workspace-control">
      <button disabled aria-label="Workspace selection unavailable">
        <span className="workspace-symbol">W</span>
        <span>
          <strong>Workspace</strong>
          <small>Selection coming soon</small>
        </span>
        <ChevronDownIcon />
      </button>
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
