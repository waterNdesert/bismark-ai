"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { Navigation, WorkspaceControl } from "./sidebar";
import { AccountMenu } from "./account-menu";
import { MenuIcon, CloseIcon } from "./icons";

export function MobileNav() {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const pathname = usePathname();
  useEffect(() => {
    dialog.current?.close();
    document.body.style.overflow = "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [pathname]);
  function close() {
    dialog.current?.close();
    document.body.style.overflow = "";
    trigger.current?.focus();
  }
  return (
    <div className="mobile-navigation">
      <button
        className="icon-button"
        ref={trigger}
        aria-label="Open navigation"
        onClick={() => {
          dialog.current?.showModal();
          document.body.style.overflow = "hidden";
        }}
      >
        <MenuIcon />
      </button>
      <dialog
        ref={dialog}
        className="navigation-drawer"
        aria-label="Navigation"
        onCancel={close}
        onClose={() => {
          document.body.style.overflow = "";
        }}
        onClick={(event) => {
          if (
            event.target === event.currentTarget &&
            event.clientX > event.currentTarget.getBoundingClientRect().right
          )
            close();
        }}
      >
        <div className="drawer-heading">
          <Link href="/app" onClick={close} className="app-brand">
            <span className="brand-symbol" aria-hidden="true">
              B
            </span>
            Bismark AI
          </Link>
          <button
            className="icon-button"
            aria-label="Close navigation"
            onClick={close}
          >
            <CloseIcon />
          </button>
        </div>
        <WorkspaceControl />
        <Navigation onNavigate={close} />
        <div className="sidebar-footer">
          <AccountMenu />
        </div>
      </dialog>
    </div>
  );
}
