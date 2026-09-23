# ADR-005 — Use Vercel for the Bismark AI Frontend

**Project:** Bismark AI  
**ADR ID:** ADR-005  
**Title:** Use Vercel for the Next.js Frontend  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 frontend deployment architecture

---

## 1. Context

Bismark AI requires a production hosting platform for its web frontend.

The frontend stack is:

```text
Next.js
TypeScript
React
Tailwind CSS
shadcn/ui
```

The frontend is responsible for:

- authentication UI;
- organization/workspace navigation;
- document upload UI;
- document status;
- chat;
- streamed responses;
- citations;
- conversation history;
- settings;
- administrative user experience.

The backend runs separately on a Hostinger VPS behind Caddy.

The project therefore needs a frontend hosting platform that supports:

- Next.js well;
- fast deployment;
- preview deployments;
- environment variables;
- CDN delivery;
- production TLS;
- simple Git integration;
- low operational overhead.

Several approaches were considered:

1. Vercel;
2. self-hosting Next.js on the Hostinger VPS;
3. static hosting/CDN platforms;
4. general-purpose cloud/container hosting.

---

## 2. Decision

Bismark AI V1 will deploy the Next.js frontend on **Vercel**.

The intended public frontend hostname is:

```text
app.bismark.ai
```

The frontend will communicate with the FastAPI backend at:

```text
api.bismark.ai
```

through HTTPS.

---

## 3. Why Vercel

### 3.1 Strong Next.js Compatibility

Vercel is well suited to the selected frontend framework.

This reduces friction around:

- builds;
- routing;
- server rendering;
- static assets;
- deployment behavior.

---

### 3.2 Fast Development Workflow

Vercel supports a straightforward flow:

```text
Git push
→ build
→ preview deployment
→ review
→ production promotion
```

This is useful for both human engineers and agentic coding workflows.

---

### 3.3 Preview Deployments

Preview deployments allow product and engineering review before production.

This is especially useful for:

- UI changes;
- chat UX;
- document flows;
- citation rendering;
- responsive behavior.

---

### 3.4 Reduced Server Operational Burden

Hosting the frontend separately keeps the Hostinger VPS focused on:

- FastAPI;
- background worker;
- Redis;
- parser;
- Caddy.

This reduces coupling between frontend deployment and backend compute.

---

### 3.5 Global Asset Delivery

Vercel provides edge/CDN delivery for frontend assets.

This improves frontend delivery without Bismark AI needing to operate its own CDN.

---

## 4. Architectural Role

The frontend is a presentation and interaction layer.

It must not become the authoritative security layer.

Conceptually:

```text
Browser
   |
   v
Vercel / Next.js
   |
   v
FastAPI
   |
   v
Application services
```

The backend remains authoritative for:

- authorization;
- tenant access;
- document permissions;
- retrieval;
- provider credentials;
- business logic.

---

## 5. Responsibilities of Vercel

Vercel is responsible for:

- frontend runtime;
- frontend build;
- frontend deployment;
- frontend TLS;
- CDN delivery;
- preview environments.

It is not responsible for:

- backend API;
- database;
- RAG;
- worker jobs;
- Redis;
- document parsing;
- tenant authorization.

---

## 6. Frontend Environment Variables

Public frontend configuration may include:

```text
NEXT_PUBLIC_APP_URL
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

Only intentionally public values may use `NEXT_PUBLIC_*`.

---

## 7. Secret Restrictions

The following must **never** be present in frontend environment variables:

```text
SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL
VOYAGE_API_KEY
LLM_API_KEY
REDIS_URL
SSH credentials
```

Vercel environment configuration must not be treated as a place to expose backend secrets to browser code.

---

## 8. Supabase Usage from Frontend

The frontend may use Supabase public configuration for supported authentication flows.

This does not mean business logic should move to the browser.

Preferred model:

```text
Supabase Auth
→ identity/session

