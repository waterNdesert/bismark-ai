# DATABASE.md — Bismark AI Database Design

**Project:** Bismark AI  
**Document Type:** Canonical Database Design  
**Status:** V1 Data Model Specification  
**Version:** 1.0  
**Primary Database:** Supabase PostgreSQL  
**Vector Extension:** pgvector  
**Audience:** Backend Engineering, Database Engineering, Security, AI/RAG Engineering, QA, DevOps, and Agentic Coding Systems

---

## 1. Purpose

This document defines the canonical V1 database model for Bismark AI.

It specifies:

- tables;
- relationships;
- tenancy boundaries;
- Row Level Security expectations;
- vector schema;
- full-text search schema;
- indexes;
- constraints;
- deletion behavior;
- migration policy;
- data lifecycle rules;
- audit requirements;
- ingestion state;
- conversation persistence;
- retrieval-related fields.

Documentation authority follows the canonical order in [AGENTS.md §2](../AGENTS.md#2-documentation-authority).
`PROJECT_STATE.md` reports current implementation state and does not override architectural decisions.

If implementation conflicts with this document, the discrepancy must be resolved explicitly rather than silently.

---

## 2. Database Platform

Bismark AI V1 uses:

- Supabase PostgreSQL;
- pgvector;
- PostgreSQL full-text search;
- Supabase Auth for identity;
- Supabase Storage for binary source files.

The database is the source of truth for durable application state.

The VPS must not host a second production PostgreSQL instance for Bismark AI V1.

---

## 3. Data Design Goals

The schema must optimize for:

1. strict tenant isolation;
2. clear ownership relationships;
3. reliable authorization;
4. RAG retrieval efficiency;
5. auditability;
6. conversation traceability;
7. safe document lifecycle management;
8. migration safety;
9. future extensibility;
10. compatibility with automated coding agents.

---

## 4. Core Tenancy Model

The top-level tenant boundary is:

```text
organization
```

Within each organization, knowledge is organized into:

```text
workspace
```

Users may belong to one or more organizations.

Users may have access to one or more workspaces within an organization.

Canonical ownership chain:

```text
auth.users
    |
    v
profiles
    |
    v
organization_members
    |
    v
organizations
    |
    v
workspaces
    |
    +--> workspace_members
    |
    +--> documents
    |
    +--> conversations
```

Document chunks inherit tenancy through both:

- `organization_id`
- `workspace_id`

This duplication is deliberate for secure and performant filtering.

---

## 5. Identity Boundary

Supabase Auth owns authentication identities.

Bismark AI application tables should reference:

```text
auth.users.id
```

through a profile row.

Recommended mapping:

```text
auth.users
   |
   | 1:1
   v
profiles
```

The application should not attempt to duplicate password hashes or authentication secrets.

---

## 6. UUID Strategy

Use UUIDs for primary keys exposed across API boundaries.

Recommended:

```sql
uuid primary key default gen_random_uuid()
```

Reasons:

- hard to enumerate;
- easy cross-service compatibility;
- safe public identifiers;
- common Supabase pattern.

Do not mix integer public IDs and UUID public IDs arbitrarily.

---

## 7. Timestamp Strategy

Use timezone-aware timestamps.

Recommended:

```sql
timestamptz
```

Standard fields:

```text
created_at
updated_at
```

Where relevant:

```text
deleted_at
processing_started_at
processing_completed_at
last_seen_at
```

Use UTC at the database layer.

---

## 8. Soft Delete Policy

Soft deletion should be used selectively.

Recommended soft-delete candidates:

- organizations;
- workspaces;
- documents;
- conversations.

Hard-delete may be appropriate for:

- transient job records;
- short-lived caches;
- orphan cleanup.

If soft delete is used, queries must explicitly exclude deleted records.

Avoid introducing `deleted_at` everywhere by default.

---

## 9. Enum Strategy

Use PostgreSQL enums carefully.

For rapidly changing product states, prefer constrained text fields where migration friction matters.

For stable lifecycle states, a PostgreSQL enum is acceptable.

For V1, recommended options:

- use text columns;
- enforce valid values with check constraints.

This gives flexibility while retaining validation.

Example:

```sql
status text not null
check (status in ('uploaded', 'queued', 'processing', 'ready', 'failed', 'deleting'))
```

---

## 10. Table Inventory

The initial schema should contain at minimum:

```text
profiles
organizations
organization_members
workspaces
workspace_members
documents
document_chunks
conversations
messages
message_sources
feedback
usage_events
audit_logs
```

Optional supporting tables may include:

```text
ingestion_jobs
workspace_settings
organization_invites
api_keys
```

Only add them when implementation requires them.

---

# PART I — CORE IDENTITY AND TENANCY

## 11. profiles

### Purpose

Stores application-level user profile metadata linked to Supabase Auth.

### Suggested Schema

```sql
create table public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    display_name text,
    avatar_url text,
    timezone text,
    locale text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

### Notes

The profile ID is the Supabase Auth user ID.

Do not create a second unrelated user identifier unless there is a documented reason.

### Indexes

Primary key is sufficient initially.

Potential future index:

```sql
create index profiles_display_name_idx
on public.profiles (display_name);
```

only if needed.

---

## 12. organizations

### Purpose

Represents a Bismark AI tenant.

### Suggested Schema

```sql
create table public.organizations (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text not null,
    status text not null default 'active',
    created_by uuid not null references public.profiles(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);
```

### Constraints

```sql
check (status in ('active', 'suspended', 'deleted'))
```

Recommended slug uniqueness:

```sql
create unique index organizations_slug_unique_idx
on public.organizations (lower(slug))
where deleted_at is null;
```

### Notes

Do not trust slug uniqueness in application code alone.

---

## 13. organization_members

### Purpose

Maps users to organizations and stores organization-level role.

### Suggested Schema

```sql
create table public.organization_members (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid not null references public.organizations(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    role text not null default 'member',
    status text not null default 'active',
    joined_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

### Role Constraint

```sql
check (role in ('owner', 'admin', 'member'))
```

### Status Constraint

```sql
check (status in ('invited', 'active', 'suspended', 'removed'))
```

### Uniqueness

```sql
create unique index organization_members_org_user_unique_idx
on public.organization_members (organization_id, user_id)
where status <> 'removed';
```

### Indexes

```sql
create index organization_members_user_idx
on public.organization_members (user_id);

create index organization_members_org_idx
on public.organization_members (organization_id);
```

---

## 14. workspaces

### Purpose

Represents a knowledge boundary inside an organization.

Examples:

- HR
- Sales
- Engineering
- Operations

### Suggested Schema

```sql
create table public.workspaces (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid not null references public.organizations(id) on delete cascade,
    name text not null,
    slug text not null,
    description text,
    status text not null default 'active',
    created_by uuid not null references public.profiles(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);
```

### Constraints

```sql
check (status in ('active', 'archived', 'deleted'))
```

### Uniqueness

```sql
create unique index workspaces_org_slug_unique_idx
on public.workspaces (organization_id, lower(slug))
where deleted_at is null;
```

### Indexes

```sql
create index workspaces_org_idx
on public.workspaces (organization_id)
where deleted_at is null;
```

---

## 15. workspace_members

### Purpose

Allows workspace-specific access when not every organization member should access every workspace.

### Suggested Schema

```sql
create table public.workspace_members (
    id uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references public.workspaces(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    role text not null default 'member',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

### Suggested Roles

```text
admin
editor
member
viewer
```

For V1, implementation may simplify to:

```text
admin
member
```

if the product does not yet need four levels.

### Uniqueness

```sql
create unique index workspace_members_workspace_user_unique_idx
on public.workspace_members (workspace_id, user_id);
```

### Indexes

```sql
create index workspace_members_user_idx
on public.workspace_members (user_id);

create index workspace_members_workspace_idx
on public.workspace_members (workspace_id);
```

---

# PART II — DOCUMENTS AND RAG DATA

## 16. documents

### Purpose

Stores canonical metadata for each source document.

### Suggested Schema

```sql
create table public.documents (
    id uuid primary key default gen_random_uuid(),

    organization_id uuid not null references public.organizations(id) on delete cascade,
    workspace_id uuid not null references public.workspaces(id) on delete cascade,

    filename text not null,
    display_name text not null,
    mime_type text not null,
    file_extension text,
    size_bytes bigint not null,

    storage_bucket text not null,
    storage_path text not null,

    status text not null default 'uploaded',

    parser_name text,
    parser_version text,

    embedding_provider text,
    embedding_model text,
    embedding_dimension integer,

    chunk_count integer not null default 0,

    processing_version integer not null default 1,

    error_code text,
    error_message text,

    checksum_sha256 text,

    created_by uuid not null references public.profiles(id),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    processing_started_at timestamptz,
    processing_completed_at timestamptz,
    deleted_at timestamptz
);
```

### Status Constraint

```sql
check (
    status in (
        'uploaded',
        'queued',
        'processing',
        'ready',
        'failed',
        'deleting',
        'deleted'
    )
)
```

### Size Constraint

```sql
check (size_bytes >= 0)
```

### Chunk Count Constraint

```sql
check (chunk_count >= 0)
```

### Processing Version Constraint

```sql
check (processing_version >= 1)
```

---

## 17. Document Storage Uniqueness

Storage path should be unique for an active source object.

```sql
create unique index documents_storage_path_unique_idx
on public.documents (storage_bucket, storage_path)
where deleted_at is null;
```

Recommended path structure:

```text
organization_id/workspace_id/document_id/original_filename
```

---

## 18. Document Indexes

Recommended:

```sql
create index documents_workspace_status_idx
on public.documents (workspace_id, status)
where deleted_at is null;

create index documents_org_workspace_idx
on public.documents (organization_id, workspace_id)
where deleted_at is null;

create index documents_created_by_idx
on public.documents (created_by);

create index documents_created_at_idx
on public.documents (created_at desc);
```

Optional checksum index:

```sql
create index documents_checksum_idx
on public.documents (checksum_sha256)
where checksum_sha256 is not null;
```

Useful for duplicate detection.

---

## 19. document_chunks

### Purpose

Stores parsed and chunked knowledge units for retrieval.

### Vector Dimension

The exact vector dimension must match the configured Voyage embedding model.

Do not hard-code the dimension in multiple places.

For illustration only:

```sql
embedding vector(1024)
```

If a different model dimension is selected, the migration must use that value.

### Suggested Schema

```sql
create table public.document_chunks (
    id uuid primary key default gen_random_uuid(),

    organization_id uuid not null references public.organizations(id) on delete cascade,
    workspace_id uuid not null references public.workspaces(id) on delete cascade,
    document_id uuid not null references public.documents(id) on delete cascade,

    processing_version integer not null,

    chunk_index integer not null,

    content text not null,

    page_number integer,
    section_title text,
    heading text,

    token_count integer,

    metadata jsonb not null default '{}'::jsonb,

    embedding vector(1024),

    search_vector tsvector,

    created_at timestamptz not null default now()
);
```

---

## 20. Chunk Constraints

```sql
check (chunk_index >= 0)
```

If present:

```sql
check (page_number > 0)
```

If present:

```sql
check (token_count >= 0)
```

---

## 21. Chunk Uniqueness

A chunk is unique inside a processing version.

```sql
create unique index document_chunks_doc_version_chunk_unique_idx
on public.document_chunks (
    document_id,
    processing_version,
    chunk_index
);
```

This supports safe reprocessing.

---

## 22. Chunk Relational Indexes

Recommended:

```sql
create index document_chunks_workspace_idx
on public.document_chunks (workspace_id);

create index document_chunks_org_workspace_idx
on public.document_chunks (organization_id, workspace_id);

create index document_chunks_document_idx
on public.document_chunks (document_id);

create index document_chunks_doc_version_idx
on public.document_chunks (document_id, processing_version);
```

---

## 23. Full-Text Search Vector

Recommended generated/update strategy:

```sql
search_vector =
    to_tsvector(
        'english',
        coalesce(heading, '') || ' ' ||
        coalesce(section_title, '') || ' ' ||
        coalesce(content, '')
    )
```

This may be implemented as:

- generated column where compatible;
- trigger;
- explicit application insert/update.

The chosen mechanism must be documented and tested.

---

## 24. Full-Text Index

Recommended:

```sql
create index document_chunks_search_vector_gin_idx
on public.document_chunks
using gin (search_vector);
```

---

## 25. Vector Index Strategy

Initial pgvector index should be chosen based on actual data size and Supabase pgvector support.

Likely choices:

- HNSW;
- IVFFlat.

Recommended V1 default:

```text
HNSW
```

when supported and operationally suitable.

Conceptual example:

```sql
create index document_chunks_embedding_hnsw_idx
on public.document_chunks
using hnsw (embedding vector_cosine_ops);
```

The exact operator class must match the chosen similarity metric.

---

## 26. Similarity Metric

Default recommendation:

```text
cosine similarity
```

unless Voyage guidance or evaluation indicates another metric.

The retrieval implementation and index operator must be consistent.

---

## 27. Null Embeddings

A chunk should not be treated as searchable semantic evidence until it has a valid embedding.

Recommended retrieval predicate:

```sql
embedding is not null
```

Documents must not be marked `ready` if required chunks are missing embeddings.

---

## 28. Metadata JSON

`metadata jsonb` may include:

```json
{
  "source_type": "pdf",
  "language": "en",
  "table": false,
  "parser_element_type": "paragraph"
}
```

Do not move core relational fields into JSON merely for convenience.

Core fields such as:

- organization_id;
- workspace_id;
- document_id;
- page_number;
- chunk_index;

must remain first-class columns.

---

# PART III — CONVERSATIONS AND ANSWERS

## 29. conversations

### Purpose

Stores user chat sessions.

### Suggested Schema

```sql
create table public.conversations (
    id uuid primary key default gen_random_uuid(),

    organization_id uuid not null references public.organizations(id) on delete cascade,
    workspace_id uuid not null references public.workspaces(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,

    title text,
    status text not null default 'active',

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);
```

### Status Constraint

```sql
check (status in ('active', 'archived', 'deleted'))
```

### Indexes

```sql
create index conversations_user_workspace_idx
on public.conversations (user_id, workspace_id, updated_at desc)
where deleted_at is null;

create index conversations_org_workspace_idx
on public.conversations (organization_id, workspace_id)
where deleted_at is null;
```

---

## 30. messages

### Purpose

Stores user and assistant messages.

### Suggested Schema

```sql
create table public.messages (
    id uuid primary key default gen_random_uuid(),

    conversation_id uuid not null references public.conversations(id) on delete cascade,

    organization_id uuid not null references public.organizations(id) on delete cascade,
    workspace_id uuid not null references public.workspaces(id) on delete cascade,

    user_id uuid references public.profiles(id),

    role text not null,
    status text not null default 'completed',

    content text not null,

    model_provider text,
    model_name text,

    prompt_version text,

    input_tokens integer,
    output_tokens integer,

    latency_ms integer,

    error_code text,
    error_message text,

    created_at timestamptz not null default now(),
    completed_at timestamptz
);
```

### Role Constraint

```sql
check (role in ('user', 'assistant', 'system'))
```

System messages may be persisted only if needed.

### Status Constraint

```sql
check (status in ('pending', 'streaming', 'completed', 'failed', 'cancelled'))
```

---

## 31. Message Indexes

```sql
create index messages_conversation_created_idx
on public.messages (conversation_id, created_at);

create index messages_workspace_created_idx
on public.messages (workspace_id, created_at desc);

create index messages_user_created_idx
on public.messages (user_id, created_at desc)
where user_id is not null;
```

---

## 32. message_sources

### Purpose

Stores the exact evidence associated with an assistant answer.

This is essential for:

- citation display;
- debugging;
- RAG evaluation;
- traceability.

### Suggested Schema

```sql
create table public.message_sources (
    id uuid primary key default gen_random_uuid(),

    message_id uuid not null references public.messages(id) on delete cascade,

    organization_id uuid not null references public.organizations(id) on delete cascade,
    workspace_id uuid not null references public.workspaces(id) on delete cascade,

    document_id uuid not null references public.documents(id),
    chunk_id uuid not null references public.document_chunks(id),

    rank integer,
    retrieval_score double precision,
    rerank_score double precision,

    citation_label text,
    excerpt text,

    page_number integer,
    section_title text,

    created_at timestamptz not null default now()
);
```

---

## 33. Source Constraints

```sql
check (rank is null or rank > 0)
```

Do not fabricate a source record for evidence that was not included in the final context.

---

## 34. Source Indexes

```sql
create index message_sources_message_idx
on public.message_sources (message_id, rank);

create index message_sources_document_idx
on public.message_sources (document_id);
```

---

## 35. Citation Immutability

Once an assistant message is completed, its associated source set should normally remain unchanged.

This preserves historical truth about what evidence the answer used.

If answer regeneration occurs, create a new assistant message rather than silently rewriting the old evidence unless the product explicitly supports message replacement.

---

# PART IV — FEEDBACK, USAGE, AND AUDIT

## 36. feedback

### Purpose

Stores user evaluation of AI responses.

### Suggested Schema

```sql
create table public.feedback (
    id uuid primary key default gen_random_uuid(),

    organization_id uuid not null references public.organizations(id) on delete cascade,
    workspace_id uuid not null references public.workspaces(id) on delete cascade,

    message_id uuid not null references public.messages(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,

    rating text not null,
    comment text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

### Rating Constraint

```sql
check (rating in ('positive', 'negative'))
```

### Uniqueness

```sql
create unique index feedback_message_user_unique_idx
on public.feedback (message_id, user_id);
```

---

## 37. usage_events

### Purpose

Stores product usage and cost-attribution events.

### Suggested Schema

```sql
create table public.usage_events (
    id uuid primary key default gen_random_uuid(),

    organization_id uuid references public.organizations(id) on delete cascade,
    workspace_id uuid references public.workspaces(id) on delete cascade,
    user_id uuid references public.profiles(id) on delete set null,

    event_type text not null,

    quantity numeric,
    unit text,

    provider text,
    model text,

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now()
);
```

### Examples

```text
document_uploaded
bytes_processed
chunks_embedded
embedding_tokens
rerank_request
chat_request
llm_input_tokens
llm_output_tokens
```

---

## 38. Usage Indexes

```sql
create index usage_events_org_created_idx
on public.usage_events (organization_id, created_at desc);

create index usage_events_workspace_created_idx
on public.usage_events (workspace_id, created_at desc);

create index usage_events_type_created_idx
on public.usage_events (event_type, created_at desc);
```

---

## 39. audit_logs

### Purpose

Stores security- and administration-relevant activity.

### Suggested Schema

```sql
create table public.audit_logs (
    id uuid primary key default gen_random_uuid(),

    organization_id uuid references public.organizations(id) on delete set null,
    workspace_id uuid references public.workspaces(id) on delete set null,
    actor_user_id uuid references public.profiles(id) on delete set null,

    action text not null,
    entity_type text,
    entity_id uuid,

    request_id text,

    ip_address inet,
    user_agent text,

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now()
);
```

### Examples

```text
organization.created
organization.member_added
organization.member_role_changed
workspace.created
document.uploaded
document.deleted
document.reprocessed
security.access_denied
```

---

## 40. Audit Log Rules

Audit logs should be append-oriented.

Do not routinely update historical audit rows.

Sensitive values must not be stored unnecessarily.

Do not store:

- passwords;
- access tokens;
- private API keys;
- full document contents.

---

# PART V — INGESTION JOB STATE

## 41. ingestion_jobs

This table is optional but recommended once worker reliability matters.

Redis alone is not durable product state.

### Purpose

Tracks ingestion attempts and retries.

### Suggested Schema

```sql
create table public.ingestion_jobs (
    id uuid primary key default gen_random_uuid(),

    document_id uuid not null references public.documents(id) on delete cascade,
    organization_id uuid not null references public.organizations(id) on delete cascade,
    workspace_id uuid not null references public.workspaces(id) on delete cascade,

    processing_version integer not null,

    status text not null default 'queued',
    attempt integer not null default 0,

    queued_at timestamptz not null default now(),
    started_at timestamptz,
    completed_at timestamptz,

    error_code text,
    error_message text,

    worker_id text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

### Status Constraint

```sql
check (status in ('queued', 'processing', 'completed', 'failed', 'cancelled'))
```

---

## 42. Ingestion Job Indexes

```sql
create index ingestion_jobs_document_idx
on public.ingestion_jobs (document_id, created_at desc);

create index ingestion_jobs_status_idx
on public.ingestion_jobs (status, queued_at);
```

---

# PART VI — OPTIONAL INVITATIONS

## 43. organization_invites

May be added when invitation workflow is implemented.

### Suggested Schema

```sql
create table public.organization_invites (
    id uuid primary key default gen_random_uuid(),

    organization_id uuid not null references public.organizations(id) on delete cascade,

    email citext not null,
    role text not null default 'member',

    token_hash text not null,

    invited_by uuid not null references public.profiles(id),

    expires_at timestamptz not null,
    accepted_at timestamptz,
    revoked_at timestamptz,

    created_at timestamptz not null default now()
);
```

Never store plaintext invitation tokens.

---

# PART VII — RELATIONSHIP MODEL

## 44. Core Relationship Diagram

```text
auth.users
    |
    | 1:1
    v
profiles
    |
    +------------------------------+
    |                              |
    v                              v
organization_members          conversations
    |                              |
    v                              v
organizations                   messages
    |                              |
    v                              v
workspaces                   message_sources
    |
    +----------------------+
    |                      |
    v                      v
workspace_members        documents
                           |
                           v
                    document_chunks
```

---

## 45. Ownership Relationships

### Organization

Owns:

- workspaces;
- organization membership;
- documents indirectly;
- conversations indirectly;
- usage;
- audit logs.

### Workspace

Owns:

- workspace membership;
- documents;
- conversations;
- retrieval boundary.

### Document

Owns:

- document chunks;
- ingestion attempts.

### Conversation

Owns:

- messages.

### Assistant Message

Owns:

- message sources;
- feedback.

---

# PART VIII — ROW LEVEL SECURITY

## 46. RLS Philosophy

Supabase RLS should be used as a defense-in-depth control.

It does not replace backend authorization.

For security-sensitive tables:

```text
Backend authorization
+
RLS
+
tenant-filtered queries
```

is preferred.

---

## 47. RLS Enablement

Enable RLS on tables containing tenant-owned or user-owned data.

Recommended:

```text
profiles
organizations
organization_members
workspaces
workspace_members
documents
document_chunks
conversations
messages
message_sources
feedback
```

Tables accessed only through trusted backend/service-role paths may use restrictive policies while remaining unavailable directly to normal browser clients.

---

## 48. Browser vs Backend Access

The V1 architecture assumes most business operations go through FastAPI.

Therefore:

- browser receives normal Supabase Auth session;
- FastAPI validates identity;
- FastAPI may use controlled privileged database access;
- RLS remains an additional safety boundary.

Do not make the browser directly responsible for complex organization authorization.

---

## 49. Helper Authorization Functions

It may be useful to create PostgreSQL helper functions such as:

```sql
is_organization_member(organization_id uuid, user_id uuid)
```

and:

```sql
has_workspace_access(workspace_id uuid, user_id uuid)
```

These must be:

- deterministic where possible;
- security-reviewed;
- indexed through underlying tables;
- tested.

Avoid deeply nested policy logic duplicated across every table.

---

## 50. profiles RLS

Recommended behavior:

Users may:

- select their own profile;
- update permitted fields on their own profile.

Admins should not gain arbitrary profile-editing rights simply because they manage an organization.

---

## 51. organizations RLS

A user may select organizations where they have active membership.

Creation may happen through backend logic.

Updates should be limited to owner/admin roles.

---

## 52. organization_members RLS

A user may read memberships for organizations they belong to, depending on product UX.

Only authorized admins/owners may:

- invite;
- modify roles;
- remove membership.

A user must not escalate their own role.

---

## 53. workspaces RLS

A workspace is visible only if:

- the user has organization membership;
- and workspace access policy permits it.

If V1 treats all organization members as workspace members by default, the logic may be simplified.

---

## 54. documents RLS

A document is readable only if the user has access to its workspace.

Write operations require stronger roles.

Deletion must require authorization.

---

## 55. document_chunks RLS

Direct user access to chunks should generally be restricted.

Preferred:

- retrieval through backend;
- no public direct browsing of chunk rows.

If direct access exists, it must enforce workspace membership.

---

## 56. conversations RLS

Users should normally see only their own conversations unless future collaboration features are introduced.

Workspace admins do not automatically need access to private conversation content unless product policy explicitly allows it.

---

## 57. messages RLS

Message visibility follows conversation visibility.

Do not rely only on `user_id` inside messages because assistant messages may have null `user_id`.

Authorization should derive through conversation ownership and workspace access.

---

## 58. message_sources RLS

Sources follow the visibility of the associated assistant message.

Do not expose source rows merely because the document is accessible if the conversation itself is not.

---

## 59. feedback RLS

Users may:

- create feedback on messages they can access;
- update their own feedback.

Admins may receive aggregated analytics later.

---

# PART IX — RETRIEVAL SECURITY

## 60. Mandatory Retrieval Scope

Every retrieval query must apply:

```text
organization_id = authenticated organization
AND
workspace_id = authorized workspace
```

before ranking results.

Never:

```text
search globally
then filter in Python
```

---

## 61. Document State Filter

Retrieval should use only active ready documents.

Recommended predicate:

```text
documents.status = 'ready'
AND documents.deleted_at IS NULL
```

Chunk rows from failed or stale processing versions must not be treated as active.

---

## 62. Processing Version Filter

Document reprocessing may create multiple chunk versions.

Recommended retrieval should match:

```text
document_chunks.processing_version = documents.processing_version
```

This allows atomic version switching.

---

# PART X — REPROCESSING MODEL

## 63. Processing Version Strategy

Each document carries:

```text
processing_version
```

When reprocessing begins:

```text
current version = N
new version = N + 1
```

New chunks are inserted using version `N + 1`.

Only after successful completion:

```text
documents.processing_version = N + 1
```

Then old chunks may be deleted asynchronously.

This avoids a partially indexed document becoming visible.

---

## 64. Reprocessing Flow

```text
Document version 1 ready
        |
        v
Create ingestion job version 2
        |
        v
Parse
Chunk
Embed
Index
        |
        v
Validate
        |
        v
Switch active version to 2
        |
        v
Delete version 1 chunks later
```

---

# PART XI — DOCUMENT DELETION

## 65. Deletion Sequence

Recommended safe sequence:

```text
mark document deleting
    |
    v
prevent retrieval
    |
    v
delete document chunks
    |
    v
delete storage object
    |
    v
handle related source references according to retention policy
    |
    v
mark deleted or hard-delete metadata
```

The exact retention semantics for historical citations should be decided before hard deletion.

---

## 66. Historical Citation Retention

Potential conflict:

- deleting a source document;
- preserving historical assistant citations.

Recommended V1 behavior:

- source records may retain document title, page, excerpt, and chunk reference metadata;
- original binary may be removed;
- source link may become unavailable.

Do not silently rewrite historical answer evidence.

---

# PART XII — FULL-TEXT SEARCH DESIGN

## 67. Search Text Composition

Recommended weighted fields:

```text
heading       high weight
section_title medium weight
content       normal weight
```

Conceptual implementation:

```sql
setweight(to_tsvector('english', coalesce(heading,'')), 'A') ||
setweight(to_tsvector('english', coalesce(section_title,'')), 'B') ||
setweight(to_tsvector('english', coalesce(content,'')), 'C')
```

This can improve exact-heading recall.

---

## 68. Language Considerations

The initial FTS configuration may use English.

If multilingual documents become common, evaluate:

- `simple` configuration;
- language detection;
- per-document configuration;
- separate search fields.

Do not assume all future knowledge is English.

---

# PART XIII — VECTOR SEARCH DESIGN

## 69. Embedding Storage

One embedding per chunk.

Do not store repeated embeddings in unrelated tables.

Query embeddings do not need to be persisted by default.

---

## 70. Similarity Query

Conceptual pattern:

```sql
select
    id,
    document_id,
    content,
    1 - (embedding <=> :query_embedding) as similarity
from document_chunks
where
    organization_id = :organization_id
    and workspace_id = :workspace_id
    and processing_version = :active_version
order by embedding <=> :query_embedding
limit :limit;
```

Actual query must account for active document states and processing versions.

---

## 71. Vector Candidate Count

Candidate counts belong in application configuration.

Do not hard-code arbitrary values into SQL functions without documentation.

Example:

```text
VECTOR_CANDIDATE_LIMIT=30
```

---

# PART XIV — HYBRID SEARCH

## 72. Candidate Sources

Hybrid retrieval combines:

```text
vector candidates
+
keyword candidates
```

Candidate fusion occurs in application logic or a controlled SQL function.

---

## 73. Fusion Metadata

For observability, candidate records may track:

```text
vector_rank
keyword_rank
vector_score
keyword_score
fusion_score
```

Not all must be persisted permanently.

They may be logged or included in retrieval diagnostics.

---

## 74. Reranking

After candidate fusion:

```text
20–40 candidates
    |
    v
Voyage reranker
    |
    v
top 5–10 evidence chunks
```

Final `message_sources` should store rerank score where available.

---

# PART XV — DATA INTEGRITY

## 75. Foreign Keys

Use foreign keys consistently.

Do not allow orphan:

- workspace documents;
- document chunks;
- conversation messages;
- message sources.

---

## 76. Cross-Tenant Integrity

Application code must verify that related foreign IDs belong to the same tenant.

For example:

A document insert must ensure:

```text
workspace.organization_id = document.organization_id
```

PostgreSQL simple foreign keys do not enforce this automatically when separate fields exist.

Potential strategies:

- application validation;
- composite foreign keys;
- database trigger;
- constrained domain functions.

The chosen strategy must be tested.

---

## 77. Composite Integrity Recommendation

Where practical, use composite uniqueness to support stronger foreign keys.

Example:

```sql
create unique index workspaces_id_org_unique_idx
on workspaces (id, organization_id);
```

Then documents may reference:

```text
(workspace_id, organization_id)
```

This improves tenant integrity.

The implementation may choose this pattern selectively where complexity remains manageable.

---

## 78. Required Consistency Checks

At minimum validate:

- workspace belongs to organization;
- document belongs to workspace;
- chunk belongs to document/workspace/org;
- conversation belongs to workspace/org;
- source belongs to message/workspace/org.

---

# PART XVI — INDEXING STRATEGY

## 79. General Index Rules

Index:

- foreign keys used in joins;
- tenant filters;
- workspace filters;
- status filters;
- timestamp sorting;
- full-text vectors;
- vector embeddings.

Do not create indexes speculatively without workload justification.

---

## 80. Organization-Centric Indexes

Typical:

```text
organization_members(organization_id)
workspaces(organization_id)
documents(organization_id, workspace_id)
conversations(organization_id, workspace_id)
usage_events(organization_id, created_at)
audit_logs(organization_id, created_at)
```

---

## 81. User-Centric Indexes

Typical:

```text
organization_members(user_id)
workspace_members(user_id)
conversations(user_id, updated_at)
feedback(user_id)
```

---

## 82. Partial Indexes

Use partial indexes to exclude deleted rows where useful.

Example:

```sql
create index documents_active_workspace_idx
on documents (workspace_id, created_at desc)
where deleted_at is null;
```

---

# PART XVII — UPDATED_AT STRATEGY

## 83. Automatic Timestamps

Use one consistent strategy for `updated_at`.

Recommended:

- database trigger.

Example conceptual function:

```sql
create function set_updated_at()
returns trigger
...
```

Apply only to mutable tables.

---

# PART XVIII — MIGRATION POLICY

## 84. Migration Tool

Backend migrations use:

```text
Alembic
```

Supabase SQL migrations may also exist where Supabase-specific configuration is required.

The project must avoid two uncontrolled competing migration histories.

---

## 85. Canonical Migration Ownership

Recommended:

- Alembic owns application schema;
- explicit SQL migration files may be used for pgvector, RLS, advanced indexes, and PostgreSQL-specific functions;
- all migrations remain version-controlled.

The project must document the exact execution order in `DEPLOYMENT.md`.

---

## 86. Migration Rules

Every schema change must:

1. be represented by a migration;
2. be committed;
3. preserve existing data where possible;
4. include relevant indexes;
5. include constraints;
6. update models;
7. update schemas;
8. update tests;
9. update this document if canonical design changes.

---

## 87. Never Rewrite Applied Migrations

Once a migration has been applied to shared staging or production:

```text
do not edit it
```

Create a new migration.

---

## 88. Destructive Migrations

Examples:

- dropping table;
- dropping column;
- changing incompatible type;
- truncating data;
- vector dimension change.

Require:

- explicit review;
- backup;
- migration plan;
- rollback strategy;
- production approval.

---

## 89. Expand-and-Contract Pattern

For risky changes:

1. add new field/table;
2. write both where needed;
3. migrate data;
4. switch reads;
5. verify;
6. remove old structure later.

Avoid one-step destructive production migrations where possible.

---

# PART XIX — EMBEDDING MODEL MIGRATION

## 90. Embedding Dimension Change

Changing embedding model may change:

- vector dimensions;
- semantic behavior;
- index compatibility.

Do not modify the vector column casually.

Recommended migration strategy:

```text
new embedding column/table/version
→ re-embed documents
→ validate retrieval
→ switch active model/version
→ remove old embeddings later
```

---

## 91. Embedding Metadata

Store enough metadata to know how a chunk was embedded.

Recommended fields:

```text
documents.embedding_provider
documents.embedding_model
documents.embedding_dimension
```

If multiple embedding versions coexist per chunk in the future, create a separate embeddings table rather than overloading one column.

---

# PART XX — RLS IMPLEMENTATION PRINCIPLES

## 92. Service Role

The Supabase service-role key bypasses RLS.

Therefore:

- it must exist only in trusted backend environments;
- it must never be exposed to the frontend;
- backend authorization must run before privileged operations;
- use should be minimized and explicit.

---

## 93. Anon Key

The browser may use the anon key for supported Supabase Auth flows.

Do not treat the anon key as a secret.

Security depends on:

- user session;
- RLS;
- backend authorization.

---

## 94. Policy Testing

Every RLS policy must have tests for:

- authorized access;
- unauthorized same-org access where relevant;
- unauthorized cross-org access;
- revoked membership;
- deleted workspace;
- suspended user if supported.

---

# PART XXI — DATABASE FUNCTIONS

## 95. Use of SQL Functions

SQL functions may be useful for:

- tenant-safe vector search;
- hybrid search;
- membership checks.

Functions must not hide unbounded access.

If a `security definer` function is used:

- set secure `search_path`;
- validate user context;
- review carefully;
- test cross-tenant behavior.

---

## 96. Retrieval RPC

A database function may expose tenant-safe semantic retrieval.

Example conceptual signature:

```text
match_document_chunks(
    p_organization_id uuid,
    p_workspace_id uuid,
    p_query_embedding vector,
    p_limit integer
)
```

However, backend authorization must still prove the caller can access the supplied workspace.

---

# PART XXII — DATA RETENTION

## 97. Document Retention

V1 should support deletion.

Future enterprise retention may add:

- retention windows;
- legal hold;
- admin policy;
- delayed purge.

Do not implement complex retention until required.

---

## 98. Conversation Retention

Conversations persist until:

- user deletion;
- organization policy;
- account deletion;
- future retention rules.

---

## 99. Audit Retention

Audit data should generally live longer than ordinary interaction data.

Exact retention duration will be defined by future policy.

---

# PART XXIII — BACKUPS

## 100. Database Backups

Production must rely on Supabase backup capabilities appropriate to the selected plan.

Deployment documentation must define:

- backup frequency;
- restore procedure;
- responsible operator;
- restore testing.

---

## 101. Storage Backup

Source files live in Supabase Storage.

The project should define future backup/export policy for critical customer files.

Do not assume database backup automatically includes binary storage.

---

# PART XXIV — DEVELOPMENT AND TEST DATABASES

## 102. Environment Isolation

Use separate projects/databases for:

- development;
- staging;
- production.

Do not run automated tests against production.

---

## 103. Test Data

Tests should use synthetic organizations and users.

Recommended fixture pattern:

```text
Organization A
    Workspace A1
    User A

Organization B
    Workspace B1
    User B
```

Cross-tenant tests must intentionally attempt forbidden access.

---

## 104. Seed Data

Development seed scripts may create:

- sample organizations;
- sample workspaces;
- sample documents metadata;
- sample conversations.

Never seed production automatically.

---

# PART XXV — DATABASE NAMING CONVENTIONS

## 105. Table Names

Use:

```text
snake_case
plural nouns
```

Examples:

```text
organization_members
document_chunks
message_sources
```

---

## 106. Column Names

Use:

```text
snake_case
```

Prefer explicit names:

```text
organization_id
workspace_id
created_at
processing_version
```

Avoid ambiguous names like:

```text
org
ws
data1
status2
```

---

## 107. Foreign Key Names

Use consistent convention if explicitly named:

```text
fk_<table>_<column>
```

Example:

```text
fk_documents_workspace_id
```

---

## 108. Index Names

Recommended convention:

```text
<table>_<columns>_idx
```

Example:

```text
documents_workspace_status_idx
```

---

# PART XXVI — CANONICAL V1 TABLE SUMMARY

## 109. Required V1 Tables

Required:

```text
profiles
organizations
organization_members
workspaces
workspace_members
documents
document_chunks
conversations
messages
message_sources
feedback
usage_events
audit_logs
```

Recommended:

```text
ingestion_jobs
```

Conditional:

```text
organization_invites
api_keys
workspace_settings
```

---

# PART XXVII — TABLE RESPONSIBILITY SUMMARY

## 110. profiles

Owns application profile metadata.

## 111. organizations

Owns tenant identity.

## 112. organization_members

Owns organization membership and roles.

## 113. workspaces

Owns knowledge boundaries.

## 114. workspace_members

Owns workspace-specific access.

## 115. documents

Owns source document lifecycle and metadata.

## 116. document_chunks

Owns parsed retrieval units and embeddings.

## 117. conversations

Owns chat sessions.

## 118. messages

Owns conversation messages.

## 119. message_sources

Owns answer-to-evidence mapping.

## 120. feedback

Owns user evaluation.

## 121. usage_events

Owns metering/analytics events.

## 122. audit_logs

Owns administrative/security history.

## 123. ingestion_jobs

Owns durable ingestion-attempt state.

---

# PART XXVIII — SECURITY INVARIANTS

## 124. Invariant 1

No row belonging to Organization A may be visible to Organization B unless an explicitly documented cross-tenant feature exists.

---

## 125. Invariant 2

No chunk may be retrieved outside the workspace authorization boundary.

---

## 126. Invariant 3

A client-supplied `organization_id` or `workspace_id` is never sufficient proof of access.

---

## 127. Invariant 4

Supabase service-role credentials never exist in browser-delivered code.

---

## 128. Invariant 5

A document is not searchable until its active processing version is complete.

---

## 129. Invariant 6

Citations correspond to actual final evidence used for the answer.

---

## 130. Invariant 7

Deleted or non-ready documents do not participate in retrieval.

---

# PART XXIX — DATABASE ACCEPTANCE CRITERIA

## 131. V1 Database Is Acceptable When

1. users map correctly to Supabase Auth;
2. organizations are isolated;
3. membership roles are constrained;
4. workspaces belong to organizations;
5. workspace access is enforceable;
6. documents carry tenant identifiers;
7. document chunks carry tenant identifiers;
8. pgvector is enabled;
9. FTS is indexed;
10. vector index exists;
11. embeddings match configured dimension;
12. ingestion state is durable;
13. document reprocessing is version-safe;
14. conversations persist;
15. messages persist;
16. citations persist;
17. feedback persists;
18. usage events can be recorded;
19. audit events can be recorded;
20. RLS policies are tested;
21. cross-tenant retrieval tests fail closed;
22. migrations reproduce the schema from scratch;
23. staging can migrate cleanly;
24. production migrations do not require manual ad-hoc SQL.

---

# PART XXX — INITIAL IMPLEMENTATION ORDER

## 132. Recommended Schema Build Sequence

### Phase 1

Create:

```text
profiles
organizations
organization_members
workspaces
workspace_members
```

### Phase 2

Create:

```text
documents
ingestion_jobs
```

### Phase 3

Enable:

```text
pgvector
```

Create:

```text
document_chunks
FTS
vector index
```

### Phase 4

Create:

```text
conversations
messages
message_sources
feedback
```

### Phase 5

Create:

```text
usage_events
audit_logs
```

### Phase 6

Implement and test:

```text
RLS
tenant-safe retrieval functions
```

---

# PART XXXI — OPEN IMPLEMENTATION DECISIONS

## 133. Decisions Still To Be Finalized

The following implementation-level choices may be finalized during development:

1. exact Voyage embedding model;
2. exact embedding dimension;
3. HNSW parameters;
4. parser choice between Docling and Unstructured;
5. exact worker library;
6. whether FTS uses generated column, trigger, or explicit writes;
7. whether ingestion jobs become mandatory in first milestone;
8. exact RLS helper function design;
9. exact hard-delete vs tombstone behavior for conversations;
10. exact historical source behavior after document deletion.

These do not change the fundamental data architecture.

---

# PART XXXII — DO NOT DO

## 134. Prohibited Database Shortcuts

Agents and developers must not:

- put all organization data into one unscoped table;
- rely only on frontend filtering;
- search vectors globally then filter in Python;
- store source documents as PostgreSQL blobs;
- duplicate Supabase Auth password data;
- expose service-role credentials;
- manually patch production schema without migration;
- silently change embedding dimension;
- mark documents ready before chunks are complete;
- delete source records without considering historical citations;
- store secrets in audit metadata;
- create a second production database for convenience;
- introduce Qdrant/Weaviate/Pinecone without an ADR;
- use JSONB as a substitute for core relational design.

---

## 135. Summary

Bismark AI V1 uses Supabase PostgreSQL as the authoritative data store.

The schema is centered on:

```text
organization
    |
    v
workspace
    |
    +--> documents
    |       |
    |       v
    |   document_chunks
    |
    +--> conversations
            |
            v
          messages
            |
            v
      message_sources
```

Security is enforced through:

```text
FastAPI authorization
+
tenant-scoped SQL
+
RLS
+
retrieval-time filtering
```

Retrieval uses:

```text
pgvector
+
PostgreSQL full-text search
+
Voyage reranking
```

The design intentionally keeps:

- relational ownership;
- vector search;
- authorization;
- citations;
- ingestion state;

inside one coherent PostgreSQL data model.

This schema should remain simple enough for rapid development while strong enough to support secure multi-tenant enterprise knowledge retrieval.
