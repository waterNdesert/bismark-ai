# ADR-007 — Use a Modular Monolith for Bismark AI V1

**Project:** Bismark AI  
**ADR ID:** ADR-007  
**Title:** Use a Modular Monolith Instead of Microservices for V1  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 application architecture

---

## 1. Context

Bismark AI requires several clear product domains:

```text
authentication
users
organizations
workspaces
documents
ingestion
retrieval
chat
conversations
feedback
audit
usage
providers
database
```

These domains are logically distinct, but the project is still in its first major product phase.

The initial priorities are:

- move quickly;
- preserve clean boundaries;
- keep deployment simple;
- avoid unnecessary distributed-system complexity;
- support agentic coding tools;
- retain a straightforward path to future service extraction.

Several architectural approaches were considered:

1. modular monolith;
2. microservices from the beginning;
3. loosely organized monolithic backend;
4. serverless function decomposition;
5. event-driven service architecture.

---

## 2. Decision

Bismark AI V1 will be implemented as a **modular monolith**.

This means:

```text
one primary backend application
+
clear domain modules
+
one shared application database
+
one deployment unit for the API
```

The background worker is a separate process/runtime role, but it reuses the same application domain code and does not make the system a microservice architecture.

---

## 3. What Modular Monolith Means

The backend is deployed as one logical application but internally separated by domain boundaries.

Recommended structure:

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

Each module should own its own domain logic.

---

## 4. Why Modular Monolith

### 4.1 Faster Delivery

Bismark AI V1 has significant product work still to build:

- secure tenancy;
- ingestion;
- retrieval;
- reranking;
- chat;
- citations;
- evaluation.

Introducing microservices now would slow development.

---

### 4.2 Lower Operational Complexity

A modular monolith avoids early requirements for:

- service discovery;
- distributed tracing across services;
- service-to-service authentication;
- message-bus coordination;
- multiple deployment pipelines;
- contract versioning between internal services;
- distributed transactions.

---

### 4.3 Easier Debugging

A single application process makes it easier to trace:

```text
request
→ authorization
→ retrieval
→ provider call
→ persistence
```

This is valuable during early product development.

---

### 4.4 Better Fit for KVM 2

The initial Hostinger KVM 2 environment is deliberately compact.

The intended runtime is:

```text
Caddy
FastAPI
worker
Redis
```

A microservice architecture would introduce unnecessary process and memory overhead.

---

### 4.5 Better Fit for Agentic Development

Agentic coding tools work more reliably when:

- repository boundaries are explicit;
- architecture is documented;
- code dependencies are easy to inspect;
- cross-service behavior is limited.

A modular monolith provides these advantages without flattening all code into one large module.

---

## 5. What This Decision Does Not Mean

A modular monolith does **not** mean:

- one giant file;
- no module boundaries;
- tightly coupled code;
- shared mutable globals;
- arbitrary imports;
- direct provider calls everywhere;
- direct database access from every route.

The application must still have clear internal architecture.

---

## 6. Module Ownership

Each domain module should own:

- its service logic;
- its schemas;
- its repository/data access where appropriate;
- its domain-specific exceptions;
- its tests.

Examples:

### `organizations/`

Owns:

- organization creation;
- organization membership;
- organization roles.

### `documents/`

Owns:

- document metadata;
- upload lifecycle;
- deletion lifecycle.

### `retrieval/`

Owns:

- vector search;
- keyword search;
- fusion;
- reranking orchestration.

### `chat/`

Owns:

- answer orchestration;
- context building;
- LLM streaming;
- citation coordination.

---

## 7. Dependency Direction

Modules should depend on stable internal interfaces.

Preferred:

```text
chat
→ retrieval service
→ provider interfaces
```

Avoid:

```text
chat
→ random SQL
→ direct Voyage SDK
→ direct storage SDK
```

---

## 8. Shared Core

Shared functionality should live in `core/` only when genuinely cross-cutting.

Examples:

- settings;
- logging;
- middleware;
- request IDs;
- shared base errors.

Do not turn `core/` into a dumping ground.

---

## 9. Database Sharing

All modules use the same PostgreSQL database.

This is deliberate.

The database provides:

- transactional consistency;
- relational integrity;
- tenant boundaries;
- RLS;
- vector search;
- full-text search.

---

## 10. Transactions

The modular monolith makes cross-domain transactions practical.

Example:

```text
create organization
+
create owner membership
```

can happen within one database transaction.

This would be more complicated across services.

---

## 11. Worker Relationship

The worker is a separate runtime process but part of the same application architecture.

Conceptually:

```text
FastAPI
   |
   +--> shared domain code
   |
Worker
   |
   +--> shared domain code
```

The worker should not duplicate business logic.

---

## 12. Provider Boundaries

External providers remain abstracted.

Expected interfaces:

```text
EmbeddingProvider
RerankProvider
LLMProvider
StorageProvider
DocumentParser
JobQueue
```

These provide internal separation without requiring independent services.

---

## 13. API Boundary

Only the public FastAPI HTTP interface is considered an external API boundary.

Internal modules should normally call Python services directly rather than calling each other over HTTP.

---

## 14. No Internal HTTP Microservices

Do not create patterns like:

```text
chat service
→ HTTP
→ retrieval service
```

inside the same VPS for V1.

Use direct internal function/service calls.

---

## 15. No Separate Databases Per Module

Do not create:

```text
chat database
document database
organization database
```

in V1.

The shared PostgreSQL model is intentional.

---

## 16. Background Queue

Redis provides asynchronous execution, not domain separation.

A queued ingestion job does not turn ingestion into an independent microservice.

---

## 17. Deployment Unit

The API is one deployable backend application image.

The worker may use the same image with a different command.

Example:

```text
bismark-api:<version>
```

used by:

```text
api
worker
```

---

## 18. Alternative Considered — Microservices

### Benefits

- independent scaling;
- independent deployment;
- clear runtime boundaries;
- team ownership separation.

### Drawbacks

- more networking;
- more deployment pipelines;
- more failure modes;
- distributed tracing required;
- service auth required;
- more operational burden;
- slower development;
- harder local development.

### Decision

Rejected for V1.

The product does not yet have scale or organizational complexity requiring microservices.

---

## 19. Alternative Considered — Unstructured Monolith

### Benefits

- fastest initial coding;
- little up-front structure.

### Drawbacks

- quickly becomes difficult to maintain;
- poor agentic readability;
- duplicated business logic;
- hard future extraction;
- unclear ownership.

### Decision

Rejected.

The application must remain modular.

---

## 20. Alternative Considered — Serverless Function Decomposition

### Benefits

- independent scaling;
- managed infrastructure.

### Drawbacks

- fragmented domain logic;
- awkward long-running workflows;
- harder streaming;
- more distributed behavior;
- poorer fit for ingestion workers.

### Decision

Rejected for the primary backend.

---

## 21. Alternative Considered — Event-Driven Services

### Benefits

- strong decoupling;
- scalable asynchronous architecture.

### Drawbacks

- unnecessary complexity for V1;
- harder consistency;
- difficult debugging;
- additional infrastructure.

### Decision

Deferred.

---

## 22. Internal Contracts

Modules should expose explicit service interfaces.

For example:

```python
class RetrievalService:
    async def retrieve(...):
        ...
```

rather than allowing callers to reach into internal implementation details.

---

## 23. Import Discipline

Avoid circular dependencies.

Recommended dependency direction:

```text
routes
→ services
→ repositories/providers
→ infrastructure
```

Domain modules should not import route modules.

---

## 24. Shared Models

Database models may live in a centralized `db/` layer or domain modules, but ownership must remain clear.

Do not duplicate ORM models.

---

## 25. Event Usage

Internal application events may be used when useful.

Example:

```text
document.ready
```

But do not introduce a full event bus without a documented requirement.

---

## 26. Future Service Extraction

The modular design should make later extraction possible.

Potential future extraction candidates:

- ingestion;
- connector processing;
- analytics;
- notification service.

Extraction should happen only if measured need exists.

---

## 27. Service Extraction Criteria

A module may justify becoming a separate service if it has:

- substantially different scaling needs;
- independent failure isolation needs;
- independent deployment cadence;
- separate team ownership;
- strict security boundary;
- specialized infrastructure.

One or more should be demonstrated, not hypothetical.

---

## 28. Example: Ingestion Extraction

Today:

```text
FastAPI app
+
worker
+
shared code
```

Future:

```text
API
→ queue
→ independent ingestion service
```

Only if parsing workload justifies it.

---

## 29. Example: Retrieval Extraction

Do not extract retrieval merely because it is important.

Consider extraction only if:

- traffic is very high;
- separate scaling is required;
- retrieval team ownership becomes distinct.

---

## 30. Security Implications

A modular monolith simplifies authorization because:

- one application owns request identity;
- one authorization layer exists;
- one data access model exists.

This reduces risk of inconsistent service-level permission logic.

---

## 31. Tenant Isolation

Tenant isolation must remain consistent across all modules.

Shared helpers/policies should prevent each module from inventing its own tenant rules.

---

## 32. Testing Implications

