# API.md — Bismark AI API Specification

**Project:** Bismark AI  
**Document Type:** Canonical REST API Contract  
**Status:** V1 API Specification  
**Version:** 1.0  
**Primary Backend:** FastAPI  
**Base Path:** `/api/v1`  
**Audience:** Backend Engineering, Frontend Engineering, QA, Security, DevOps, and Agentic Coding Systems

## Current implementation scope

Implemented: `/health`, `/ready` (process), `/ready/database` (database), and
GET/POST `/api/v1/me`. Other routes below remain target contracts.

Phase 1C GET `/api/v1/me` returns only `{id, email, display_name}` from the
verified identity and existing profile. Missing profiles return 404
`PROFILE_NOT_FOUND`. POST `/api/v1/me` initializes the verified user's profile
idempotently and returns the same response with HTTP 200. It accepts no identity
or profile fields; supplied bodies/IDs cannot choose another user. Existing names
are preserved. No membership is created. The browser calls POST only after GET
returns 404. Future avatar/timezone/locale/organization fields below are not yet
implemented and are not synthesized.

Both routes require `Authorization: Bearer <access_token>` and return
`Cache-Control: no-store`. Auth errors use the standard error envelope and
`X-Request-ID`: 401 `AUTHENTICATION_REQUIRED` for missing credentials, 401
`TOKEN_INVALID` for invalid/expired credentials, 503 `AUTH_UNAVAILABLE` for
provider failure/unconfigured auth, and 503 `DATABASE_UNAVAILABLE` for profile
storage failure. Supabase does not reliably distinguish expired tokens in this
adapter, so `TOKEN_EXPIRED` remains reserved. 401 includes `WWW-Authenticate`.
Health endpoints retain their existing response format.

---

## 1. Purpose

This document defines the canonical HTTP API contract for Bismark AI V1.

It specifies:

- endpoint structure;
- authentication requirements;
- authorization expectations;
- request and response conventions;
- error handling;
- pagination;
- idempotency;
- streaming;
- organization and workspace routes;
- document routes;
- chat routes;
- conversation routes;
- feedback routes;
- health routes;
- audit and usage boundaries.