FastAPI
→ authorization/business logic
```

---

## 9. API Communication

Frontend requests to the backend should use:

```text
NEXT_PUBLIC_API_URL
```

Production:

```text
https://api.bismark.ai
```

Do not hard-code production URLs throughout frontend modules.

---

## 10. CORS Consequence

Because frontend and API are on different origins:

```text
app.bismark.ai
api.bismark.ai
```

FastAPI must explicitly allow the approved frontend origin.

Production should not use wildcard CORS.

---

## 11. Authentication Consequence

Session/token handling must work correctly across the Vercel-hosted frontend and FastAPI backend.

The browser should send the Supabase access token to FastAPI through:

```http
Authorization: Bearer <token>
```

or another explicitly documented secure mechanism.

---

## 12. Streaming Requirement

Bismark AI chat uses streamed responses.

The frontend must support:

```text
FastAPI
→ HTTPS
→ Vercel-hosted browser client
```

without requiring generation to pass through an unnecessary Vercel serverless hop.

Preferred:

```text
browser
→ api.bismark.ai
```

for streamed chat.

---

## 13. Avoid Unnecessary Proxying

Do not proxy all backend traffic through Next.js unless there is a documented reason.

Direct browser-to-FastAPI API access is simpler for:

- streaming;
- uploads;
- source URLs;
- request tracing.

---

## 14. File Upload Consequence

Large document uploads should normally go:

```text
Browser
→ FastAPI
→ Supabase Storage
```

or through a future secure direct-upload strategy.

Do not route large files through unnecessary frontend serverless handlers.

---

## 15. Alternative Considered — Self-Host Next.js on Hostinger

### Benefits

- one server;
- fewer hosting vendors;
- potentially simpler DNS.

### Drawbacks

- frontend competes with parser/backend resources;
- deployments become more coupled;
- frontend availability tied to the VPS;
- fewer preview deployment capabilities;
- more web-server operational responsibility.

### Decision

Rejected for V1.

---

## 16. Alternative Considered — Static Hosting

### Benefits

- simple;
- inexpensive;
- CDN-friendly.

### Drawbacks

- may limit Next.js runtime features;
- less natural fit if server-side capabilities are used.

### Decision

Not selected as the canonical deployment model.

---

## 17. Alternative Considered — General Cloud Compute

Examples:

- AWS;
- GCP;
- Azure;
- generic VPS.

### Benefits

- broad infrastructure capabilities;
- full control.

### Drawbacks

- unnecessary frontend operations;
- more deployment complexity;
- less convenient preview workflow.

### Decision

Not selected for V1 frontend hosting.

---

## 18. Build Strategy

The frontend should use a reproducible package manager workflow.

Expected:

```text
pnpm install
pnpm build
```

or the repository-selected equivalent.

The package manager and lockfile must remain consistent.

---

## 19. Preview Environment

Every meaningful pull request may receive a preview deployment.

Preview environments should use:

- development/staging API endpoints;
- non-production Supabase configuration where practical.

Do not connect arbitrary preview deployments to production admin functionality without deliberate configuration.

---

## 20. Production Environment

Production Vercel settings should include only production-safe frontend configuration.

Expected:

```text
NEXT_PUBLIC_APP_URL=https://app.bismark.ai
NEXT_PUBLIC_API_URL=https://api.bismark.ai
NEXT_PUBLIC_SUPABASE_URL=<public project URL>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<public anon key>
```

---

## 21. Environment Separation

Recommended:

```text
Development
Preview
Production
```

Do not reuse production credentials casually in preview builds.

---

## 22. DNS

The production frontend domain should be configured in Vercel.

Example:

```text
app.bismark.ai
```

DNS records must follow the active Vercel configuration.

---

## 23. TLS

Vercel will manage frontend TLS.

The backend TLS remains Caddy's responsibility.

Thus:

```text
app.bismark.ai
→ Vercel TLS

