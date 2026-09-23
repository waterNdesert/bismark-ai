# ADR-009 — Use PostgreSQL Hybrid Search with pgvector and Full-Text Search

**Project:** Bismark AI  
**ADR ID:** ADR-009  
**Title:** Use PostgreSQL Hybrid Search with pgvector and Full-Text Search  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 retrieval architecture

---

## 1. Context

Bismark AI requires reliable retrieval across private organizational documents.

A retrieval system based only on semantic embeddings can perform poorly for:

- exact policy identifiers;
- names;
- dates;
- acronyms;
- error codes;
- part numbers;
- technical strings;
- exact phrases.

A retrieval system based only on lexical search can perform poorly for:

- paraphrases;
- conceptual similarity;
- synonym-rich questions;
- natural-language reformulations.

The V1 data platform already uses Supabase PostgreSQL with:

- pgvector;
- full-text search;
- tenant metadata;
- workspace metadata;
- relational document state.

Several retrieval architectures were considered:

1. vector search only;
2. keyword search only;
3. PostgreSQL hybrid search;
4. separate vector database plus PostgreSQL;
5. Elasticsearch/OpenSearch plus PostgreSQL;
6. a complete external RAG engine.

---

## 2. Decision

Bismark AI V1 will use **PostgreSQL hybrid retrieval** combining:

```text
pgvector semantic search
+
PostgreSQL full-text search
+
candidate fusion
+
Voyage reranking
```

The initial retrieval flow is:

```text
user query
   |
   v
authorization scope
   |
   +----------------------+
   |                      |
   v                      v
query embedding        FTS query
   |                      |
   v                      v
pgvector search       lexical search
   |                      |
   +----------+-----------+
              |
              v
       candidate fusion
              |
              v
       Voyage reranking
              |
              v
      final evidence set
```

---

## 3. Why Hybrid Search

### 3.1 Semantic and Lexical Strengths Are Complementary

Vector search is strong at:

- meaning;
- paraphrases;
- conceptual similarity.

Full-text search is strong at:

- exact terms;
- identifiers;
- acronyms;
- named entities;
- technical strings.

Bismark AI needs both.

---

### 3.2 One Database for Retrieval and Permissions

Using PostgreSQL keeps:

```text
content
embeddings
tenant IDs
workspace IDs
document state
search metadata
```

in one place.

This simplifies:

- tenant filtering;
- document filtering;
- joins;
- RLS;
- version filtering;
- operational management.

---

### 3.3 Avoids Premature Infrastructure

A separate search engine or vector database would add:

- another service;
- another index;
- data synchronization;
- more credentials;
- more operational burden;
- more failure modes.

That is not justified for V1.

---

### 3.4 Better Security Posture

Tenant and workspace filters can be applied directly in the retrieval query.

This is safer than:

```text
global retrieval
→ application filtering
```

which is explicitly prohibited.

---

## 4. Retrieval Scope

Every retrieval operation must include:

```text
organization_id
workspace_id
active document state
active processing version
```

before ranking.

---

## 5. Vector Search

Semantic retrieval uses:

```text
document_chunks.embedding
```

stored with pgvector.

The user query is embedded using Voyage.

---

## 6. Full-Text Search

Lexical retrieval uses:

```text
document_chunks.search_vector
```

with a GIN index.

Recommended weighted fields:

```text
heading
section_title
content
```

---

## 7. Candidate Counts

Initial configurable values:

```text
vector candidates: 20–40
keyword candidates: 20–40
```

A reasonable starting point:

```text
30
```

for each path.

These are not permanent constants.

---

## 8. Candidate Fusion

Vector and keyword results must be merged before reranking.

The initial preferred fusion method is:

```text
Reciprocal Rank Fusion
```

because raw vector and FTS scores are not naturally comparable.

---

## 9. Reciprocal Rank Fusion

Conceptual formula:

```text
RRF(d) =
1 / (k + rank_vector)
+
1 / (k + rank_keyword)
```

The exact `k` value remains configurable.

Initial:

```text
RAG_RRF_K=60
```

may be used as a starting point.

---

## 10. Deduplication

If the same chunk appears in both retrieval paths:

- preserve one candidate;
- preserve both ranking signals;
- do not duplicate the chunk.

Canonical deduplication key:

```text
chunk_id
```

---

## 11. Reranking

After fusion, candidate chunks are sent to Voyage reranking.

Expected:

```text
20–40 fused candidates
→ rerank
→ 5–10 final evidence chunks
```

The final evidence set is what enters the LLM context.

---

## 12. Why Not Vector Search Only

### Benefits

- simple;
- common RAG implementation.

### Drawbacks

May underperform on:

- exact policy numbers;
- serials;
- codes;
- names;
- acronyms;
- exact phrases.

### Decision

Rejected as the complete V1 retrieval strategy.

---

## 13. Why Not Keyword Search Only

### Benefits

- deterministic;
- fast;
- strong exact matching.

### Drawbacks

