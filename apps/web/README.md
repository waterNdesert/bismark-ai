# Web development foundation

Use Node.js 24 and pnpm 10.33.2. From this directory:

```sh
pnpm install --frozen-lockfile
pnpm dev --hostname 127.0.0.1
pnpm lint
pnpm typecheck
pnpm build
pnpm start --hostname 127.0.0.1
```

The App Router root page displays only the project name and Phase 0 status.
Type checking generates Next.js types before running TypeScript. Tailwind uses
PostCSS and ESLint uses Next.js presets. No environment variables are required
or consumed yet. NEXT_PUBLIC_APP_URL and NEXT_PUBLIC_API_URL in the root template
are reserved for future integration; never expose backend credentials.

Supabase, authentication, chat, shadcn/ui components and product pages are deferred.
Dependencies are locked here; no Node workspace wraps the Python backend.

Compatibility notes: TypeScript is pinned to 5.9 because the current ESLint parser
does not support 7. ESLint 9 is retained because Next.js React plugins fail with
10; its install-time deprecation warning remains a tooling follow-up. pnpm skips
unrs-resolver's install script; all current checks pass without it. Next.js
generates local AGENTS.md/CLAUDE.md guidance, which is tracked.