Unit tests can test modules independently.

Integration tests can test full in-process workflows.

This makes it easier to verify:

```text
authorization
+
database
+
retrieval
+
chat
```

without distributed test infrastructure.

---

## 33. Local Development

Developers should be able to run:

```text
frontend
backend
worker
redis
```

without orchestrating many internal services.

---

## 34. CI/CD

The modular monolith reduces CI complexity.

Typical pipeline:

```text
backend lint
backend tests
backend build
frontend lint
frontend tests
frontend build
```

No per-microservice pipelines are needed.

---

## 35. Observability

One backend process simplifies logging and tracing.

Structured logs should include:

- request ID;
- user ID;
- organization ID;
- workspace ID;
- service/module context.

---

## 36. Performance

Internal Python calls are significantly simpler and lower overhead than HTTP calls between microservices.

This is appropriate for early-stage scale.

---

## 37. Failure Boundaries

The main backend process remains one failure domain.

This is accepted for V1.

The worker is separated operationally so parser failures do not necessarily crash the API.

---

## 38. Code Review

Reviewers should verify that new code goes into the correct domain module.

Do not add functionality to arbitrary utility files.

---

## 39. Module Growth

If a module becomes large, split internally.

Example:

```text
documents/
├── routes.py
├── service.py
├── repository.py
├── schemas.py
├── models.py
└── policies.py
```

Do not jump directly to service extraction.

---

## 40. Shared Utilities

Only truly generic functionality belongs in shared utility modules.

Business rules should stay with their domain.

---

## 41. Dependency Injection

Use dependency injection where it improves testability and provider replacement.

Avoid elaborate DI frameworks unless needed.

FastAPI's dependency system and explicit constructor injection are sufficient initially.

---

## 42. Database Repository Pattern

Repositories may be used to isolate database operations.

Do not create excessive abstraction where SQLAlchemy usage is already clear.

The goal is clean boundaries, not ceremony.

---

## 43. Domain Services

Complex business workflows should live in services.

Example:

```text
DocumentService
IngestionService
RetrievalService
ChatService
```

These names are illustrative, not mandatory.

---

## 44. Agentic Development Implication

Coding agents must preserve module boundaries.

They must not:

- move unrelated logic into one file;
- create new services casually;
- introduce internal HTTP communication;
- duplicate domain logic.

---

## 45. Documentation Implication

If a domain boundary changes materially:

- update `ARCHITECTURE.md`;
- update relevant technical docs;
- create ADR if architectural.

---

## 46. Deployment Implication

The backend remains easy to deploy:

```text
one image
two runtime roles
```

Roles:

```text
api
worker
```

---

## 47. Scaling Implication

Initial scaling:

```text
increase API workers
increase background workers
upgrade VPS
```

not:

```text
split into ten services
```

---

## 48. Data Consistency

Because modules share one PostgreSQL database, strong relational constraints remain practical.

This is useful for:

- memberships;
- documents;
- messages;
- citations.

---

## 49. Migration Simplicity

One migration history can manage the application schema.

This avoids coordinating schema ownership across services.

---

## 50. Future Organizational Growth

If Bismark AI later has multiple engineering teams, module ownership may map naturally to future services.

The modular monolith preserves that path.

---

## 51. Prohibited Actions

Without a superseding ADR, do not:

- split core domains into independent microservices;
- add service-to-service HTTP communication;
- create separate databases per module;
- introduce a service mesh;
- introduce Kubernetes for internal service orchestration;
- introduce Kafka solely to decouple modules;
- duplicate authorization per service.

---

## 52. Review Triggers

Revisit this decision when:

- multiple teams need independent release cadence;
- a domain requires independent scaling;
- uptime needs require failure isolation;
- workloads exceed practical monolith scaling;
- enterprise architecture requires strict service separation.

---

## 53. Consequences

### Positive

- fast development;
- simple deployment;
- easy debugging;
- strong transactions;
- straightforward security;
- lower infrastructure cost;
- good agentic maintainability.

### Negative

- one primary API failure domain;
- modules can become tightly coupled if discipline is poor;
- independent scaling is limited until extraction.

---

## 54. Status

**Accepted**

Bismark AI V1 will use a modular monolith.

The canonical shape is:

```text
FastAPI application
├── auth
├── organizations
├── workspaces
├── documents
├── ingestion
├── retrieval
├── chat
├── conversations
├── feedback
├── audit
└── providers
```

with:

```text
one shared PostgreSQL database
one API deployment unit
one worker runtime role
```

Any move to microservices must be justified by measured requirements and documented in a new or superseding ADR.