Weak for:

- paraphrases;
- semantic similarity;
- natural-language reformulation.

### Decision

Rejected as the complete V1 retrieval strategy.

---

## 14. Alternative Considered — Separate Vector Database

Examples:

```text
Qdrant
Weaviate
Pinecone
```

### Benefits

- specialized vector capabilities;
- potentially stronger at very large scale;
- advanced vector filtering.

### Drawbacks

- extra infrastructure;
- duplicated metadata;
- synchronization complexity;
- more expensive operational model;
- more complex tenant security.

### Decision

Rejected for V1.

---

## 15. Alternative Considered — Elasticsearch/OpenSearch

### Benefits

- strong lexical search;
- mature ranking;
- large-scale search.

### Drawbacks

- another cluster/service;
- more operational complexity;
- duplicated index state;
- unnecessary at initial scale.

### Decision

Rejected for V1.

---

## 16. Alternative Considered — External RAG Engine

### Benefits

- prebuilt retrieval;
- fast prototype.

### Drawbacks

- reduced control;
- duplicated product logic;
- weaker architecture ownership;
- harder tenant isolation guarantees;
- harder citation traceability.

### Decision

Rejected as the production retrieval core.

---

## 17. Data Model

Each searchable chunk should contain:

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
embedding
search_vector
```

---

## 18. Vector Index

Recommended initial index:

```text
HNSW
```

when supported by the deployed pgvector version and operationally appropriate.

Conceptual:

```sql
create index document_chunks_embedding_hnsw_idx
on document_chunks
using hnsw (embedding vector_cosine_ops);
```

---

## 19. Full-Text Index

Recommended:

```sql
create index document_chunks_search_vector_gin_idx
on document_chunks
using gin (search_vector);
```

---

## 20. Similarity Metric

Initial default:

```text
cosine similarity
```

The query operator and index operator class must match.

---

## 21. Full-Text Language Configuration

Initial language may be:

```text
english
```

If multilingual knowledge becomes common, reevaluate:

- `simple`;
- language-specific configurations;
- per-document language metadata.

---

## 22. Weighted FTS

Recommended conceptual weighting:

```text
heading        A
section_title  B
content        C
```

This gives headings more lexical significance.

---

## 23. Security Invariant

The retrieval layer must never execute:

```text
select global candidates
→ filter unauthorized chunks later
```

Required:

```text
filter authorized scope
→ rank within scope
```

---

## 24. Document State Filter

Only:

```text
status = ready
```

documents participate.

Deleted, failed, queued, and processing documents must be excluded.

---

## 25. Processing Version Filter

Only the active processing version should be searchable.

This supports safe reprocessing.

---

## 26. Metadata Filtering

Future filters may include:

- document;
- type;
- date;
- tags;
- source connector.

Tenant/workspace constraints remain mandatory.

---

## 27. Query Preparation

Query preparation may preserve both:

- semantic interpretation;
- exact lexical terms.

Do not rewrite away identifiers that keyword search needs.

---

## 28. Exact Identifier Example

Source contains:

```text
POLICY-HR-2026-04
```

User asks:

```text
What does POLICY-HR-2026-04 say?
```

FTS should contribute strongly.

---

## 29. Semantic Example

Source:

```text
Employees receive twenty days of annual leave.
```

User asks:

```text
How much vacation time do staff get?
```

Vector retrieval should contribute strongly.

---

## 30. Fusion Observability

Diagnostics should preserve:

```text
vector_rank
vector_score
keyword_rank
keyword_score
fusion_score
```

where useful.

---

## 31. Rerank Observability

Also preserve:

```text
rerank_score
final_rank
```

for debugging/evaluation.

---

## 32. Persistence

Not every retrieval score needs permanent storage.

However, final evidence can store:

```text
retrieval_score
rerank_score
rank
```

in `message_sources`.

---

## 33. Query Latency

Hybrid retrieval introduces more work than vector-only search.

This trade-off is accepted because answer quality is more important than minimal retrieval complexity.

Latency should be measured and optimized based on data.

---

## 34. Parallel Retrieval

Vector and keyword retrieval may run concurrently where implementation allows.

This can reduce total retrieval latency.

---

## 35. Database Load

Monitor:

- vector query latency;
- FTS latency;
- index size;
- tenant filter selectivity;
- query plans.

Do not assume indexes are optimal indefinitely.

---

## 36. Scale Assumptions

PostgreSQL hybrid retrieval is expected to be sufficient for:

- MVP;
- early production;
- moderate document volumes.

At large scale, architecture may need reconsideration.

---

## 37. Scale Triggers

Revisit if:

- vector queries become consistently slow;
- index growth causes unacceptable performance;
- tenant filtering degrades ANN behavior;
- database load competes heavily with transactional workloads;
- corpus grows far beyond initial assumptions.

---

## 38. Future Retrieval Options

Potential later architecture:

```text
PostgreSQL
+
dedicated vector search
+
dedicated lexical search
```

Only if measurements justify it.

---

## 39. Knowledge Graph

A graph-based retrieval system is not part of V1.

If added later:

```text
vector
+
keyword
+
graph
```

could feed a shared reranking layer.

Requires a separate ADR.

---

## 40. Evaluation Requirement

Hybrid search must be evaluated against alternatives.

At minimum compare:

```text
vector only
keyword only
hybrid
hybrid + reranker
```

Metrics may include:

- Recall@K;
- MRR;
- nDCG;
- hit rate;
- citation quality.

---

## 41. No Quality Claims Without Measurement

Once the evaluation suite exists, changes to fusion or ranking should not be called "better" without evidence.

---

## 42. Query Debugging

Development/staging may expose internal retrieval diagnostics to authorized developers.

Do not expose debug retrieval data to normal production users.

---

## 43. Error Handling

If vector retrieval fails:

- do not broaden access;
- do not silently search globally.

If FTS fails:

- fallback behavior must be explicit.

If reranking fails:

- fallback must be documented/configurable.

---

## 44. Graceful Degradation

Possible future controlled fallback:

```text
hybrid without reranker
```

or:

```text
keyword only
```

but only if:

- explicitly configured;
- safe;
- tested;
- observable.

No silent degradation.

---

## 45. Provider Independence

PostgreSQL retrieval should not be tightly bound to Voyage.

Voyage creates embeddings and reranks candidates, but:

```text
storage
search
tenant scope
fusion
```

remain application-controlled.

---

## 46. Embedding Model Changes

Changing Voyage embedding model may require:

- new dimension;
- re-embedding;
- vector reindex.

The retrieval architecture remains the same.

---

## 47. Search Vector Maintenance

The application must ensure `search_vector` remains synchronized with chunk content.

Implementation options:

- generated column;
- trigger;
- application write.

Whichever is selected must be tested.

---

## 48. Index Migration

Changes to HNSW or GIN indexes must use version-controlled migrations.

Do not create production indexes manually without recording them.

---

## 49. Query Plan Review

For performance-sensitive retrieval queries, use:

```text
EXPLAIN
EXPLAIN ANALYZE
```

in safe test/staging environments.

Optimize based on evidence.

---

## 50. Multi-Tenant Indexing

Tenant filters should be included in relational indexes where useful.

Example:

```text
organization_id
workspace_id
document_id
```

The vector index itself may not encode all relational filtering semantics, so query planning must be tested with realistic multi-tenant data.

---

## 51. Security Testing

Required cases:

```text
User A queries unique phrase in Org B
→ no result

