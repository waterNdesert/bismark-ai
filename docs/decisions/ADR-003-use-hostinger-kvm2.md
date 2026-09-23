# ADR-003 — Use Hostinger KVM 2 for the Initial Backend Compute Layer

**Project:** Bismark AI  
**ADR ID:** ADR-003  
**Title:** Use Hostinger KVM 2 for the Initial Backend Compute Layer  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 deployment architecture

---

## 1. Context

Bismark AI needs a production compute environment for the backend application.

The V1 backend must run:

- FastAPI;
- background worker;
- Redis;
- document parser dependencies;
- temporary document-processing workloads;
- Caddy reverse proxy.

The backend does **not** need to run:

- production PostgreSQL;
- permanent object storage;
- embedding inference;
- reranking inference;
- LLM inference.

Those responsibilities are externalized to:

- Supabase;
- Voyage AI;
- external LLM provider.

The project therefore needs a modest but reliable general-purpose VPS rather than a large machine designed for databases or AI model inference.

Hostinger offers several VPS sizes, including KVM 1, KVM 2, KVM 4, and KVM 8.

For the intended Bismark AI V1 architecture, the key question is:

```text
What is the smallest reasonable VPS that gives enough headroom
for FastAPI, parsing, Redis, worker processes, Docker, and Caddy
without paying prematurely for unused capacity?
```

---

## 2. Decision

Bismark AI V1 will start on:

```text
Hostinger KVM 2
```

with approximately:

```text
2 vCPU
8 GB RAM
100 GB NVMe
8 TB bandwidth
```

The VPS will run:

```text
Caddy
FastAPI
background worker
Redis
document parser dependencies
temporary processing storage
```

The VPS will **not** initially run:

```text
production PostgreSQL
permanent document storage
local embedding models
local reranking models
local LLM inference
```

---

## 3. Why KVM 2

### 3.1 Fits the Actual Workload

The Bismark AI backend is orchestration-heavy, not model-inference-heavy.

The VPS primarily handles:

- HTTP requests;
- authorization;
- API orchestration;
- parsing;
- chunking;
- queueing;
- streaming;
- temporary file handling.

Most compute-intensive AI operations are external.

Therefore, a much larger VPS is not justified initially.

---

### 3.2 More Practical Than KVM 1

KVM 1 provides less CPU and memory headroom.

Bismark AI needs to support multiple co-located services:

```text
Caddy
FastAPI
worker
Redis
parser
Docker daemon
operating system
```

Document parsing can create short-lived CPU and RAM spikes.

KVM 2 gives more practical operating margin.

---

### 3.3 Lower Cost Than Premature KVM 4

KVM 4 would provide more resources, but Bismark AI should scale from measured workload.

Starting with KVM 2 keeps infrastructure cost controlled while preserving a straightforward upgrade path.

---

### 3.4 Good Fit with Externalized State

Critical durable state lives outside the VPS.

This means the server is replaceable.

If the VPS fails:

```text
provision replacement
restore Docker deployment
restore secrets/config
point DNS
restart services
```

The core application data remains in Supabase.

---

## 4. Role of the VPS

The VPS is a compute layer.

It is not the durable data layer.

Conceptually:

```text
Hostinger VPS
    |
    +--> API compute
    +--> worker compute
    +--> Redis
    +--> parser
    +--> reverse proxy

Supabase
    |
    +--> database
    +--> auth
    +--> storage
    +--> vectors

Voyage
    |
    +--> embeddings
    +--> reranking

LLM Provider
    |
    +--> generation
```

---

## 5. Services Running on the VPS

### 5.1 Caddy

Responsibilities:

- HTTPS;
- automatic TLS;
- reverse proxy;
- public API entry point.

---

### 5.2 FastAPI

Responsibilities:

- authentication validation;
- authorization;
- organization/workspace logic;
- document orchestration;
- retrieval orchestration;
- chat;
- citations;
- audit;
- API responses.

---

### 5.3 Background Worker

Responsibilities:

- document retrieval;
- parsing;
- normalization;
- chunking;
- embedding requests;
- indexing;
- retries;
- cleanup.

---

### 5.4 Redis

Responsibilities:

- background job queue;
- transient coordination.

Redis is not the durable source of truth.

---

## 6. What Must Not Run on KVM 2 Initially

Without a new architecture decision, do not add:

- production PostgreSQL;
- Qdrant;
- Weaviate;
- Elasticsearch;
- MinIO;
- local LLM;
- local embedding service;
- local reranker service;
- Kafka;
- RabbitMQ;
- Kubernetes.

These would increase resource pressure and operational complexity.

---

## 7. Alternatives Considered

### 7.1 Hostinger KVM 1

#### Benefits

- lower cost;
- enough for a very small API.

#### Drawbacks

- limited CPU headroom;
- limited memory;
- parser workloads may compete with API;
- less room for worker concurrency.

#### Decision

Not selected.

KVM 2 provides safer baseline capacity.

---

### 7.2 Hostinger KVM 4

#### Benefits

- more CPU;
- more RAM;
- better parsing concurrency;
- more room for growth.

#### Drawbacks

- higher cost;
- likely unnecessary before real load exists.

#### Decision

Deferred.

Upgrade when measurements justify it.

---

### 7.3 Managed Container Platform

Examples could include:

- Render;
- Fly.io;
- Railway;
- cloud container platforms.

#### Benefits

- easier deployments;
- managed runtime;
- less host administration.

#### Drawbacks

- potentially higher recurring cost;
- less control;
- parser/background-worker workloads may be less convenient;
- Bismark AI already has a Hostinger deployment direction.

#### Decision

Not selected for V1.

---

### 7.4 AWS / GCP Compute

#### Benefits

- mature cloud ecosystem;
- strong scaling options;
- managed networking and observability.

#### Drawbacks

- more configuration;
- potentially higher cost;
- more operational complexity than required for initial product.

#### Decision

Not selected for initial V1.

May be revisited for enterprise scale.

---

## 8. Capacity Assumptions

KVM 2 is expected to be sufficient while:

- API traffic is moderate;
- worker concurrency is low;
- document parsing is not continuously saturated;
- external AI services perform model computation;
- database/storage remain external.

---

## 9. Initial Process Model

Recommended:

```text
1 Caddy container
1 API container
1 worker container
1 Redis container
```

The API container may run multiple Python workers later if needed.

Do not increase concurrency blindly.

---

## 10. Resource Contention Risks

The main KVM 2 risk is document parsing.

Large PDFs, OCR, or complex Office documents may consume:

- CPU;
- RAM;
- disk I/O.

Mitigations:

- worker concurrency limit;
- parser timeout;
- file-size limits;
- temporary file cleanup;
- queue backpressure;
- resource monitoring.

---

## 11. Upgrade Triggers

Consider KVM 4 when any of the following becomes persistent:

```text
CPU > 70–80%
memory pressure / swapping
worker queue continuously increasing
parsing delays affect user experience
API latency degrades under ingestion
multiple simultaneous large documents cause failures
```

Use measurements, not assumptions.

---

## 12. Scale-Up Path

The first scale step is vertical:

```text
KVM 2
→ KVM 4
```

This is preferred over premature multi-node architecture.

---

## 13. Scale-Out Path

Only later, if justified:

```text
multiple API replicas
multiple workers
managed Redis
separate worker host
load balancer
```

This requires architecture review.

---

## 14. Storage Strategy

The VPS filesystem is not authoritative storage for source documents.

Original uploads belong in Supabase Storage.

The VPS may use temporary processing files only.

---

## 15. Temporary Files

Temporary parser files should be stored in a controlled path such as:

```text
/tmp/bismark
```

or a dedicated ephemeral mount.

They should be removed after:

- success;
- failure;
- retry cleanup.

---

## 16. Docker Requirement

Production services should run through Docker Compose.

Initial services:

```text
caddy
api
worker
redis
```

---

## 17. Networking

Only Caddy should expose backend application traffic publicly.

Expected inbound ports:

```text
22/tcp
80/tcp
443/tcp
```

Optional:

```text
443/udp
```

for HTTP/3.

Redis must not be publicly exposed.

---

## 18. Security Baseline

The VPS must use:

- UFW;
- default deny incoming;
- SSH key authentication;
- password authentication disabled;
- automatic security updates;
- Docker log rotation;
- limited public ports.

Fail2ban may be added as supplementary protection.

---

## 19. Reverse Proxy

Caddy is the required V1 reverse proxy.

It provides:

- automatic HTTPS;
- certificate renewal;
- reverse proxy to FastAPI.

Do not replace Caddy without a new ADR.

---

## 20. Durable State Requirement

The architecture intentionally minimizes irreplaceable local state.

