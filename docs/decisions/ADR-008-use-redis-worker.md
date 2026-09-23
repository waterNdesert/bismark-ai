# ADR-008 — Use Redis with a Background Worker for Asynchronous Processing

**Project:** Bismark AI  
**ADR ID:** ADR-008  
**Title:** Use Redis and a Python Background Worker for Asynchronous Jobs  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 asynchronous processing architecture

---

## 1. Context

Bismark AI performs work that should not run inside ordinary HTTP request lifecycles.

Examples include:

- document parsing;
- normalization;
- chunking;
- embedding generation;
- indexing;
- document reprocessing;
- potentially future connector synchronization.

Some of these operations may take:

- several seconds;
- tens of seconds;
- several minutes.

Running them synchronously inside FastAPI request handlers would create:

- poor user experience;
- timeouts;
- blocked application workers;
- weak retry behavior;
- difficult failure recovery.

The architecture therefore requires an asynchronous execution layer.

Several approaches were considered:

1. Redis plus a lightweight Python worker framework;
2. Celery with Redis/RabbitMQ;
3. RabbitMQ;
4. Kafka;
5. database-backed polling only;
6. serverless background functions;
7. synchronous FastAPI background tasks.

---

## 2. Decision

Bismark AI V1 will use:

```text
Redis
+
one or more Python background workers
```

for asynchronous document-processing jobs.

The exact Python worker framework may be selected during implementation, but it must remain lightweight and compatible with the V1 architecture.

Potential candidates include:

```text
RQ
ARQ
Dramatiq
Celery
```

The framework choice is an implementation detail unless it materially changes infrastructure.

---

## 3. Primary Use Case

The initial asynchronous workload is document ingestion.

Canonical flow:

```text
Upload request
    |
    v
FastAPI
    |
    +--> validate
    +--> persist source
    +--> create document record
    +--> create ingestion job
    +--> enqueue document ID
    |
    v
Return 202 Accepted
```

Worker:

```text
document ID
    |
    v
load authoritative metadata
    |
    v
parse
    |
    v
normalize
    |
    v
chunk
    |
    v
embed
    |
    v
index
    |
    v
mark ready
```

---

## 4. Why Redis

### 4.1 Simple Infrastructure

Redis is lightweight and well suited to:

- queues;
- transient coordination;
- retry scheduling;
- worker signaling.

It fits the initial single-VPS deployment.

---

### 4.2 Operationally Small

Bismark AI does not need a large message-broker platform for V1.

Redis can run as one Docker container alongside:

```text
api
worker
caddy
```

---

### 4.3 Familiar Ecosystem

Python has multiple mature worker libraries that use Redis.

This gives implementation flexibility without changing the architecture.

---

### 4.4 Suitable for Current Workload

The initial queue workload is moderate and task-oriented.

It does not require:

- high-throughput event streaming;
- complex routing;
- event replay;
- distributed consumer groups.

---

## 5. Why a Separate Worker Process

A separate worker prevents CPU-heavy or long-running document processing from blocking FastAPI request handling.

This keeps:

```text
API responsiveness
```

separate from:

```text
ingestion execution
```

---

## 6. Worker Responsibilities

The worker may perform:

- source retrieval;
- parser execution;
- text normalization;
- chunking;
- Voyage embedding requests;
- vector/index writes;
- processing retries;
- temporary file cleanup;
- processing status updates.

---

## 7. Worker Non-Responsibilities

The worker should not own:

- interactive user sessions;
- frontend request authorization;
- organization membership decisions;
- public HTTP APIs;
- permanent business state outside PostgreSQL.

---

## 8. Queue Payload Design

Queue payloads should be small.

Preferred:

```json
{
  "document_id": "uuid"
}
```

or an equivalent stable identifier.

Do not enqueue:

- full file bytes;
- large extracted text;
- access tokens;
- service secrets;
- large provider payloads.

---

## 9. Authoritative State

Redis is **not** the source of truth.

Durable state belongs in PostgreSQL.

Examples:

```text
document status
processing version
ingestion attempt
failure reason
timestamps
```

Redis may lose transient queue state without causing the product to falsely believe a job completed.

---

## 10. Recommended Durable Job Model

Bismark AI should use a database table such as:

```text
ingestion_jobs
```

for durable job metadata.

Suggested fields:

```text
id
document_id
organization_id
workspace_id
processing_version
status
attempt
queued_at
started_at
completed_at
error_code
error_message
worker_id
```

---

## 11. State Relationship

Redis represents:

```text
what should execute
```

PostgreSQL represents:

```text
what the product believes happened
```

This distinction is important.

---

## 12. Job States

Recommended durable states:

```text
queued
processing
completed
failed
cancelled
```

Document state remains separately tracked.

---

## 13. Retry Strategy

Transient failures may be retried.

Examples:

- temporary network failure;
- Voyage 429;
- provider 5xx;
- storage timeout.

Use:

- bounded retries;
- exponential backoff;
- jitter.

Do not retry permanently invalid documents forever.

---

## 14. Retry Limits

Configuration should include:

```text
JOB_MAX_RETRIES
```

