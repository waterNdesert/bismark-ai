# ADR-001 — Use Supabase as the Core Managed Data Platform

**Project:** Bismark AI  
**ADR ID:** ADR-001  
**Title:** Use Supabase for PostgreSQL, Auth, Storage, and pgvector  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 architecture

---

## 1. Context

Bismark AI requires a durable data platform that can support:

- relational application data;
- authentication;
- private document storage;
- vector embeddings;
- PostgreSQL full-text search;
- row-level security;
- multi-tenant data isolation;
- development and production environments.

The project also needs to move quickly without introducing unnecessary infrastructure complexity.

Several approaches were considered:

1. self-host PostgreSQL on the Hostinger VPS;
2. use a managed PostgreSQL provider plus separate auth and object storage;
3. use a separate vector database such as Qdrant, Weaviate, or Pinecone;
4. use Supabase as an integrated managed platform for PostgreSQL, Auth, Storage, and pgvector.

The Bismark AI architecture already uses:

- Hostinger KVM 2 for application compute;
- Vercel for frontend hosting;
- Voyage AI for embeddings and reranking;
- an external LLM provider for answer generation.

The goal is to keep the application layer custom while minimizing operational burden for infrastructure that does not create direct product differentiation.

---

## 2. Decision

Bismark AI V1 will use **Supabase** as the primary managed data platform.

Supabase will provide:

```text
PostgreSQL
Supabase Auth
Supabase Storage
pgvector
```

PostgreSQL will remain the source of truth for application state.

Supabase Storage will hold original uploaded documents.

pgvector will store document chunk embeddings.

PostgreSQL full-text search will provide lexical retrieval.

Supabase Auth will provide user identity and session management.

---

## 3. Architectural Role

Supabase is infrastructure, not the product.

Bismark AI owns:

- organizations;
- memberships;
- workspaces;
- authorization policy;
- documents;
- conversations;
- messages;
- citations;
- feedback;
- usage;
- audit;
- retrieval orchestration;
- RAG logic;
- model/provider abstractions.

Supabase should not become a replacement for the FastAPI application layer.

---

## 4. Reasons for This Decision

### 4.1 Reduced Operational Complexity

Using Supabase avoids operating production PostgreSQL directly on the application VPS.

This reduces responsibility for:

- database patching;
- replication;
- connection exposure;
- local disk durability;
- database failover;
- database backup infrastructure.

---

### 4.2 Consolidated Data Platform

Supabase provides multiple required capabilities in one platform:

```text
database
+
authentication
+
storage
+
vector support
```

This avoids combining several unrelated services during V1.

---

### 4.3 PostgreSQL Remains the Core

Bismark AI benefits from PostgreSQL because it can support:

- relational data;
- transactions;
- foreign keys;
- JSONB;
- full-text search;
- pgvector;
- RLS;
- SQL functions;
- mature indexing.

This allows both application state and retrieval metadata to remain coherent.

---

### 4.4 Multi-Tenancy Support

Supabase/PostgreSQL supports:

- explicit organization IDs;
- workspace IDs;
- relational ownership;
- RLS;
- indexed tenant filters.

This fits Bismark AI's security model.

---

### 4.5 Compatible with Hybrid Retrieval

Bismark AI needs both:

- semantic retrieval;
- keyword retrieval.

Using:

```text
pgvector
+
PostgreSQL FTS
```

keeps the V1 retrieval stack inside one database.

---

### 4.6 Faster V1 Delivery

The project can focus engineering effort on:

- ingestion;
- chunking;
- retrieval;
- reranking;
- citations;
- permissions;
- user experience;

rather than maintaining database infrastructure.

---

## 5. Alternatives Considered

### 5.1 PostgreSQL on Hostinger VPS

#### Benefits

- full operational control;
- potentially lower direct service cost;
- fewer managed-provider dependencies.

#### Drawbacks

- more operational burden;
- local database competes with API/parser/worker for CPU and RAM;
- more complex backup/recovery;
- higher risk from VPS failure;
- less separation between compute and durable state.

#### Decision

Rejected for V1.

The VPS should remain primarily an application compute layer.

---

### 5.2 Separate Managed PostgreSQL + Separate Auth + Separate Storage

#### Benefits

- provider specialization;
- ability to choose best-of-breed services.

#### Drawbacks

- more services;
- more credentials;
- more configuration;
- more integration work;
- more failure boundaries.

#### Decision

Rejected for V1 because the additional complexity is not justified.

---

### 5.3 Dedicated Vector Database

Examples:

- Qdrant;
- Weaviate;
- Pinecone.

#### Benefits

- vector-specialized capabilities;
- potentially better scaling at very large vector volumes.

#### Drawbacks

- another production service;
- duplicated metadata;
- more complex tenant filtering;
- more synchronization;
- additional cost;
- more operational surface area.

#### Decision

Rejected for V1.

pgvector is sufficient for the initial scale and keeps permissions close to relational data.

---

### 5.4 Complete Third-Party RAG Application

Examples might include all-in-one RAG platforms.

