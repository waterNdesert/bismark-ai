"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getAuthClient, loadProfile, type Profile } from "../lib/auth";

const ProfileContext = createContext<Profile | null>(null);
export function useProfile() {
  return useContext(ProfileContext);
}

export function AppSession({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    let unsubscribe = () => {};
    let version = 0;
    try {
      const auth = getAuthClient().auth;
      const { data } = auth.onAuthStateChange((event, session) => {
        const current = ++version;
        if (event === "PASSWORD_RECOVERY") {
          setProfile(null);
          router.replace("/");
          return;
        }
        if (!session) {
          setProfile(null);
          router.replace("/");
          return;
        }
        setProfile((previous) =>
          previous?.id === session.user.id ? previous : null,
        );
        // Keep provider calls outside the synchronous auth callback.
        void loadProfile(session.access_token, controller.signal)
          .then((result) => {
            if (!controller.signal.aborted && current === version) {
              if (result.id !== session.user.id)
                throw new Error("Identity mismatch");
              setProfile(result);
              setError(false);
            }
          })
          .catch(() => {
            if (!controller.signal.aborted && current === version) {
              setProfile(null);
              setError(true);
            }
          });
      });
      unsubscribe = () => data.subscription.unsubscribe();
      void auth.getSession().then(({ error }) => {
        if (error && !controller.signal.aborted) setError(true);
      });
    } catch {
      router.replace("/");
    }
    return () => {
      controller.abort();
      unsubscribe();
    };
  }, [router]);
  if (!profile)
    return (
      <main className="session-gate">
        <span className="brand">Bismark AI</span>
        {error ? (
          <>
            <h1>Account access unavailable</h1>
            <p>
              We couldn’t verify your account. Return to sign in and try again.
            </p>
            <Link className="app-link-button" href="/">
              Return to sign in
            </Link>
          </>
        ) : (
          <p role="status">Opening your workspace…</p>
        )}
      </main>
    );
  return <ProfileContext value={profile}>{children}</ProfileContext>;
}
