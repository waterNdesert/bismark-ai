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

export const navigation: NavSection[] = [
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
