# PROJECT_STATE.md — Bismark AI

**Last updated:** 2026-10-01  
**Current phase:** Phase 2B–2D — tenant application foundation and Manual Upload
**Current task:** Documentation catch-up after live verification
**Phase status:** Tenant context, role-aware shell, Sources and Manual Upload UI implemented; live owner upload verification passed.
**Overall status:** Source-centric upload foundation through migration `20260928_0011` is implemented. Two live uploads verified source reuse and private Storage. Processing and retrieval remain planned.

## Current checkpoint — 2026-10-01

- Authenticated `/api/v1/me/context` returns real organization roles and explicit
  workspace memberships. TenantProvider reuses AppSession authentication;
  selection is memory-only and roles stay separate.
- Owners/admins see Overview, Ask Bismark, Sources, Documents, Conversations,
  Analytics, Members, Usage and Settings. Members see Ask Bismark/Conversations;
  Account/sign-out remain available. Analytics is a placeholder, not real metrics.
- Sources and Documents share the operational Manual Upload dialog. The UI
  requires an owner/admin organization role plus selected workspace access;
  the API independently checks both memberships (not an owner/admin-only policy).
- KnowledgeSource schema, tenant target key, nullable document source linkage,
  canonical source uniqueness and race recovery are implemented. Prior live
  migration verification reported head `20260928_0011`; this audit does not
  re-query migration state.
- Live owner login, context/navigation, two HTTP 201 uploads, canonical source
  reuse, private object contents and sign-out/reload passed. Two live test
  documents remain intentionally stored. See [TESTING.md](docs/TESTING.md).
- Automated checkpoint supplied for this catch-up: targeted backend context
  tests, Ruff and mypy passed; frontend ESLint, typecheck, production build and
  Playwright **51/51** passed. These are prior results, not reruns in this audit.

### Remaining limitations

Persistent Documents listing API/UI, document deletion/management, automatic
ingestion-job creation, workers, parsing, normalization, chunks, embeddings,
hybrid retrieval, real Ask Bismark backend/citations, production analytics,
third-party connectors, platform super-admin/control plane, billing and
entitlements are **not implemented**.

### Next implementation sequence

1. Documents listing/management API.
2. Documents admin UI backed by real listing.
3. Automatic ingestion-job creation.
4. Worker foundation.
5. Parsing/normalization.
6. Chunks.
7. Embeddings/indexing.
8. Retrieval.
9. Real Ask Bismark chat and citations.

Platform super-admin remains a parallel planned track, not an immediate blocker.
Older dated checkpoints below are historical and do not supersede this section.

## Documentation authority