Documentation authority follows the canonical order in [AGENTS.md §2](../AGENTS.md#2-documentation-authority).
`PROJECT_STATE.md` reports current implementation state and does not override architectural decisions.

If implementation diverges from this API contract, update this document in the same change.

---

## 2. API Design Principles

The Bismark AI API should be:

- versioned;
- explicit;
- tenant-aware;
- secure by default;
- consistent;
- predictable;
- easy for the frontend to consume;
- friendly to typed SDK generation;
- observable;
- safe for retry where appropriate.

Prefer boring, clear REST contracts over clever endpoint design.

---

## 3. Base URL

Production example:

```text
https://api.bismark.ai/api/v1
```

Environment-specific examples:

```text
https://api.staging.bismark.ai/api/v1
http://localhost:8000/api/v1
```

Never hard-code production URLs into application logic.

---

## 4. API Versioning

The initial API version is:

```text
v1
```

Base path:

```text
/api/v1
```

Breaking contract changes should require:

- a new version;
- or a documented migration strategy.

Do not silently break deployed clients.

---

## 5. Content Types

Default JSON request type:

```http
Content-Type: application/json
```

Default JSON response type:

```http
Content-Type: application/json
```

File upload endpoints use:

```http
multipart/form-data
```

Streaming chat may use:

```http
text/event-stream
```

or another explicitly documented streaming media type.

---

## 6. Authentication

Protected endpoints require an authenticated Supabase session token.

Recommended header:

```http
Authorization: Bearer <access_token>
```

FastAPI must validate the token and resolve the authenticated user.

The frontend must never send a user ID as proof of identity.

---

## 7. Authorization

Authentication answers:

```text
Who is the user?
```

Authorization answers:

```text
What can the user access?
```

Every protected endpoint must validate:

- authenticated user;
- organization membership;
- workspace access when applicable;
- role/permission where applicable.

Client-provided `organization_id` or `workspace_id` must never be trusted without verification.

---

## 8. Request ID

Every request should have a request identifier.

Recommended behavior:

- accept `X-Request-ID` if valid;
- otherwise generate one;
- include it in logs;
- include it in response headers;
- include it in error bodies where useful.

Response header:

```http
X-Request-ID: 9f1d...
```

---

## 9. Standard Success Response

Resource endpoints may return the resource directly.

Example:

```json
{
  "id": "uuid",
  "name": "HR",
  "created_at": "2026-09-23T20:00:00Z"
}
```

Collection endpoints should use a consistent envelope.

Example:

```json
{
  "items": [],
  "next_cursor": null
}
```

---

## 10. Standard Error Format

All API errors should follow a common shape.

Recommended:

```json
{
  "error": {
    "code": "WORKSPACE_ACCESS_DENIED",
    "message": "You do not have access to this workspace.",
    "details": null,
    "request_id": "9f1d..."
  }
}
```

### Error Fields

- `code`: stable machine-readable error code;
- `message`: user-safe description;
- `details`: optional structured metadata;
- `request_id`: trace identifier.

Do not expose stack traces in production responses.

---

## 11. HTTP Status Conventions

Use standard semantics.

### 200 OK

Successful read or update.

### 201 Created

Successful resource creation.

### 202 Accepted

Accepted asynchronous operation.

Examples:

- document ingestion queued.

### 204 No Content

Successful delete or action with no body where appropriate.

### 400 Bad Request

Malformed or logically invalid request.

### 401 Unauthorized

Missing or invalid authentication.

### 403 Forbidden

Authenticated but not allowed.

### 404 Not Found

Resource does not exist or should not be revealed.

### 409 Conflict

State conflict.

Examples:

- duplicate organization slug;
- retry not allowed in current state.

### 413 Payload Too Large

Upload exceeds configured maximum.

### 415 Unsupported Media Type

Unsupported file type.

### 422 Unprocessable Entity

Pydantic/schema validation failure.

### 429 Too Many Requests

Rate limit exceeded.

### 500 Internal Server Error

Unexpected server failure.

### 502 Bad Gateway

External provider failure if surfaced at gateway level.

### 503 Service Unavailable

Temporary dependency or readiness failure.

---

## 12. Pagination

Large collections must use pagination.

Preferred V1 pattern:

```text
cursor pagination
```

Example request:

```http
GET /api/v1/documents?limit=20&cursor=...
```

Example response:

```json
{
  "items": [],
  "next_cursor": "opaque-token"
}
```

### Default Limit

Recommended:

```text
20
```

### Maximum Limit

Recommended:

```text
100
```

Do not expose raw offset pagination for large frequently changing datasets unless specifically needed.

---

## 13. Sorting

Where supported:

```text
sort=created_at
order=desc
```

Only documented sortable fields should be accepted.

Reject unsupported sort fields rather than interpolating arbitrary SQL identifiers.

---

## 14. Filtering

Filtering should be explicit.

Example:

```http
GET /documents?status=ready
```

Do not expose generic client-defined SQL-like filtering.

---

## 15. Idempotency

For endpoints where retries may create duplicates, support an idempotency key.

Recommended header:

```http
Idempotency-Key: <opaque-client-key>
```

Likely candidates:

- organization creation;
- document upload metadata creation;
- chat submission;
- invitation creation;
- future billing actions.

Exact implementation may be phased.

---

# PART I — AUTHENTICATED USER

## 16. GET `/me`

Returns the current authenticated Bismark AI user profile.

### Auth

Required.

### Response

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "User Name",
  "avatar_url": null,
  "timezone": "Africa/Lagos",
  "locale": "en",
  "organizations": [
    {
      "id": "uuid",
      "name": "Acme Ltd",
      "slug": "acme",
      "role": "owner"
    }
  ]
}
```

### Errors

- `401 AUTHENTICATION_REQUIRED`
- `404 PROFILE_NOT_FOUND`

---

## 17. PATCH `/me`

Updates permitted profile fields.

### Auth

Required.

### Request

```json
{
  "display_name": "User Name",
  "timezone": "Africa/Lagos",
  "locale": "en"
}
```

### Response

Updated profile.

### Restrictions

Users may not change:

- their internal user ID;
- organization roles;
- service-level security fields.

---

# PART II — ORGANIZATIONS

## 18. POST `/organizations`

Creates an organization.

### Auth

Required.

### Request

```json
{
  "name": "Acme Ltd",
  "slug": "acme"
}
```

### Behavior

Server must:

1. validate authenticated user;
2. validate name and slug;
3. create organization;
4. create owner membership;
5. write audit event;
6. return created organization.

Prefer transactional creation.

### Response

`201 Created`

```json
{
  "id": "uuid",
  "name": "Acme Ltd",
  "slug": "acme",
  "status": "active",
  "role": "owner",
  "created_at": "2026-09-23T20:00:00Z"
}
```

### Errors

- `409 ORGANIZATION_SLUG_EXISTS`
- `422 VALIDATION_ERROR`

---

## 19. GET `/organizations`

Returns organizations available to the authenticated user.

### Auth

Required.

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Acme Ltd",
      "slug": "acme",
      "role": "owner",
      "status": "active"
    }
  ],
  "next_cursor": null
}
```

