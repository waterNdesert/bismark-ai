# PROJECT_STATE.md — Bismark AI

**Last updated:** 2026-09-24  
**Current phase:** Phase 0 — Repository Foundation
**Current task:** Phase 0 complete; Phase 1 pending approval
**Phase status:** COMPLETE
**Overall status:** Repository foundation, local Docker/Redis baseline, and CI/tooling validation are complete. Phase 1 has not started.

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

- FastAPI under `apps/api` with typed environment settings, explicit CORS,
  `/health` and process-only `/ready` routes. No provider credentials required.
- Next.js App Router, TypeScript and Tailwind under `apps/web`, displaying only
  the project name and Phase 0 status. No environment variables consumed yet.
- Python 3.12.14 managed by uv (supported minor 3.12), per-app uv.lock.
- Node.js 24, pnpm 10.33.2 and frontend pnpm-lock.yaml; no Node workspace.
- Ruff, strict mypy, pytest, Next.js ESLint presets, TypeScript and build commands
  exposed through the root Makefile and application READMEs.
- Prettier frontend formatting with `format` and `format:check` scripts.
- GitHub Actions validation for backend, frontend and Docker Compose configuration
  on pull requests and pushes to `main`.
- Framework-generated web AGENTS.md/CLAUDE.md guidance retained because Next.js
  recreates it during development startup.

The local Docker/Redis baseline is validated for the approved Phase 0 scope.
The API image builds and starts as non-root `appuser`; `/health` and `/ready`
return HTTP 200, Redis responds with `PONG`, Redis remains internal-only, and
the stack tears down cleanly.
No database, authentication, domain features, migrations, ingestion worker,
Caddy production config or production deployment exists. Dependencies installed remain
limited to the current application/tooling foundation and local Docker service
stack. Git remains on `main` with no remote.

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

| Area                                                      | Status                       | Evidence                                                                                                            |
| --------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Documentation and repository skeleton                     | PARTIAL FOUNDATION           | Paths normalized; applications and tooling present.                                                                 |
| Frontend / backend                                        | PARTIAL                      | Minimal page and health routes validated; product features absent.                                                  |
| Dependency management / lint / formatting / type checking | COMPLETE                     | Locked app dependencies, Ruff, mypy, Prettier, ESLint, TypeScript and builds pass locally; CI runs the same checks. |
| Database / migrations / Supabase                          | NOT STARTED                  | Specifications only; no connection or migration executed.                                                           |
| Auth / organizations / workspaces / authorization         | NOT STARTED                  | Specifications only.                                                                                                |
| Documents / storage / ingestion                           | NOT STARTED                  | Specifications only.                                                                                                |
| Redis / worker / parser / chunking                        | PARTIAL                      | Redis local development baseline is validated in Docker; no worker implementation yet.                              |
| Embeddings / vector / FTS / fusion / reranking            | NOT STARTED                  | Specifications only.                                                                                                |
| Conversations / chat / streaming / citations              | NOT STARTED                  | Specifications only.                                                                                                |
| Feedback / audit / usage                                  | NOT STARTED                  | Specifications only.                                                                                                |
| Tests / evaluations                                       | PARTIAL                      | 10 backend tests pass; frontend component tests and RAG evaluations are not implemented.                            |
| Docker / Compose / local infrastructure                   | COMPLETED (Phase 0 baseline) | FastAPI image and Redis service validated under `infra/docker/compose.dev.yaml`; Redis is not host-published.       |
| CI / Vercel / Caddy / production deployment               | PARTIAL                      | GitHub Actions validation is complete; Vercel, Caddy and production deployment remain deferred.                     |
| Production                                                | UNKNOWN externally           | No production deployment performed or verified from this workspace.                                                 |

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

Domain authorization, tenant isolation and RAG remain documented requirements,
not implemented or tested controls. Phase 0 CORS validation has negative tests.

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

Phase 1 has not started. No provider configuration, migrations or deployments ran.
Open parser, worker, model and citation-retention decisions remain unchanged.

## Next phase

Phase 1 — Supabase Foundation.

## Recommended next task

Establish Supabase project configuration, PostgreSQL connection, extensions, and
migration foundation.
