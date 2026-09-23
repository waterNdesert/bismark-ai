# ADR-006 — Use FastAPI as the Bismark AI Backend Application Framework

**Project:** Bismark AI  
**ADR ID:** ADR-006  
**Title:** Use FastAPI for the Primary Backend Application Layer  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 backend architecture

---

## 1. Context

Bismark AI requires a backend framework capable of supporting:

- authenticated REST APIs;
- organization and workspace authorization;
- document upload orchestration;
- asynchronous job creation;
- retrieval orchestration;
- streamed chat responses;
- provider integrations;
- typed request and response models;
- OpenAPI documentation;
- database access;
- structured error handling;
- security middleware;
- testing.

The broader V1 stack already uses:

```text
Python
Supabase PostgreSQL
SQLAlchemy
Alembic
Redis
Voyage AI
external LLM provider
```

The backend must remain simple enough for rapid development while still supporting strong architecture and security.

Several backend approaches were considered:

1. FastAPI;
2. Django/Django REST Framework;
3. Flask;
4. Node.js/NestJS;
5. serverless backend functions;
6. a third-party AI application backend.

---

## 2. Decision

Bismark AI V1 will use **FastAPI** as the primary backend application framework.

The backend will be written in Python and use:

```text
FastAPI
Pydantic
SQLAlchemy
Alembic
```

FastAPI will own:

- HTTP API;
- authentication verification;
- authorization;
- tenant scoping;
- organization/workspace business logic;
- document lifecycle orchestration;
- retrieval orchestration;
- chat orchestration;
- streaming;
- audit and usage events;
- provider abstraction coordination.

---

## 3. Why FastAPI

### 3.1 Strong Python Fit

Bismark AI's AI/RAG pipeline is naturally Python-oriented.

The project requires:

- document parsing;
- embeddings;
- reranking;
- LLM integration;
- worker logic;
- retrieval evaluation.

Using Python for the backend reduces language fragmentation.

---

### 3.2 Typed Request and Response Models

FastAPI integrates tightly with Pydantic.

This supports:

- explicit request schemas;
- explicit response schemas;
- validation;
- generated OpenAPI;
- predictable API contracts.

This is important for both frontend development and agentic coding systems.

---

### 3.3 Async Support

Bismark AI performs many network-bound operations:

- Supabase;
- Voyage;
- LLM providers;
- Redis;
- streaming.

FastAPI's async capabilities fit these workloads.

---

### 3.4 Streaming Support

The product requires streamed AI responses.

FastAPI can support:

- Server-Sent Events;
- streaming HTTP responses;
- long-lived generation responses.

This fits the V1 chat design.

---

### 3.5 OpenAPI

FastAPI generates OpenAPI automatically.

This enables:

- API documentation;
- client generation;
- schema validation;
- contract testing.

The generated API should remain consistent with `docs/API.md`.

---

### 3.6 Lightweight Application Layer

FastAPI provides less framework overhead than a full batteries-included framework while still giving enough structure for a modular monolith.

This aligns with the V1 architecture.

---

## 4. Architectural Role

FastAPI is the central trusted application control plane.

Conceptually:

```text
Next.js
   |
   v
FastAPI
   |
   +--> PostgreSQL
   +--> Supabase Storage
   +--> Redis
   +--> Voyage
   +--> LLM Provider
```

FastAPI is where business and authorization logic live.

---

## 5. Responsibilities

FastAPI is responsible for:

- authenticating requests;
- resolving application user;
- authorizing organization membership;
- authorizing workspace access;
- enforcing roles;
- validating request input;
- exposing versioned REST APIs;
- creating document records;
- coordinating uploads;
- enqueueing ingestion jobs;
- orchestrating retrieval;
- orchestrating reranking;
- constructing chat context;
- invoking LLM provider;
- streaming responses;
- persisting messages and citations;
- recording audit/usage events;
- normalizing errors.

---

## 6. Responsibilities FastAPI Must Not Own

FastAPI should not directly become responsible for:

- permanent object storage;
- running long document parsing inside request handlers;
- local model inference;
- direct frontend rendering;
- Redis persistence as product state;
- manually managing raw passwords.

---

## 7. Versioned API

Public API paths must use:

```text
/api/v1
```

This provides a stable contract boundary between frontend and backend.

---

## 8. Recommended Backend Structure

