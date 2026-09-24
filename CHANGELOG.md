# CHANGELOG.md — Bismark AI

All notable changes to Bismark AI should be documented in this file.

This changelog is intended for:

- engineering;
- product;
- DevOps;
- QA;
- security;
- agentic coding systems;
- future maintainers.

The format is inspired by **Keep a Changelog** and uses semantic-style version sections where practical.

---

## How to Use This File

Add meaningful changes under:

```text
[Unreleased]
```

When a release is created:

1. move completed entries from `[Unreleased]` into a versioned section;
2. add the release date;
3. keep entries concise but specific;
4. include deployment or migration notes where relevant.

Do not add trivial formatting changes unless they materially affect the product or development workflow.

---

## Change Categories

Use these headings when relevant:

### Added

New features, capabilities, endpoints, tables, integrations, or infrastructure.

### Changed

Existing behavior that was intentionally modified.

### Fixed

Bug fixes.

### Security

Security hardening, authorization fixes, vulnerability remediation, secret rotation, or tenant-isolation corrections.

### Deprecated

Functionality that remains available temporarily but is scheduled for removal.

### Removed

Features, APIs, infrastructure, or code paths that were removed.

### Database

Schema changes, migrations, indexes, RLS changes, vector changes, or data migrations.

### RAG

Changes to parsing, chunking, embeddings, retrieval, reranking, prompting, citations, or evaluation.

### Deployment

Vercel, VPS, Docker, Caddy, Supabase, CI/CD, backup, or infrastructure changes.

### Testing

New or materially changed tests, evaluation suites, release gates, or QA processes.

---

# [Unreleased]

## Added

- FastAPI Phase 0 scaffold with typed settings, explicit CORS and health/readiness routes.
- Minimal Next.js App Router, TypeScript and Tailwind frontend scaffold.
- Backend tests, Ruff/mypy tooling, frontend lint/type/build checks and per-app lockfiles.
- Root Makefile and application development instructions.

- Initialized Git on `main` and committed the initial repository baseline.
- Added Markdown-specific whitespace attributes to preserve existing hard breaks and test examples during Git checks.

- Phase 0 repository skeleton with application, infrastructure, scripts, tests, and evaluation directories.
- README documenting the planning-only state and canonical documentation entry points.
- `.gitignore` protecting environment secrets and generated/runtime artifacts.

- Initial Bismark AI product definition.
- Canonical `PRD.md`.
- Repository-level `AGENTS.md` for Codex, Claude Code, Cursor, OpenHands, and other agentic development tools.
- Canonical system architecture specification.
- Canonical database specification.
- Canonical API specification.
- Canonical RAG specification.
- Canonical security specification.
- Canonical deployment specification.
- Canonical testing strategy.
- Canonical phased roadmap.

## Changed

- Normalized canonical documentation paths to root `PRD.md`, `.env.example`, and `docs/decisions/`; moved all nine accepted ADRs.
- Reconciled documentation authority, retrieval scoping, conceptual worker networking, and migration ordering.
- Left parser and embedding dimension unset in the environment template; recorded historical citation retention as an open design issue.
- Updated project state from the verified repository inventory.
- Product direction standardized around a custom Bismark AI application rather than using a complete third-party RAG application as the core product.
- Initial infrastructure model standardized around:
  - Next.js on Vercel;
  - FastAPI on Hostinger KVM 2;
  - Supabase PostgreSQL;
  - Supabase Auth;
  - Supabase Storage;
  - pgvector;
  - Voyage AI embeddings;
  - Voyage AI reranking;
  - Redis;
  - Caddy;
  - Docker Compose;
  - external LLM provider.

## RAG

- Defined the initial retrieval architecture as:
  - structured document parsing;
  - structure-aware chunking;
  - Voyage embeddings;
  - pgvector semantic retrieval;
  - PostgreSQL full-text search;
  - hybrid candidate fusion;
  - Voyage reranking;
  - bounded evidence selection;
  - conversation-aware context construction;
  - source-grounded LLM generation;
  - validated citations.
- Established that only evidence actually supplied to the model may be cited.
- Established that previous assistant messages are conversation context, not authoritative organization knowledge.
- Established that retrieval must be tenant- and workspace-scoped before ranking.

## Database

