# Bismark AI — Product Requirements Document (PRD)

**Document Version:** 1.0  
**Product Name:** Bismark AI  
**Document Type:** Product Requirements Document  
**Status:** Initial Build Specification  
**Primary Audience:** Product, Engineering, AI/ML, DevOps, QA, Security, and Agentic Coding Assistants

---

## 1. Product Overview

Bismark AI is a multi-tenant enterprise knowledge intelligence platform that enables organizations to securely upload, organize, search, and converse with their internal knowledge using retrieval-augmented generation (RAG).

The product will combine a modern SaaS application layer with a custom RAG pipeline. It will use Next.js for the frontend, FastAPI for backend APIs and AI orchestration, Supabase for PostgreSQL, authentication, storage, and pgvector, Voyage AI for embeddings and reranking, and an external large language model provider for answer generation.

The backend and document-processing infrastructure will run on a Hostinger VPS using Docker. The frontend will be deployed on Vercel.

The first version must prioritize speed of delivery, clean architecture, strong tenant isolation, reliable citations, and a foundation that can evolve into a more sophisticated enterprise AI knowledge platform.

---

## 2. Product Vision

Bismark AI should become an organization's trusted AI interface to its internal knowledge.

Instead of employees manually searching across policies, manuals, SOPs, presentations, reports, technical documents, and other internal resources, they should be able to ask natural-language questions and receive grounded answers supported by citations to approved company knowledge.

The long-term goal is to evolve from document Q&A into an enterprise knowledge intelligence system capable of:

- understanding structured and unstructured company information;
- maintaining organizational context;
- connecting knowledge across departments;
- providing source-grounded answers;
- supporting organizational memory;
- integrating with enterprise systems;
- handling multiple modalities;
- supporting private and controlled AI workflows;
- providing measurable AI quality and governance.

---

## 3. Product Principles

Bismark AI must be built around the following principles:

### 3.1 Grounded Answers

Answers must be generated from retrieved organization-approved knowledge whenever the user is asking about organizational information.

The system should avoid presenting unsupported statements as facts.

### 3.2 Source Transparency

Users should be able to see which documents and document sections contributed to an answer.

### 3.3 Tenant Isolation

Data belonging to one organization or workspace must never be exposed to another.

### 3.4 Product Ownership

Bismark AI must own its application layer, user experience, permissions, business logic, conversations, metadata, and RAG orchestration.

Third-party AI services are infrastructure components, not the product.

### 3.5 Provider Independence

The architecture should minimize tight coupling to any single LLM provider.

### 3.6 Fast Initial Delivery

The first release should favor a modular monolith and a limited feature set over premature microservices or infrastructure complexity.

### 3.7 Evolution Without Rewrite

Core boundaries should allow future replacement of embeddings, LLMs, document parsers, retrieval algorithms, and deployment infrastructure without rebuilding the entire product.

---

## 4. Target Users

### 4.1 Organization Owner

Creates and manages an organization, invites users, manages workspaces, and controls organization-level settings.

### 4.2 Organization Admin

Manages members, workspaces, documents, access, and operational settings.

### 4.3 Workspace Member

Uses approved workspace knowledge, uploads documents when permitted, and interacts with Bismark AI.

### 4.4 Knowledge Manager

Maintains the quality, organization, lifecycle, and availability of documents and knowledge sources.

### 4.5 Future Enterprise Administrator

Manages audit, security, compliance, SSO, retention, integrations, and organization-wide governance.

---

## 5. Initial Use Cases

Bismark AI V1 must support the following core workflows.

### 5.1 Organization Setup

A user can:

1. create an account;
2. create an organization;
3. create one or more workspaces;
4. invite or add members;
5. assign workspace access.

### 5.2 Document Upload

An authorized user can:

1. select a workspace;
2. upload a supported document;
3. see upload progress;
4. see processing status;
5. receive confirmation when the document is searchable.

### 5.3 Ask a Question

A user can:

1. open a workspace;
2. start a conversation;
3. ask a natural-language question;
4. receive a streamed AI response;
5. inspect supporting sources;
6. continue with follow-up questions.

### 5.4 Review Sources

A user can inspect:

- document name;
- page number when available;
- section or heading when available;
- supporting excerpt;
- source relevance.

### 5.5 Conversation History

A user can:

- view previous conversations;
- reopen a conversation;
- continue a conversation;
- rename a conversation;
- delete a conversation.

### 5.6 Knowledge Management