---

## 20. GET `/organizations/{organization_id}`

Returns organization details.

### Auth

Required.

### Authorization

Active organization membership required.

### Response

```json
{
  "id": "uuid",
  "name": "Acme Ltd",
  "slug": "acme",
  "status": "active",
  "role": "admin",
  "created_at": "..."
}
```

### Errors

- `404 ORGANIZATION_NOT_FOUND`
- `403 ORGANIZATION_ACCESS_DENIED`

Where disclosure is sensitive, implementation may return 404 instead of 403.

---

## 21. PATCH `/organizations/{organization_id}`

Updates organization metadata.

### Auth

Required.

### Authorization

Owner or admin.

### Request

```json
{
  "name": "Acme Group",
  "slug": "acme-group"
}
```

### Response

Updated organization.

### Audit

Required.

---

## 22. DELETE `/organizations/{organization_id}`

Deletes or schedules deletion of an organization.

### Auth

Required.

### Authorization

Owner only.

### V1 Recommendation

Prefer soft deletion / controlled destructive flow.

### Response

`202 Accepted` or `204 No Content`

### Safety

Must not perform irreversible tenant destruction without explicit product confirmation flow.

---

# PART III — ORGANIZATION MEMBERS

## 23. GET `/organizations/{organization_id}/members`

Lists organization members.

### Auth

Required.

### Authorization

Organization membership required.

### Response

```json
{
  "items": [
    {
      "id": "membership-uuid",
      "user_id": "uuid",
      "display_name": "Jane Doe",
      "email": "jane@example.com",
      "role": "member",
      "status": "active",
      "joined_at": "..."
    }
  ],
  "next_cursor": null
}
```

---

## 24. POST `/organizations/{organization_id}/invites`

Creates an invitation.

### Auth

Required.

### Authorization

Owner/admin.

### Request

```json
{
  "email": "newuser@example.com",
  "role": "member"
}
```

### Response

`201 Created`

```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "role": "member",
  "status": "pending",
  "expires_at": "..."
}
```

### Notes

Never return plaintext invite token after initial delivery if not required.

---

## 25. PATCH `/organizations/{organization_id}/members/{user_id}`

Changes member role/status.

### Auth

Required.

### Authorization

Owner/admin, with safeguards.

### Request

```json
{
  "role": "admin"
}
```

### Rules

Must prevent unsafe actions such as:

- member escalating self;
- removing last owner;
- admin promoting beyond permitted capability if policy disallows it.

### Audit

Required.

---

## 26. DELETE `/organizations/{organization_id}/members/{user_id}`

Removes organization membership.

### Auth

Required.

### Authorization

Owner/admin, subject to role rules.

### Response

`204 No Content`

### Audit

Required.

---

# PART IV — WORKSPACES

## 27. POST `/organizations/{organization_id}/workspaces`

Creates a workspace.

### Auth

Required.

### Authorization

Owner/admin.

### Request

```json
{
  "name": "HR",
  "slug": "hr",
  "description": "Human resources knowledge"
}
```

### Response

`201 Created`

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "name": "HR",
  "slug": "hr",
  "description": "Human resources knowledge",
  "status": "active",
  "created_at": "..."
}
```

---

## 28. GET `/organizations/{organization_id}/workspaces`

Lists workspaces visible to current user.

### Auth

Required.

### Authorization

Organization membership and workspace visibility rules.

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "HR",
      "slug": "hr",
      "description": "Human resources knowledge",
      "role": "member",
      "status": "active"
    }
  ],
  "next_cursor": null
}
```

---

## 29. GET `/workspaces/{workspace_id}`

Returns workspace details.

### Auth

Required.

### Authorization

Workspace access required.

---

## 30. PATCH `/workspaces/{workspace_id}`

Updates workspace metadata.

### Auth

Required.

### Authorization

Workspace admin or organization owner/admin.

### Request

```json
{
  "name": "People Operations",
  "description": "HR policies and procedures"
}
```

### Audit

Required.

---

## 31. DELETE `/workspaces/{workspace_id}`

Deletes or archives workspace.

### Auth

Required.

### Authorization

Organization owner/admin.

### V1 Recommendation

Prefer controlled soft delete/archive.

### Audit

Required.

---

# PART V — WORKSPACE MEMBERS

## 32. GET `/workspaces/{workspace_id}/members`

Lists workspace members.

### Auth

Required.

### Authorization

Workspace access required.

---

## 33. POST `/workspaces/{workspace_id}/members`

Adds an existing organization member to workspace.

### Auth