- Defined the initial multi-tenant data model around:
  - profiles;
  - organizations;
  - organization_members;
  - workspaces;
  - workspace_members;
  - documents;
  - document_chunks;
  - conversations;
  - messages;
  - message_sources;
  - feedback;
  - usage_events;
  - audit_logs;
  - optional ingestion_jobs.
- Established pgvector as the V1 vector store.
- Established PostgreSQL full-text search for lexical retrieval.
- Defined processing-version strategy for safe re-indexing.
- Defined RLS as a defense-in-depth control.

## API

- Standardized API base path as `/api/v1`.
- Defined organization, workspace, document, conversation, chat, feedback, membership, health, and readiness routes.
- Defined a stable error response structure.
- Defined streamed chat as the preferred answer-delivery pattern.
- Defined source access using short-lived signed URLs.

## Security

- Established organization-level tenancy as the primary isolation boundary.
- Established workspace-level knowledge access boundaries.
- Prohibited unscoped global vector retrieval.
- Prohibited Supabase service-role credentials in browser-delivered code.
- Defined private Supabase Storage for organization documents.
- Established cross-tenant data exposure as a release-blocking defect.
- Added prompt-injection security requirements for user queries and uploaded documents.
- Added upload validation, parser-isolation, Docker, Redis, CORS, and secret-management requirements.

## Deployment

- Selected Hostinger KVM 2 as the initial backend VPS class.
- Selected Vercel for the Next.js frontend.
- Selected Caddy for TLS termination and reverse proxying.
- Selected Docker Compose for backend service orchestration.
- Established that production PostgreSQL and permanent source storage should remain outside the VPS.
- Defined initial VPS services as:
  - Caddy;
  - FastAPI;
  - worker;
  - Redis.
- Defined recovery strategy around external durable state in Supabase.

## Testing

- Defined tenant-isolation testing as a top-priority release gate.
- Defined RLS, authorization, ingestion, retrieval, reranking, citation, chat-streaming, provider-failure, frontend, E2E, security, and deployment smoke testing.
- Established RAG evaluation requirements for future retrieval changes.
- Established that agentic coding tools must not claim tests passed unless they were actually run.

---

# Release Entry Template

Copy this section when preparing a release.

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Security
- ...

### Database
- ...

### RAG
- ...

### Deployment
- ...

### Testing
- ...

### Migration Notes
- ...

### Breaking Changes
- None.
```

---

# Versioning Guidance

Bismark AI should generally follow semantic versioning principles.

```text
MAJOR.MINOR.PATCH
```

### Major

Use when there are incompatible API, architecture, or product contract changes.

Examples:

- incompatible API version replacement;
- major tenant-model change;
- major authentication replacement;
- incompatible data model change.

### Minor

Use for backward-compatible feature releases.

Examples:

- new workspace feature;
- new supported document type;
- new connector;
- new admin analytics.

### Patch

Use for backward-compatible fixes.

Examples:

- authorization bug fix;
- parser bug fix;
- retrieval tuning with no contract change;
- UI defect.

Pre-1.0 releases may use:

```text
0.x.y
```

while the product is still evolving rapidly.

---

# Breaking Change Rules

A breaking change must be called out explicitly.

Examples:

- endpoint removed;
- response field removed or renamed;
- database migration requires manual action;
- environment variable renamed without compatibility;
- vector dimension changed;
- authentication flow changed;
- role semantics changed.

Use:

```markdown
### Breaking Changes
- `OLD_VAR` replaced by `NEW_VAR`.
```

Do not hide breaking changes under generic `Changed`.

---

# Database Migration Notes

For releases containing database changes, record:

- migration identifier;
- whether migration is additive;
- whether downtime is required;
- whether reindexing is required;
- whether rollback is safe;
- whether backup is required.

Example:

```markdown
### Database
- Added `document_chunks.search_vector`.
- Added GIN index for full-text search.

