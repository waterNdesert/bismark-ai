# ROADMAP.md — Bismark AI Product and Engineering Roadmap

**Project:** Bismark AI  
**Document Type:** Canonical Delivery Roadmap  
**Status:** V1 Build Sequence  
**Version:** 1.0  
**Audience:** Product, Engineering, AI/RAG, DevOps, QA, Security, and Agentic Coding Systems

---

## 1. Purpose

This document defines the ordered delivery plan for Bismark AI.

It exists to prevent the project from becoming distracted by advanced features before the core product is stable.

It defines:

- what should be built first;
- what should wait;
- milestone dependencies;
- exit criteria;
- production-readiness gates;
- future expansion areas;
- what agents should not implement yet.

This roadmap must remain consistent with:

- `PRD.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/DATABASE.md`
- `docs/API.md`
- `docs/RAG.md`
- `docs/SECURITY.md`
- `docs/DEPLOYMENT.md`
- `docs/TESTING.md`

---

## 2. Product Goal

The first meaningful release of Bismark AI must let a real organization securely complete this workflow:

```text
sign up
→ create organization
→ create workspace
→ upload documents
→ wait for processing
→ ask questions
→ receive grounded answers
→ inspect citations
→ continue the conversation
→ manage users and documents
```

Everything in V1 exists to make that workflow reliable.

---

## 3. Roadmap Principle

The project should follow this order:

```text
foundation
→ identity
→ tenancy
→ documents
→ ingestion
→ retrieval
→ reranking
→ chat
→ citations
→ permissions
→ testing
→ deployment
→ evaluation
→ product polish
```

Do not reverse this order without a documented reason.

---

# PHASE 0 — REPOSITORY FOUNDATION

## 4. Objective

Create a clean, understandable, agent-friendly repository.

## 5. Deliverables

Create:

```text
apps/web
apps/api
docs
infra
scripts
tests
evals
```

Add:

```text
README.md
PRD.md
AGENTS.md
PROJECT_STATE.md
ROADMAP.md
CHANGELOG.md
CONTRIBUTING.md
.env.example
```

Configure:

- Next.js;
- FastAPI;
- TypeScript;
- Python tooling;
- linting;
- formatting;
- testing;
- Docker;
- CI baseline.

## 6. Exit Criteria

Phase 0 is complete when:

- frontend starts locally;
- backend starts locally;
- Redis starts;
- lint runs;
- tests run;
- environment validation works;
- docs exist;
- CI runs on pull request.

---

# PHASE 1 — SUPABASE FOUNDATION

## 7. Objective

Connect Bismark AI to its durable data platform.

## 8. Deliverables

Configure:

- Supabase project;
- PostgreSQL;
- Supabase Auth;
- Supabase Storage;
- pgvector;
- development environment.

Create initial migrations for:

```text
profiles
organizations
organization_members
workspaces
workspace_members
```

## 9. Security Work

Implement:

- RLS baseline;
- backend database configuration;
- service-role secret handling;
- no privileged key in frontend.

## 10. Exit Criteria

Phase 1 is complete when:

- migrations reproduce schema;
- user profile can be created;
- pgvector is enabled;
- private storage bucket exists;
- backend can connect;
- frontend can authenticate.

---

# PHASE 2 — AUTHENTICATION AND TENANCY

## 11. Objective

Make organizations and workspaces real product boundaries.

## 12. Deliverables

Implement:

- signup;
- login;
- logout;
- password reset;
- `/me`;
- organization creation;
- organization listing;
- organization membership;
- workspace creation;
- workspace listing;
- workspace access.

## 13. Required Tests

Test:

- unauthenticated access denied;
- cross-organization access denied;
- workspace restriction;
- role enforcement.

## 14. Exit Criteria

A user can:

```text
register
→ create organization
→ create workspace
→ reopen application
→ still see authorized workspace
```

---

# PHASE 3 — DOCUMENT MANAGEMENT

## 15. Objective

Allow authorized users to upload and manage private knowledge sources.

## 16. Deliverables

Implement:

- document metadata table;
- file validation;
- private Supabase Storage upload;
- document listing;
- processing status;
- deletion;
- signed source access.

Document states:

```text
uploaded
queued
processing
ready
failed
deleting
deleted
```

## 17. Required Security