Required.

### Authorization

Workspace admin or org admin/owner.

### Request

```json
{
  "user_id": "uuid",
  "role": "member"
}
```

### Response

`201 Created`

---

## 34. PATCH `/workspaces/{workspace_id}/members/{user_id}`

Updates workspace role.

### Auth

Required.

### Authorization

Workspace admin or org admin/owner.

---

## 35. DELETE `/workspaces/{workspace_id}/members/{user_id}`

Removes user from workspace.

### Auth

Required.

### Authorization

Workspace admin or org admin/owner.

---

# PART VI — DOCUMENTS

## 36. POST `/workspaces/{workspace_id}/documents`

Uploads a document.

### Auth

Required.

### Authorization

Workspace upload permission required.

### Content Type

```http
multipart/form-data
```

### Request Parts

Recommended:

```text
file
display_name (optional)
```

### Server Flow

1. authenticate;
2. authorize workspace;
3. validate file size;
4. validate file type;
5. create document ID;
6. determine private storage path;
7. upload to Supabase Storage;
8. create document record;
9. create ingestion job;
10. enqueue worker job;
11. return immediately.

### Response

`202 Accepted`

```json
{
  "id": "document-uuid",
  "workspace_id": "workspace-uuid",
  "display_name": "Employee Handbook",
  "filename": "employee-handbook.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1845520,
  "status": "queued",
  "created_at": "..."
}
```

### Errors

- `413 FILE_TOO_LARGE`
- `415 FILE_TYPE_NOT_SUPPORTED`
- `403 DOCUMENT_UPLOAD_DENIED`
- `502 STORAGE_UPLOAD_FAILED`

---

## 37. GET `/workspaces/{workspace_id}/documents`

Lists documents in workspace.

### Auth

Required.

### Authorization

Workspace access required.

### Filters

Potential:

```text
status
mime_type
created_by
```

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "display_name": "Employee Handbook",
      "filename": "employee-handbook.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 1845520,
      "status": "ready",
      "chunk_count": 93,
      "created_by": {
        "id": "uuid",
        "display_name": "Jane Doe"
      },
      "created_at": "...",
      "processing_completed_at": "..."
    }
  ],
  "next_cursor": null
}
```

---

## 38. GET `/documents/{document_id}`

Returns document metadata.

### Auth

Required.

### Authorization

Workspace access required.

### Response

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "workspace_id": "uuid",
  "display_name": "Employee Handbook",
  "filename": "employee-handbook.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1845520,
  "status": "ready",
  "chunk_count": 93,
  "parser_name": "docling",
  "embedding_model": "configured-model",
  "created_at": "...",
  "processing_started_at": "...",
  "processing_completed_at": "...",
  "error": null
}
```

---

## 39. GET `/documents/{document_id}/status`

Returns compact processing status.

### Auth

Required.

### Authorization

Workspace access required.

### Response

```json
{
  "id": "uuid",
  "status": "processing",
  "progress": null,
  "error": null,
  "updated_at": "..."
}
```

V1 does not require exact percentage progress.

---

## 40. POST `/documents/{document_id}/retry`

Retries failed document processing.

### Auth

Required.

### Authorization

Upload/manage permission required.

### Allowed State

Usually:

```text
failed
```

### Response

`202 Accepted`

```json
{
  "id": "uuid",
  "status": "queued",
  "processing_version": 2
}
```

### Errors

- `409 DOCUMENT_RETRY_NOT_ALLOWED`
- `403 DOCUMENT_MANAGE_DENIED`

---

## 41. DELETE `/documents/{document_id}`

Deletes document.

### Auth

Required.

### Authorization

Manage permission required.

### Behavior

Should:

- block retrieval;
- transition to deleting if asynchronous;
- remove chunks;
- remove storage object;
- preserve historical source metadata according to retention policy;
- write audit event.

### Response

`202 Accepted` or `204 No Content`

---

## 42. GET `/documents/{document_id}/source`

Returns an authorized source-access URL or proxied source.

### Auth

Required.

### Authorization

Workspace access required.

### Recommended Response

Short-lived signed URL:

```json
{
  "url": "https://...",
  "expires_at": "..."
}
```

Do not expose permanent public URLs for private documents.

---

# PART VII — CONVERSATIONS

## 43. POST `/workspaces/{workspace_id}/conversations`

Creates a conversation.

### Auth

Required.

### Authorization

Workspace access required.

### Request

```json
{
  "title": null
}
```

### Response

