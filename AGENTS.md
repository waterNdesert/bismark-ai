# AGENTS.md — Bismark AI Agent Operating Guide

**Project:** Bismark AI  
**Purpose:** Operating rules for AI coding agents and automated development assistants  
**Applies to:** Codex, Claude Code, Cursor, OpenHands, Copilot agents, autonomous coding tools, and similar systems  
**Status:** Canonical repository-level agent instructions  
**Version:** 1.0

---

## 1. Purpose of This File

This file defines how any agentic AI must work inside the Bismark AI repository.

It exists to ensure that coding agents:

- understand the product before modifying it;
- preserve the agreed architecture;
- do not invent conflicting infrastructure;
- work in small, reviewable increments;
- protect tenant isolation and security boundaries;
- test their changes;
- document significant decisions;
- keep the repository understandable for future humans and agents.

This file is not a product requirements document. Product intent is defined in `PRD.md`.

---

## 2. Documentation Authority

Agents must follow repository documentation in this priority order:

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

If two documents conflict:

- do not silently choose one;
- identify the conflict;
- prefer the higher-authority document;
- make the smallest safe change;
- update documentation if the implementation decision is intentionally changed.

Do not invent a new architecture because a different library, framework, or pattern is familiar to you.

---

## 3. Product Context

Bismark AI is a multi-tenant enterprise knowledge intelligence platform.

The initial product enables organizations to:

- create accounts and organizations;
- create workspaces;
- upload internal documents;
- process and index those documents;
- ask questions against authorized workspace knowledge;
- receive grounded AI answers;
- inspect citations and sources;
- preserve conversation history;
- manage documents and members;
- provide answer feedback.

The core product is trusted organizational knowledge access.

Do not turn Bismark AI into a generic chatbot, general autonomous agent framework, local model hosting platform, or unrelated automation system unless explicitly requested.

---

## 4. Locked Initial Architecture

Unless a documented architecture decision changes this, agents must preserve the following initial architecture.

### Frontend

- Next.js
- TypeScript
- React
- Tailwind CSS
- shadcn/ui
- deployed on Vercel

### Backend

- FastAPI
- Python
- Pydantic
- SQLAlchemy
- Alembic
- deployed on Hostinger VPS
- Docker-based deployment

### Data Platform

Supabase provides:

- PostgreSQL
- Supabase Auth
- Supabase Storage
- pgvector

### AI Retrieval

Voyage AI provides:

- embeddings
- reranking

### RAG

The initial RAG design uses:

- structured document parsing
- semantic or structure-aware chunking
- PostgreSQL full-text search
- pgvector semantic retrieval
- hybrid candidate fusion
- metadata and permission filtering
- Voyage reranking
- context construction
- LLM answer generation
- citations tied to actual supplied evidence

### Infrastructure

Hostinger VPS runs:

- FastAPI
- background worker
- Redis
- document parser dependencies
- Caddy

It must not initially host:

- production PostgreSQL
- permanent source document storage
- local LLM inference
- a separate vector database
- unnecessary duplicated SaaS services

### Deployment Boundary

- Next.js: Vercel
- FastAPI: Hostinger VPS
- PostgreSQL/Auth/Storage/pgvector: Supabase
- embeddings/reranking: Voyage
- generation: external LLM provider
- HTTPS/reverse proxy: Caddy

---

## 5. Architecture Philosophy

Bismark AI should begin as a modular monolith.

Agents must not split the project into microservices unless there is a documented and approved reason.

Prefer:

```text
one frontend
one backend application
one worker process
one Redis instance
one PostgreSQL database
```

over:

```text
many independently deployed services
multiple message brokers
multiple vector stores
multiple databases
premature distributed architecture
```

Complexity must be introduced only in response to a concrete requirement or measured bottleneck.

---

## 6. Repository Structure

The target repository structure is:

```text
bismark-ai/
├── apps/
│   ├── web/
│   └── api/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── API.md
│   ├── RAG.md
│   ├── SECURITY.md
│   ├── DEPLOYMENT.md
│   ├── TESTING.md
│   └── decisions/
├── infra/
│   ├── docker/
│   └── caddy/
├── scripts/
├── AGENTS.md
├── PRD.md
├── PROJECT_STATE.md
├── ROADMAP.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── docker-compose.yml
├── .env.example
└── .gitignore
```

Agents must preserve a clear separation between:

- product code;
- infrastructure;
- documentation;
- scripts;
- generated artifacts.