Authorized users can:

- view uploaded documents;
- see processing state;
- retry failed processing;
- remove documents;
- inspect document metadata.

### 5.7 Feedback

Users can provide positive or negative feedback on AI responses.

Feedback must be stored for future evaluation and product improvement.

---

## 6. V1 Scope

### 6.1 Included

The first production-capable release will include:

- authentication;
- user profiles;
- organizations;
- organization memberships;
- workspaces;
- workspace memberships;
- basic role-based access;
- document uploads;
- Supabase Storage integration;
- asynchronous document processing;
- document parsing;
- semantic chunking;
- Voyage embeddings;
- PostgreSQL pgvector storage;
- PostgreSQL full-text retrieval;
- hybrid retrieval;
- Voyage reranking;
- workspace-scoped chat;
- streaming responses;
- grounded answer generation;
- citations;
- conversation history;
- feedback;
- document management;
- basic audit events;
- health endpoints;
- structured logging;
- deployment using Docker;
- Vercel frontend deployment;
- Hostinger VPS backend deployment.

### 6.2 Explicitly Out of Scope for V1

The following should not delay the MVP:

- fine-tuning;
- local LLM inference;
- autonomous agents;
- complex workflow automation;
- voice assistants;
- video understanding;
- graph visualization;
- advanced knowledge graphs;
- SAML;
- enterprise SCIM provisioning;
- billing automation;
- marketplace integrations;
- dozens of data connectors;
- browser automation;
- custom model training;
- native mobile applications;
- complex analytics dashboards.

These may be added after the core RAG product has been validated.

---

## 7. Technology Stack

### 7.1 Frontend

- Next.js
- TypeScript
- React
- Tailwind CSS
- shadcn/ui
- Vercel

### 7.2 Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- async-compatible PostgreSQL driver
- Docker

### 7.3 Database and Platform Services

Supabase will provide:

- PostgreSQL;
- Supabase Auth;
- Supabase Storage;
- pgvector;
- Row Level Security where appropriate.

### 7.4 AI Retrieval

Voyage AI will provide:

- document embeddings;
- query embeddings;
- reranking.

The initial embedding model should be configurable through environment variables and must not be hard-coded into business logic.

### 7.5 LLM

The generation provider must be abstracted behind an internal application interface.

The initial implementation may use a cloud LLM API.

The application should support replacing or adding providers later without rewriting the chat domain logic.

### 7.6 Document Parsing

The initial document-processing service should use an open-source parser such as Docling or Unstructured.

The parser must be isolated behind an application interface so it can be replaced.

### 7.7 Queue

A lightweight asynchronous job architecture will be used for document ingestion.

Initial infrastructure:

- Redis;
- one background worker;
- a Python job framework compatible with FastAPI.

The exact library may be selected during implementation, but the application should not process long-running ingestion synchronously inside upload HTTP requests.

### 7.8 Reverse Proxy

Caddy will terminate HTTPS and reverse proxy traffic to FastAPI on the VPS.

---

## 8. Deployment Architecture

### 8.1 Vercel

Vercel hosts:

- Next.js frontend.

Example:

`app.bismark.ai`

### 8.2 Hostinger VPS

A Hostinger KVM 2 class server is the intended starting deployment target.

Target resources:

- 2 vCPU;
- 8 GB RAM;
- 100 GB NVMe;
- Docker Engine;
- Docker Compose.

It will run:

- FastAPI API;
- document worker;
- Redis;
- document parsing dependencies;
- Caddy.

It will not initially run:

- PostgreSQL;
- persistent user document storage;
- local LLMs;
- separate vector databases.

Example:

`api.bismark.ai`

### 8.3 Supabase

Supabase hosts:

- application PostgreSQL;
- vector data;
- authentication;
- source document storage.

### 8.4 External AI Services

Voyage:

- embeddings;
- reranking.

LLM provider:

- response generation.

---

## 9. High-Level System Architecture

```text
                           User
                            |
                            v
                    +---------------+
                    |    Next.js    |
                    |    Vercel     |
                    +-------+-------+
                            |
                            | HTTPS
                            v
                    +---------------+
                    |    FastAPI    |
                    | Hostinger VPS |
                    +-------+-------+
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
     +----------+       +---------+        +---------+
     | Supabase |       | Voyage  |        |   LLM   |
     +----------+       +---------+        +---------+
          |
    +-----+------------------------+
    |              |               |
    v              v               v
 PostgreSQL      Storage         pgvector
```