Recommended initial value:

```text
3
```

This may be tuned later.

---

## 15. Job Timeout

Jobs must have bounded execution time.

Configuration:

```text
JOB_TIMEOUT_SECONDS
```

A separate parser timeout may also exist:

```text
PARSER_TIMEOUT_SECONDS
```

---

## 16. Idempotency

Workers must assume jobs may execute more than once.

A duplicate job must not corrupt state.

Potential strategies:

- processing version;
- unique chunk constraints;
- stale-chunk cleanup;
- atomic activation;
- idempotent write patterns.

---

## 17. Document Processing Version

Each ingestion attempt should use:

```text
processing_version
```

New chunks are written for the new version.

Only after complete success should that version become active.

This avoids partially indexed documents.

---

## 18. Worker Crash

If a worker crashes mid-job:

- the document must not become `ready`;
- the durable job remains incomplete;
- partial chunks must not become active;
- retry/reconciliation must be possible.

---

## 19. API Crash

If FastAPI crashes after enqueueing:

- worker should still be able to process the job;
- authoritative metadata must already exist.

This is one reason the worker should resolve data from PostgreSQL.

---

## 20. Redis Crash

If Redis crashes:

- running/queued transient tasks may be affected;
- product state in PostgreSQL remains intact;
- incomplete jobs can be reconciled.

The system must not silently mark failed work complete.

---

## 21. Redis Persistence

Redis persistence may be enabled to improve queue resilience.

Possible:

```text
AOF
RDB
```

Exact configuration depends on selected worker framework and operational needs.

However, PostgreSQL remains the durable source of truth.

---

## 22. Public Exposure

Redis must not be publicly accessible.

Do not publish:

```text
6379
```

to the internet.

Use an internal Docker network.

---

## 23. Authentication

For a single-host internal Docker network, network isolation is the primary boundary.

If Redis later becomes remotely reachable:

- require authentication;
- consider TLS;
- restrict firewall/network access.

---

## 24. Docker Deployment

Initial services:

```text
caddy
api
worker
redis
```

The worker and Redis should live on the internal Docker network.

---

## 25. Resource Limits

Worker concurrency should remain conservative on KVM 2.

Initial:

```text
WORKER_CONCURRENCY=1
```

Increase only after observing:

- CPU;
- memory;
- queue depth;
- parsing latency.

---

## 26. Parser Workload

Document parsing is likely to be the largest local resource consumer.

Therefore:

- parser runs in worker;
- enforce timeout;
- control concurrency;
- clean temp files;
- avoid parsing in API process.

---

## 27. Embedding Calls

Worker handles document embedding generation.

It should batch requests where appropriate.

Query embeddings remain request-time operations in the API.

---

## 28. Future Queue Uses

The same queue may later support:

- document reprocessing;
- connector synchronization;
- bulk import;
- export generation;
- maintenance jobs.

Do not overload it with unrelated real-time communication.

---

## 29. Alternative Considered — Synchronous Processing

### Benefits

- simplest code;
- no queue.

### Drawbacks

- request timeouts;
- blocked API workers;
- poor retry semantics;
- weak failure isolation.

### Decision

Rejected.

---

## 30. Alternative Considered — FastAPI BackgroundTasks

### Benefits

- built into FastAPI;
- simple.

### Drawbacks

- tied to API process lifecycle;
- weak durability;
- poor crash recovery;
- unsuitable for long-running ingestion.

### Decision

Rejected for core ingestion.

---

## 31. Alternative Considered — RabbitMQ

### Benefits

- strong broker semantics;
- mature messaging;
- routing capabilities.

### Drawbacks

- another heavier service;
- more configuration;
- unnecessary for current task queue requirements.

### Decision

Deferred.

---

## 32. Alternative Considered — Kafka

### Benefits

- high-throughput event streaming;
- durable logs;
- consumer groups;
- replay.

### Drawbacks

- substantial operational complexity;
- far beyond current requirements;
- poor fit for simple background jobs.

### Decision

Rejected for V1.

---

## 33. Alternative Considered — Database Polling Only

### Benefits

- no Redis;
- durable queue naturally in PostgreSQL.

### Drawbacks

- polling overhead;
- more custom scheduling logic;
- less convenient worker ecosystem.

### Decision

Not selected for V1.

A PostgreSQL-backed queue may be reconsidered later if simplification becomes attractive.

---

## 34. Alternative Considered — Serverless Background Jobs

### Benefits

- managed execution;
- autoscaling.

### Drawbacks

- parser workloads may exceed execution constraints;
- temp-file behavior may be awkward;
- more provider coupling;
- harder local parity.

### Decision

Not selected initially.

---

## 35. Framework Selection Criteria

The chosen Python queue framework should support:

- Redis;
- async or sync Python as required;
- retry;
- timeout;
- worker concurrency;
- job IDs;
- simple operational model;
- testing.

---

## 36. Celery Consideration

Celery is acceptable if its maturity is required.

However, it may be more infrastructure/complexity than needed.

Do not select it automatically merely because it is common.

---

## 37. RQ Consideration

RQ is attractive for:

- simplicity;
- Redis-native job queues;
- straightforward worker model.

Evaluate async/provider integration requirements before final selection.

---

## 38. ARQ Consideration

ARQ may fit well if an asyncio-oriented stack is preferred.

Evaluate project maintenance and operational fit before selection.

---

## 39. Dramatiq Consideration

Dramatiq may also be appropriate.

The final choice should optimize for:

```text
simplicity
reliability
testability
maintenance
```

not novelty.

---

## 40. Logging

Every job should produce structured logs including:

```text
job_id
document_id
organization_id
workspace_id
processing_version
attempt
duration
status
error_class
```

---

## 41. Metrics

Useful metrics:

- queue depth;
- job wait time;
- job duration;
- success rate;
- failure rate;
- retry count;
- parser duration;
- embedding duration.

---

## 42. Reconciliation

A periodic reconciliation task may identify:

```text
document status = processing
but no active worker/job
```

Such records may be marked retryable after a safe timeout.

This may be implemented after basic ingestion works.

---

## 43. Dead Jobs

Jobs exceeding maximum retries should become:

```text
failed
```

with safe diagnostics.

They should not disappear silently.

---

## 44. User Visibility

Users should be able to see document status:

```text
queued
processing
ready
failed
```

Redis internals should not be exposed directly.

---

## 45. Manual Retry

Authorized users may trigger:

```text
POST /documents/{id}/retry
```

The API should create a new safe processing attempt.

---

## 46. Security

Queue data must not bypass authorization.

The API authorizes whether the job may be created.

The worker trusts database-owned metadata, not arbitrary client input.

---

## 47. Tenant Isolation

Worker processing must preserve:

```text
organization_id
workspace_id
document_id
```

for every chunk and write.

No job may write chunks to another tenant.

---

## 48. Temporary Files

Worker may download documents to a temporary directory.

Rules:

- server-controlled path;
- no executable use;
- cleanup on success;
- cleanup on failure;
- cleanup on startup/maintenance if stale.

---

## 49. Process Isolation

Running worker separately from FastAPI provides failure isolation.

A parser crash should not necessarily terminate API service.

---

## 50. Scaling

Initial:

```text
1 worker
```

Scale later:

```text
2+ workers
```

if queue depth and resources justify it.

---

## 51. Worker Scaling Boundary

On one KVM 2 server, increasing worker count may hurt API performance.

Monitor before increasing concurrency.

---

## 52. Future Separate Worker Host

If ingestion load grows substantially:

```text
API host
+
worker host
```

may become appropriate.

This can still use Redis or a managed queue.

A material topology change should be documented.

---

## 53. Managed Redis

Future managed Redis may be introduced if:

- multiple nodes exist;
- availability requirements increase;
- Redis operations become burdensome.

Not required for V1.

---

## 54. Deployment Recovery

After VPS restart:

- Redis restarts;
- worker restarts;
- incomplete durable jobs are reconciled;
- active source data remains in Supabase.

---

## 55. Testing

Required tests include:

- enqueue success;
- job execution;
- retry;
- timeout;
- duplicate execution;
- parser failure;
- embedding failure;
- worker crash simulation;
- document state consistency.

---

## 56. Fake Queue

Unit tests should support a fake/in-process queue interface where appropriate.

Do not require live Redis for every service test.

---

## 57. Integration Tests

A separate integration suite should verify real Redis behavior.

---

## 58. Configuration

Expected variables:

```text
REDIS_URL
WORKER_CONCURRENCY
JOB_MAX_RETRIES
JOB_TIMEOUT_SECONDS
PARSER_TIMEOUT_SECONDS
WORKER_NAME
```

---

## 59. Agentic Development Implication

Coding agents must not implement long-running document processing directly in upload handlers.

They must preserve:

```text
upload
→ enqueue
→ worker
```

---

## 60. Prohibited Actions

Without a superseding ADR, do not:

- process complete documents synchronously in API requests;
- expose Redis publicly;
- store service secrets in queue payloads;
- use Redis as canonical document state;
- introduce Kafka for ordinary ingestion jobs;
- add RabbitMQ without demonstrated need;
- send full binary documents through Redis.

---

## 61. Review Triggers

Revisit this ADR if:

- job volume grows beyond Redis/task queue suitability;
- multiple worker hosts require stronger broker guarantees;
- exactly-once-style processing requirements emerge;
- enterprise workflows require durable event replay;
- queue availability becomes a major operational concern.

---

## 62. Consequences

### Positive

- responsive API;
- simple async architecture;
- low infrastructure overhead;
- retry support;
- easy worker scaling;
- strong separation of request and ingestion workloads.

### Negative

- Redis becomes another runtime dependency;
- job framework must be selected and maintained;
- queue recovery/reconciliation requires care;
- single VPS remains one compute failure domain.

---

## 63. Status

**Accepted**

Bismark AI V1 will use:

```text
Redis
+
Python worker
```

for asynchronous document processing.

The canonical flow is:

```text
FastAPI
→ Redis
→ Worker
→ PostgreSQL/Supabase/Voyage
```

Any major replacement of this queue architecture should be documented through a new or superseding ADR.
