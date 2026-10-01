"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navigationForRole } from "../lib/navigation";
import { MobileNav } from "./mobile-nav";
import { AskIcon } from "./icons";
import { useTenant } from "./tenant-context";

export function TopBar() {
  const pathname = usePathname();
  const { organizationRole } = useTenant();
  const current = navigationForRole(organizationRole)
    .flatMap((s) => s.items)
    .find((i) => i.href === pathname);
  return (
    <header className="app-topbar">
      <MobileNav />
      <div className="app-breadcrumb">
        <span>Bismark AI</span>
        <span aria-hidden="true">/</span>
        <strong>{current?.label || "Workspace"}</strong>
      </div>
      <Link className="header-ask" href="/app/ask">
        <AskIcon />
        <span>Ask Bismark</span>
      </Link>
    </header>
  );
}