Persistent local state may include only:

- Caddy certificate data;
- Redis queue state where configured;
- deployment configuration.

Critical product data must remain external.

---

## 21. Recovery Consequence

Because durable data is external, VPS recovery should be relatively fast.

Recovery sequence:

```text
new VPS
→ Docker
→ firewall
→ deployment files
→ environment secrets
→ start containers
→ update DNS if required
→ verify health
```

---

## 22. Backup Consequence

The VPS itself does not require the same backup priority as the database.

Back up:

- deployment config;
- Caddy config;
- operational scripts;
- secure environment recovery procedure.

Database and storage backups remain separate.

---

## 23. Monitoring Requirements

Track:

- CPU;
- memory;
- disk;
- swap;
- container restarts;
- API latency;
- worker failures;
- queue depth;
- parser execution time.

---

## 24. Disk Management

100 GB NVMe is more than sufficient for application runtime if temporary files are cleaned correctly.

Do not let:

- Docker images;
- logs;
- temp documents;

grow without limits.

Use log rotation and periodic image cleanup.

---

## 25. Redis Persistence

Redis persistence may be enabled for queue resilience.

However, PostgreSQL should record durable ingestion state.

Redis loss must not make the product believe documents completed successfully when they did not.

---

## 26. Cost Philosophy

The project should:

```text
pay for measured demand
```

rather than:

```text
pre-pay for hypothetical scale
```

KVM 2 fits that philosophy.

---

## 27. Performance Implications

KVM 2 should provide adequate performance for:

- early customers;
- low-to-moderate concurrent API usage;
- limited parallel ingestion;
- external AI inference.

If document parsing becomes dominant, scale worker capacity before redesigning the whole architecture.

---

## 28. Deployment Model

Expected production topology:

```text
Hostinger KVM 2

Docker Compose:
├── caddy
├── api
├── worker
└── redis
```

External:

```text
Supabase
Voyage
LLM Provider
Vercel
```

---

## 29. Environment Configuration

Server-side environment should include:

```text
DATABASE_URL
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
VOYAGE_API_KEY
LLM_API_KEY
REDIS_URL
```

Secrets must not be committed.

---

## 30. Operational Simplicity

Using one VPS for API and worker initially provides:

- simple deployment;
- simple logs;
- simple networking;
- low cost;
- easy debugging.

This is preferable to distributed infrastructure before real demand exists.

---

## 31. Failure Domain

The VPS is one compute failure domain.

If it fails:

- API becomes unavailable;
- worker stops;
- Redis becomes unavailable.

But:

- user database remains safe;
- source files remain safe;
- vector data remains safe;
- auth data remains safe.

This separation is intentional.

---

## 32. Availability Trade-Off

A single VPS is not highly available.

That is accepted for V1.

High availability may be introduced later when:

- customer requirements demand it;
- downtime cost justifies complexity.

---

## 33. Future Enterprise Evolution

Possible future architecture:

```text
load balancer
├── API node 1
├── API node 2
└── API node N

worker cluster
managed Redis
managed observability
```

Do not build this before necessary.

---

## 34. Prohibited Actions

Without a superseding ADR, do not:

- treat the VPS as primary durable database host;
- store source files permanently on local disk;
- add local LLM inference;
- add Kubernetes;
- expose Redis publicly;
- run all services as root;
- open unnecessary firewall ports;
- scale infrastructure without measurement.

---

## 35. Review Triggers

Revisit this ADR if:

- API traffic consistently saturates KVM 2;
- document ingestion consistently causes contention;
- uptime requirements demand redundancy;
- enterprise customer requires dedicated compute;
- regional deployment becomes necessary;
- local model inference becomes a requirement;
- cost/performance becomes unfavorable.

---

## 36. Consequences

### Positive

- low initial cost;
- simple operations;
- enough memory for V1 services;
- easy Docker deployment;
- easy vertical scaling;
- durable state remains external.

### Negative

- single compute failure domain;
- parser-heavy workloads may saturate CPU;
- limited horizontal scaling;
- host maintenance responsibility remains with Bismark AI.

---

## 37. Status

**Accepted**

Hostinger KVM 2 is the canonical starting compute environment for Bismark AI V1.

The expected backend deployment is:

```text
Hostinger KVM 2
+
Docker Compose
+
Caddy
+
FastAPI
+
Worker
+
Redis
```

Any major change to this topology should be documented with a new or superseding ADR.