Background ingestion:

```text
Upload
  |
  v
FastAPI
  |
  +--> Supabase Storage
  |
  +--> document record
  |
  +--> Redis job
          |
          v
        Worker
          |
          v
      Document Parser
          |
          v
     Semantic Chunking
          |
          v
    Voyage Embeddings
          |
          v
   Supabase / pgvector
```

---

## 10. RAG Architecture

Bismark AI should not use basic vector search as its complete retrieval system.

The first production retrieval pipeline should be:

```text
User Query
    |
    v
Authorization + Workspace Scope
    |
    v
Query Preparation
    |
    +------------------+
    |                  |
    v                  v
Vector Search      Keyword Search
(pgvector)         (PostgreSQL FTS)
    |                  |
    +---------+--------+
              |
              v
       Candidate Fusion
              |
              v
       Metadata Filtering
              |
              v
       Voyage Reranker
              |
              v
       Best Evidence
              |
              v
       Context Builder
              |
              v
             LLM
              |
              v
      Answer + Citations
```

---

## 11. Retrieval Requirements

The retrieval layer must support:

- workspace scoping;
- organization scoping;
- document filters;
- semantic vector retrieval;
- keyword retrieval;
- hybrid candidate fusion;
- reranking;
- metadata filtering;
- configurable candidate count;
- configurable final context count;
- page and section metadata;
- retrieval diagnostics for development.

A user must never retrieve chunks from a workspace they cannot access.

---

## 12. Document Processing

### 12.1 Supported Initial Formats

Target initial support:

- PDF;
- DOCX;
- TXT;
- Markdown;
- HTML.

PPTX may be added to V1 if the selected parser supports it reliably without delaying release.

### 12.2 Processing Lifecycle

Documents should have one of the following states:

- uploaded;
- queued;
- processing;
- ready;
- failed;
- deleting.

### 12.3 Parsing Requirements

Where available, the parser should preserve:

- document title;
- page number;
- section heading;
- paragraph structure;
- lists;
- tables;
- source metadata.

### 12.4 Chunking

Chunking must not rely exclusively on fixed character counts.

The initial implementation should prefer section-aware or semantic chunking.

Each stored chunk should contain enough metadata to trace it back to its source.

---

## 13. Core Data Model

The initial data model should include at minimum:

### profiles

Application-level user profile linked to Supabase Auth identity.

### organizations

Represents a customer or tenant.

### organization_members

Maps users to organizations and stores roles.

### workspaces

Logical knowledge containers within an organization.

Examples:

- HR;
- Engineering;
- Sales;
- Operations.

### workspace_members

Controls user access to specific workspaces when necessary.

### documents

Stores metadata and processing state for source files.

### document_chunks

Stores parsed text, embeddings, metadata, and search fields.

### conversations

Represents user chat sessions.

### messages

Stores user and assistant messages.

### message_sources

Stores the retrieved evidence associated with an assistant answer.

### feedback

Stores feedback associated with messages.

### usage_events

Stores usage measurements required for future limits, analytics, or billing.

### audit_logs

Stores security- and administration-relevant actions.

---

## 14. Suggested Document Table

Key fields:

```text
id
organization_id
workspace_id
filename
display_name
mime_type
size_bytes
storage_bucket
storage_path
status
parser_name
parser_version
embedding_model
chunk_count
error_message
created_by
created_at
processing_started_at
processing_completed_at
updated_at
```

---

## 15. Suggested Document Chunk Table

Key fields:

```text
id
organization_id
workspace_id
document_id
chunk_index
content
embedding
search_vector
page_number
section_title
heading
token_count
metadata
created_at
```

The embedding dimension must match the selected Voyage model configuration.

---

## 16. Multi-Tenancy

Bismark AI will be multi-tenant from the beginning.

Every tenant-owned entity must be traceable to an organization.

Workspace-level resources must additionally carry a workspace identifier.

Tenant security must exist at more than one layer:

1. application authorization;
2. SQL query scoping;
3. Supabase RLS where appropriate;
4. retrieval filtering.

No retrieval query should run without organization and workspace constraints derived from authenticated access.

---

## 17. Authentication and Authorization

Supabase Auth will be the initial identity provider.

Initial authentication requirements:

- email/password;
- verified email where configured;
- secure session handling;
- logout;
- password reset.

Future authentication may include:

- Google;
- Microsoft;
- SAML/SSO.

