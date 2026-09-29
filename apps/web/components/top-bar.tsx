"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navigation } from "../lib/navigation";
import { MobileNav } from "./mobile-nav";
import { AskIcon } from "./icons";

export function TopBar() {
  const pathname = usePathname();
  const current = navigation
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
