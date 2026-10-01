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

export type UploadedDocument = {
  original_filename: string;
  mime_type: string | null;
  size_bytes: number | null;
  status: string;
  created_at: string;
};

export class DocumentUploadError extends Error {}

export async function uploadDocument(
  token: string,
  organizationId: string,
  workspaceId: string,
  file: File,
  signal: AbortSignal,
): Promise<UploadedDocument> {
  const form = new FormData();
  form.append("file", file);
  let response: Response;
  try {
    response = await fetch(
      `${apiUrl()}/api/v1/organizations/${encodeURIComponent(organizationId)}` +
        `/workspaces/${encodeURIComponent(workspaceId)}/documents`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
        cache: "no-store",
        signal: AbortSignal.any([signal, AbortSignal.timeout(60000)]),
        redirect: "error",
      },
    );
  } catch {
    throw new DocumentUploadError(
      "Upload failed. Check your connection and try again.",
    );
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (response.status === 201 && payload && typeof payload === "object") {
    const data = payload as Record<string, unknown>;
    if (
      typeof data.original_filename === "string" &&
      typeof data.status === "string" &&
      typeof data.created_at === "string" &&
      (typeof data.mime_type === "string" || data.mime_type === null) &&
      (typeof data.size_bytes === "number" || data.size_bytes === null)
    ) {
      return {
        original_filename: data.original_filename,
        mime_type: data.mime_type,
        size_bytes: data.size_bytes,
        status: data.status,
        created_at: data.created_at,
      };
    }
    throw new DocumentUploadError(
      "Upload completed, but its confirmation was invalid.",
    );
  }

  const errorCode =
    payload &&
    typeof payload === "object" &&
    "error" in payload &&
    payload.error &&
    typeof payload.error === "object" &&
    "code" in payload.error &&
    typeof payload.error.code === "string"
      ? payload.error.code
      : "";
  if (response.status === 400)
    throw new DocumentUploadError(
      "We couldn’t accept this file. Check it and try again.",
    );
  if (response.status === 401)
    throw new DocumentUploadError(
      "Your session expired. Sign in again to upload.",
    );
  if (response.status === 403)
    throw new DocumentUploadError(
      "You don’t have permission to upload to this workspace.",
    );
  if (response.status === 409 && errorCode === "SOURCE_UNAVAILABLE")
    throw new DocumentUploadError(
      "The upload source is unavailable right now. Try again later.",
    );
  throw new DocumentUploadError("Upload failed. Try again later.");
}

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