`201 Created`

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "title": null,
  "status": "active",
  "created_at": "..."
}
```

---

## 44. GET `/workspaces/{workspace_id}/conversations`

Lists current user's conversations in workspace.

### Auth

Required.

### Authorization

Workspace access required.

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Annual Leave Policy",
      "updated_at": "...",
      "created_at": "..."
    }
  ],
  "next_cursor": null
}
```

---

## 45. GET `/conversations/{conversation_id}`

Returns conversation metadata and optionally messages.

### Auth

Required.

### Authorization

Conversation ownership/access required.

### Suggested Query

```text
include_messages=true
```

### Response

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "title": "Annual Leave Policy",
  "status": "active",
  "messages": []
}
```

---

## 46. PATCH `/conversations/{conversation_id}`

Updates conversation metadata.

### Request

```json
{
  "title": "Leave Policy"
}
```

### Authorization

Conversation owner.

---

## 47. DELETE `/conversations/{conversation_id}`

Deletes/archives conversation.

### Authorization

Conversation owner.

### Response

`204 No Content`

---

# PART VIII — CHAT

## 48. POST `/conversations/{conversation_id}/messages`

Submits a user question and starts assistant generation.

### Auth

Required.

### Authorization

Conversation owner and workspace access required.

### Request

```json
{
  "content": "How many annual leave days do employees receive?"
}
```

### Non-Streaming Response Option

For clients that do not use streaming:

```json
{
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "How many annual leave days do employees receive?"
  },
  "assistant_message": {
    "id": "uuid",
    "role": "assistant",
    "status": "completed",
    "content": "Employees receive ...",
    "sources": []
  }
}
```

### Preferred V1

Streaming is preferred.

---

## 49. POST `/conversations/{conversation_id}/messages/stream`

Starts streamed chat generation.

### Auth

Required.

### Authorization

Conversation owner and workspace access required.

### Request

```json
{
  "content": "How many annual leave days do employees receive?"
}
```

### Response Type

Recommended:

```http
Content-Type: text/event-stream
```

---

## 50. Streaming Event Contract

Recommended event types:

### `message.created`

```json
{
  "user_message_id": "uuid",
  "assistant_message_id": "uuid"
}
```

### `retrieval.started`

```json
{
  "workspace_id": "uuid"
}
```

### `retrieval.completed`

```json
{
  "candidate_count": 30,
  "selected_source_count": 6
}
```

Do not expose sensitive internal text in this event unless product explicitly requires it.

### `content.delta`

```json
{
  "delta": "Employees receive "
}
```

### `sources`

```json
{
  "sources": [
    {
      "id": "source-uuid",
      "document_id": "document-uuid",
      "document_title": "Employee Handbook",
      "page_number": 14,
      "section_title": "Annual Leave",
      "citation_label": "1",
      "excerpt": "..."
    }
  ]
}
```

### `message.completed`

```json
{
  "message_id": "uuid",
  "status": "completed",
  "usage": {
    "input_tokens": 1800,
    "output_tokens": 240
  }
}
```

### `error`

```json
{
  "code": "LLM_PROVIDER_ERROR",
  "message": "Unable to generate a response."
}
```

---

## 51. Chat Processing Contract

The backend must perform:

1. authentication;
2. conversation authorization;
3. workspace authorization;
4. persist user message;
5. prepare conversation context;
6. perform tenant-scoped retrieval;
7. perform reranking;
8. select final evidence;
9. construct model context;
10. create assistant message;
11. stream generation;
12. persist completed answer;
13. persist `message_sources`;
14. record usage;
15. record errors safely if generation fails.

---

## 52. Chat Failure Semantics

If retrieval fails before generation:

- assistant message may be marked failed;
- user message remains persisted;
- retry should not duplicate user message unless user explicitly resubmits.

If generation fails after partial output:

- assistant message should be marked failed;
- partial content handling must be consistent;
- UI should permit retry.

---

## 53. POST `/messages/{message_id}/retry`

Retries a failed assistant response or regenerates response.

### Auth

Required.

### Authorization

Conversation owner.

### Behavior

Prefer creating a new assistant message linked to the same user question rather than silently overwriting history.

### Response

Streaming or `202 Accepted`, depending implementation.

---

## 54. GET `/messages/{message_id}/sources`

Returns source evidence for an assistant message.

### Auth

Required.

### Authorization

Conversation access required.

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "document_id": "uuid",
      "document_title": "Employee Handbook",
      "page_number": 14,
      "section_title": "Annual Leave",
      "citation_label": "1",
      "excerpt": "...",
      "rank": 1,
      "rerank_score": 0.92
    }
  ]
}
```

Potentially hide raw internal ranking scores from end users while preserving them in admin/debug environments.

---

# PART IX — FEEDBACK

## 55. POST `/messages/{message_id}/feedback`

