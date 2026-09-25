import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | undefined;

export function getAuthClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) throw new Error("Account access is not configured yet.");
  if (new URL(url).protocol !== "https:")
    throw new Error("Account access needs a secure connection.");
  // This module accepts only the public key; all data access goes through FastAPI.
  client ??= createClient(url, key, {
    global: {
      fetch: (input, init) =>
        fetch(input, {
          ...init,
          signal: AbortSignal.any([
            ...(init?.signal ? [init.signal] : []),
            AbortSignal.timeout(15000),
          ]),
        }),
    },
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
  return client;
}

export function apiUrl(): string {
  const value = process.env.NEXT_PUBLIC_API_URL;
  if (!value) throw new Error("Account access is not configured yet.");
  const url = new URL(value);
  if (
    (url.protocol !== "https:" &&
      !(
        url.protocol === "http:" &&
        ["localhost", "127.0.0.1"].includes(url.hostname)
      )) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    url.pathname !== "/"
  )
    throw new Error("Account access needs a valid API address.");
  return url.origin;
}

export type Profile = {
  id: string;
  email: string;
  display_name: string | null;
};

export async function loadProfile(
  token: string,
  signal: AbortSignal,
): Promise<Profile> {
  const url = `${apiUrl()}/api/v1/me`;
  const options = {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store" as const,
    signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]),
    redirect: "error" as const,
  };
  let response = await fetch(url, options);
  if (response.status === 404)
    response = await fetch(url, { ...options, method: "POST" });
  if (!response.ok) {
    throw new Error(
      response.status === 401
        ? "Your session has expired. Sign out and sign in again."
        : "We couldn’t load your account. Try again.",
    );
  }
  return response.json();
}