### Migration Notes
- Run `alembic upgrade head` before deploying the new API image.
- No downtime expected.
```

---

# RAG Change Notes

RAG changes should mention the part of the pipeline affected.

Examples:

```markdown
### RAG
- Changed chunk target from 700 to 800 tokens.
- Added Reciprocal Rank Fusion for vector and keyword results.
- Updated Voyage reranker model.
```

Where applicable, include evaluation outcome:

```text
Recall@10: 0.81 -> 0.87
Citation precision: unchanged
Median retrieval latency: +23 ms
```

Do not state improvement without measured evidence when evaluation infrastructure exists.

---

# Security Change Notes

Security fixes must be explicit enough for operators to understand impact without revealing exploit details unnecessarily.

Example:

```markdown
### Security
- Fixed workspace authorization check on document source access.
- Added cross-tenant regression coverage.
```

If a secret was exposed:

```markdown
### Security
- Rotated affected provider credentials.
```

Do not commit actual secret values.

---

# Deployment Change Notes

Deployment changes should record operational consequences.

Examples:

```markdown
### Deployment
- Increased worker concurrency from 1 to 2.
- Upgraded Hostinger VPS from KVM 2 to KVM 4.
- Added Caddy request-size limits.
```

If manual operator action is required, include it.

---

# Documentation Change Policy

Documentation-only changes may be included when they materially change:

- architecture;
- operational procedure;
- security requirements;
- build order;
- API contract;
- migration rules.

Minor wording edits do not need changelog entries.

---

# Agentic AI Rules

Agentic coding systems must:

1. inspect `[Unreleased]` before making meaningful changes;
2. add a changelog entry for meaningful completed work;
3. avoid marking future/planned work as completed;
4. describe only verified implementation;
5. mention migrations when introduced;
6. mention security fixes explicitly;
7. mention breaking changes explicitly.

Agents must not write:

```text
Implemented complete RAG system
```

if only scaffolding was added.

Preferred:

```text
Added Voyage embedding provider interface and mocked unit tests.
```

---

# Changelog Quality Standard

Good entry:

```text
- Added workspace-scoped document upload with private Supabase Storage persistence.
```

Weak entry:

```text
- Updated backend.
```

Good entry:

```text
- Fixed cross-workspace retrieval by applying workspace filtering inside the pgvector query.
```

Weak entry:

```text
- Fixed security.
```

---

# Current Project Baseline

At the time this changelog was created, Bismark AI is in the planning and architecture-definition stage.

The intended V1 stack is:

```text
Frontend
Next.js
TypeScript
Tailwind
shadcn/ui
Vercel

Backend
FastAPI
Python
SQLAlchemy
Alembic
Hostinger KVM 2
Docker Compose

Data
Supabase PostgreSQL
Supabase Auth
Supabase Storage
pgvector
PostgreSQL full-text search

AI
Voyage embeddings
Voyage reranking
External LLM provider

Processing
Docling or Unstructured
Redis
background worker

Edge
Caddy
HTTPS
```

No implementation should be considered complete merely because it appears in planning documentation.

---

# Initial Planned Release Labels

These labels are suggestions and may change.

## 0.1.0 — Foundation

Expected:

- repository structure;
- frontend skeleton;
- backend skeleton;
- configuration;
- CI;
- documentation baseline.

## 0.2.0 — Identity and Tenancy

Expected:

- Supabase Auth;
- profiles;
- organizations;
- memberships;
- workspaces;
- authorization.

## 0.3.0 — Document Pipeline

Expected:

- uploads;
- storage;
- worker;
- parser;
- chunking.

## 0.4.0 — Retrieval

Expected:

- Voyage embeddings;
- pgvector;
- FTS;
- hybrid search;
- reranking.

## 0.5.0 — Chat

Expected:

- conversations;
- streaming;
- LLM integration;
- citations.

## 0.6.0 — Administration

Expected:

- member management;
- feedback;
- audit;
- usage.

## 0.7.0 — Production Hardening

Expected:

- security review;
- test automation;
- staging;
- backups;
- observability.

## 1.0.0 — Bismark AI V1

Expected:

A real organization can securely:

```text
sign up
→ create organization
→ create workspace
→ upload documents
→ process knowledge
→ ask questions
→ receive grounded answers
→ inspect citations
→ manage users/documents
```

with production security, deployment, and test requirements satisfied.

---

# Summary

`CHANGELOG.md` is the durable history of meaningful changes to Bismark AI.

It should answer:

```text
What changed?
Why does it matter operationally?
Did the database change?
Did the RAG pipeline change?
Did security change?
Does deployment require action?
Is anything breaking?
```

Keep it factual, concise, current, and tied to work that actually exists.