Canonical structure:

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
├── usage/
├── providers/
└── db/
```

This structure should preserve domain ownership.

---

## 9. Route Design

Routes should remain thin.

Preferred:

```text
route
→ service
→ repository/provider
```

Avoid implementing full business logic directly in endpoint functions.

---

## 10. Authentication

FastAPI must validate Supabase Auth access tokens.

The backend should derive the user identity from the verified token.

It must not trust:

```text
user_id from request body
```

as proof of identity.

---

## 11. Authorization

FastAPI is the primary application authorization layer.

It must enforce:

```text
organization membership
workspace membership
role
resource ownership
```

RLS remains defense in depth.

---

## 12. Dependency Injection

FastAPI dependencies should be used for reusable request-level concerns such as:

```text
current_user
organization_access
workspace_access
request_id
database_session
```

This reduces duplicated authorization logic.

---

## 13. Database Access

Use SQLAlchemy for application database access.

Alembic owns schema migrations.

Avoid direct SQL scattered throughout controllers.

Specialized SQL is acceptable for:

- pgvector;
- FTS;
- tenant-safe retrieval functions;
- advanced indexes.

Such SQL should remain encapsulated and tested.

---

## 14. Request Validation

Use Pydantic request models.

Validate:

- strings;
- enums;
- pagination;
- IDs;
- field lengths;
- supported state transitions.

Do not rely on frontend validation.

---

## 15. Response Models

Public routes should use explicit response models.

Benefits:

- stable contracts;
- accidental field leakage prevention;
- OpenAPI quality;
- frontend typing.

---

## 16. Error Handling

Use centralized application errors.

Conceptual hierarchy:

```text
ApplicationError
├── AuthenticationError
├── AuthorizationError
├── NotFoundError
├── ConflictError
├── ValidationError
├── ProviderError
└── InternalError
```

Map these to the stable API format defined in `API.md`.

---

## 17. Exception Safety

Do not expose raw Python exceptions or stack traces to production clients.

Log internal details with request ID.

---

## 18. Middleware

Potential middleware includes:

- request ID;
- structured logging;
- CORS;
- rate limiting;
- trusted proxy handling;
- security headers where appropriate.

Do not add middleware without understanding ordering and performance effects.

---

## 19. CORS

Production should allow only approved frontend origins.

Example:

```text
https://app.bismark.ai
```

Wildcard CORS is not acceptable for authenticated production traffic.

---

## 20. Streaming

Preferred V1 answer delivery:

```text
SSE
```

or another documented streaming HTTP pattern.

FastAPI should proxy LLM token/event output to the browser while maintaining:

- persistence;
- error state;
- source mapping.

---

## 21. Long-Running Work

Long-running ingestion must not happen inside the upload request handler.

Required:

```text
FastAPI
→ Redis queue
→ background worker
```

The API should return:

```text
202 Accepted
```

where appropriate.

---

## 22. Background Worker Relationship

The worker may reuse backend domain modules.

However, it should run as a separate process/container.

Shared code may include:

- database;
- providers;
- parsing;
- chunking;
- ingestion services.

---

## 23. Redis

FastAPI may enqueue jobs to Redis.

Redis is not authoritative application state.

Durable processing state belongs in PostgreSQL.

---

## 24. Provider Abstractions

FastAPI domain services should depend on:

```text
EmbeddingProvider
RerankProvider
LLMProvider
StorageProvider
DocumentParser
JobQueue
```

not directly on provider SDKs throughout the application.

---

## 25. Voyage Integration

Voyage SDK/API usage should remain inside provider modules.

Do not import it into route files.

---

## 26. LLM Integration

The LLM provider must be abstracted.

This makes it possible to change:

- provider;
- model;
- endpoint;

without rewriting chat orchestration.

---

## 27. Storage Integration

Supabase Storage usage should sit behind a storage abstraction where practical.

FastAPI controls authorization before source access.

---

## 28. Health Endpoints

FastAPI should expose:

```text
GET /health
GET /ready
```

`/health`:

- liveness.

`/ready`:

- readiness of critical dependencies.

---

## 29. OpenAPI

Development/staging may expose:

```text
/docs
/redoc
/openapi.json
```

Production exposure may be restricted if desired.

---

## 30. Testing

FastAPI is well suited to:

- unit testing;
- route testing;
- dependency overrides;
- integration tests.

Security-sensitive dependencies should be directly testable.

---

## 31. Performance

The expected workload is mainly:

- API orchestration;
- network I/O;
- database I/O;
- streaming.

This fits FastAPI well.

CPU-heavy document parsing remains in worker processes.

---

## 32. Concurrency

Async should be used for I/O-bound operations.

CPU-bound parsing should not block the event loop.

Use worker/job processes for heavy computation.

---

## 33. Process Model

Initial production may use:

```text
1 API container
```

with one or more worker processes depending on measured load.

Do not overprovision process count relative to 2 vCPU.

---

## 34. Observability

FastAPI should emit structured logs.

Capture:

```text
request_id
method
path
status
latency
user_id
organization_id
workspace_id
```

where safe.

---

## 35. Security

Security-sensitive code must not be implemented as optional middleware alone.

Endpoint/domain authorization remains explicit.

---

## 36. Alternative Considered — Django + DRF

### Benefits

- mature ecosystem;
- strong ORM;
- built-in admin;
- established authentication patterns.

### Drawbacks

- heavier framework;
- less natural fit for the desired lightweight modular architecture;
- Bismark AI does not require Django admin or template stack;
- additional abstraction beyond current needs.

### Decision

Not selected for V1.

---

## 37. Alternative Considered — Flask

### Benefits

- lightweight;
- mature;
- flexible.

### Drawbacks

- more manual work for typed APIs;
- validation/OpenAPI less integrated;
- more conventions must be assembled separately.

### Decision

Not selected.

FastAPI provides better defaults for the desired API-first architecture.

---

## 38. Alternative Considered — NestJS

### Benefits

- strong architecture patterns;
- TypeScript;
- dependency injection.

### Drawbacks

- splits AI/backend work across JavaScript/TypeScript and Python;
- Python remains needed for parser/RAG worker stack;
- increases language/runtime complexity.

### Decision

Not selected for V1.

---

## 39. Alternative Considered — Serverless Functions

### Benefits

- auto-scaling;
- managed infrastructure.

### Drawbacks

- document parsing may exceed function constraints;
- streaming and long-running work can become awkward;
- worker/Redis architecture fits a persistent backend better.

### Decision

Not selected as the primary backend runtime.

---

## 40. Alternative Considered — Third-Party AI Backend

### Benefits

- faster prototype;
- prebuilt RAG behavior.

### Drawbacks

- poor ownership of tenancy;
- limited architecture control;
- product differentiation risk;
- difficult long-term customization.

### Decision

Rejected as the core Bismark AI backend.

---

## 41. Dependency Policy

FastAPI-related dependencies should remain focused.

Avoid adding multiple competing libraries for:

- validation;
- ORM;
- DI;
- HTTP clients;
- background jobs.

---

## 42. HTTP Client

Use one preferred async HTTP client for external providers where SDKs are not used.

Avoid many different HTTP libraries.

---

## 43. Configuration

Use a typed settings system.

Configuration should fail at startup when required values are missing.

Do not let production fail later due to silently absent critical config.

---

## 44. Environment-Specific Behavior

Production-specific behavior should come from configuration.

Avoid:

```python
if hostname == ...
```

style environment detection.

---

## 45. Security Boundaries

FastAPI must not:

- expose service-role key;
- log authorization headers;
- return raw provider secrets;
- accept arbitrary organization IDs without membership validation;
- trust frontend role flags.

---

## 46. API Contract Stability

Frontend should consume stable documented response models.

If a response changes materially:

- update `API.md`;
- update frontend types;
- add tests;
- update changelog.

---

## 47. Future Service Extraction

If a future domain needs independent scaling, it may be extracted.

Potential candidates:

- ingestion workers;
- connector ingestion;
- analytics.

Do not extract services preemptively.

---

## 48. Modular Monolith Relationship

This ADR should be read with the modular-monolith decision.

FastAPI is the framework.

The modular monolith defines how the application is structured inside it.

---

## 49. Deployment

FastAPI runs in Docker on Hostinger.

Public traffic flows:

```text
Internet
→ Caddy
→ FastAPI
```

FastAPI should not publish its internal port directly to the public internet.

---

## 50. Rollback

Application images should be versioned.

Rollback should not require framework-specific state beyond:

- compatible database schema;
- environment variables;
- image version.

---

## 51. Provider Failure Handling

FastAPI must normalize failures from:

- Supabase;
- Voyage;
- LLM provider;
- Redis.

Do not leak raw vendor response payloads to clients.

---

## 52. Rate Limiting

FastAPI should enforce rate limits on:

- chat;
- upload;
- retries;
- invitations.

Implementation may use middleware or service-level controls.

---

## 53. Idempotency

Where duplicate client retries are dangerous, support idempotent behavior.

Examples:

- organization creation;
- document submission;
- chat submission.

---

## 54. File Upload

FastAPI should:

- validate file size;
- validate file type;
- create server-controlled storage path;
- store source;
- enqueue processing.

It must not parse large documents synchronously.

---

## 55. Agentic Development Implication

Agentic coding tools should treat FastAPI as a stable architectural choice.

They must not replace it because another framework is preferred.

---

## 56. Prohibited Actions

Without a superseding ADR, do not:

- replace FastAPI with Django;
- replace FastAPI with Flask;
- replace backend with Node/NestJS;
- move core backend logic into Next.js;
- make serverless functions the primary backend;
- duplicate backend business logic in multiple frameworks.

---

## 57. Review Triggers

Revisit this decision if:

- FastAPI becomes a measured bottleneck;
- team skill profile changes dramatically;
- enterprise deployment requires a different runtime;
- platform constraints make Python unsuitable;
- maintenance burden becomes unacceptable.

---

## 58. Consequences

### Positive

- strong fit with AI/RAG ecosystem;
- typed API development;
- OpenAPI generation;
- async support;
- streaming support;
- simple deployment;
- one language for backend and RAG.

### Negative

- Python performance limits for CPU-heavy work;
- requires disciplined module structure;
- heavy parsing must be separated from API event loop.

---

## 59. Status

**Accepted**

FastAPI is the canonical Bismark AI V1 backend application framework.

Expected backend stack:

```text
FastAPI
Pydantic
SQLAlchemy
Alembic
```

Any replacement requires a new or superseding ADR.