The canonical authority order is defined in [AGENTS.md §2](AGENTS.md#2-documentation-authority):

1. Accepted ADRs under `docs/decisions/`
2. `docs/SECURITY.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DATABASE.md`
5. `docs/API.md`
6. `docs/RAG.md`
7. `docs/DEPLOYMENT.md`
8. `docs/TESTING.md`
9. `ROADMAP.md`
10. `PRD.md`
11. `AGENTS.md`
12. `PROJECT_STATE.md` for current implementation state
13. `CONTRIBUTING.md`
14. `CHANGELOG.md`

This file reports current state. It does not override architectural decisions.

## Verified repository state

Repository normalization and Git baseline are complete. The application foundation
now includes:

- FastAPI under `apps/api` with typed settings, explicit CORS, process/database
  health routes and verified GET/POST `/api/v1/me`. Health needs no auth credentials;
  profile operations require Supabase public configuration and a database connection.
- Next.js account screen with Supabase signup/login/logout, refresh, email-link
  confirmation, password recovery, and backend-verified profile display.
- Python 3.12.14 managed by uv (supported minor 3.12), per-app uv.lock.
- Node.js 24, pnpm 10.33.2 and frontend pnpm-lock.yaml; no Node workspace.
- Ruff, strict mypy, pytest, Next.js ESLint presets, TypeScript and build commands
  exposed through the root Makefile and application READMEs.
- Prettier frontend formatting with `format` and `format:check` scripts.
- GitHub Actions validation for backend, frontend and Docker Compose configuration
  on pull requests and pushes to `main`.
- SQLAlchemy 2.x, Alembic, and psycopg database foundation.
- Secret-typed Supabase/database settings and generic `/ready/database` health.
- Framework-generated web AGENTS.md/CLAUDE.md guidance retained because Next.js
  recreates it during development startup.

The local Docker/Redis baseline is validated for the approved Phase 0 scope.
The API image builds and starts as non-root `appuser`; `/health` and `/ready`
return HTTP 200, Redis responds with `PONG`, Redis remains internal-only, and
the stack tears down cleanly.
Supabase PostgreSQL connectivity via the Session Pooler and the extension-only
migration are verified.
The five-table tenant schema and account/profile authentication foundation exist.
Organization/workspace authorization helpers are implemented and RLS is enabled
on the five tenancy tables. Private storage, secure manual upload, documents and
ingestion_jobs metadata are implemented; documents/jobs have hardened RLS/grants.
No tenant management endpoints, ingestion worker, Caddy production config or
production deployment is recorded. Dependencies installed remain
limited to the current application/tooling foundation and local Docker service
stack. Work remains on `main`; earlier tasks recorded GitHub CI verification.

## Completed version-control foundation

- Repository normalization and canonical documentation structure completed.
- Git repository initialized; `main` branch established.
- Baseline commit created: `3465bfe` — `chore: establish Bismark AI project foundation`.
- Baseline contains 33 files: documentation, environment example, ignore rules,
  Markdown whitespace attributes, and seven empty directory placeholders.
- `.gitattributes` permits Markdown end-of-line spaces used for hard breaks and
  whitespace examples; other Git whitespace checks remain enabled.
- Secret scan found no likely credentials; sensitive example fields are blank.
- Ignore checks passed for local environment files, dependencies, and caches;
  `.env.example` is tracked. Staged whitespace checks passed.
- Initial commit verification found a clean working tree and no remote.
- This state record and changelog are recorded separately from the baseline.

## Accepted architecture

The accepted ADRs remain unchanged:

- [ADR-001: Supabase](docs/decisions/ADR-001-use-supabase.md)
- [ADR-002: Voyage](docs/decisions/ADR-002-use-voyage.md)
- [ADR-003: Hostinger KVM 2](docs/decisions/ADR-003-use-hostinger-kvm2.md)
- [ADR-004: Caddy](docs/decisions/ADR-004-use-caddy.md)
- [ADR-005: Vercel](docs/decisions/ADR-005-use-vercel-for-frontend.md)
- [ADR-006: FastAPI](docs/decisions/ADR-006-use-fastapi.md)
- [ADR-007: Modular monolith](docs/decisions/ADR-007-use-modular-monolith.md)
- [ADR-008: Redis and Python worker](docs/decisions/ADR-008-use-redis-worker.md)
- [ADR-009: PostgreSQL hybrid search](docs/decisions/ADR-009-use-postgres-hybrid-search.md)

The intended deployment remains Next.js on Vercel; FastAPI, worker, Redis, and
Caddy on Hostinger; PostgreSQL/Auth/Storage/pgvector on Supabase; Voyage embeddings
and reranking; external generation through `LLMProvider`.

## Implementation inventory

| Area                                                      | Status                       | Evidence                                                                                                                                          |
| --------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Documentation and repository skeleton                     | PARTIAL FOUNDATION           | Paths normalized; applications and tooling present.                                                                                               |
| Frontend / backend                                        | PARTIAL                      | Tenant context, role-aware app and Manual Upload UI/API implemented; listing and downstream knowledge features planned.                                                                                |
| Dependency management / lint / formatting / type checking | COMPLETE                     | Locked app dependencies, Ruff, mypy, Prettier, ESLint, TypeScript and builds pass locally; CI runs the same checks.                               |
| Database / migrations / Supabase                          | COMPLETE (Phase 1A)          | Supabase PostgreSQL connection verified; SQLAlchemy/Alembic foundation and vector extension migration applied.                                    |
| Auth / organizations / workspaces / authorization         | COMPLETE (Phase 1D)          | Application-layer organization/workspace authorization complete; RLS enabled on five tenancy tables; live two-user isolation passed 20/20 checks. |
| Documents / storage / ingestion                           | PARTIAL                      | Private storage, source-linked upload, canonical source uniqueness and ingestion_jobs metadata implemented; automatic jobs/workers planned.                                                                                                                              |
| Redis / worker / parser / chunking                        | PARTIAL                      | Redis local development baseline is validated in Docker; no worker implementation yet.                                                            |
| Embeddings / vector / FTS / fusion / reranking            | NOT STARTED                  | Specifications only.                                                                                                                              |
| Conversations / chat / streaming / citations              | NOT STARTED                  | Specifications only.                                                                                                                              |
| Feedback / audit / usage                                  | NOT STARTED                  | Specifications only.                                                                                                                              |
| Tests / evaluations                                       | PARTIAL                      | Phase 1D authorization/RLS tests and 20 live RLS checks passed; RAG evaluation absent.                                                            |
| Docker / Compose / local infrastructure                   | COMPLETED (Phase 0 baseline) | FastAPI image and Redis service validated under `infra/docker/compose.dev.yaml`; Redis is not host-published.                                     |
| CI / Vercel / Caddy / production deployment               | PARTIAL                      | GitHub Actions validation is complete; Vercel, Caddy and production deployment remain deferred.                                                   |
| Production                                                | UNKNOWN externally           | No production deployment performed or verified from this workspace.                                                                               |

## Security and RAG invariants

- FastAPI validates identity and authorizes organization/workspace access.
- Both vector and FTS queries apply tenant/workspace and eligible-document filters
  inside the database query before returning candidates.
- NEVER retrieve globally and filter unauthorized results in Python.
- Reranking receives authorized candidates only.
- Citations reference only evidence actually supplied to the LLM.
- Conversation history is context, not authoritative organizational evidence.
- Source documents remain private in Supabase Storage; VPS files are temporary.
- Privileged credentials remain server-side. Cross-tenant exposure blocks release.

Application-layer organization/workspace authorization is complete. RLS is
enabled on profiles, organizations, organization_members, workspaces, and
workspace_members. Live two-user cross-tenant isolation passed all 20 checks.
The private `bismark_rls` helper schema is not exposed through the Supabase Data
API. No organization/workspace write or administrative RLS policies were added;
the existing profile self-update policy remains in scope. RAG remains incomplete.

## Open decisions

| Decision               | Current state / timing                                                                         |
| ---------------------- | ---------------------------------------------------------------------------------------------- |
| Parser                 | Docling or Unstructured; select before parser implementation.                                  |
| Worker framework       | RQ, ARQ, Dramatiq, Celery, or a justified alternative; select before worker implementation.    |
| Voyage embedding model | Open; select before vector schema finalization.                                                |
| Embedding dimension    | Open until the selected model is verified; no assumed 1024 default.                            |
| Voyage rerank model    | Open; must remain configurable.                                                                |
| LLM provider / model   | Open; integrate behind `LLMProvider`.                                                          |
| FTS maintenance        | Generated column, trigger, or application writes; select and test with schema implementation.  |
| Document retention     | Soft/hard deletion, retention duration, deletion audit, and source removal timing remain open. |

Additional database implementation choices remain documented in
[DATABASE.md §133](docs/DATABASE.md#133-decisions-still-to-be-finalized), including
HNSW parameters, RLS helpers, ingestion-job timing, and conversation tombstones.

### OPEN DESIGN ISSUE — historical citations and deletion

The suggested `message_sources` schema has required foreign keys to documents and
chunks. Reprocessing/deletion guidance also proposes removing chunks while
retaining historical evidence. These requirements must be reconciled before the
related migration is implemented. Citation retention, source references, and
purge behavior require an explicit design decision; this task selects no schema
solution and creates no migration.

### Remaining configuration cautions

The environment template still contains development/test defaults, including
fake-provider flags and a `latest` image tag. They are not production readiness
claims. Production settings validation and immutable deployment tags remain
future implementation work. The example Redis hostname assumes container
networking; a host-run development process will need appropriate configuration.

## Normalization validation (prior task)

Validation completed on 2026-09-23:

- `find . -maxdepth 3 -type f | sort`: 32 files, including 7 empty placeholders.
- Requested stale-reference search: 14 matches, all valid `.env.example` references;
  the pattern also matches canonical names. A stricter stale-path check found none.
- Requested fixed-default search: no matches (exit 1).
- Requested authority-heading search: 6 matches; all point to the approved order.
- Read-only Python assertions: all 9 ADRs present and byte-identical to originals;
  all 16 README links resolve; all 3 full authority lists identical; all 7 technical
  documents reference canonical authority; no stale paths or root-level ADR links.
- All 6 unresolved parser/model settings and 7 credential fields are blank;
  no credential-pattern matches in `.env.example`.
- All 23 requested ignore patterns are present; `*.env` additionally covers
  documented deployment environment files.
- Scope check: no application code, dependency files, migrations, runtime
  configuration, or Git metadata created. No dependencies installed.

Counts above describe the completed validation before this results entry was
added; subsequent text searches may also match the validation record itself.
Application tests, builds, lint, and type checks cannot run because no application
or tooling is configured. No live infrastructure or provider checks are claimed.

## Application foundation validation — 2026-09-24

Passed:

- `cd apps/api && uv run --locked python -c 'from app.main import app; print(app.title)'`: Bismark AI.
- `cd apps/api && uv run ruff check .`: no errors.
- `make api-format-check`: 10 files already formatted.
- `cd apps/api && uv run mypy app tests`: no issues in 9 source files.
- `cd apps/api && uv run pytest`: 10 passed, 1 dependency warning.
- `make web-lint`: no errors or warnings.
- `make web-typecheck`: Next.js type generation and TypeScript pass.
- `NEXT_TELEMETRY_DISABLED=1 make web-build`: successful static production build.
- Brief uvicorn and Next.js development boot checks: HTTP 200 from API /health
  on loopback port 18000 and frontend / on loopback port 13000. Both stopped.

Known tooling warnings/decisions:

- TypeScript 7 was incompatible with the installed ESLint parser; pinned to 5.9.3.
- ESLint 10 was incompatible with Next.js React lint plugins; retained ESLint 9.39.5,
  which emits an install-time deprecation warning. Revisit when presets support 10.
- Starlette warns that its TestClient httpx integration is deprecated; current
  tests pass using the requested httpx dependency. No extra HTTP library added.
- pnpm skipped unrs-resolver's install script; lint/type/build work without it.
- shadcn/ui and frontend environment consumption are deferred. Settings currently
  read process environment, not dotenv files.

## Phase 0 exit verification

- Frontend and backend start locally.
- Redis starts in the local Docker baseline.
- Backend lint, formatting, type checking and tests pass.
- Frontend formatting, lint, type checking and build pass.
- Environment defaults and malformed origin validation are covered by tests.
- GitHub Actions runs backend, frontend and Compose configuration validation on
  pull requests and pushes to `main`.
- Documentation and repository structure are present.

Phase 1A, Phase 1B and Phase 1C are complete. CI run `35966963645` passed for
commit `7f905b2`. Phase 1D implementation is complete: the RLS migration is
applied live and two-user behavioral verification passed 20/20 checks. Phase 1D
closeout had Ruff findings in that historical record. The current foundation
has since advanced through `20260927_0007`, including Storage. Checks were not
rerun in this documentation task; production deployment and open parser, worker,
model and citation-retention decisions remain unchanged.

## Phase 1C implementation — 2026-09-25

- Browser Supabase SDK handles email/password signup, login, confirmation,
  password reset/recovery, refresh and local-session logout.
- FastAPI verifies bearer tokens online against the configured Supabase Auth
  server; no custom signature decoder or service-role key is used.
- GET `/api/v1/me` reads only the verified user's profile. POST initializes that
  profile idempotently without granting memberships or overwriting existing data.
- No migrations added or applied and no production deployment performed.
- User confirmed live signup, Supabase confirmation email delivery, redirect to
  localhost, session establishment, profile loading and displayed signed-in email.
- Automated results: `make api-test` (51 passed), `make web-test` (9 passed),
  `make check` and `git diff --check` passed.
- Browser tests confirm session persistence after reload, logout persistence
  after reload, generic incorrect-password errors followed by successful retry,
  refresh, profile initialization and rejection of invalid API sessions.
- Password recovery request, recovery-link handling, token removal from the URL
  and password-update submission pass with mocked Supabase responses. Live reset
  email delivery/password change was not reported as manually verified.
- Browser failures were test-selector/URL assertions and a conflict with the
  running development server. Tests now use an isolated `.next-e2e` directory.
- Ruff normalized the three existing formatting-only Python edits; migration
  and model behavior is unchanged. No broad documentation edits were made.
- Local credential-value/private-key scan passed; `.env` and
  `apps/web/.env.local` are ignored and excluded from commits.
- The Phase 1D commit and GitHub Actions verification are pending successful
  completion of the required repository checks.
- Simple manual steps: [Auth test guide](docs/AUTH_TESTING.md).

## Phase 1D implementation — historical record, 2026-09-26

- Application-layer organization and workspace authorization are complete.
- RLS is enabled on profiles, organizations, organization_members, workspaces,
  and workspace_members; migration `20260925_0003` is applied live.
- Live two-user cross-tenant isolation verification passed 20/20 checks.
- Confirmed `bismark_rls` is not exposed through the Supabase Data API.
- No organization/workspace write or administrative RLS policies were added.
- Phase 1D targeted authorization/RLS tests passed (19 tests). `make check`
  stopped at Ruff with six findings in the Phase 1D migration and RLS test;
  remaining checks and GitHub Actions have not been verified.
- This was the state at the Phase 1D checkpoint; the current checkpoint is at the top of this file.

## Historical baseline — Phase 1E-XA, 2026-09-28

### IMPLEMENTED

- Supabase Auth, organization/workspace authorization, tenancy RLS and hardened
  grants; private Supabase Storage and the secure manual upload API.
- `documents` metadata (`20260926_0004`), document tenant key
  (`20260927_0005`), `ingestion_jobs` metadata (`20260927_0006`), and backend-only
  document/job RLS with revoked anon/authenticated grants (`20260927_0007`).
- Migration head `20260927_0007` is reported live by the current task handoff.
  Models/migrations were inspected for schema facts; no live database checks,
  tests or deployments were performed in this documentation-only task.
- Manual upload is designated Connector / Source #001 (`manual_upload`). Existing
  Storage + documents + ingestion_jobs remain its implementation foundation;
  this designation does not imply a source record or Connector framework exists.

### PLANNED / NOT IMPLEMENTED

- `knowledge_sources` (next schema step) and source-aware document provenance.
- Connector framework, sync engine and originating-system ACL propagation.
- Automatic Ingestion Job creation after upload and worker foundation.
- Parsing/normalization, chunks, embeddings/indexes, retrieval and citations/chat.
- Website source, Google Drive / Notion and other third-party connectors.
- Embeddable website assistant, voice and future Slack/Teams/mobile interfaces.
- Production reranking flow, usage ledger and source ACL synchronization.
- Global → plan → tenant override entitlements, usage/cost telemetry,
  customer limits/allowances and later billing based on measured unit economics.

### Documentation alignment and next sequence

Phase 1E-XA records the Company Intelligence Layer direction and one common
Knowledge Source → Connector → Document / Knowledge Object → Ingestion Job
pipeline. It changes no application behavior, schema, storage or security policy.
Next: source schema, attach manual uploads/documents to sources, automatic jobs,
workers, parsing/normalization, chunking, embeddings/indexing, retrieval, then
citations/chat. Source identity/backfill, connector selection, sync/deletion and
ACL semantics remain design work; historical citation retention remains open.
Historical test/CI results above are not a fresh closeout of current code changes.

## Phase 1E-XA2 audit — 2026-09-28

Repository comparison covered current models, migrations 0001–0007, tenancy
helpers, Storage setup/service/paths, upload route/settings, runtime dependencies
and targeted test areas. Only documentation changed; no tests, live operations,
commits, pushes or CI ran. Prior results below are from the supplied live handoff.

Live migration head at that historical checkpoint: **20260927_0007**.

| Revision | Implemented foundation |
| --- | --- |
| 20260924_0001 | pgvector |
| 20260924_0002 | Tenancy schema |
| 20260925_0003 | Tenancy RLS/private helpers |
| 20260926_0004 | documents |
| 20260927_0005 | Document tenant-reference key |
| 20260927_0006 | ingestion_jobs metadata |
| 20260927_0007 | Document/job RLS and grant hardening |

Private `knowledge-documents` bucket and backend Storage upload/download/delete
were verified live. A real Auth + membership upload smoke returned 201, verified
safe response fields, document tenant/uploader identity and private object content,
and cleaned up its object/row. Original tenancy cross-tenant RLS checks passed;
`bismark_rls` is not exposed through the Data API. Documents/jobs separately have
RLS enabled, FORCE RLS disabled, zero policies and no anon/authenticated CRUD
grants. Full schema/constraints are in DATABASE.md, HTTP behavior in API.md,
setup command in DEPLOYMENT.md and targeted coverage/evidence in TESTING.md.

Only Ingestion Job metadata exists: no automatic creation, queue/claim/retry
execution, worker, parsing/normalization, chunks or AI processing. The historical
Phase 1D formatting/CI checkpoint is retained; this documentation audit does not
claim those repository checks have subsequently passed. Planned source provenance
and the Company Intelligence Layer architecture remain unchanged.

## Documentation catch-up boundary

This task updates documentation only; no application changes, migrations, app
tests, commits, pushes or CI runs. Next work follows the current checkpoint above.
