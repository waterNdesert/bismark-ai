# Web development foundation

Use Node.js 24 and pnpm 10.33.2. From this directory:

```sh
pnpm install --frozen-lockfile
pnpm dev --hostname 127.0.0.1
pnpm format
pnpm format:check
pnpm lint
pnpm typecheck
pnpm build
pnpm start --hostname 127.0.0.1
```

The root page provides signup, login, logout, email confirmation handling,
password reset/recovery, and a backend-verified account view. Supabase manages
browser session persistence and refresh; FastAPI owns profile data. Product
workspaces, chat and shadcn/ui components remain deferred.

Create ignored `apps/web/.env.local` with only:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-public-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Never put a service-role key, database URL or signing secret here. These values
are build-time browser configuration. Restart Next.js after changing them. The
API accepts HTTPS origins or loopback HTTP for development. Without configuration,
the page shows a disabled account form; builds still work.

In Supabase Auth, enable email/password and configure Site URL and allowed redirect
URLs for your actual frontend origin (for example `http://localhost:3000`).
Signup confirmation and reset links return to that origin. Use the same hostname
throughout; `localhost` and `127.0.0.1` are different origins. Configure email
confirmation and email delivery/SMTP in Supabase before live acceptance testing.

Browser regression tests use fake credentials and intercepted services:

```sh
pnpm exec playwright install chromium
pnpm test:e2e
```

The runner starts its own Next.js development server on port 3100. Tests do not
contact a real Supabase project. Type checking, formatting, lint and build remain
available through the commands above. Dependencies are locked per app.

Compatibility notes: TypeScript is pinned to 5.9 because the current ESLint parser
does not support 7. ESLint 9 is retained because Next.js React plugins fail with
10; its install-time deprecation warning remains a tooling follow-up. pnpm skips
unrs-resolver's install script; all current checks pass without it. Next.js
generates local AGENTS.md/CLAUDE.md guidance, which is tracked.
