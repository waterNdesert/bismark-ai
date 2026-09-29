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
browser session persistence and refresh; FastAPI owns profile data. The `/app`
shell waits for session/profile verification and provides navigation, account
settings and local sign-out. Backend authorization remains authoritative.

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

## Authenticated UI refinement

The app shares a neutral charcoal theme with the account entry. All eight app
routes support desktop, tablet and mobile layouts. The account menu in the desktop
sidebar or mobile navigation contains settings and Sign out. Password recovery
stays on the account entry until the user continues to the workspace.

The workspace selector is explicitly unavailable until workspace discovery is
wired. Manual Upload links to the documents page; its upload dialog explains this
prerequisite and does not send files. Document/member listings, conversations,
usage, connectors and billing are marked unavailable or coming soon. Ask supports
local draft prompts only; it does not generate or save answers. No sample metrics,
members, workspaces or documents are presented as live data.

To check locally, sign in, reload `/app`, open the account menu, and sign out.
Reload again and confirm the sign-in screen. On mobile, open navigation to find
the same menu. Test Escape, Tab and arrow keys in menus/dialogs. Run `pnpm lint`,
`pnpm typecheck`, `pnpm build` and `pnpm test:e2e`; browser tests mock Auth/profile
services and cover all app routes at 1440, 1280, 768 and 390 pixels. Screenshots are
written to ignored Playwright test results. The public reference site returned
HTTP 403 during the audit, so exact visual parity was not verified.

### Phase 2C: Ask conversation foundation

`/app/ask` uses a reusable, auto-growing `ChatComposer` and a viewport with a
separate bottom composer area. Enter submits only when a future submit handler
is supplied; Shift+Enter inserts a newline. Today, send is disabled and all
suggestions only fill a local, unsaved draft. Voice and attachments are omitted.
Reusable message, response-action, citation and follow-up components are tested
with isolated static fixtures; no demonstration answers or sources appear in
the app. To check manually, choose a prompt, type multiple lines, then clear the
composer and confirm it shrinks. The existing E2E suite also verifies scrolling
and final-message visibility at desktop, tablet and mobile sizes.