Creates or replaces current user's feedback.

### Auth

Required.

### Authorization

User must have access to message.

### Request

```json
{
  "rating": "positive",
  "comment": "This answered the question clearly."
}
```

or:

```json
{
  "rating": "negative",
  "comment": "The cited policy did not answer the question."
}
```

### Response

```json
{
  "id": "uuid",
  "message_id": "uuid",
  "rating": "positive",
  "comment": "...",
  "updated_at": "..."
}
```

---

## 56. DELETE `/messages/{message_id}/feedback`

Removes current user's feedback.

### Auth

Required.

### Authorization

Feedback owner.

### Response

`204 No Content`

---

# PART X — SEARCH / RETRIEVAL DEBUGGING

## 57. Debug Endpoints

RAG debugging endpoints must not be exposed to ordinary production users by default.

Potential internal/staging endpoint:

```text
POST /internal/retrieval/debug
```

It may return:

- vector candidates;
- keyword candidates;
- fused ranks;
- rerank scores;
- final evidence.

This should be gated by:

- environment;
- admin role;
- internal auth.

Never expose another tenant's candidates.

---

# PART XI — ADMIN

## 58. Admin API Philosophy

Avoid building a broad global admin API in V1 unless required.

Any administrative endpoint must be explicit and strongly authorized.

Potential organization admin endpoints belong under organization scope.

Avoid:

```text
/admin/users/all
```

without a clear platform-administration model.

---

# PART XII — HEALTH AND READINESS

## 59. GET `/health`

Unauthenticated.

Purpose:

- process liveness.

### Response

```json
{
  "status": "ok"
}
```

Should not perform expensive dependency checks.

---

## 60. GET `/ready`

Unauthenticated or infrastructure-restricted.

Purpose:

- readiness.

### Example Response

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

Do not expose secrets or detailed infrastructure information publicly.

---

## 61. GET `/version`

Optional.

Returns deployment metadata safe for exposure.

Example:

```json
{
  "version": "1.0.0",
  "commit": "abc1234"
}
```

May be environment-restricted.

---

# PART XIII — ERROR CODES

## 62. Authentication Codes

```text
AUTHENTICATION_REQUIRED
TOKEN_INVALID
TOKEN_EXPIRED
PROFILE_NOT_FOUND
```

---

## 63. Authorization Codes

```text
ORGANIZATION_ACCESS_DENIED
WORKSPACE_ACCESS_DENIED
DOCUMENT_ACCESS_DENIED
DOCUMENT_MANAGE_DENIED
CONVERSATION_ACCESS_DENIED
ROLE_CHANGE_DENIED
```

---

## 64. Organization Codes

```text
ORGANIZATION_NOT_FOUND
ORGANIZATION_SLUG_EXISTS
ORGANIZATION_INACTIVE
LAST_OWNER_REMOVAL_DENIED
```

---

## 65. Workspace Codes

```text
WORKSPACE_NOT_FOUND
WORKSPACE_SLUG_EXISTS
WORKSPACE_ARCHIVED
```

---

## 66. Document Codes

```text
DOCUMENT_NOT_FOUND
FILE_TOO_LARGE
FILE_TYPE_NOT_SUPPORTED
STORAGE_UPLOAD_FAILED
DOCUMENT_PROCESSING_FAILED
DOCUMENT_NOT_READY
DOCUMENT_RETRY_NOT_ALLOWED
DOCUMENT_DELETE_FAILED
```

---

## 67. RAG Codes

```text
RETRIEVAL_FAILED
EMBEDDING_PROVIDER_ERROR
RERANK_PROVIDER_ERROR
NO_RELEVANT_EVIDENCE
CONTEXT_BUILD_FAILED
```

---

## 68. LLM Codes

```text
LLM_PROVIDER_ERROR
LLM_RATE_LIMITED
LLM_TIMEOUT
LLM_RESPONSE_INVALID
```

---

## 69. Generic Codes

```text
VALIDATION_ERROR
RESOURCE_NOT_FOUND
CONFLICT
RATE_LIMIT_EXCEEDED
INTERNAL_ERROR
SERVICE_UNAVAILABLE
```

Stable error codes should be documented and not casually renamed.

---

# PART XIV — VALIDATION

## 70. Input Validation

All JSON bodies should use Pydantic models.

Validate:

- length;
- format;
- enum values;
- IDs;
- upload size;
- allowed file types;
- pagination limits.

Do not rely on frontend validation.

---

## 71. String Limits

Recommended examples:

```text
organization name: 1–120 chars
workspace name: 1–120 chars
slug: 2–80 chars
conversation title: 1–200 chars
feedback comment: max 2000 chars
chat message: configurable maximum
```