User A queries restricted Workspace A2
→ no result
```

This must hold for:

- vector search;
- keyword search;
- hybrid fusion;
- reranking input.

---

## 52. Functional Testing

Test:

- exact phrase;
- code;
- acronym;
- semantic paraphrase;
- multi-document question;
- duplicate candidate;
- no-evidence query.

---

## 53. Performance Testing

Measure:

- vector retrieval latency;
- FTS latency;
- fusion latency;
- reranking latency;
- total retrieval latency.

---

## 54. Configuration

Expected variables:

```text
RAG_VECTOR_CANDIDATES
RAG_KEYWORD_CANDIDATES
RAG_FUSED_CANDIDATES
RAG_RERANK_CANDIDATES
RAG_FINAL_EVIDENCE_COUNT
RAG_FUSION_STRATEGY
RAG_RRF_K
```

---

## 55. Agentic Development Implication

Coding agents must preserve hybrid retrieval.

They must not simplify the system to:

```text
vector top-k
→ LLM
```

unless explicitly instructed and documented.

---

## 56. Prohibited Actions

Without a superseding ADR, do not:

- remove PostgreSQL FTS;
- remove pgvector;
- add a dedicated vector DB;
- add Elasticsearch/OpenSearch;
- perform global search before tenant filtering;
- bypass active document version checks;
- send unauthorized candidates to Voyage;
- hard-code retrieval counts across code.

---

## 57. Review Triggers

Revisit this decision if:

- PostgreSQL retrieval becomes a proven bottleneck;
- corpus size materially exceeds expected scale;
- advanced search requirements emerge;
- dedicated search infrastructure gives measurable quality/latency benefits;
- tenant filtering becomes operationally difficult with pgvector.

---

## 58. Consequences

### Positive

- strong exact + semantic retrieval;
- one search database;
- simpler security;
- fewer services;
- lower cost;
- straightforward observability;
- tight integration with tenant metadata.

### Negative

- PostgreSQL carries both transactional and retrieval load;
- ANN/filter tuning may be required at scale;
- lexical and vector scoring require fusion;
- future large-scale search may need dedicated infrastructure.

---

## 59. Status

**Accepted**

Bismark AI V1 will use:

```text
PostgreSQL full-text search
+
pgvector
+
hybrid candidate fusion
+
Voyage reranking
```

as the canonical retrieval architecture.

This is the final planned foundational ADR for the initial Bismark AI V1 architecture.
