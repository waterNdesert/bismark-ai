# Test account access locally

## One-time configuration

1. In the ignored root `.env`, set `SUPABASE_URL`, `SUPABASE_ANON_KEY`,
   `DATABASE_URL`, and `CORS_ORIGINS=http://localhost:3000`.
2. Create ignored `apps/web/.env.local` with:

   ```dotenv
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-public-anon-key
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

   Use the same Supabase project as the backend. Never put the service-role key
   or database password in frontend variables.
3. In Supabase Auth, enable email/password and allow `http://localhost:3000`
   as a redirect URL. Configure email delivery and confirmation as needed.
   The existing Phase 1B database migration must already be applied.

## Run

From the repository root, in two terminals:

```sh
make api-dev-env
```

```sh
make web-dev
```

Open **http://localhost:3000** (use localhost consistently).

## Try these flows

1. Create an account; confirm the email if requested.
2. Sign in. Your email should appear after the backend loads your profile.
3. Reload. You should stay signed in.
4. Sign out. The sign-in form should return and stay after reload.
5. Try an incorrect password. An error should appear and allow another attempt.
6. Use Forgot password, open the email link, and save a new password.
7. Repeat with a second test account. Each account should show only its own email.

Optional automated checks:

```sh
make api-test
pnpm --dir apps/web exec playwright install chromium
make web-test
```

## Phase 1C verification result

- `make api-test`: 51 passed.
- `make web-test`: 9 passed. Tests use mocked Auth/API responses and an isolated
  `.next-e2e` directory, so a normal local development server may remain running.
- `make check` and `git diff --check`: passed.
- Confirmed by browser tests: reload session persistence, logout persistence,
  generic invalid-password error with successful retry, token refresh and profile
  initialization. Recovery tests verify the reset request, recovery link, URL
  token removal and password-update request.
- Confirmed live manually by the user: signup, Supabase confirmation email,
  redirect to localhost, authenticated session, profile view and signed-in email.
- Live password-reset email delivery and password change remain unverified;
  recovery is implemented and tested with mocked provider responses.

No secrets are committed. No migrations or production deployment were performed.
Phase 1C is complete; Phase 1D, RLS and tenant authorization have not started.