api.bismark.ai
→ Caddy TLS
```

---

## 24. Deployment Independence

Frontend and backend should remain independently deployable.

This requires:

- stable API contracts;
- backward-compatible deployment where practical;
- environment-based API URLs.

Do not require exact simultaneous deployment for routine changes.

---

## 25. API Versioning

Frontend should call:

```text
/api/v1
```

Backend API versioning prevents frontend deployments from relying on undocumented endpoint changes.

---

## 26. Rollback

Vercel should allow rollback/promotion to a previous working deployment.

Before rollback:

- confirm API compatibility;
- confirm environment configuration.

---

## 27. Build Failure

A failed frontend build must not affect the currently active production deployment.

Only successful reviewed builds should be promoted.

---

## 28. Observability

Frontend errors should eventually be observable.

Possible future tools:

- Sentry;
- Vercel analytics;
- OpenTelemetry-compatible tooling.

These are optional for early V1.

---

## 29. Logging

Do not log sensitive tokens in client console output.

Remove debug logs that expose:

- access tokens;
- source URLs;
- user-private content;
- environment details.

---

## 30. Security Headers

Security headers may be configured through Next.js/Vercel where appropriate.

Potential:

- Content Security Policy;
- Referrer Policy;
- frame restrictions;
- Permissions Policy.

They should be tested carefully rather than copied blindly.

---

## 31. XSS Consideration

Model output, Markdown, filenames, and document-derived metadata are untrusted content.

Frontend rendering must sanitize unsafe HTML.

Do not render model output with unrestricted `dangerouslySetInnerHTML`.

---

## 32. Performance

Vercel should help frontend delivery performance through:

- CDN;
- optimized static assets;
- deployment infrastructure.

Application-level performance still depends on:

- client bundle size;
- API latency;
- streaming;
- component behavior.

---

## 33. Server Components / Client Components

Use Next.js server/client boundaries deliberately.

Do not place secrets in client components.

Do not move backend authorization into server components as a replacement for FastAPI authorization.

---

## 34. BFF Pattern

A Backend-for-Frontend layer inside Next.js is not required for V1.

If later introduced, it must have a clear reason such as:

- session normalization;
- UI-specific aggregation;
- edge behavior.

It must not duplicate core FastAPI business logic.

---

## 35. Availability Implication

Vercel and Hostinger are separate failure domains.

Possible states:

```text
frontend available / API unavailable
frontend unavailable / API available
```

The frontend should handle API unavailability gracefully.

---

## 36. Error UX

If backend cannot be reached, frontend should show a controlled service error.

Do not expose internal fetch stack traces to users.

---

## 37. CI/CD

Recommended:

```text
Git repository
→ CI checks
→ Vercel preview
→ review
→ production deployment
```

Production promotion should depend on passing required checks.

---

## 38. Branch Strategy

Preview deployments may follow feature/PR branches.

Production should deploy from the approved main branch or production release process.

---

## 39. Repository Structure

Frontend lives under:

```text
apps/web
```

Vercel project root should be configured accordingly if using a monorepo.

---

## 40. Monorepo Consequence

The repository also contains:

```text
apps/api
docs
infra
```

Vercel must build only the frontend workspace.

Backend deployment remains independent.

---

## 41. Dependency Management

Frontend dependencies should be locked.

Avoid adding large packages without clear value.

---

## 42. Cost Consideration

Vercel offers a low-friction path for early product development.

If frontend hosting cost later becomes materially unfavorable, migration is possible because Bismark AI uses standard Next.js.

---

## 43. Provider Lock-In

Bismark AI should avoid unnecessary Vercel-specific application logic.

Keep the application deployable to another Node-compatible environment if future needs change.

---

## 44. Migration Away

If leaving Vercel later:

1. retain Next.js;
2. move build/runtime to another platform;
3. reconfigure domain/TLS;
4. migrate environment variables;
5. verify server-side behavior;
6. update this ADR.

This should not require rewriting core product logic.

---

## 45. Future Enterprise Hosting

Large enterprise customers may later require:

- dedicated frontend deployment;
- private network access;
- regional hosting;
- on-prem deployment.

Those modes are outside V1.

---

## 46. Prohibited Actions

Without a superseding ADR, do not:

- self-host production frontend on the same VPS merely for convenience;
- expose backend secrets through `NEXT_PUBLIC_*`;
- route every backend request through Vercel unnecessarily;
- make frontend authorization authoritative;
- bypass FastAPI for privileged data access;
- connect production frontend previews to unsafe production operations without controls.

---

## 47. Review Triggers

Revisit this decision if:

- Vercel cost becomes materially unfavorable;
- enterprise deployment requires private hosting;
- Next.js runtime requirements become incompatible;
- deployment control requirements increase;
- frontend and backend need to be co-located for a measured technical reason.

---

## 48. Consequences

### Positive

- excellent Next.js workflow;
- fast deployments;
- preview environments;
- low frontend operational burden;
- automatic frontend TLS;
- CDN delivery;
- independent backend scaling.

### Negative

- additional vendor dependency;
- separate frontend/backend deployment surfaces;
- cross-origin configuration required;
- enterprise private-hosting needs may require another deployment mode.

---

## 49. Status

**Accepted**

Vercel is the canonical Bismark AI V1 frontend hosting platform.

The intended public topology is:

```text
Browser
   |
   v
app.bismark.ai
Vercel / Next.js
   |
   v
api.bismark.ai
FastAPI / Hostinger
```

Any replacement should be documented through a new or superseding ADR.