Enforce:

- workspace upload permission;
- private bucket;
- server-controlled storage paths;
- file-size limits;
- MIME validation.

## 18. Exit Criteria

Authorized user can upload a source and see:

```text
queued
```

without parsing occurring inside the request.

---

# PHASE 4 — BACKGROUND PROCESSING

## 19. Objective

Create reliable asynchronous processing.

## 20. Deliverables

Implement:

- Redis;
- worker;
- ingestion job model;
- retries;
- worker health;
- temp file cleanup;
- processing timestamps.

## 21. Required Behaviors

The worker must:

```text
receive document ID
→ load authoritative metadata
→ process
→ update durable status
```

Do not send full binary document through Redis.

## 22. Exit Criteria

Document jobs survive normal application request boundaries and failures are visible.

---

# PHASE 5 — DOCUMENT PARSING

## 23. Objective

Convert uploaded knowledge into structured internal content.

## 24. Deliverables

Implement:

```text
DocumentParser abstraction
```

Choose:

- Docling; or
- Unstructured.

Support initially:

- PDF;
- DOCX;
- TXT;
- Markdown;
- HTML.

## 25. Preserve

Where available:

- title;
- heading;
- section;
- paragraph;
- list;
- table;
- page number.

## 26. Exit Criteria

Representative documents are parsed into stable normalized elements.

---

# PHASE 6 — CHUNKING AND INDEXING

## 27. Objective

Turn normalized documents into retrieval-ready knowledge units.

## 28. Deliverables

Implement:

- structure-aware chunking;
- token limits;
- overlap;
- metadata;
- processing versions;
- `document_chunks`.

Each chunk contains:

```text
organization_id
workspace_id
document_id
processing_version
chunk_index
content
page_number
section_title
heading
metadata
```

## 29. Exit Criteria

Documents produce stable, traceable chunks without naive fixed-character splitting as the only method.

---

# PHASE 7 — VOYAGE EMBEDDINGS

## 30. Objective

Enable semantic retrieval.

## 31. Deliverables

Implement:

```text
EmbeddingProvider
VoyageEmbeddingProvider
```

Add:

- batching;
- retries;
- rate-limit handling;
- model configuration;
- vector persistence;
- vector index.

## 32. Exit Criteria

A processed document has valid embeddings for all active searchable chunks.

---

# PHASE 8 — KEYWORD SEARCH

## 33. Objective

Support exact and lexical queries.

## 34. Deliverables

Implement PostgreSQL full-text search.

Search should work for:

- names;
- IDs;
- codes;
- acronyms;
- exact phrases;
- dates;
- technical strings.

## 35. Exit Criteria

A query such as:

```text
POLICY-HR-2026-04
```

retrieves the correct chunk.

---

# PHASE 9 — HYBRID RETRIEVAL

## 36. Objective

Combine semantic and lexical strengths.

## 37. Deliverables

Implement:

```text
vector search
+
keyword search
+
candidate deduplication
+
fusion
```

Preferred initial fusion:

```text
Reciprocal Rank Fusion
```

## 38. Security Requirement

All retrieval must be scoped before ranking by:

```text
organization
workspace
document state
processing version
```

## 39. Exit Criteria

Hybrid search performs correctly on both semantic and exact-match evaluation cases.

---

# PHASE 10 — VOYAGE RERANKING

## 40. Objective

Improve evidence quality before generation.

## 41. Deliverables

Implement:

```text
RerankProvider
VoyageRerankProvider
```

Flow:

```text
20–40 candidates
→ reranker
→ 5–10 final evidence chunks
```

## 42. Exit Criteria

Reranking improves representative retrieval examples and preserves source mapping.

---

# PHASE 11 — CONVERSATIONS

## 43. Objective

Create persistent workspace-scoped chat sessions.

## 44. Deliverables

Implement:

```text
conversations
messages
```

Support:

- create;
- list;
- rename;
- delete/archive;
- recent context.

## 45. Exit Criteria

Users can leave and return to a conversation with history intact.

---

# PHASE 12 — CONTEXT BUILDER

## 46. Objective

Create controlled LLM input.

## 47. Deliverables

Implement:

- evidence serialization;
- source labels;
- conversation window;
- token budgeting;
- deduplication;
- prompt versioning.

Prompt sections should clearly separate:

```text
SYSTEM
CONVERSATION
EVIDENCE
QUESTION
```

## 48. Exit Criteria

The LLM receives only bounded, authorized, relevant context.

---

# PHASE 13 — LLM GENERATION

## 49. Objective

Generate grounded answers.

## 50. Deliverables

Implement:

```text
LLMProvider
```

with configurable provider/model.

Support:

- streaming;
- timeouts;
- failure handling;
- grounded system prompt.

## 51. Exit Criteria

The system streams answers and fails safely when generation provider fails.

---

# PHASE 14 — CITATIONS

## 52. Objective

Make answers verifiable.

## 53. Deliverables

Implement:

```text
message_sources
source labels
citation validation
citation rendering
```

Each source should expose:

- document;
- page;
- section;
- excerpt.

## 54. Exit Criteria

Every rendered citation maps to final evidence actually supplied to the LLM.

---

# PHASE 15 — NO-EVIDENCE AND CONFLICT HANDLING

## 55. Objective

Prevent confident hallucination.

## 56. Deliverables

Implement behavior for:

- no relevant evidence;
- weak evidence;
- conflicting documents;
- unsupported questions.

## 57. Exit Criteria

The system can explicitly say it lacks enough workspace evidence instead of inventing an answer.

---

# PHASE 16 — MEMBER MANAGEMENT

## 58. Objective

Complete basic team administration.

## 59. Deliverables

Implement:

- invites;
- member listing;
- member removal;
- organization roles;
- workspace membership;
- workspace roles.

## 60. Exit Criteria

Owner/admin can manage access without engineering intervention.

---

# PHASE 17 — FEEDBACK

## 61. Objective

Capture answer quality signals.

## 62. Deliverables

Implement:

- positive feedback;
- negative feedback;
- optional comment;
- feedback update/delete.

## 63. Exit Criteria

Feedback is persisted and linked to the assistant message.

---

# PHASE 18 — AUDIT AND USAGE

## 64. Objective

Create operational traceability.

## 65. Deliverables

Implement:

- audit logs;
- usage events;
- provider usage;
- upload events;
- chat usage;
- role-change events.

## 66. Exit Criteria

Important administrative actions are traceable.

---

# PHASE 19 — FRONTEND PRODUCT POLISH

## 67. Objective

Turn the technical system into a usable SaaS product.

## 68. Deliverables

Polish:

- onboarding;
- navigation;
- workspace switcher;
- documents page;
- processing states;
- chat;
- source cards;
- empty states;
- error states;
- settings;
- responsive layout.

## 69. Exit Criteria

A non-technical user can complete the primary workflow without developer assistance.

---

# PHASE 20 — SECURITY HARDENING

## 70. Objective

Verify production trust boundaries.

## 71. Deliverables

Complete:

- RLS review;
- cross-tenant tests;
- CORS;
- rate limiting;
- signed URLs;
- secret review;
- parser safety;
- Docker hardening;
- audit review;
- dependency review.

## 72. Release Blockers

Do not ship with:

- cross-tenant exposure;
- public private documents;
- service-role key exposure;
- unscoped retrieval;
- missing privileged-route authorization.

---

# PHASE 21 — TEST AUTOMATION

## 73. Objective

Make regressions difficult to introduce.

## 74. Deliverables

Automate:

- backend unit tests;
- frontend tests;
- API integration tests;
- RLS tests;
- ingestion tests;
- retrieval tests;
- citation tests;
- E2E;
- security regression.

## 75. Exit Criteria

Critical tests run in CI and block merge/release.

---

# PHASE 22 — STAGING

## 76. Objective

Validate production topology before launch.

## 77. Deliverables

Deploy:

- staging frontend;
- staging backend;
- staging Supabase;
- Voyage test configuration;
- LLM test configuration.

## 78. Exit Criteria

Full workflow succeeds in staging.

---

# PHASE 23 — PRODUCTION DEPLOYMENT

## 79. Objective

Launch Bismark AI V1.

## 80. Deliverables

Deploy:

```text
Next.js -> Vercel
FastAPI -> Hostinger KVM 2
Worker -> Hostinger KVM 2
Redis -> Hostinger KVM 2
Caddy -> Hostinger KVM 2
Supabase -> managed
Voyage -> managed
LLM -> external
```

