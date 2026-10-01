"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getAuthClient } from "../lib/auth";
import { useProfile } from "./app-session";
import { ChevronDownIcon } from "./icons";

export function AccountMenu() {
  const profile = useProfile();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    menu.current?.querySelector<HTMLElement>("[role=menuitem]")?.focus();
    function close(event: PointerEvent) {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [open]);
  async function signOut() {
    setBusy(true);
    setError("");
    try {
      const { error } = await getAuthClient().auth.signOut({ scope: "local" });
      if (error) throw error;
      router.replace("/");
    } catch {
      setError("Couldn’t sign out. Check your connection and try again.");
      setBusy(false);
    }
  }
  const name = profile?.display_name || "Your account";
  return (
    <div
      className="account-control"
      ref={root}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <button
        ref={trigger}
        className="account-trigger"
        aria-label="Account menu"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        <span className="avatar">
          {(profile?.display_name || profile?.email || "A")
            .charAt(0)
            .toUpperCase()}
        </span>
        <span className="account-identity">
          <strong>{name}</strong>
          <span>{profile?.email}</span>
        </span>
        <ChevronDownIcon />
      </button>
      {open && (
        <div
          ref={menu}
          className="account-popover"
          role="menu"
          aria-label="Account actions"
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              event.preventDefault();
              event.stopPropagation();
              setOpen(false);
              trigger.current?.focus();
            }
            if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
              event.preventDefault();
              const items = Array.from(
                event.currentTarget.querySelectorAll<HTMLElement>(
                  "[role=menuitem]",
                ),
              );
              const index = items.indexOf(
                document.activeElement as HTMLElement,
              );
              items[
                event.key === "Home"
                  ? 0
                  : event.key === "End"
                    ? items.length - 1
                    : (index +
                        (event.key === "ArrowUp" ? -1 : 1) +
                        items.length) %
                      items.length
              ]?.focus();
            }
          }}
        >
          <Link
            role="menuitem"
            href="/app/account"
            onClick={() => setOpen(false)}
          >
            Account
          </Link>
          <button role="menuitem" onClick={signOut} disabled={busy}>
            {busy ? "Signing out…" : "Sign out"}
          </button>
          {error && <p role="alert">{error}</p>}
        </div>
      )}
    </div>
  );
}