Exact values should be centralized and tested.

---

## 72. Slug Validation

Suggested pattern:

```text
[a-z0-9]+(?:-[a-z0-9]+)*
```

Normalize to lowercase.

---

# PART XV — RATE LIMITING

## 73. Rate Limit Targets

Potential limits:

- authentication-adjacent endpoints;
- uploads;
- chat;
- retries;
- invitation creation.

Limits may be applied by:

- IP;
- user;
- organization;
- endpoint class.

---

## 74. Rate Limit Response

Status:

```http
429 Too Many Requests
```

Example:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Try again later.",
    "details": {
      "retry_after_seconds": 30
    },
    "request_id": "..."
  }
}
```

Also set:

```http
Retry-After: 30
```

where appropriate.

---

# PART XVI — CORS

## 75. CORS Policy

Production API should allow only approved frontend origins.

Example:

```text
https://app.bismark.ai
```

Do not use wildcard origin with authenticated credential flows.

---

# PART XVII — FILE UPLOAD POLICY

## 76. Initial Supported File Types

Target:

```text
application/pdf
application/vnd.openxmlformats-officedocument.wordprocessingml.document
text/plain
text/markdown
text/html
```

PPTX may be added if parser support is validated.

---

## 77. File Size Limit

Must be configurable.

Example:

```text
MAX_UPLOAD_SIZE_MB=50
```

Do not hard-code only in frontend.

---

## 78. Upload Security

Backend should:

- inspect filename safely;
- sanitize display fields;
- validate MIME;
- enforce extension sanity;
- generate server-controlled storage path;
- never trust client path;
- avoid executing uploads.

---

# PART XVIII — RESPONSE MODELS

## 79. OrganizationSummary

```json
{
  "id": "uuid",
  "name": "Acme Ltd",
  "slug": "acme",
  "status": "active",
  "role": "owner"
}
```

---

## 80. WorkspaceSummary

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "name": "HR",
  "slug": "hr",
  "description": null,
  "status": "active",
  "role": "member"
}
```

---

## 81. DocumentSummary

```json
{
  "id": "uuid",
  "display_name": "Employee Handbook",
  "filename": "employee-handbook.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1845520,
  "status": "ready",
  "chunk_count": 93,
  "created_at": "...",
  "processing_completed_at": "..."
}
```

---

## 82. ConversationSummary

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "title": "Annual Leave Policy",
  "status": "active",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 83. MessageResponse

```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "assistant",
  "status": "completed",
  "content": "Employees receive...",
  "created_at": "...",
  "completed_at": "...",
  "sources": []
}
```

---

# PART XIX — API SECURITY INVARIANTS

## 84. Invariant 1

Every protected route requires validated identity.

---

## 85. Invariant 2

Every organization-scoped route validates active membership.

---

## 86. Invariant 3

Every workspace-scoped route validates workspace access.

---

## 87. Invariant 4

Every document operation validates document-to-workspace tenancy.

---

## 88. Invariant 5

Every conversation operation validates conversation ownership/access.

---

## 89. Invariant 6

No browser-facing route accepts Supabase service-role credentials.

---

## 90. Invariant 7

No chat route retrieves chunks outside authorized workspace scope.

---

# PART XX — OPENAPI

## 91. FastAPI OpenAPI

FastAPI should generate OpenAPI automatically.

Production exposure of interactive docs may be:

- enabled;
- disabled;
- restricted;

depending on security posture.

Recommended paths in development/staging:

```text
/docs
/redoc
/openapi.json
```

---

## 92. Canonical Contract

Where possible, OpenAPI should remain aligned with this document.

If generated OpenAPI differs materially from `API.md`, resolve the inconsistency.

---

# PART XXI — FRONTEND CLIENT CONTRACT

## 93. Typed Client

The frontend should use a typed API client.

Options:

- generated from OpenAPI;
- hand-written with strongly typed shared schemas.

Avoid ad-hoc `fetch()` response assumptions scattered throughout the UI.

---

## 94. Client Error Handling

Frontend should distinguish:

- authentication expired;
- access denied;
- not found;
- validation error;
- rate limit;
- provider failure;
- general server failure.

Do not display raw backend diagnostics.

---

# PART XXII — STREAMING CLIENT BEHAVIOR

## 95. Chat UI Must Support

- initial pending state;
- retrieval state;
- token deltas;
- sources;
- completion;
- cancellation;
- network failure;
- retry.

---

## 96. Disconnect Behavior

If the browser disconnects:

- backend should attempt cancellation where practical;
- persisted state must remain coherent;
- partial response should not be marked complete unless finalized.

---

# PART XXIII — API OBSERVABILITY

## 97. Metrics Candidates

Track:

- request count;
- response status;
- latency;
- chat latency;
- first-token latency;
- upload rate;
- failed upload rate;
- provider failure rate;
- rate limit events.

---

## 98. Logs

Each request log should include:

```text
request_id
method
path
status_code
latency_ms
user_id where known
organization_id where relevant
workspace_id where relevant
```

Never log access tokens or service keys.

---

# PART XXIV — API TESTING REQUIREMENTS

## 99. Authentication Tests

Test:

- no token;
- invalid token;
- expired token;
- valid token.

---

## 100. Organization Authorization Tests

Test:

- member reads own org;
- non-member denied;
- member cannot perform admin action;
- admin can perform permitted action;
- last owner cannot be removed.

---

## 101. Workspace Authorization Tests

Test:

- authorized workspace access;
- unauthorized same-org workspace access;
- cross-org workspace access denied;
- removed member denied.

---

## 102. Document Tests

Test:

- supported upload;
- unsupported MIME;
- oversized file;
- missing access;
- processing status;
- retry failed document;
- delete document.

---

## 103. Chat Tests

Test:

- valid question;
- conversation ownership;
- cross-user conversation denial;
- retrieval failure;
- LLM failure;
- stream completion;
- citation persistence.

---

## 104. Feedback Tests

Test:

- create feedback;
- update feedback;
- delete feedback;
- feedback on inaccessible message denied.

---

# PART XXV — API IMPLEMENTATION ORDER

## 105. Phase 1

Implement:

```text
GET /me
POST /organizations
GET /organizations
GET /organizations/{id}
POST /organizations/{id}/workspaces
GET /organizations/{id}/workspaces
GET /workspaces/{id}
```

---

## 106. Phase 2

Implement:

```text
POST /workspaces/{id}/documents
GET /workspaces/{id}/documents
GET /documents/{id}
GET /documents/{id}/status
POST /documents/{id}/retry
DELETE /documents/{id}
```

---

## 107. Phase 3

Implement:

```text
POST /workspaces/{id}/conversations
GET /workspaces/{id}/conversations
GET /conversations/{id}
PATCH /conversations/{id}
DELETE /conversations/{id}
```

---

## 108. Phase 4

Implement:

```text
POST /conversations/{id}/messages/stream
GET /messages/{id}/sources
POST /messages/{id}/retry
```

---

## 109. Phase 5

Implement:

```text
POST /messages/{id}/feedback
DELETE /messages/{id}/feedback
```

---

## 110. Phase 6

Implement:

```text
organization membership
workspace membership
invites
administrative APIs
```

---

# PART XXVI — DO NOT DO

## 111. Prohibited API Shortcuts

Agents and developers must not:

- expose service-role keys;
- accept `user_id` as identity proof;
- skip authorization because frontend hides a route;
- return raw SQL/database errors;
- expose stack traces in production;
- send permanent public source URLs;
- expose unscoped retrieval endpoints;
- let client choose arbitrary storage paths;
- make ingestion synchronous;
- return another tenant's resource existence unnecessarily;
- silently change response shapes;
- use unversioned public API routes;
- couple frontend directly to private provider APIs;
- expose internal retrieval diagnostics to normal users.

---

# PART XXVII — ACCEPTANCE CRITERIA

## 112. API V1 Is Acceptable When

1. all protected endpoints authenticate users;
2. all scoped endpoints authorize tenant access;
3. OpenAPI schemas are generated cleanly;
4. request/response models are typed;
5. errors use a stable format;
6. upload is asynchronous;
7. document status is queryable;
8. retry is safe;
9. chat supports streaming;
10. citations are returned from persisted evidence;
11. conversations persist;
12. feedback works;
13. rate limiting exists for expensive routes;
14. request IDs exist;
15. health/readiness endpoints exist;
16. CORS is restricted;
17. tests cover cross-tenant denial;
18. frontend can operate without direct privileged database access;
19. no secrets are returned to clients;
20. API contract is documented and consistent with implementation.

---

## 113. Summary

Bismark AI V1 exposes a versioned FastAPI REST API under:

```text
/api/v1
```

The API is responsible for:

```text
identity verification
+
authorization
+
application orchestration
+
document lifecycle
+
conversation lifecycle
+
RAG orchestration
+
streaming
+
citations
+
feedback
```

The frontend should treat the API as the authoritative business interface.

The API must remain secure, explicit, tenant-aware, and stable enough that both humans and agentic development tools can extend it without inventing undocumented behavior.