Configure:

- DNS;
- SSL;
- firewall;
- backups;
- logs;
- health checks.

## 81. Exit Criteria

Production smoke test passes.

---

# PHASE 24 — RAG EVALUATION

## 82. Objective

Make retrieval quality measurable.

## 83. Deliverables

Create held-out evaluation dataset.

Include:

- exact lookup;
- semantic paraphrase;
- multi-document;
- follow-up;
- acronym;
- unanswerable;
- conflicting source;
- cross-workspace case.

Measure:

- Recall@K;
- MRR;
- hit rate;
- citation correctness;
- groundedness;
- latency.

## 84. Exit Criteria

RAG changes can be compared objectively.

---

# PHASE 25 — OBSERVABILITY

## 85. Objective

Improve debugging and production visibility.

## 86. Deliverables

Add:

- structured trace IDs;
- retrieval diagnostics;
- provider latency;
- queue metrics;
- ingestion failures;
- first-token latency;
- model usage.

A dedicated LLM observability platform may be added later if justified.

---

# V1 LAUNCH DEFINITION

## 87. V1 Is Ready When

A customer can securely:

```text
create account
create organization
create workspace
invite member
upload document
wait for processing
ask question
receive grounded streamed answer
inspect citation
continue conversation
manage document
provide feedback
```

and:

- tenant isolation tests pass;
- backups exist;
- deployment is repeatable;
- production secrets are secure;
- no critical release blockers remain.

---

# POST-V1 — NEAR-TERM ENHANCEMENTS

## 88. Phase 26 — Better Document Intelligence

Potential:

- improved table extraction;
- scanned PDF OCR;
- PPTX;
- spreadsheets;
- richer metadata;
- document preview;
- chunk visual debugging.

---

## 89. Phase 27 — Search and Knowledge UX

Potential:

- standalone search;
- source browsing;
- filters;
- document tags;
- saved queries;
- suggested questions.

---

## 90. Phase 28 — Admin Analytics

Potential:

- active users;
- question volume;
- document usage;
- failed queries;
- feedback trends;
- provider cost;
- top knowledge gaps.

---

## 91. Phase 29 — Knowledge Quality

Potential:

- stale document detection;
- duplicate detection;
- conflicting-source alerts;
- low-confidence answer reports;
- unanswered-question dashboard.

---

# FUTURE — CONNECTORS

## 92. Phase 30 — Connector Framework

Build a canonical source adapter layer.

Then support selectively:

- Google Drive;
- OneDrive;
- SharePoint;
- Dropbox;
- Notion;
- Confluence;
- websites;
- Slack;
- email.

Do not build every connector at once.

---

# FUTURE — ADVANCED AI

## 93. Knowledge Graph

Only after hybrid RAG is measured and stable.

Potential:

```text
vector
+
keyword
+
graph
```

Requires ADR.

---

## 94. Persistent Organizational Memory

Future memory should require:

- provenance;
- tenant scope;
- approval;
- lifecycle;
- deletion.

Do not let the system silently convert conversations into permanent organization truth.

---

## 95. Agentic Workflows

Potential future capabilities:

- report generation;
- research;
- action execution;
- workflow automation.

These require:

- tool permissions;
- audit;
- approval;
- safety boundaries.

Not V1.

---

## 96. Voice and Call Knowledge

Potential:

- call transcription;
- meeting ingestion;
- speech search;
- spoken answers.

Not V1.

---

## 97. Local LLMs

Potential enterprise/private deployment.

Only introduce behind:

```text
LLMProvider
```

Requires cost and infrastructure analysis.

---

# FUTURE — ENTERPRISE

## 98. SSO and SCIM

Potential:

- Microsoft Entra ID;
- Google Workspace;
- SAML;
- SCIM.

Not required for initial V1.

---

## 99. Compliance Features

Potential:

- configurable retention;
- legal hold;
- audit export;
- access review;
- data residency;
- DLP;
- customer-managed keys.

---

## 100. Dedicated Tenant Deployment

Potential for large enterprise customers.

Possible:

```text
dedicated database
dedicated storage
dedicated compute
private model endpoint
```

Requires separate deployment architecture.

---

# INFRASTRUCTURE EVOLUTION

## 101. KVM 2

Start here.

Use while:

- CPU acceptable;
- memory acceptable;
- worker queue healthy;
- latency acceptable.

---

## 102. KVM 4

Upgrade when measured workload requires:

- more parser concurrency;
- more API capacity;
- more simultaneous streams.

---

## 103. Managed Redis

Consider when:

- Redis availability becomes operational burden;
- multiple VPS nodes exist;
- queue durability requirements increase.

---

## 104. Separate Worker Host

Consider when document ingestion causes user-facing API resource pressure.

---

## 105. Microservices

Do not introduce until a clear service boundary has:

- independent scaling need;
- independent ownership need;
- reliability need.

---

# WHAT NOT TO BUILD YET

## 106. Explicitly Deferred

Do not build during V1 unless requirements change:

- Kubernetes;
- Kafka;
- RabbitMQ;
- Qdrant;
- Weaviate;
- Pinecone;
- Elasticsearch;
- local GPU inference;
- fine-tuning;
- autonomous multi-agent framework;
- graph database;
- browser automation;
- native mobile app;
- voice assistant;
- full billing engine;
- plugin marketplace;
- dozens of integrations;
- custom model training.

---

# AGENTIC DEVELOPMENT RULES

## 107. Agents Must Follow Current Phase

An agent should not jump from Phase 3 to Phase 30 because a future feature appears useful.

Before implementation:

- read `PROJECT_STATE.md`;
- identify current roadmap phase;
- implement only the requested phase unless explicitly told otherwise.

---

## 108. Phase Completion Reporting

After a phase, update `PROJECT_STATE.md` with:

```text
phase
completed items
tests
known issues
migrations
deployment state
next task
```

---

## 109. Do Not Mark Complete Prematurely

A phase is not complete because:

```text
code exists
```

It is complete when:

```text
code
+
tests
+
security
+
documentation
+
verification
```

are done where applicable.

---

# PRIORITY LABELS

## 110. P0 — Critical

Examples:

- authentication;
- tenant isolation;
- storage privacy;
- retrieval scoping;
- data integrity;
- deployment recovery.

---

## 111. P1 — Required for V1

Examples:

- document management;
- chat;
- citations;
- conversation history;
- feedback;
- member management.

---

## 112. P2 — Post-V1 Important

Examples:

- advanced analytics;
- improved OCR;
- richer admin insights;
- connector framework.

---

## 113. P3 — Future

Examples:

- knowledge graphs;
- autonomous agents;
- voice;
- local models;
- enterprise dedicated deployments.

---

# DELIVERY ESTIMATE

## 114. Rapid MVP Target

With disciplined scope and strong agentic development support, a functional internal MVP can target approximately:

```text
1–2 weeks
```

for the core happy path.

That does not equal production readiness.

---

## 115. Production-Capable V1 Target

A more realistic target for:

- full permissions;
- testing;
- security hardening;
- deployment;
- evaluation;
- polished UX;

is approximately:

```text
3–6 weeks
```

depending on team size, document-parser complexity, provider integration issues, and QA depth.

This is a planning estimate, not a guarantee.

---

# ROADMAP ACCEPTANCE CRITERIA

## 116. Roadmap Is Being Followed Correctly When

1. current phase is documented;
2. agents do not skip foundational work;
3. advanced features remain deferred;
4. every phase has exit criteria;
5. security work happens throughout;
6. testing grows with implementation;
7. deployment begins before final polish;
8. RAG evaluation exists before major optimization;
9. infrastructure scales only after measurement;
10. architectural changes create ADRs.

---

# SUMMARY

## 117. Canonical Build Order

```text
0. Repository
1. Supabase
2. Auth/Tenancy
3. Documents
4. Worker
5. Parsing
6. Chunking
7. Embeddings
8. Keyword Search
9. Hybrid Retrieval
10. Reranking
11. Conversations
12. Context Builder
13. LLM
14. Citations
15. No-Evidence Handling
16. Members
17. Feedback
18. Audit/Usage
19. UX Polish
20. Security Hardening
21. Automated Tests
22. Staging
23. Production
24. RAG Evaluation
25. Observability
```

The roadmap deliberately postpones advanced AI features until Bismark AI can prove one thing extremely well:

```text
securely turn an organization's private documents
into reliable, source-grounded answers.
```

That is the V1 product.