Do not place operational scripts randomly inside application modules.

---

## 7. Before Making Changes

Before modifying code, every agent must:

1. read `PRD.md`;
2. read this file;
3. inspect `PROJECT_STATE.md` if it exists;
4. inspect the relevant technical document for the task;
5. inspect related code before changing it;
6. inspect relevant tests;
7. identify affected boundaries;
8. state or record any assumptions that are not already documented.

If a referenced document does not yet exist, do not invent its contents. Work only from currently authoritative material.

---

## 8. Change Scope

Agents should make the smallest complete change that satisfies the current task.

Do not:

- refactor unrelated areas;
- rename broad sections of the codebase without need;
- introduce unrelated dependencies;
- rewrite working components merely for style preference;
- migrate frameworks without explicit instruction;
- change database models casually;
- alter deployment topology during feature work;
- add speculative features.

A task should remain reviewable.

---

## 9. No Silent Architectural Changes

The following require an Architecture Decision Record before implementation:

- replacing Supabase;
- replacing PostgreSQL;
- replacing pgvector;
- adding another vector database;
- replacing Voyage;
- introducing a model gateway;
- introducing a knowledge graph;
- introducing microservices;
- adding a second backend framework;
- changing the authentication provider;
- moving FastAPI off the VPS;
- moving the frontend off Vercel;
- adding local LLM inference;
- replacing Caddy;
- changing document storage strategy;
- changing multi-tenancy strategy;
- changing the canonical API versioning approach.

If explicitly instructed to make such a change, create or update the appropriate ADR as part of the task.

---

## 10. Security Is a Product Requirement

Security constraints are not optional implementation details.

Every protected feature must preserve:

- authenticated identity;
- organization boundary;
- workspace boundary;
- role or permission checks;
- database scoping;
- retrieval scoping;
- storage access controls.

A feature is incomplete if it works functionally but bypasses authorization.

---

## 11. Multi-Tenancy Rules

Bismark AI is multi-tenant from the beginning.

Agents must assume that:

- organizations are tenant boundaries;
- workspaces are knowledge-access boundaries inside an organization;
- documents belong to workspaces;
- conversations belong to users and workspaces;
- retrieval must always be scoped to authorized knowledge.

Never write retrieval code that searches the global `document_chunks` corpus and filters afterward in application memory.

Tenant and workspace filters must be applied during the database retrieval query.

Never trust IDs received from the client without validating access.

---

## 12. Authentication Rules

Supabase Auth is the initial identity provider.

Agents must:

- validate authenticated user identity on the backend;
- never trust a frontend-supplied user ID as authoritative;
- never expose the Supabase service-role key in browser code;
- never commit tokens or private keys;
- use secure session/token handling;
- enforce authorization independently of frontend visibility.

A hidden button is not an authorization control.

---

## 13. Supabase Rules

### PostgreSQL

Use migrations for schema changes.

Do not make undocumented manual production schema edits.

### Auth

Application users must map cleanly to application profile records where required.

### Storage

Original uploaded documents should be stored in Supabase Storage, not permanently on the VPS filesystem.

### pgvector

The embedding dimension must match the configured Voyage embedding model.

Do not hard-code dimensions in multiple unrelated locations.

### RLS

Where RLS is enabled:

- policies must be documented;
- service-role usage must be deliberate;
- backend authorization must still exist where appropriate;
- policies must be tested.

---

## 14. Database Change Rules

Every database schema change must include:

- a migration;
- model updates;
- validation/schema updates;
- relevant indexes;
- updated tests;
- documentation updates if the canonical model changes.

Do not modify production tables manually.

Do not create duplicate columns that represent the same concept under different names.

Prefer UUIDs for externally exposed entity identifiers unless documented otherwise.

Use timestamps consistently.

---

## 15. API Rules

The backend API must use a versioned base path:

```text
/api/v1
```

Agents must preserve:

- predictable resource naming;
- explicit request schemas;
- explicit response schemas;
- consistent error format;
- authentication requirements;
- authorization checks;
- pagination where collections can grow;
- idempotency where relevant;
- structured logs.

Do not make the frontend depend on undocumented response shapes.

If an endpoint contract changes, update `docs/API.md`.

---

## 16. Backend Module Boundaries

The expected FastAPI domain structure is approximately:

```text
app/
├── main.py
├── core/
├── auth/
├── users/
├── organizations/
├── workspaces/
├── documents/
├── ingestion/
├── retrieval/
├── chat/
├── conversations/
├── feedback/
├── audit/
├── providers/
│   ├── embeddings/
│   ├── reranking/
│   ├── llm/
│   └── storage/
└── db/
```

