# ARCHITECTURE.md — Bismark AI System Architecture

**Project:** Bismark AI  
**Document Type:** System Architecture  
**Status:** Canonical V1 Architecture  
**Version:** 1.0  
**Audience:** Engineering, DevOps, Security, AI/ML, QA, and Agentic Coding Systems

---

## 1. Purpose

This document defines the system architecture for Bismark AI V1.

It describes:

- component boundaries;
- responsibilities;
- data flows;
- deployment topology;
- integration interfaces;
- trust boundaries;
- scaling assumptions;
- failure boundaries;
- architectural constraints.

This document should be read together with:

- `PRD.md`
- `AGENTS.md`
- `DATABASE.md`
- `API.md`
- `RAG.md`
- `SECURITY.md`
- `DEPLOYMENT.md`
- `TESTING.md`

If implementation changes materially alter the architecture described here, the change must be documented and, where appropriate, accompanied by an Architecture Decision Record under `docs/decisions/`.

---

Documentation authority follows [AGENTS.md §2](../AGENTS.md#2-documentation-authority).

## 2. Architecture Summary

Bismark AI is built as a modular monolith with a separate frontend, backend API, background worker, external data platform, and external AI providers.

The initial topology is:

```text
User Browser
    |
    v
Vercel
Next.js Web App
    |
    | HTTPS
    v
Hostinger VPS
Caddy
    |
    v
FastAPI API
    |
    +----------------------+----------------------+-------------------+
    |                      |                      |                   |
    v                      v                      v                   v
Supabase PostgreSQL   Supabase Storage       Voyage AI          LLM Provider
    |                      |                      |                   |
    v                      v                      v                   v
Application Data      Original Files       Embeddings          Generated Answers
pgvector
Full-Text Search

Hostinger VPS also runs:
- Redis
- background worker
- document parser dependencies
```

---

## 3. Architectural Goals

The V1 architecture optimizes for:

1. fast delivery;
2. strong tenant isolation;
3. clear ownership boundaries;
4. low infrastructure complexity;
5. reliable RAG behavior;
6. maintainability;
7. provider replaceability;
8. incremental scalability;
9. secure cloud-native deployment;
10. good compatibility with agentic development workflows.

---

## 4. Architectural Non-Goals

V1 does not optimize for:

- Kubernetes;
- multi-region active-active;
- on-premise LLM inference;
- local GPU inference;
- multi-service event architecture;
- high-frequency streaming analytics;
- complex service meshes;
- distributed vector databases;
- dedicated knowledge graph databases;
- enterprise SSO federation;
- massive-scale connector ingestion;
- autonomous multi-agent orchestration.

These may be considered later if justified by product demand or measured bottlenecks.

---

## 5. Core Architectural Principle

Bismark AI owns the application.

External tools are supporting infrastructure.

The product must not become:

```text
Bismark UI
    |
    v
Third-Party AI App
```

Instead:

```text
Bismark AI
    |
    +--> Supabase
    +--> Voyage
    +--> LLM Provider
    +--> Parser
```

Bismark AI must own:

- organizations;
- users;
- workspaces;
- permissions;
- documents;
- conversations;
- messages;
- feedback;
- usage;
- audit history;
- RAG orchestration;
- provider configuration;
- citations;
- business rules.

---

## 6. Component Overview

The major V1 components are:

1. Next.js frontend;
2. FastAPI backend;
3. background worker;
4. Redis;
5. Supabase PostgreSQL;
6. Supabase Auth;
7. Supabase Storage;
8. pgvector;
9. PostgreSQL full-text search;
10. Voyage embeddings;
11. Voyage reranking;
12. document parser;
13. external LLM provider;
14. Caddy reverse proxy;
15. Docker Compose deployment.

---

## 7. Next.js Frontend

### 7.1 Responsibilities

The frontend is responsible for:

- authentication UI;
- organization and workspace navigation;
- document upload UI;
- document processing state;
- chat interface;
- streamed answer display;
- citations display;
- conversation history;
- member management;
- settings;
- feedback UI;
- user-facing errors;
- loading and empty states.

### 7.2 Responsibilities It Must Not Own

The frontend must not own authoritative:

- authorization decisions;
- tenant scoping;
- document permissions;
- retrieval filtering;
- service-role credentials;
- direct vector queries;
- provider secrets;
- business-critical validation.

### 7.3 Deployment

The frontend is deployed to Vercel.

Initial public hostname:

```text
app.<production-domain>
```

The exact production domain is environment-specific and must not be hard-coded.

---

## 8. FastAPI Backend

### 8.1 Role

FastAPI is the central application backend and orchestration layer.

It is the primary trusted server-side control plane for Bismark AI.

### 8.2 Responsibilities

FastAPI owns:

- authentication verification;
- authorization;
- user context;
- organizations;
- memberships;
- workspaces;
- workspace permissions;
- document metadata;
- upload orchestration;
- job creation;
- chat orchestration;
- retrieval requests;
- reranking coordination;
- LLM generation requests;
- citations assembly;
- conversation persistence;
- feedback persistence;
- audit logging;
- usage tracking;
- API error normalization;
- provider abstraction.

### 8.3 Architectural Position

```text
Frontend
   |
   v
FastAPI
   |
   +--> Supabase
   +--> Redis
   +--> Voyage
   +--> LLM
```

The frontend should not communicate directly with privileged provider APIs where backend authorization is required.

---

## 9. Background Worker

### 9.1 Purpose

The worker handles long-running and asynchronous document-processing tasks.

### 9.2 Responsibilities

The worker handles:

- source file retrieval;
- parsing;
- text normalization;
- semantic/structural chunking;
- embedding generation;
- document chunk insertion;
- indexing;
- retry logic;
- processing-status updates;
- failure logging;
- cleanup of temporary files.

### 9.3 Worker Boundary

The worker should not own:

- frontend sessions;
- user-facing authorization decisions;
- product navigation;
- general chat orchestration.

### 9.4 Queue Transport

Redis is used as the initial queue transport.

The exact Python worker framework may be selected during implementation but must remain lightweight.

---

## 10. Redis

### 10.1 Responsibilities

Redis is used for:

- ingestion job queueing;
- lightweight transient coordination;
- retry scheduling;
- worker communication.

### 10.2 Non-Responsibilities

Redis is not the source of truth for:

- documents;
- organizations;
- conversations;
- permissions;
- job history that matters to the user.

Durable product state belongs in PostgreSQL.

### 10.3 Security

Redis must not be publicly exposed.

It should only be reachable on the Docker network or private host network.

---

## 11. Supabase PostgreSQL

### 11.1 Role

Supabase PostgreSQL is the primary durable application database.

### 11.2 Responsibilities

It stores:

- profiles;
- organizations;
- memberships;
- workspaces;
- documents;
- chunks;
- conversations;
- messages;
- citations;
- feedback;
- audit logs;
- usage events;
- processing state;
- vector embeddings;
- search metadata.

### 11.3 Search Responsibilities

PostgreSQL provides:

- pgvector semantic similarity;
- full-text search;
- metadata filtering;
- tenant filtering;
- workspace filtering.

### 11.4 Source of Truth

PostgreSQL is the source of truth for application state.

The vector index is not treated as an independent knowledge source detached from relational permissions.

---

## 12. Supabase Auth

### 12.1 Role

Supabase Auth provides initial identity management.

### 12.2 Responsibilities

It provides:

- identity;
- login;
- password reset;
- session/token issuance;
- optional email verification.

### 12.3 Authorization Boundary

Supabase Auth answers:

```text
Who is this user?
```

Bismark AI answers:

```text
What may this user access?
```

Organization and workspace authorization is Bismark AI domain logic.

---

## 13. Supabase Storage

### 13.1 Role

Supabase Storage holds original uploaded documents.

### 13.2 Storage Model

Recommended logical key structure:

```text
organization_id/
    workspace_id/
        document_id/
            original_filename.ext
```

### 13.3 Rules

- files should be private by default;
- source documents should not live permanently on the VPS;
- temporary worker files should be deleted after use;
- direct public URLs should not be used for private knowledge files;
- access must be authorized.

---

## 14. pgvector

### 14.1 Role

pgvector stores semantic embeddings for document chunks.

### 14.2 Data Relationship

Embeddings remain attached to relational records containing:

- organization ID;
- workspace ID;
- document ID;
- chunk metadata.

### 14.3 Security Boundary

Vector retrieval must include tenant/workspace filtering at query time.

Never retrieve globally and filter later in application memory.

---

## 15. PostgreSQL Full-Text Search

### 15.1 Role

Full-text search complements semantic retrieval.

### 15.2 Why It Exists

Semantic vector search may underperform on:

- exact IDs;
- codes;
- acronyms;
- product names;
- names of people;
- exact policy phrases;
- dates;
- technical terms.

Full-text search provides lexical recall.

---

## 16. Voyage AI

### 16.1 Role

Voyage is the initial embedding and reranking provider.

### 16.2 Responsibilities

Voyage provides:

- document embeddings;
- query embeddings;
- reranking scores.

### 16.3 Integration Boundary

Voyage must be accessed through provider interfaces.

Example:

```text
EmbeddingProvider
    |
    v
VoyageEmbeddingProvider
```

and:

```text
RerankProvider
    |
    v
VoyageRerankProvider
```

### 16.4 Provider Isolation

Domain code must not directly scatter Voyage SDK calls across unrelated modules.

---

## 17. External LLM Provider

### 17.1 Role

The LLM provider generates final natural-language responses.

### 17.2 Responsibilities

It receives:

- system instructions;
- conversation context;
- retrieved evidence;
- question;
- citation/source mapping instructions.

### 17.3 Abstraction

The application should define an internal interface such as:

```text
LLMProvider
```

This allows later support for multiple providers.

### 17.4 Non-Authority

The LLM is not the source of truth.

The retrieved evidence is the grounding source for organization-specific claims.

---

## 18. Document Parser

### 18.1 Initial Options

Initial parser:

- Docling; or
- Unstructured.

### 18.2 Role

The parser converts raw documents into structured content.

### 18.3 Expected Output

The parser should preserve where possible:

- title;
- page number;
- heading;
- section;
- paragraph;
- table;
- list;
- metadata.

### 18.4 Abstraction

The parser should be accessed through an internal parser interface.

---

## 19. Caddy

### 19.1 Role

Caddy provides:

- HTTPS;
- TLS certificate management;
- reverse proxying;
- secure public API entry point.

### 19.2 Public Exposure

Only required public ports should be exposed.

Typical public ports:

```text
80
443
22
```

SSH should be hardened separately.

### 19.3 Internal Services

The following should not be publicly exposed:

- Redis;
- worker port;
- internal FastAPI container port;
- internal parser services.

---

## 20. Docker Compose

### 20.1 Purpose

Docker Compose manages VPS runtime services.

### 20.2 Initial Services

```text
caddy
api
worker
redis
```

### 20.3 Not Included Initially

Do not initially add:

- PostgreSQL;
- Qdrant;
- Weaviate;
- Elasticsearch;
- local LLM;
- MinIO;
- Kafka;
- RabbitMQ;
- Kubernetes.

These are unnecessary for V1.

---

## 21. Deployment Topology

```text
                   +------------------+
                   |      Browser     |
                   +--------+---------+
                            |
                            v
                   +------------------+
                   |      Vercel      |
                   |     Next.js      |
                   +--------+---------+
                            |
                       HTTPS API
                            |
                            v
                +-------------------------+
                |     Hostinger VPS       |
                |                         |
                |  +-------------------+  |
Internet ------>|  |       Caddy       |  |
                |  +---------+---------+  |
                |            |            |
                |            v            |
                |  +-------------------+  |
                |  |      FastAPI      |  |
                |  +---------+---------+  |
                |            |            |
                |            +--------+   |
                |                     |   |
                |  +-----------+      |   |
                |  |  Worker   |<-----+   |
                |  +-----+-----+          |
                |        |                |
                |  +-----v-----+          |
                |  |   Redis   |          |
                |  +-----------+          |
                +-------------------------+
                         |
        +----------------+-------------------+
        |                |                   |
        v                v                   v
   Supabase          Voyage AI          LLM Provider
```

---

## 22. Trust Boundaries

Bismark AI has several major trust boundaries.

### 22.1 Browser Boundary

The browser is untrusted.

Never trust:

- user IDs;
- organization IDs;
- workspace IDs;
- permissions;
- role claims;
- filenames;
- MIME types;
- document metadata;

without backend validation.

### 22.2 API Boundary

FastAPI is trusted application logic.

It must authenticate and authorize every protected request.

### 22.3 Worker Boundary

The worker is trusted but should operate on explicit job data and durable database state.

### 22.4 External Provider Boundary

Voyage and the LLM provider are third-party systems.

Only necessary data should be sent.

### 22.5 Storage Boundary

Private source files remain private.

Signed access or privileged backend retrieval should be used.

---

## 23. User Authentication Flow

```text
User
 |
 v
Next.js
 |
 v
Supabase Auth
 |
 v
Session / Access Token
 |
 v
FastAPI
 |
 v
Verify Token
 |
 v
Resolve Application Profile
 |
 v
Resolve Organization/Workspace Membership
 |
 v
Authorized Request
```

---

## 24. Organization Creation Flow

```text
Authenticated User
    |
    v
POST /api/v1/organizations
    |
    v
FastAPI
    |
    +--> validate request
    +--> create organization
    +--> create owner membership
    +--> audit event
    |
    v
Return organization
```

This should be transactional where possible.

---

## 25. Workspace Creation Flow

```text
Organization Member
    |
    v
POST /api/v1/workspaces
    |
    v
Check organization permission
    |
    v
Create workspace
    |
    v
Persist
    |
    v
Return workspace
```

---

## 26. Document Upload Flow

```text
User
 |
 v
Next.js
 |
 v
FastAPI
 |
 +--> authenticate
 +--> authorize workspace
 +--> validate file
 +--> create document record
 +--> upload source to Supabase Storage
 +--> enqueue ingestion job
 |
 v
Return:
document_id
status=queued
```

The upload request must not wait for parsing, embeddings, or indexing.

---

## 27. Document Ingestion Flow

```text
Redis Job
    |
    v
Worker
    |
    +--> load document metadata
    +--> fetch source from Supabase Storage
    +--> mark processing
    +--> parse document
    +--> normalize
    +--> chunk
    +--> embed batches with Voyage
    +--> insert chunks
    +--> build search fields
    +--> validate result
    +--> mark ready
    +--> delete temp files
```

On failure:

```text
mark failed
store safe error
log diagnostics
allow retry
```

---

## 28. Chat Request Flow

```text
User Question
    |
    v
Next.js
    |
    v
FastAPI
    |
    +--> authenticate
    +--> authorize workspace
    +--> load conversation context
    +--> run retrieval
    +--> rerank evidence
    +--> construct context
    +--> call LLM
    +--> stream response
    +--> persist answer
    +--> persist sources
    +--> usage/audit
```

---

## 29. Retrieval Flow

```text
Question
    |
    v
Authenticate
    |
    v
Authorize Organization and Workspace
    |
    v
Query Preparation
    |
    +-----------------------------------+
    |                                   |
    v                                   v
Voyage Query Embedding              FTS Query
    |                                   |
    v                                   v
SQL scope: organization,            SQL scope: organization,
workspace, ready/non-deleted        workspace, ready/non-deleted
documents, active version           documents, active version
    |                                   |
    v                                   v
pgvector Retrieval                 FTS Retrieval
    |                                   |
    +-----------------+-----------------+
                      |
                      v
               Candidate Fusion
                      |
                      v
               Voyage Reranking
                      |
                      v
               Evidence Selection
                      |
                      v
               Context Construction
                      |
                      v
                 LLM Generation
```

Both database retrieval queries apply the authorized organization/workspace scope
and document eligibility predicates before returning ranked candidates. Fusion
and reranking receive only authorized candidates. Any later evidence selection
narrows that already authorized set; it is not an authorization filter.

NEVER retrieve globally and filter unauthorized results in Python.

---

## 30. Context Construction Flow

The final LLM context should contain:

1. system behavior instructions;
2. organization/workspace-safe metadata where useful;
3. recent relevant conversation context;
4. retrieved evidence;
5. source identifiers;
6. user question.

The system should avoid:

- excessive unrelated history;
- stale citations;
- evidence not actually passed to the model;
- duplicate chunks;
- cross-tenant context.

---

## 31. Citation Flow

```text
Retrieved Chunk
    |
    v
Source Metadata
    |
    +--> document_id
    +--> page_number
    +--> section_title
    +--> chunk_id
    +--> excerpt
    |
    v
Context Builder
    |
    v
LLM
    |
    v
Answer with source references
    |
    v
Persist message_sources
```

The citation display should map back to persisted source records, not trust free-form model text alone.

---

## 32. Conversation Context Architecture

Conversation memory is not the same as organizational knowledge.

Use:

```text
Conversation History
    |
    v
Recent Context
```

and separately:

```text
Organization Knowledge
    |
    v
RAG Retrieval
```

Then:

```text
Recent Context + Retrieved Knowledge
    |
    v
LLM
```

This separation prevents earlier assistant answers from becoming unquestioned factual truth.

---

## 33. Data Ownership Boundaries

### Frontend owns

- presentation state;
- local interaction state;
- temporary form state.

### Backend owns

- business logic;
- authorization;
- orchestration;
- validation;
- canonical API responses.

### PostgreSQL owns

- durable application state.

### Storage owns

- original binary documents.

### Worker owns

- asynchronous processing execution.

### Voyage owns

- embedding/reranking computation.

### LLM provider owns

- generation computation.

---

## 34. Backend Domain Boundaries

Recommended FastAPI modules:

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

### `core/`

Contains:

- settings;
- logging;
- common errors;
- shared middleware;
- request IDs.

### `auth/`

Contains:

- auth token verification;
- authenticated principal resolution.

### `organizations/`

Contains:

- organization domain logic;
- membership management.

### `workspaces/`

Contains:

- workspace domain logic;
- workspace membership/authorization.

### `documents/`

Contains:

- document metadata;
- upload lifecycle;
- deletion lifecycle.

### `ingestion/`

Contains:

- parser orchestration;
- chunking;
- embedding;
- indexing.

### `retrieval/`

Contains:

- vector retrieval;
- keyword retrieval;
- candidate fusion;
- reranking;
- filtering.

### `chat/`

Contains:

- answer orchestration;
- prompt/context construction;
- streaming.

### `providers/`

Contains:

- embedding adapter;
- reranking adapter;
- LLM adapter;
- storage adapter;
- parser adapter.

---

## 35. Frontend Domain Boundaries

Recommended structure:

```text
src/
├── app/
├── components/
├── features/
│   ├── auth/
│   ├── organizations/
│   ├── workspaces/
│   ├── documents/
│   ├── chat/
│   ├── conversations/
│   └── settings/
├── hooks/
├── lib/
└── types/
```

Feature modules should avoid depending on unrelated feature internals.

---

## 36. Provider Interface Pattern

Example conceptual interface:

```python
class EmbeddingProvider:
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    async def embed_query(self, text: str) -> list[float]:
        ...
```

Concrete implementation:

```python
class VoyageEmbeddingProvider(EmbeddingProvider):
    ...
```

Similarly:

```text
RerankProvider
LLMProvider
StorageProvider
DocumentParser
```

This is a deliberate architectural boundary.

---

## 37. API Interface Boundary

Frontend communicates with backend through versioned HTTP APIs.

Initial base:

```text
/api/v1
```

The frontend should not query the Supabase database directly for protected domain operations unless explicitly documented.

Direct browser use of Supabase may be used for authentication/session flows where appropriate, but business authorization remains backend-controlled.

---

## 38. Worker Interface Boundary

FastAPI enqueues work.

Worker executes work.

The queue payload should contain stable identifiers rather than raw massive file contents.

Preferred pattern:

```text
job:
document_id
```

The worker then resolves authoritative metadata from PostgreSQL.

This avoids stale or manipulated job payloads.

---

## 39. Document Processing State Machine

Recommended lifecycle:

```text
uploaded
   |
   v
queued
   |
   v
processing
   |
   +------> failed
   |
   v
ready
```

Deletion may introduce:

```text
deleting
```

Avoid ambiguous processing states.

---

## 40. Chat Message State

Recommended conceptual states:

```text
pending
streaming
completed
failed
cancelled
```

Not all must necessarily be stored in V1, but the application should handle these states correctly.

---

## 41. Error Boundaries

The architecture should isolate failures.

### Parser failure

Must not crash API.

### Voyage failure

Must not corrupt documents.

### LLM failure

Must not destroy conversation history.

### Redis failure

Must not silently mark work as complete.

### Storage failure

Must not create fake ready documents.

### Database failure

Must fail safely.

---

## 42. Retry Boundaries

Safe retries are appropriate for:

- embedding provider transient errors;
- reranker transient errors;
- storage transient errors;
- parsing worker crashes.

Unsafe or duplicate-prone operations must be idempotent or protected.

---

## 43. Idempotency

Document processing should avoid duplicate chunk insertion when a job is retried.

Strategies may include:

- deleting stale chunks before reindex;
- processing version identifiers;
- unique chunk constraints;
- transactional replacement.

The exact approach will be defined in `DATABASE.md` and `RAG.md`.

---

## 44. Observability Architecture

At minimum:

```text
Request
   |
   v
Request ID
   |
   v
Structured Logs
```

Important fields:

- request_id;
- user_id;
- organization_id;
- workspace_id;
- document_id;
- conversation_id;
- job_id;
- provider;
- latency;
- status;
- error_class.

---

## 45. Health Architecture

The backend should expose:

```text
GET /health
GET /ready
```

### `/health`

Indicates the process is alive.

### `/ready`

Indicates the service can satisfy requests, including critical dependencies as appropriate.

Caddy or infrastructure tooling may use these endpoints.

---

## 46. Scaling Model

V1:

```text
1 API
1 Worker
1 Redis
```

First scaling step:

```text
N API replicas
N Workers
1 Redis or managed Redis
```

The stateless API should be horizontally scalable.

The database and storage remain external.

---

## 47. Scaling Triggers

Scale only in response to measurements such as:

- CPU saturation;
- memory pressure;
- ingestion queue depth;
- parser latency;
- API latency;
- provider throttling;
- concurrent streaming load;
- database query latency.

Do not preemptively introduce complexity.

---

## 48. KVM 2 Suitability

The intended Hostinger KVM 2 class environment is suitable because:

- PostgreSQL is external;
- source storage is external;
- embeddings are external;
- reranking is external;
- LLM inference is external;
- no GPU workloads run locally.

The VPS primarily performs:

- API handling;
- orchestration;
- parsing;
- chunking;
- queueing;
- temporary file processing.

Upgrade to a larger VPS when workload measurements justify it.

---

## 49. Local Development Topology

Recommended local environment:

```text
Developer Machine
    |
    +--> Next.js dev server
    +--> FastAPI dev server
    +--> Docker Redis
    +--> Optional local parser dependencies
    |
    +--> Supabase cloud dev project
    +--> Voyage test key
    +--> LLM test key
```

A full local Supabase stack is optional, not mandatory.

---

## 50. Environment Separation

Recommended environments:

```text
development
staging
production
```

Each should have separate:

- database;
- storage;
- secrets;
- API keys where possible;
- domains;
- CORS configuration.

Production data must never be casually reused in development.

---

## 51. Staging

A staging environment is strongly recommended before production.

Staging should mirror production topology closely:

- Vercel frontend;
- VPS backend;
- Supabase project;
- provider credentials;
- representative test documents.

---

## 52. Production Domain Pattern

Suggested pattern:

```text
app.bismark.ai
api.bismark.ai
```

Optional later:

```text
status.bismark.ai
docs.bismark.ai
```

Do not expose internal service hostnames.

---

## 53. Security Zones

### Public Zone

- Vercel frontend;
- Caddy HTTPS endpoint.

### Application Zone

- FastAPI;
- worker;
- Redis.

### Data Zone

- Supabase PostgreSQL;
- Supabase Storage.

### External AI Zone

- Voyage;
- LLM provider.

Each boundary must be treated explicitly in `SECURITY.md`.

---

## 54. File Upload Boundary

Uploads must be validated by backend policy.

Validation should include:

- max file size;
- MIME type;
- extension sanity;
- allowed parser types;
- tenant quota when added;
- storage success.

The backend should not trust MIME type reported only by the browser.

---

## 55. Document Deletion Flow

Recommended flow:

```text
Authorized User
   |
   v
DELETE document
   |
   v
Mark deleting
   |
   +--> remove chunks
   +--> remove storage object
   +--> clean related sources
   +--> audit
   |
   v
delete or tombstone metadata
```

Exact retention policy will be defined later.

---

## 56. Reprocessing Flow

A failed or stale document may be reprocessed.

Recommended:

```text
document
   |
   v
new processing_version
   |
   v
parse
embed
index
   |
   v
atomic activation
```

Avoid exposing partially reindexed documents if possible.

---

## 57. Model Configuration

Provider models must be configurable.

Example:

```text
VOYAGE_EMBEDDING_MODEL
VOYAGE_RERANK_MODEL
LLM_PROVIDER
LLM_MODEL
```

Do not hard-code provider model names into domain logic.

---

## 58. Retrieval Configuration

Configuration should support:

- vector candidate count;
- keyword candidate count;
- fused candidate count;
- reranker candidate count;
- final evidence count;
- max context tokens;
- score thresholds where used.

These should be centralized.

---

## 59. API Streaming Boundary

Recommended streaming path:

```text
LLM Provider
    |
    v
FastAPI
    |
    v
HTTP Stream / SSE
    |
    v
Next.js
```

The frontend should not open a direct privileged LLM connection.

---

## 60. Data Consistency

Important consistency rules:

- document marked `ready` only after chunks are available;
- assistant message marked completed only after final persistence succeeds;
- citation records correspond to actual final evidence;
- workspace membership is checked before retrieval;
- file deletion and chunk deletion should not drift indefinitely.

---

## 61. Transactions

Use database transactions where operations logically belong together.

Examples:

- organization + owner membership;
- conversation + initial message where appropriate;
- final answer + source records where feasible.

External network calls should not hold database transactions open unnecessarily.

---

## 62. Audit Architecture

Audit-worthy actions include:

- organization creation;
- member invite/removal;
- role changes;
- workspace creation/deletion;
- document upload;
- document deletion;
- sensitive settings changes;
- administrative actions.

Audit logs should be append-oriented.

---

## 63. Usage Architecture

The system should record usage signals useful for:

- future quotas;
- analytics;
- cost attribution;
- abuse detection.

Examples:

- documents uploaded;
- bytes processed;
- chunks embedded;
- questions asked;
- model tokens;
- rerank calls.

---

## 64. Rate Limiting

Rate limiting should be implemented at the API layer.

Potential dimensions:

- user;
- organization;
- IP;
- endpoint.

Special attention:

- login-related routes;
- upload;
- chat;
- expensive AI operations.

---

## 65. Future Connector Architecture

Future connectors should feed the same ingestion boundary.

Example:

```text
Google Drive
SharePoint
Notion
Website
Email
    |
    v
Source Adapter
    |
    v
Canonical Document
    |
    v
Ingestion Pipeline
```

Do not build separate RAG pipelines for each connector.

---

## 66. Future Knowledge Graph Architecture

Knowledge graphs are explicitly outside V1.

If later added, they should complement rather than replace the existing retrieval layer.

Potential future pattern:

```text
Vector Retrieval
Keyword Retrieval
Graph Retrieval
       |
       v
Candidate Fusion
       |
       v
Reranking
```

This requires a separate ADR.

---

## 67. Future Local Model Architecture

Local LLM inference is outside V1.

If introduced later:

- it should sit behind `LLMProvider`;
- it should not require rewriting chat orchestration;
- infrastructure costs must be evaluated;
- data processing mode should be configurable.

---

## 68. Future Model Gateway

A model gateway such as LiteLLM may be introduced later if:

- multiple providers are used;
- routing is needed;
- centralized cost controls are needed.

It is not required for V1.

---

## 69. Dependency Direction

Domain logic should depend inward on abstractions, not outward on vendor SDKs.

Preferred:

```text
Chat Service
    |
    v
LLMProvider interface
    |
    v
Vendor adapter
```

Avoid:

```text
Chat Service
    |
    v
OpenAI SDK directly
```

throughout the codebase.

---

## 70. Canonical Interfaces

Expected provider abstractions:

```text
AuthVerifier
StorageProvider
DocumentParser
EmbeddingProvider
RerankProvider
LLMProvider
JobQueue
```

These names may vary, but the boundaries should remain.

---

## 71. Data Transfer Minimization

Only necessary content should be sent to external providers.

For Voyage:

- chunks or queries required for embedding/reranking.

For LLM:

- user question;
- required conversation context;
- final selected evidence.

Do not send entire private knowledge bases unnecessarily.

---

## 72. Prompt Boundary

Prompts belong inside the application layer, not frontend code.

Prompt construction should be versioned or centrally managed.

The RAG document will define prompt expectations in greater detail.

---

## 73. Architecture Testing

Architecture-sensitive tests should include:

- cross-tenant document access;
- cross-workspace retrieval;
- unauthorized API access;
- worker retry;
- failed storage upload;
- failed embedding;
- failed reranking;
- failed generation;
- citation persistence;
- duplicate job execution.

---

## 74. Failure Example: Voyage Unavailable

Expected behavior:

```text
Voyage unavailable
    |
    v
Embedding/retrieval operation fails safely
    |
    v
Bounded retry where appropriate
    |
    v
User receives controlled error
    |
    v
No corrupted document state
```

---

## 75. Failure Example: LLM Unavailable

Expected behavior:

```text
Retrieval succeeds
LLM fails
    |
    v
Assistant response marked failed
    |
    v
User may retry
    |
    v
No duplicate user message
```

---

## 76. Failure Example: Worker Crash

Expected behavior:

```text
Worker crashes mid-ingestion
    |
    v
Document does not become ready
    |
    v
Job becomes retryable/failed
    |
    v
No partial chunks treated as canonical
```

---

## 77. Failure Example: Storage Upload Fails

Expected behavior:

```text
Metadata prepared
Storage fails
    |
    v
Document remains non-ready
    |
    v
User receives error
    |
    v
No ingestion job created for missing source
```

---

## 78. Deployment Responsibility Matrix

### Vercel

Owns:

- frontend runtime;
- frontend build;
- frontend CDN;
- frontend TLS.

### Hostinger

Owns:

- VPS compute;
- Docker runtime;
- backend containers;
- worker containers;
- Redis;
- Caddy.

### Supabase

Owns:

- PostgreSQL;
- Auth;
- Storage;
- pgvector extension.

### Voyage

Owns:

- embedding service;
- reranking service.

### LLM Provider

Owns:

- model inference.

---

## 79. Upgrade Path

Likely evolution:

### Stage 1

```text
KVM 2
1 API
1 Worker
Redis
```

### Stage 2

```text
KVM 4
2 API workers/processes
2 ingestion workers
Redis
```

### Stage 3

Possible:

- managed Redis;
- separated worker host;
- dedicated observability;
- load balancer.

Only after measured need.

---

## 80. Repository Architecture Documentation

The architecture should be reflected in:

```text
docs/ARCHITECTURE.md
docs/DATABASE.md
docs/API.md
docs/RAG.md
docs/SECURITY.md
docs/DEPLOYMENT.md
```

Agents must update relevant docs when boundaries change.

---

## 81. Architecture Decision Record Triggers

Create an ADR for changes such as:

- database platform replacement;
- vector database introduction;
- parser replacement if architecturally significant;
- model gateway introduction;
- local model hosting;
- multi-region deployment;
- major authentication replacement;
- microservice extraction;
- knowledge graph introduction;
- queue technology replacement with major infrastructure impact.

---

## 82. V1 Architecture Acceptance Criteria

The architecture is correctly implemented when:

1. frontend and backend are independently deployable;
2. backend enforces authorization;
3. documents persist in Supabase Storage;
4. metadata persists in PostgreSQL;
5. embeddings persist in pgvector;
6. vector and keyword retrieval are both available;
7. Voyage reranking is integrated;
8. worker handles ingestion asynchronously;
9. Redis is private;
10. the LLM is abstracted;
11. Voyage is abstracted;
12. source citations are traceable;
13. cross-tenant retrieval is impossible under tested conditions;
14. backend services run in Docker;
15. Caddy terminates production HTTPS;
16. the frontend runs on Vercel;
17. the system can be upgraded without rewriting major product layers.

---

## 83. Architectural Constraints

The following are deliberate constraints for V1:

- no local production LLM;
- no separate vector database;
- no production PostgreSQL on VPS;
- no permanent local source document storage;
- no microservices;
- no Kubernetes;
- no knowledge graph;
- no direct browser access to privileged AI providers;
- no global unscoped retrieval;
- no synchronous long-running ingestion.

---

## 84. Summary

Bismark AI V1 uses a deliberately compact architecture:

```text
Next.js / Vercel
        |
        v
FastAPI / Hostinger
        |
        +--> Worker / Redis
        |
        +--> Supabase
        |
        +--> Voyage
        |
        +--> LLM Provider
```

Supabase acts as the durable platform for:

- database;
- identity;
- storage;
- vector retrieval.

The Hostinger VPS acts as the compute and orchestration layer.

Voyage provides retrieval intelligence.

The external LLM provides generation.

Bismark AI itself owns the product, permissions, data relationships, retrieval logic, conversation system, and user experience.

The design intentionally prioritizes speed, security, clarity, and future replaceability over premature infrastructure complexity.