Initial roles:

- owner;
- admin;
- member.

More granular roles can be added later.

---

## 18. API Requirements

The API will use a versioned base path:

`/api/v1`

Initial route groups:

```text
/auth
/users
/organizations
/workspaces
/documents
/conversations
/messages
/chat
/feedback
/admin
/health
```

Example routes:

```text
GET    /api/v1/me

POST   /api/v1/organizations
GET    /api/v1/organizations/{organization_id}

POST   /api/v1/workspaces
GET    /api/v1/workspaces
GET    /api/v1/workspaces/{workspace_id}

POST   /api/v1/documents
GET    /api/v1/documents
GET    /api/v1/documents/{document_id}
DELETE /api/v1/documents/{document_id}

POST   /api/v1/chat
GET    /api/v1/conversations
GET    /api/v1/conversations/{conversation_id}
DELETE /api/v1/conversations/{conversation_id}

POST   /api/v1/messages/{message_id}/feedback

GET    /health
GET    /ready
```

Exact contracts must be documented in the API specification before frontend implementation depends on them.

---

## 19. Chat Requirements

The chat experience must support:

- workspace-scoped conversations;
- streamed responses;
- previous message context;
- grounded retrieval;
- citations;
- markdown;
- code blocks;
- error recovery;
- retry;
- feedback.

The system must store both the final answer and the evidence used to produce it.

This is important for debugging and evaluation.

---

## 20. Citation Requirements

Each answer source should be capable of exposing:

- document ID;
- document title;
- page;
- section;
- chunk ID;
- excerpt;
- relevance/reranking metadata where appropriate.

Citations must correspond only to evidence actually supplied to the generation model.

---

## 21. Conversation Context

Follow-up questions should understand recent conversation context.

However, conversation history must not blindly be appended without limits.

The implementation should support:

- recent message window;
- future conversation summarization;
- clear separation between conversation memory and retrieved company evidence.

Answers about company facts should remain grounded in retrieved knowledge.

---

## 22. Frontend Pages

Initial routes should include:

```text
/
 /login
 /signup

/app
/app/onboarding

/app/[organization]
/app/[organization]/workspaces
/app/[organization]/workspaces/[workspace]
/app/[organization]/workspaces/[workspace]/chat
/app/[organization]/workspaces/[workspace]/documents

/app/[organization]/members
/app/[organization]/settings

/app/profile
```

Route structure may be refined during frontend architecture design.

---

## 23. Primary UI Layout

Desktop application:

```text
+------------------------------------------------------+
| Bismark AI                             Profile        |
+----------------+-------------------------------------+
|                |                                     |
| Workspaces     |          Current workspace          |
|                |                                     |
| HR             |          Chat / Documents           |
| Engineering    |                                     |
| Sales          |                                     |
|                |                                     |
| Conversations  |                                     |
|                |                                     |
| Settings       |                                     |
+----------------+-------------------------------------+
```

The visual design should be modern, restrained, enterprise-friendly, and optimized for knowledge work.

---

## 24. Document UX

The document manager should display:

- filename;
- type;
- upload date;
- owner;
- processing state;
- chunk count where useful;
- actions.

Status should update without requiring the user to repeatedly reload the page.

---

## 25. Streaming

AI responses should stream from the backend.

The system should support a transport such as:

- Server-Sent Events; or
- streaming HTTP.

The frontend must handle:

- partial tokens;
- cancellation;
- timeout;
- API errors;
- completion metadata.

---

## 26. Security Requirements

Minimum security requirements:

- HTTPS only in production;
- secure secrets management;
- no service-role Supabase key exposed to the browser;
- authorization on every protected backend route;
- tenant-scoped database access;
- tenant-scoped retrieval;
- signed/private document URLs where required;
- file size restrictions;
- MIME validation;
- upload validation;
- API rate limiting;
- CORS restrictions;
- security headers;
- structured audit logs;
- dependency updates;
- container image updates;
- database backups;
- VPS firewall;
- SSH key authentication;
- least privilege.

---

## 27. Privacy Requirements

Documents uploaded by organizations are private organization data.

Bismark AI must:

- avoid making documents public by default;
- avoid cross-tenant training or reuse;
- avoid logging full sensitive documents unnecessarily;
- minimize third-party disclosure;
- document which external AI providers receive retrieved context;
- support future configurable data-processing modes.

---

## 28. Observability

The MVP should include:

