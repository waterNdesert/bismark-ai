"use client";

import type { Session } from "@supabase/supabase-js";
import { useEffect, useState, type FormEvent } from "react";
import { getAuthClient, loadProfile, type Profile } from "../lib/auth";

type Mode = "login" | "signup" | "reset";

export default function Account() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);
  const [configured, setConfigured] = useState(true);
  const [mode, setMode] = useState<Mode>("login");
  const [recovery, setRecovery] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [profileError, setProfileError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    let unsubscribe = () => {};
    async function initialize() {
      try {
        const auth = getAuthClient().auth;
        const { data } = auth.onAuthStateChange((event, nextSession) => {
          if (!active) return;
          setSession(nextSession);
          setReady(true);
          if (event === "PASSWORD_RECOVERY") setRecovery(true);
          if (event === "SIGNED_OUT") {
            setRecovery(false);
            setProfile(null);
          }
        });
        unsubscribe = () => data.subscription.unsubscribe();
        const { error } = await auth.getSession();
        if (error && active) {
          setError("We couldn’t restore your session. Sign in again.");
          setReady(true);
        }
      } catch {
        if (active) {
          setConfigured(false);
          setError(
            "Account access is not configured yet. Contact your administrator.",
          );
          setReady(true);
        }
      }
    }
    void initialize();
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  const token = session?.access_token;
  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    void loadProfile(token, controller.signal)
      .then((nextProfile) => {
        if (!controller.signal.aborted) {
          setProfile(nextProfile);
          setProfileError("");
        }
      })
      .catch((failure: unknown) => {
        if (!controller.signal.aborted) {
          setProfile(null);
          setProfileError(
            failure instanceof Error
              ? failure.message
              : "We couldn’t load your account.",
          );
        }
      });
    return () => controller.abort();
  }, [token, attempt]);

  function changeMode(next: Mode) {
    setMode(next);
    setError("");
    setMessage("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const email = String(fields.get("email") ?? "").trim();
    const password = String(fields.get("password") ?? "");
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const auth = getAuthClient().auth;
      if (recovery) {
        const { error } = await auth.updateUser({ password });
        if (error)
          throw new Error(
            "Your password could not be updated. Try a new reset link.",
          );
        setRecovery(false);
        setMessage("Your password has been updated.");
      } else if (mode === "reset") {
        const { error } = await auth.resetPasswordForEmail(email, {
          redirectTo: window.location.origin,
        });
        if (error)
          throw new Error("We couldn’t send a reset link. Try again shortly.");
        setMessage(
          "If an account matches that address, you’ll receive a password reset link.",
        );
      } else if (mode === "signup") {
        const { data, error } = await auth.signUp({
          email,
          password,
          options: { emailRedirectTo: window.location.origin },
        });
        if (error)
          throw new Error(
            "We couldn’t create your account. Check your details or try signing in.",
          );
        if (!data.session)
          setMessage(
            "Check your email to confirm your account, then return to sign in.",
          );
      } else {
        const { error } = await auth.signInWithPassword({ email, password });
        if (error)
          throw new Error(
            "Sign-in failed. Check your details and confirm your email, then try again.",
          );
      }
      form.reset();
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "The request failed. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const { error } = await getAuthClient().auth.signOut({ scope: "local" });
      if (error) throw error;
      setProfile(null);
      setProfileError("");
      setMode("login");
    } catch {
      setError(
        "We couldn’t sign you out. Check your connection and try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  const heading = recovery
    ? "Choose a new password"
    : session
      ? "Your account"
      : mode === "signup"
        ? "Create your account"
        : mode === "reset"
          ? "Reset your password"
          : "Welcome back";
  return (
    <section
      className="account-panel"
      aria-labelledby="account-heading"
      aria-busy={busy}
    >
      <h2 id="account-heading">{heading}</h2>
      {!ready ? (
        <p role="status">Checking your session…</p>
      ) : (
        <>
          {error && (
            <p className="notice error" role="alert">
              {error}
            </p>
          )}
          {message && (
            <p className="notice" role="status">
              {message}
            </p>
          )}
          {session && !recovery ? (
            <>
              {profile?.id === session.user.id ? (
                <>
                  <p className="account-email">{profile.email}</p>
                  <p>
                    You’re signed in. Workspace access will appear here when
                    it’s available.
                  </p>
                </>
              ) : profileError ? (
                <>
                  <p role="alert" className="notice error">
                    {profileError}
                  </p>
                  <button
                    className="text-button"
                    onClick={() => {
                      setProfileError("");
                      setAttempt(attempt + 1);
                    }}
                  >
                    Try again
                  </button>
                </>
              ) : (
                <p role="status">Loading your account…</p>
              )}
              <button
                className="primary-button"
                disabled={busy}
                onClick={signOut}
              >
                {busy ? "Signing out…" : "Sign out"}
              </button>
            </>
          ) : (
            <>
              <p>
                {recovery
                  ? "Use a password you haven’t used before."
                  : mode === "reset"
                    ? "Enter your account email and we’ll send a reset link."
                    : "Use your email to access Bismark AI."}
              </p>
              <form onSubmit={submit} key={`${mode}-${recovery}`}>
                <fieldset disabled={busy || !configured}>
                  {!recovery && (
                    <label>
                      Email address
                      <input
                        name="email"
                        type="email"
                        autoComplete="email"
                        required
                        maxLength={254}
                      />
                    </label>
                  )}
                  {(mode !== "reset" || recovery) && (
                    <label>
                      {recovery ? "New password" : "Password"}
                      <input
                        name="password"
                        type="password"
                        autoComplete={
                          mode === "signup" || recovery
                            ? "new-password"
                            : "current-password"
                        }
                        minLength={mode === "signup" || recovery ? 8 : 1}
                        maxLength={128}
                        required
                      />
                      {(mode === "signup" || recovery) && (
                        <span className="field-hint">
                          Use at least 8 characters.
                        </span>
                      )}
                    </label>
                  )}
                  <button className="primary-button" type="submit">
                    {busy
                      ? "Please wait…"
                      : recovery
                        ? "Save new password"
                        : mode === "signup"
                          ? "Create account"
                          : mode === "reset"
                            ? "Send reset link"
                            : "Sign in"}
                  </button>
                </fieldset>
              </form>
              {!recovery && (
                <nav className="account-options" aria-label="Account options">
                  <button
                    className="text-button"
                    disabled={busy}
                    onClick={() =>
                      changeMode(mode === "login" ? "signup" : "login")
                    }
                  >
                    {mode === "login" ? "Create an account" : "Back to sign in"}
                  </button>
                  {mode === "login" && (
                    <button
                      className="text-button"
                      disabled={busy}
                      onClick={() => changeMode("reset")}
                    >
                      Forgot password?
                    </button>
                  )}
                </nav>
              )}
              {recovery && (
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={signOut}
                >
                  Cancel and sign out
                </button>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
