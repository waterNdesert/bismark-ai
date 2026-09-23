# ADR-002 — Use Voyage AI for Embeddings and Reranking

**Project:** Bismark AI  
**ADR ID:** ADR-002  
**Title:** Use Voyage AI for Embeddings and Reranking  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 RAG architecture

---

## 1. Context

Bismark AI requires high-quality retrieval over private organizational knowledge.

The V1 retrieval pipeline needs two distinct capabilities:

```text
1. embeddings
2. reranking
```

Embeddings are required for semantic retrieval over `document_chunks`.

Reranking is required to improve relevance after initial hybrid retrieval.

The project also requires:

- provider replaceability;
- predictable API integration;
- support for both document and query embeddings;
- compatibility with pgvector;
- reasonable latency;
- minimal infrastructure burden.

Several approaches were considered:

1. local embedding models on the VPS;
2. OpenAI embeddings;
3. open-source embeddings hosted separately;
4. Voyage AI embeddings and reranking;
5. skipping reranking entirely.

---

## 2. Decision

Bismark AI V1 will use **Voyage AI** for:

```text
document embeddings
query embeddings
reranking
```

The integration must sit behind internal provider abstractions.

Conceptual interfaces:

```text
EmbeddingProvider
RerankProvider
```

Concrete implementations:

```text
VoyageEmbeddingProvider
VoyageRerankProvider
```

Domain logic must not depend directly on Voyage-specific SDK calls.

---

## 3. Why Voyage AI

### 3.1 Retrieval Quality

Bismark AI depends heavily on retrieval quality.

The product value is not merely generation quality.

A strong embedding and reranking provider improves:

- semantic recall;
- candidate ordering;
- evidence quality;
- citation relevance;
- answer groundedness.

---

### 3.2 Combined Embedding and Reranking Support

Using one provider for both capabilities simplifies:

- credential management;
- provider integration;
- operational monitoring;
- retry policy;
- cost attribution.

---

### 3.3 Reduced Infrastructure Complexity

Using Voyage avoids running embedding or reranking models locally on the Hostinger VPS.

This is important because the initial VPS is intended for:

- FastAPI;
- worker;
- Redis;
- document parsing;
- orchestration.

It is not intended to serve large ML models.

---

### 3.4 Fits the Hybrid Retrieval Architecture

The intended V1 pipeline is:

```text
query
→ vector retrieval
→ keyword retrieval
→ fusion
→ Voyage reranking
→ final evidence
```

Voyage fits cleanly into that architecture.

---

## 4. Alternatives Considered

### 4.1 Local Embedding Models

#### Benefits

- full control;
- no external API dependency;
- potentially lower marginal cost at scale;
- private processing.

#### Drawbacks

- requires additional compute;
- increases VPS resource pressure;
- operational complexity;
- model management;
- versioning;
- likely need for more powerful infrastructure.

#### Decision

Rejected for V1.

Local embeddings may be revisited for private enterprise deployment later.

---

### 4.2 OpenAI Embeddings

#### Benefits

- mature API;
- simple integration;
- broad ecosystem support.

#### Drawbacks

- Bismark AI already intends to use a separate LLM abstraction;
- retrieval should not be unnecessarily coupled to one generation provider;
- Voyage is specifically selected for retrieval-oriented use.

#### Decision

Not selected for V1.

---

### 4.3 Open-Source Embeddings on Separate Infrastructure

#### Benefits

- flexibility;
- control;
- lower vendor dependency.

#### Drawbacks

- additional service;
- model hosting;
- scaling burden;
- monitoring burden;
- more deployment complexity.

#### Decision

Rejected for initial V1.

---

### 4.4 No Reranker

#### Benefits

- simpler architecture;
- lower latency;
- lower cost.

#### Drawbacks

- weaker final evidence selection;
- more irrelevant chunks reach LLM;
- worse citation quality;
- harder multi-document retrieval.

#### Decision

Rejected.