Agents should preserve domain ownership.

Examples:

- document upload logic belongs under documents/ingestion;
- Voyage integration belongs behind provider interfaces;
- raw Supabase implementation details should not leak throughout the domain layer;
- chat orchestration should not contain database migration code;
- authorization should not be reimplemented differently in every endpoint.

---

## 17. Provider Abstraction Rules

External providers must be accessed through application-owned interfaces.

This applies to:

- embeddings;
- reranking;
- LLM generation;
- object storage;
- document parsing.

Business logic must not depend directly on a provider SDK throughout the codebase.

Preferred pattern:

```text
domain/service
    ↓
provider interface
    ↓
Voyage/OpenAI/Supabase/etc.
```

This allows future provider replacement without rewriting the application.

---

## 18. RAG Rules

The RAG pipeline is a core product capability.

Agents must not reduce the retrieval system to:

```text
query
→ vector search
→ top 5
→ LLM
```

The intended V1 pipeline is:

```text
query
→ permission scope
→ query preparation
→ vector retrieval
→ keyword retrieval
→ candidate fusion
→ metadata filtering
→ Voyage reranking
→ evidence selection
→ context construction
→ generation
→ citations
```

Any simplification must be deliberate, documented, and justified.

---

## 19. Document Ingestion Rules

Long-running document processing must not happen inside the upload request lifecycle.

Required pattern:

```text
upload
→ validate
→ store original
→ create document record
→ enqueue processing
→ return response
```

Worker:

```text
job
→ fetch source
→ parse
→ chunk
→ embed
→ index
→ mark ready
```

Document states should be explicit and persisted.

Errors must be observable and retryable.

---

## 20. Parsing Rules

The initial parser may use Docling or Unstructured.

Parsing should preserve structure where available:

- title;
- headings;
- paragraphs;
- page numbers;
- lists;
- tables;
- metadata.

Do not flatten rich documents into arbitrary character windows if structured information is available.

---

## 21. Chunking Rules

Avoid naive fixed-size character splitting as the only chunking strategy.

Prefer:

- section-aware boundaries;
- paragraph boundaries;
- heading context;
- token-aware size limits;
- controlled overlap when justified.

Every chunk must retain traceability to:

- organization;
- workspace;
- document;
- page when available;
- section/heading when available;
- chunk index.

---

## 22. Embedding Rules

Voyage is the initial embedding provider.

Agents must:

- make model names configurable;
- keep embedding dimension configuration centralized;
- batch embedding requests where appropriate;
- handle provider timeouts;
- handle rate limits;
- implement bounded retries;
- avoid re-embedding unchanged content unnecessarily.

Embedding version/model metadata should be stored when required for migration or reindexing.

---

## 23. Hybrid Search Rules

The retrieval layer should combine:

- pgvector semantic search;
- PostgreSQL full-text/keyword search.

Agents should preserve the ability to support:

- exact names;
- policy IDs;
- technical strings;
- abbreviations;
- dates;
- semantic concepts.

Candidate fusion logic must be testable.

---

## 24. Reranking Rules

Voyage reranking should occur after initial candidate retrieval.

Do not send the entire knowledge base to the reranker.

Typical flow:

```text
retrieve 20–40 candidates
→ rerank
→ retain best evidence
```

Exact values should remain configurable.

---

## 25. Citation Rules

Citations must refer only to evidence actually supplied to the generation model.

Do not:

- generate citations from unused retrieval results;
- fabricate page numbers;
- cite documents that were not part of the final context;
- allow the model to invent source identifiers.

The application should preserve source metadata independently of generated prose.

---

## 26. Conversation Context Rules

Conversation context and retrieved organizational knowledge are different concepts.

Agents must preserve that separation.

Follow-up understanding may use:

- recent messages;
- future conversation summaries.

Organizational factual claims should still be grounded in retrieved authorized sources.

Do not allow prior assistant messages to become unquestioned factual authority.

---

## 27. Frontend Rules

Frontend code should be:

- TypeScript-first;
- accessible;
- responsive;
- componentized;
- clear about loading/error/empty states;
- consistent with the existing design system.

Prefer server-side data loading where appropriate, but do not create unnecessary complexity.

Do not store security-sensitive authorization decisions only in client state.

---

## 28. UI Behavior Requirements

