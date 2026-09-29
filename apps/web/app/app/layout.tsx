import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppSession } from "../../components/app-session";
import { Sidebar } from "../../components/sidebar";
import { TopBar } from "../../components/top-bar";

export const metadata: Metadata = {
  title: {
    template: "%s — Bismark AI",
    default: "Bismark AI",
  },
};

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AppSession>
      <div className="app-shell">
        <a className="skip-link" href="#app-content">
          Skip to content
        </a>
        <Sidebar />
        <div className="app-main">
          <TopBar />
          <main id="app-content" tabIndex={-1}>
            {children}
          </main>
        </div>
      </div>
    </AppSession>
  );
}