Reranking is part of the intended V1 retrieval quality strategy.

---

## 5. Integration Boundary

Voyage must be isolated behind application-owned interfaces.

Preferred architecture:

```text
Retrieval Service
      |
      v
EmbeddingProvider
      |
      v
VoyageEmbeddingProvider
```

and:

```text
Retrieval Service
      |
      v
RerankProvider
      |
      v
VoyageRerankProvider
```

Do not import the Voyage client throughout unrelated modules.

---

## 6. Model Configuration

Voyage model names must be configurable.

Required environment variables include:

```text
VOYAGE_EMBEDDING_MODEL
VOYAGE_EMBEDDING_DIMENSION
VOYAGE_RERANK_MODEL
```

Do not hard-code model identifiers into domain logic.

---

## 7. Embedding Dimension

The selected embedding model determines vector dimension.

The database schema must match the configured dimension.

For example:

```text
vector(1024)
```

may be used if the selected model outputs 1024 dimensions.

The exact dimension must be validated against the configured model before production use.

---

## 8. Embedding Responsibilities

Voyage embeddings will be used for:

- document chunks;
- user query vectors.

Document embeddings should be generated during ingestion.

Query embeddings should be generated at request time.

---

## 9. Reranking Responsibilities

Voyage reranking occurs after initial candidate retrieval.

Expected flow:

```text
vector candidates
+
keyword candidates
→ candidate fusion
→ 20–40 candidates
→ Voyage reranker
→ 5–10 final evidence chunks
```

Exact values remain configurable.

---

## 10. Security Implications

The Voyage API key is sensitive.

Rules:

```text
backend only
never committed
never logged
never exposed to browser
```

Environment variable:

```text
VOYAGE_API_KEY
```

---

## 11. Data Exposure

Voyage receives only the content necessary for:

- embedding;
- reranking.

Do not send:

- entire organization corpus;
- unrelated tenant documents;
- secrets;
- access tokens;
- application credentials.

---

## 12. Multi-Tenancy

Voyage is not responsible for tenant isolation.

Tenant filtering occurs before candidate content is sent for reranking.

Required sequence:

```text
authorize workspace
→ tenant-scoped retrieval
→ rerank authorized candidates
```

Never send cross-tenant candidate sets to Voyage.

---

## 13. Retry Behavior

Transient failures may be retried.

Examples:

- timeout;
- HTTP 429;
- provider 5xx.

Use:

- bounded retries;
- exponential backoff;
- jitter.

Do not infinitely retry invalid input.

---

## 14. Timeout Behavior

Voyage calls must have explicit timeouts.

Suggested variables:

```text
VOYAGE_TIMEOUT_SECONDS
VOYAGE_RERANK_TIMEOUT_SECONDS
```

---

## 15. Ingestion Failure

If document embedding fails:

```text
document must not become ready
```

The ingestion job should fail safely and remain retryable.

---

## 16. Query-Time Failure

If query embedding fails:

- retrieval should fail safely;
- do not perform unscoped fallback retrieval.

---

## 17. Reranker Failure

Two acceptable future strategies exist:

### Strategy A — Fail Safe

Return a controlled error.

### Strategy B — Controlled Fallback

Use fused retrieval ranking without reranking.

If Strategy B is implemented, it must be:

- explicit;
- configurable;
- tested;
- documented.

The system must not silently degrade without observability.

---

## 18. Embedding Versioning

Store enough metadata to identify embedding configuration.

Recommended on documents:

```text
embedding_provider
embedding_model
embedding_dimension
```

If multiple embedding models coexist in the future, a dedicated embedding-version model may be introduced.

---

## 19. Re-Embedding

Changing embedding model may require:

```text
reprocess
→ re-embed
→ reindex
```

Do not switch dimensions in place casually.

Use processing versions and safe activation.

---

## 20. Evaluation Requirement

Changes to:

- embedding model;
- reranker model;
- candidate count;
- reranking threshold;