- structured backend logs;
- request IDs;
- job IDs;
- document processing logs;
- RAG timing information;
- provider failure logging;
- token/usage measurement where exposed;
- health endpoints.

Future versions may integrate a dedicated LLM observability platform.

---

## 29. Evaluation

Bismark AI must eventually maintain a repeatable evaluation dataset.

The initial codebase should therefore make it possible to capture:

- user question;
- retrieved chunks;
- reranked chunks;
- generated answer;
- citations;
- model used;
- embedding model;
- user feedback;
- latency.

A future evaluation suite should test:

- retrieval relevance;
- answer correctness;
- citation correctness;
- groundedness;
- hallucination rate;
- latency;
- provider cost.

---

## 30. Failure Handling

### Upload Failure

The document becomes `failed` with a user-readable state.

### Parser Failure

The system stores the error and permits retry.

### Embedding Provider Failure

The job should retry according to a bounded retry policy.

### LLM Failure

The UI should provide a retry action without duplicating user messages incorrectly.

### Supabase Failure

The system should return a controlled error and never silently lose state.

---

## 31. Performance Targets

Initial targets rather than contractual SLAs:

- normal API request latency: under 500 ms where no external AI operation is required;
- chat first-token latency: target under 3 seconds when providers permit;
- document upload API response: near-immediate after validation/storage/queueing;
- ingestion: asynchronous;
- workspace navigation: responsive on desktop and mobile;
- retrieval: designed to remain fast as knowledge bases grow.

---

## 32. Scalability Strategy

V1 intentionally avoids premature infrastructure complexity.

Initial:

```text
1 API container
1 worker container
1 Redis container
1 Caddy container
```

Future scaling may introduce:

- multiple API replicas;
- multiple workers;
- managed Redis;
- separate ingestion service;
- dedicated search infrastructure;
- knowledge graph retrieval;
- model gateway;
- observability platform;
- GPU inference infrastructure.

Scaling must happen in response to measured bottlenecks.

---

## 33. Repository Structure

Recommended monorepo:

```text
bismark-ai/
|
├── apps/
│   ├── web/
│   │   └── Next.js application
│   │
│   └── api/
│       └── FastAPI application
|
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── API.md
│   ├── RAG.md
│   ├── SECURITY.md
│   ├── DEPLOYMENT.md
│   ├── TESTING.md
│   └── decisions/
|
├── infra/
│   ├── docker/
│   └── caddy/
|
├── scripts/
|
├── PRD.md
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## 34. Engineering Conventions

The project should enforce:

- typed interfaces;
- small cohesive modules;
- explicit domain boundaries;
- migrations for all database changes;
- no schema changes directly in production;
- tests for permissions;
- tests for tenant isolation;
- tests for retrieval filtering;
- automated formatting;
- automated linting;
- meaningful commit history;
- environment configuration through validated settings;
- no secrets committed to Git.

Agentic coding tools must follow the repository documentation rather than inventing new architecture independently.

---

## 35. Proposed Backend Modules

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

The provider abstraction is important because infrastructure dependencies may change.

---

## 36. Proposed Frontend Domains

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
├── lib/
├── hooks/
└── types/
```

---

## 37. Environment Configuration

Expected configuration categories:

```text
APP_ENV
APP_URL
API_URL

SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET

DATABASE_URL

VOYAGE_API_KEY
VOYAGE_EMBEDDING_MODEL
VOYAGE_RERANK_MODEL

LLM_PROVIDER
LLM_MODEL
LLM_API_KEY

REDIS_URL

CORS_ORIGINS
LOG_LEVEL
```

`.env.example` must contain names and descriptions but no real secrets.

---

## 38. Initial Product Milestones

### Milestone 0 — Repository Foundation

Deliver:

- repository structure;
- frontend skeleton;
- backend skeleton;
- configuration;
- local Docker services;
- CI baseline;
- documentation baseline.

### Milestone 1 — Identity and Tenancy

Deliver:

- Supabase Auth;
- profiles;
- organizations;
- memberships;
- workspaces;
- authorization.

### Milestone 2 — Document Management

Deliver:

- uploads;
- Supabase Storage;
- document metadata;
- processing states;
- worker queue.

### Milestone 3 — Ingestion

Deliver:

- parsing;
- chunking;
- Voyage embeddings;
- pgvector storage;
- retries.

### Milestone 4 — Retrieval

Deliver:

- vector search;
- keyword search;
- hybrid retrieval;
- metadata filtering;
- Voyage reranking.