#### Benefits

- fast initial prototype;
- prebuilt user interface;
- prebuilt ingestion.

#### Drawbacks

- Bismark AI would inherit another product's architecture;
- weaker ownership of tenancy;
- weaker control over citations;
- harder product differentiation;
- harder future customization;
- risk of making Bismark AI a wrapper around another application.

#### Decision

Rejected as the core production architecture.

Third-party systems may be used for benchmarking or reference only.

---

## 6. Consequences

### Positive

Bismark AI gains:

- managed PostgreSQL;
- managed identity;
- managed object storage;
- pgvector support;
- easier environment provisioning;
- reduced VPS state;
- simpler recovery from VPS loss;
- strong PostgreSQL feature set.

---

### Negative

Bismark AI becomes dependent on Supabase for several critical capabilities.

Potential concerns:

- provider outage affects multiple subsystems;
- migration away may require significant work;
- service-role key is highly privileged;
- RLS must be carefully designed;
- pricing may grow with usage.

---

## 7. Mitigations

To reduce provider lock-in:

- use SQLAlchemy for application data access;
- keep business logic inside FastAPI;
- keep provider-specific code isolated;
- use internal storage abstractions where practical;
- avoid relying excessively on proprietary Supabase-only behavior;
- store canonical schema/migrations in the repository;
- maintain export/backup procedures.

Supabase Auth and Storage are still provider-specific, so replacement would require planned migration.

---

## 8. Security Consequences

Supabase introduces privileged credentials.

Most important:

```text
SUPABASE_SERVICE_ROLE_KEY
```

Rules:

- backend only;
- never exposed to browser;
- never stored in Git;
- never logged;
- rotate immediately if exposed.

RLS must be enabled where appropriate.

Backend authorization remains mandatory even when service-role access is used.

---

## 9. Data Ownership

Bismark AI owns its data model.

Supabase hosts the data but does not define the Bismark AI domain.

Canonical data model remains documented in:

```text
docs/DATABASE.md
```

---

## 10. Storage Decision

Original user documents will be stored in a private Supabase Storage bucket.

Recommended structure:

```text
organization_id/
workspace_id/
document_id/
original_filename
```

Files must not be publicly accessible by default.

---

## 11. Vector Decision

Document embeddings will be stored in PostgreSQL using pgvector.

This means:

```text
document metadata
+
tenant IDs
+
workspace IDs
+
content
+
embedding
```

remain tightly connected.

---

## 12. Full-Text Search Decision

PostgreSQL full-text search will provide lexical retrieval.

This avoids adding Elasticsearch or another search service in V1.

---

## 13. Authentication Decision

Supabase Auth provides identity.

Bismark AI still owns authorization.

Conceptually:

```text
Supabase Auth
    |
    v
Who is this user?

Bismark AI
    |
    v
What can this user access?
```

---

## 14. Failure Implications

A Supabase outage may affect:

- login;
- database access;
- file access;
- vector retrieval.

The application must fail safely and must not fabricate successful operations during such outages.

---

## 15. Backup Implications

Database backup and storage backup must be considered separately.

A PostgreSQL backup does not automatically guarantee backup of source files in Storage.

Backup/recovery procedures must remain documented in:

```text
docs/DEPLOYMENT.md
```

---

## 16. Scaling Implications

Supabase can support V1 and early growth.

If future workload exceeds the selected plan or architecture, options include:

- larger Supabase plan;
- dedicated PostgreSQL;
- read replicas;
- separate vector infrastructure.

Any migration away requires a new ADR.

---

## 17. Migration Away

If Bismark AI later leaves Supabase:

- PostgreSQL data should be exportable;
- SQLAlchemy/domain logic should remain reusable;
- provider-specific auth/storage code should be replaced behind boundaries;
- object storage migration must be planned;
- user identity migration requires special care.

---

## 18. Implementation Requirements

Agents implementing this decision must:

- use Supabase PostgreSQL;
- enable pgvector;
- configure private storage;
- integrate Supabase Auth;
- keep service credentials backend-only;
- write migrations;
- implement RLS;
- preserve FastAPI as the application authority.

---

## 19. Prohibited Actions

Without a replacement ADR, do not:

- self-host production PostgreSQL on the VPS;
- introduce Qdrant;
- introduce Weaviate;
- introduce Pinecone;
- introduce a second primary application database;
- replace Supabase Auth;
- replace Supabase Storage;
- make storage public.

---

## 20. Review Triggers

Revisit this decision if:

- Supabase cost becomes materially problematic;
- regulatory/data-residency requirements demand another deployment;
- database scale exceeds reasonable Supabase limits;
- enterprise customers require dedicated infrastructure;
- provider outages create unacceptable availability risk;
- vector workload clearly requires specialized infrastructure.

---

## 21. Status

**Accepted**

This decision is authoritative for Bismark AI V1.

Any agent or engineer proposing to reverse it must:

1. explain the problem;
2. provide evidence;
3. document alternatives;
4. create a superseding ADR;
5. obtain explicit approval before implementation.