User-facing asynchronous actions must expose state.

Examples:

### Document ingestion

```text
Uploaded
Queued
Processing
Ready
Failed
```

### Chat

```text
Sending
Retrieving
Generating
Completed
Failed
```

The exact UI representation may differ, but users should not be left guessing whether a long-running process is active or broken.

---

## 29. Streaming Rules

Chat responses should stream.

The frontend must handle:

- partial output;
- completion;
- cancellation;
- network interruption;
- API failure;
- retriable errors.

Do not duplicate assistant messages when retrying failed requests.

---

## 30. Background Job Rules

The initial background-processing stack is:

- Redis;
- one worker process;
- a lightweight Python job framework.

Agents should not add Kafka, RabbitMQ, NATS, or other infrastructure without a documented need.

Jobs must have:

- durable status in PostgreSQL where product state depends on them;
- bounded retries;
- error logging;
- idempotent behavior where practical.

---

## 31. Error Handling

Do not expose raw stack traces to users.

Application errors should:

- be structured;
- carry request IDs where available;
- distinguish validation, authorization, not-found, conflict, provider, and internal errors;
- log diagnostic details server-side.

Provider failures should not silently corrupt application state.

---

## 32. Logging

Use structured logging.

Logs should include useful context such as:

- request ID;
- user ID where appropriate;
- organization ID;
- workspace ID;
- document ID;
- job ID;
- provider;
- latency;
- error class.

Do not log:

- passwords;
- auth tokens;
- service-role keys;
- full private documents by default;
- raw secrets.

---

## 33. Secrets

Secrets must come from environment configuration or a secret-management system.

Never commit:

- API keys;
- JWT signing secrets;
- service-role keys;
- database passwords;
- cloud credentials;
- private certificates.

`.env.example` must contain placeholders only.

---

## 34. Testing Expectations

Every meaningful change should include appropriate tests.

Agents must consider:

- unit tests;
- API integration tests;
- authorization tests;
- tenant-isolation tests;
- storage tests;
- ingestion tests;
- retrieval tests;
- RAG evaluation tests;
- frontend tests;
- end-to-end tests.

Security-sensitive code requires negative tests, not just happy-path tests.

Example:

It is not enough to test that a user can read their workspace.

Also test that they cannot read:

- another workspace;
- another organization;
- documents they do not have access to.

---

## 35. Tenant Isolation Is a Release Blocker

Any confirmed cross-tenant data exposure is a release-blocking defect.

Agents must treat the following as critical:

- cross-tenant document access;
- cross-tenant retrieval;
- cross-tenant conversation access;
- cross-tenant storage access;
- cross-tenant administration.

Never defer these as minor bugs.

---

## 36. Code Quality Rules

Prefer:

- clear names;
- typed functions;
- small modules;
- explicit interfaces;
- dependency injection where useful;
- straightforward control flow;
- documented non-obvious behavior.

Avoid:

- giant utility files;
- deeply nested abstractions without value;
- duplicated authorization logic;
- magic constants;
- undocumented side effects;
- provider-specific logic spread across the codebase.

---

## 37. Dependency Rules

Before adding a dependency, determine:

1. whether the project already has equivalent functionality;
2. whether standard library/framework capabilities are sufficient;
3. whether the dependency is actively maintained;
4. whether it materially reduces implementation risk or effort;
5. whether it introduces major transitive complexity.

Do not add libraries merely because they are popular.

Record significant infrastructure dependencies in documentation.

---

## 38. Configuration Rules

Environment-specific settings must be configurable.

Do not hard-code:

- production domains;
- Supabase URLs;
- model names;
- storage bucket names;
- CORS origins;
- database URLs;
- API keys;
- retrieval candidate counts;
- reranking counts.

Configuration should be validated at application startup.

---

## 39. Migration Rules

Database migrations must be:

- deterministic;
- committed;
- reversible where practical;
- safe for existing data;
- reviewed for indexes and constraints.

Do not rewrite old production-applied migrations.

Create a new migration.

---

## 40. Performance Rules

Do not optimize blindly.

Use measurement.

Potential bottlenecks include:

- document parsing;
- embedding API calls;
- database retrieval;
- reranking;
- LLM latency;
- frontend waterfall requests.

Use batching and concurrency carefully, especially around external provider rate limits.

---

## 41. File Storage Rules

Original uploaded files belong in Supabase Storage.

The VPS filesystem is temporary processing space only unless documentation explicitly defines otherwise.

