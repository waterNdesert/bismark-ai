# PROJECT_STATE.md — Bismark AI

**Last updated:** 2026-09-23  
**Current phase:** Phase 0 — Repository Foundation  
**Current task:** Repository normalization and canonical structure  
**Task status:** COMPLETED — documentation normalization validated  
**Overall status:** Documentation and directory skeleton only; Phase 0 remains incomplete.

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

The initial read-only assessment found 22 Markdown documents and one environment
example, with no application source or Git metadata. Repository normalization
preserves those documents and adds the following foundation:

- Root `PRD.md` and `.env.example` use canonical filenames.
- All nine accepted ADRs are under `docs/decisions/`.
- README links the project documentation and states that no runnable product exists.
- `.gitignore` protects environment secrets and generated/runtime artifacts.
- `apps/web`, `apps/api`, `infra/docker`, `infra/caddy`, `scripts`, `tests`, and
  `evals` contain only empty `.gitkeep` placeholders.
- Documentation authority is reconciled with the explicitly approved order.
- Retrieval documentation places authorization and SQL filters before both searches.
- Conceptual worker networking separates private Redis access from outbound HTTPS.
- Migration documentation places required extensions before dependent schema objects.
- Parser and embedding dimension are unset in the environment template.

No application code, manifests, lockfiles, migrations, Supabase configuration,
Dockerfiles, runnable Compose configuration, Caddyfile, or CI workflows exist.
No dependencies were installed. Git has not been initialized.

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

| Area | Status | Evidence |
|---|---|---|
| Documentation and repository skeleton | PARTIAL FOUNDATION | Paths normalized; applications and tooling absent. |
| Frontend / backend | NOT STARTED | Empty application directories only. |
| Dependency management / lint / formatting / type checking | NOT STARTED | No manifests, lockfiles, or tool configuration. |
| Database / migrations / Supabase | NOT STARTED | Specifications only; no connection or migration executed. |
| Auth / organizations / workspaces / authorization | NOT STARTED | Specifications only. |
| Documents / storage / ingestion | NOT STARTED | Specifications only. |
| Redis / worker / parser / chunking | NOT STARTED | Specifications only. |
| Embeddings / vector / FTS / fusion / reranking | NOT STARTED | Specifications only. |
| Conversations / chat / streaming / citations | NOT STARTED | Specifications only. |
| Feedback / audit / usage | NOT STARTED | Specifications only. |
| Tests / evaluations | NOT STARTED | Empty directories; no executable suites. |
| Docker / Caddy / Vercel integration / CI | NOT STARTED | Documentation only. |
| Production | UNKNOWN externally | No deployment performed or verified from this workspace. |

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

These are documented requirements, not implemented or tested controls.

## Open decisions

| Decision | Current state / timing |
|---|---|
| Parser | Docling or Unstructured; select before parser implementation. |
| Worker framework | RQ, ARQ, Dramatiq, Celery, or a justified alternative; select before worker implementation. |
| Voyage embedding model | Open; select before vector schema finalization. |
| Embedding dimension | Open until the selected model is verified; no assumed 1024 default. |
| Voyage rerank model | Open; must remain configurable. |
| LLM provider / model | Open; integrate behind `LLMProvider`. |
| FTS maintenance | Generated column, trigger, or application writes; select and test with schema implementation. |
| Document retention | Soft/hard deletion, retention duration, deletion audit, and source removal timing remain open. |

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

## Validation

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

## Remaining Phase 0 work

- Initialize Git.
- Scaffold the Next.js frontend.
- Scaffold the FastAPI backend.
- Select runtime versions and reproducible dependency management.
- Implement environment loading and validation.
- Configure linting, formatting, and type checking.
- Establish a test harness and initial tests.
- Add the local Docker/Redis baseline.
- Configure pull-request CI.
- Verify frontend/backend/Redis startup and all Phase 0 exit criteria.

Phase 1 has not started. No Supabase initialization, migrations, or production
operations were performed. Next work requires approval; a bounded Git
initialization task can precede application scaffolding.