### Milestone 5 — AI Chat

Deliver:

- workspace chat;
- streaming;
- conversations;
- answer generation;
- citations.

### Milestone 6 — Product Completion

Deliver:

- document UX;
- conversation history;
- feedback;
- member management;
- settings;
- error states.

### Milestone 7 — Production Hardening

Deliver:

- security review;
- tenant-isolation tests;
- backups;
- monitoring;
- rate limiting;
- deployment;
- smoke tests.

---

## 39. MVP Acceptance Criteria

The MVP is considered functionally complete when:

1. a new user can create an account;
2. the user can create an organization;
3. the user can create a workspace;
4. an authorized user can upload a document;
5. the document is stored in Supabase Storage;
6. processing occurs asynchronously;
7. document chunks are stored with Voyage embeddings;
8. users can ask questions against a workspace;
9. retrieval is restricted to authorized workspace content;
10. hybrid retrieval and reranking are used;
11. the answer streams to the frontend;
12. answers show supporting citations;
13. conversations persist;
14. users can provide feedback;
15. authorized users can delete documents;
16. tenant-isolation tests pass;
17. production deployment uses HTTPS;
18. secrets are not exposed to the frontend;
19. a failed document job can be identified and retried;
20. critical functionality is documented.

---

## 40. Initial Success Metrics

Early product metrics should include:

- number of organizations;
- number of active workspaces;
- documents uploaded;
- successful ingestion rate;
- median ingestion time;
- questions per active user;
- retrieval latency;
- first-token latency;
- answer completion latency;
- positive/negative feedback ratio;
- citation usage;
- failed query rate;
- failed ingestion rate.

Later versions should add formal RAG quality metrics.

---

## 41. Future Roadmap

After V1 stability, potential expansion areas include:

### Knowledge Intelligence

- knowledge graphs;
- entity relationships;
- temporal knowledge;
- organizational memory;
- cross-document reasoning.

### Connectors

- Google Drive;
- SharePoint;
- OneDrive;
- Dropbox;
- Slack;
- Notion;
- Confluence;
- email;
- websites.

### Multimodality

- audio transcription;
- meeting knowledge;
- call-center recordings;
- images;
- presentations;
- scanned documents.

### Enterprise

- SSO;
- SCIM;
- custom retention;
- compliance controls;
- private model deployment;
- dedicated tenant infrastructure;
- advanced audit.

### AI Capabilities

- specialized agents;
- workflow execution;
- research;
- report generation;
- proactive knowledge insights;
- evaluation-driven model routing.

---

## 42. Non-Goals

Bismark AI is not initially intended to be:

- a general-purpose ChatGPT clone;
- an AI coding assistant;
- an unrestricted autonomous agent platform;
- a local-model hosting platform;
- a replacement for primary business databases;
- an enterprise integration platform.

Its core product is trusted organizational knowledge access.

---

## 43. Decision Summary

The initial Bismark AI architecture is intentionally opinionated:

- **Next.js on Vercel** for the user interface.
- **FastAPI on Hostinger VPS** for application logic and RAG orchestration.
- **Docker Compose** for backend deployment.
- **Supabase PostgreSQL** for application data.
- **Supabase Auth** for identity.
- **Supabase Storage** for original documents.
- **Supabase pgvector** for vector retrieval.
- **Voyage AI** for embeddings and reranking.
- **PostgreSQL full-text search + pgvector** for hybrid retrieval.
- **Docling or Unstructured** for document parsing.
- **Redis + worker** for asynchronous ingestion.
- **External LLM API** for generation.
- **Caddy** for reverse proxy and HTTPS.

The architecture should remain a modular monolith until usage demonstrates a need to split services.

---

## 44. Documentation Authority

This PRD defines **what Bismark AI is expected to become and what V1 must deliver**.

It does not replace lower-level technical documentation.

The canonical documentation authority order is:

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

`PROJECT_STATE.md` reports current implementation state; it does not override architectural decisions.

Agents must not silently contradict higher-authority documents. If documentation conflicts, the discrepancy must be surfaced before a structural change is made.

---

## 45. Definition of Done for V1

Bismark AI V1 is done when a real organization can securely:

**sign up → create a workspace → upload internal documents → wait for processing → ask questions → receive source-grounded answers with citations → continue the conversation → manage the underlying documents and users**

without engineering intervention during normal operation.

That workflow is the primary product contract for the initial release.