Processing workflow should clean temporary files after completion or failure.

Do not assume the VPS filesystem is durable application storage.

---

## 42. Docker Rules

Production backend components should be containerized.

Containers should:

- run as non-root where practical;
- use minimal images;
- expose only required ports;
- include health checks where appropriate;
- avoid baking secrets into images;
- use pinned or controlled versions;
- write persistent state only to intentional volumes.

Do not publish Redis directly to the public internet.

---

## 43. Caddy Rules

Caddy is the initial reverse proxy and TLS termination layer.

It should:

- terminate HTTPS;
- proxy only required backend routes;
- use secure defaults;
- avoid exposing internal container ports publicly.

Do not replace Caddy with Nginx, Traefik, or another proxy without an explicit architecture decision.

---

## 44. Vercel Rules

Vercel is the initial frontend deployment platform.

Agents should:

- keep server/client boundaries clear;
- avoid leaking private backend secrets into `NEXT_PUBLIC_*`;
- use environment-specific configuration;
- preserve preview deployment compatibility.

---

## 45. Git and Commit Behavior

When operating with repository write access, agents should:

- keep commits scoped;
- avoid combining unrelated changes;
- use descriptive commit messages;
- avoid rewriting shared history unless explicitly instructed;
- not force-push without explicit approval.

Recommended commit style:

```text
feat(chat): add streamed workspace responses
fix(auth): enforce workspace membership
docs(rag): document hybrid retrieval pipeline
test(security): add cross-tenant document checks
```

---

## 46. Documentation Update Rules

Documentation is part of the product.

When a change affects:

- architecture;
- schema;
- API;
- retrieval;
- security;
- deployment;
- testing;
- roadmap;

update the corresponding document in the same change.

Do not leave major behavior changes documented only in code comments.

---

## 47. PROJECT_STATE.md

Once created, `PROJECT_STATE.md` is the short operational memory of the repository.

Agents should update it after substantial tasks.

It should contain:

- current milestone;
- completed work;
- current implementation state;
- migrations applied;
- tests passing/failing;
- deployment state;
- known issues;
- blockers;
- next recommended task.

Do not use `PROJECT_STATE.md` to redefine architecture.

It records current state, not canonical product requirements.

---

## 48. CHANGELOG.md

Significant user-visible or operational changes should be recorded.

Do not add trivial formatting changes.

Record:

- features;
- fixes;
- security changes;
- migrations;
- breaking changes;
- deployment-impacting changes.

---

## 49. Architecture Decision Records

Store ADRs under:

```text
docs/decisions/
```

Suggested format:

```text
ADR-001-use-supabase.md
ADR-002-use-voyage.md
ADR-003-use-hostinger-kvm2.md
```

Each ADR should include:

- status;
- context;
- decision;
- alternatives considered;
- consequences;
- date.

Use ADRs for durable architectural decisions, not ordinary implementation details.

---

## 50. Agent Work Protocol

For each implementation task, follow this sequence.

### Step 1 — Understand

Read relevant documentation and code.

### Step 2 — Plan

Identify:

- files to change;
- data model impact;
- API impact;
- security impact;
- migration impact;
- test impact.

### Step 3 — Implement

Make the smallest complete change.

### Step 4 — Test

Run the relevant test suite and static checks.

### Step 5 — Verify

Confirm:

- authorization;
- tenant scoping;
- errors;
- configuration;
- documentation.

### Step 6 — Document

Update any canonical docs affected.

### Step 7 — Report

Summarize:

- what changed;
- tests run;
- unresolved issues;
- follow-up work.

---

## 51. When to Stop and Ask

An agent should stop and request clarification rather than guess when:

- a change contradicts the PRD;
- a security requirement is ambiguous;
- tenant behavior is unclear;
- a schema change would destroy or reinterpret existing data;
- a requested change requires a major architecture replacement;
- external provider behavior is undocumented;
- required secrets or credentials are missing;
- the task could materially change costs or infrastructure;
- production data could be deleted.

Do not proceed destructively based on assumptions.

---

## 52. Destructive Operations

Agents must never perform destructive production actions without explicit authorization.

Examples:

- dropping tables;
- deleting production buckets;
- deleting organizations;
- wiping vector data;
- resetting production databases;
- replacing production storage;
- rotating live credentials;
- deleting VPS volumes.

For development-only data, destructive actions must still be clearly identified.

---

## 53. Generated Code

Generated code is not exempt from quality requirements.

Agents must inspect generated code for:

- correctness;
- security;
- duplicate logic;
- architecture violations;
- dead code;
- unnecessary dependencies;
- missing tests.

Do not commit a large generated scaffold merely because it compiles.

---

## 54. Mocking External Providers

Tests should not depend unnecessarily on live provider APIs.

Provide abstractions that allow:

- fake embedding provider;
- fake reranker;
- fake LLM;
- fake storage where appropriate.

Integration tests against real providers may exist separately.

Never make every unit test require Voyage or an LLM API key.

---

## 55. RAG Evaluation Discipline

Do not claim a retrieval change is better based only on intuition.

When evaluation infrastructure exists, compare:

- retrieval recall;
- evidence relevance;
- reranking quality;
- answer groundedness;
- citation correctness;
- latency;
- cost.

Retain representative evaluation questions.

Do not train or tune retrieval behavior directly against private test answers in ways that invalidate the evaluation set.

---

## 56. Initial Non-Goals for Agents

Until the roadmap explicitly reaches them, do not introduce:

- local LLM hosting;
- fine-tuning;
- autonomous multi-agent systems;
- knowledge graphs;
- browser automation;
- voice AI;
- mobile apps;
- SAML;
- SCIM;
- complex billing;
- dozens of connectors;
- Kubernetes;
- Kafka;
- separate vector databases;
- unnecessary microservices.

These are future capabilities, not V1 prerequisites.

---

## 57. Preferred Development Order

Unless the roadmap says otherwise, agents should generally build in this order:

1. repository foundation;
2. configuration and local development;
3. Supabase connection;
4. authentication;
5. organizations;
6. workspaces;
7. authorization;
8. document metadata;
9. file upload/storage;
10. background processing;
11. parsing;
12. chunking;
13. embeddings;
14. vector indexing;
15. keyword retrieval;
16. hybrid search;
17. reranking;
18. chat;
19. citations;
20. conversation history;
21. feedback;
22. administration;
23. security hardening;
24. deployment;
25. evaluation.

Do not build advanced AI behavior before secure knowledge ingestion and retrieval work correctly.

---

## 58. Definition of a Complete Agent Task

A coding task is not complete merely because code was written.

It is complete when applicable items are satisfied:

- implementation works;
- type checks pass;
- lint passes;
- tests pass;
- migrations exist;
- authorization is enforced;
- tenant isolation is preserved;
- failure states are handled;
- docs are updated;
- no secrets are committed;
- no unrelated changes are included.

---

## 59. Communication Style for Agents

When reporting work:

Be precise.

Prefer:

```text
Implemented:
- workspace-scoped document upload
- Supabase Storage persistence
- document status transitions

Tests:
- 18 passed
- cross-tenant upload denied
- invalid MIME type rejected

Not implemented:
- ingestion worker
- embeddings
```

Avoid vague statements such as:

```text
Everything is done.
The backend is complete.
Security is handled.
```

unless that claim is actually verified.

---

## 60. Source of Truth

The repository itself must become the durable source of truth for Bismark AI.

Agents must not rely on:

- prior chat history;
- personal memory;
- undocumented assumptions;
- temporary prompts;

when repository documentation and implementation provide the necessary context.

If an important decision exists only in conversation, it should be written into the appropriate repository document before depending on it long term.

---

## 61. Current Project Direction

At the time of this document's creation, the intended Bismark AI V1 stack is:

```text
Frontend:
Next.js + TypeScript + Tailwind + shadcn/ui
Hosted on Vercel

Backend:
FastAPI + Python + SQLAlchemy + Alembic
Hosted on Hostinger KVM 2
Docker Compose

Database:
Supabase PostgreSQL

Authentication:
Supabase Auth

Storage:
Supabase Storage

Vector Search:
Supabase pgvector

Keyword Search:
PostgreSQL full-text search

Embeddings:
Voyage AI

Reranking:
Voyage AI

Document Parsing:
Docling or Unstructured

Background Jobs:
Redis + Python worker

LLM:
External provider behind internal abstraction

Reverse Proxy:
Caddy
```

This direction should remain stable unless deliberately changed through documentation and an architecture decision.

---

## 62. Final Rule

Optimize for a Bismark AI codebase that another capable engineer or coding agent can understand, test, operate, and extend without needing the original author present.

Every architectural shortcut, hidden dependency, undocumented assumption, and security bypass makes that goal harder.

Prefer clarity, explicit boundaries, measured complexity, and safe incremental progress.