should be measured using the RAG evaluation suite once available.

Relevant metrics:

- Recall@K;
- MRR;
- nDCG;
- reranker uplift;
- citation precision;
- groundedness;
- latency;
- cost.

---

## 21. Cost Considerations

Voyage introduces external API cost.

Usage should be observable.

Potential usage events:

```text
embedding_request
embedding_tokens
rerank_request
rerank_documents
```

Cost optimization should not reduce retrieval quality blindly.

---

## 22. Caching

Possible future optimizations:

- avoid re-embedding unchanged chunks;
- cache deterministic document embeddings;
- reuse content hashes.

Do not cache query embeddings globally without evaluating privacy and usefulness.

---

## 23. Provider Lock-In Mitigation

To reduce lock-in:

- use provider interfaces;
- centralize model configuration;
- store model metadata;
- keep raw chunk text in PostgreSQL;
- keep retrieval orchestration provider-neutral.

This ensures another provider can be introduced later.

---

## 24. Future Provider Replacement

If replacing Voyage:

1. implement new `EmbeddingProvider`;
2. implement new `RerankProvider`;
3. evaluate;
4. re-embed documents if necessary;
5. update schema if dimension changes;
6. create a superseding ADR.

---

## 25. Future Multi-Provider Support

A future system may support:

```text
Voyage
OpenAI
Cohere
local models
```

through common abstractions.

V1 should not implement unnecessary multi-provider complexity before it is needed.

---

## 26. Local Enterprise Mode

Future enterprise deployments may require:

- private embeddings;
- local reranking;
- no external data processing.

This can be supported later without rewriting domain logic if provider interfaces remain clean.

---

## 27. Operational Monitoring

Track:

- embedding latency;
- rerank latency;
- provider errors;
- rate limits;
- retry counts;
- batch sizes;
- usage volume.

---

## 28. Required Environment Variables

```text
VOYAGE_API_KEY=
VOYAGE_EMBEDDING_MODEL=
VOYAGE_EMBEDDING_DIMENSION=
VOYAGE_EMBEDDING_BATCH_SIZE=
VOYAGE_TIMEOUT_SECONDS=
VOYAGE_MAX_RETRIES=
VOYAGE_RERANK_MODEL=
VOYAGE_RERANK_TIMEOUT_SECONDS=
VOYAGE_RERANK_MAX_RETRIES=
```

---

## 29. Testing Requirements

Tests must cover:

- embedding adapter success;
- embedding adapter timeout;
- embedding provider 429;
- embedding dimension mismatch;
- batch mapping;
- reranker ordering;
- reranker timeout;
- reranker mapping;
- mocked provider use in unit tests.

Live Voyage tests should be separate from ordinary unit tests.

---

## 30. Prohibited Actions

Without a replacement ADR, do not:

- remove Voyage reranking from the intended V1 pipeline;
- hard-code model names throughout the codebase;
- expose Voyage credentials to frontend;
- send unfiltered tenant data to reranker;
- change vector dimension without migration;
- introduce local embedding infrastructure as an undocumented replacement.

---

## 31. Review Triggers

Revisit this decision if:

- Voyage quality becomes unacceptable;
- pricing becomes materially problematic;
- provider availability is insufficient;
- enterprise privacy requirements require local processing;
- a different provider clearly outperforms Voyage in Bismark AI evaluation;
- model deprecation requires migration.

---

## 32. Consequences

### Positive

- strong retrieval-oriented provider;
- no local ML infrastructure;
- embeddings and reranking from one provider;
- easy integration;
- fast V1 delivery.

### Negative

- external dependency;
- usage cost;
- network latency;
- provider outage risk;
- re-embedding may be needed if models change.

---

## 33. Status

**Accepted**

Voyage AI is the canonical V1 provider for:

```text
embeddings
reranking
```

Any engineer or agent proposing a replacement must create a superseding ADR before changing the architecture.
