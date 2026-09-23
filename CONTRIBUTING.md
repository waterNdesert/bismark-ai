# CONTRIBUTING.md — Bismark AI Contribution Guide

**Project:** Bismark AI  
**Document Type:** Engineering Contribution Guide  
**Status:** V1 Contribution Baseline  
**Version:** 1.0  
**Audience:** Human Engineers, Reviewers, Maintainers, and Agentic Coding Systems

---

## 1. Purpose

This document defines how changes should be proposed, implemented, reviewed, tested, documented, and merged into Bismark AI.

It exists to keep development:

- consistent;
- secure;
- reviewable;
- traceable;
- compatible with agentic coding workflows;
- aligned with the canonical architecture.

This guide applies to:

- backend code;
- frontend code;
- database changes;
- RAG changes;
- infrastructure changes;
- documentation;
- tests;
- security fixes.

---

## 2. Required Reading

Before contributing, read:

1. `PRD.md`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/SECURITY.md`
5. the technical document relevant to your change
6. `ROADMAP.md`
7. `PROJECT_STATE.md` if present

Do not begin implementation from repository assumptions alone.

---

## 3. Contribution Principles

Every contribution should be:

- scoped;
- justified;
- tested;
- documented;
- backward-aware;
- secure by default.

Avoid mixing unrelated changes.

One pull request should answer a clear question:

```text
What problem does this change solve?
```

---

## 4. Branching Strategy

Recommended branch types:

```text
main
feature/<short-name>
fix/<short-name>
security/<short-name>
docs/<short-name>
chore/<short-name>
```

Examples:

```text
feature/document-upload
feature/hybrid-retrieval
fix/workspace-auth
security/source-url-access
docs/rag-evaluation
```

---

## 5. Main Branch

`main` should always represent:

- reviewed code;
- passing required checks;
- deployable state;
- canonical documentation.

Do not push unreviewed experimental work directly to `main`.

---

## 6. Pull Request Scope

Prefer small to medium PRs.

Good:

```text
Add workspace-scoped document upload.
```

Poor:

```text
Rewrite auth, add uploads, replace retrieval, redesign UI, migrate database.
```

If a task naturally spans multiple phases, split it.

---

## 7. Commit Style

Recommended format:

```text
<type>(<scope>): <summary>
```

Examples:

```text
feat(chat): add streamed assistant responses
fix(auth): block cross-workspace document access
docs(database): document processing version strategy
test(security): add cross-tenant retrieval regression
chore(ci): add backend lint job
```

---

## 8. Commit Types

Suggested:

```text
feat
fix
docs
test
refactor
security
chore
perf
build
ci
```

---

## 9. Commit Quality

Commits should be meaningful and reversible.

Avoid:

```text
update
changes
fix stuff
more work
```

Prefer:

```text
fix(documents): prevent duplicate chunk activation on retry
```

---

## 10. Do Not Rewrite Shared History

Do not force-push shared branches without explicit agreement.

Do not rewrite commits after review has started unless necessary and communicated.

---

# PART I — CODE STYLE

## 11. Python

Use:

- type annotations;
- explicit return types;
- Pydantic models;
- SQLAlchemy models/repositories;
- small functions;
- domain modules;
- async patterns where appropriate.

Avoid:

- untyped dictionaries as primary domain contracts;
- giant service files;
- global mutable state;
- raw SQL string interpolation.

---

## 12. TypeScript

Use:

- strict TypeScript;
- typed API responses;
- typed props;
- explicit component contracts;
- server/client boundaries appropriate to Next.js.

Avoid:

- broad `any`;
- duplicated response interfaces;
- hidden side effects.

---

## 13. Formatting

Use automated formatters.

Recommended:

### Python

```text
ruff
```

and optionally formatter support via Ruff.

### TypeScript

```text
eslint
prettier
```

or project-selected equivalents.

Once configured, do not introduce competing formatter stacks without reason.

---

## 14. Linting

CI should lint:

- Python;
- TypeScript;
- frontend code;
- potentially Dockerfiles and YAML later.

Warnings that represent real defects should not be ignored habitually.

---

# PART II — BACKEND CONTRIBUTIONS

## 15. FastAPI Structure

Changes should respect domain boundaries defined in `ARCHITECTURE.md`.

Do not put unrelated logic in `main.py`.

---

## 16. Route Design

New public endpoints must:

- live under `/api/v1`;
- use request/response models;
- enforce auth;
- document authorization;
- use stable errors;
- be added to `API.md`.

---

## 17. Business Logic

Prefer:

```text
route
→ service
→ repository/provider
```

over:

```text
route
→ everything inline
```

---

## 18. Provider Integrations

Voyage, LLM, storage, parser, and future provider integrations should sit behind interfaces.

Do not scatter vendor SDK calls through domain modules.

---

# PART III — FRONTEND CONTRIBUTIONS

## 19. UI Consistency

Use existing:

- design tokens;
- shadcn/ui patterns;
- layout conventions;
- typography;
- spacing.

Do not create visually inconsistent one-off primitives without need.

---

## 20. Accessibility

Interactive UI should support:

- keyboard navigation;
- labels;
- focus states;
- semantic elements;
- readable contrast;
- screen-reader friendly text where practical.

---

## 21. Loading and Error States

Any async UI must define:

- loading;
- empty;
- success;
- error.

Do not leave indefinite spinners.

---

## 22. Authorization UX

Frontend permission checks improve UX but are not security controls.

Backend remains authoritative.

---

# PART IV — DATABASE CONTRIBUTIONS

## 23. Schema Changes

Every schema change requires:

- migration;
- model changes;
- tests;
- docs update;
- index review;
- authorization impact review.

---

## 24. Migration Naming

Use descriptive migration names.

Examples:

```text
add_document_chunks
add_workspace_members
add_message_sources
```

---

## 25. Applied Migrations

Do not edit migrations already applied to shared staging or production.

Create a new migration.

---

## 26. Destructive Database Changes

Require:

- explicit review;
- migration plan;
- rollback or forward-fix plan;
- backup;
- release notes.

---

# PART V — RAG CONTRIBUTIONS

## 27. RAG Changes Require Evidence

Changes to:

- parsing;
- chunking;
- embeddings;
- retrieval;
- fusion;
- reranking;
- prompts;
- context;
- citations;

should be evaluated when evaluation infrastructure exists.

Do not claim an improvement solely because output looks better in one manual example.

---

## 28. Retrieval Security

Any retrieval change must preserve:

```text
organization scope
workspace scope
document state
processing version
```

---

## 29. Prompt Changes

Prompt changes should be:

- versioned where practical;
- tested;
- documented if behavior materially changes.

---

# PART VI — SECURITY CONTRIBUTIONS

## 30. Security Review Required

Security review is mandatory for changes affecting:

- auth;
- roles;
- RLS;
- storage;
- signed URLs;
- document access;
- retrieval;
- secrets;
- CORS;
- rate limiting;
- admin routes.

---

## 31. Cross-Tenant Tests

Any change touching tenancy must include negative tests.

Example:

```text
User A cannot access Organization B.
```

---

## 32. Secret Handling

Never commit:

- service-role key;
- database password;
- Voyage key;
- LLM key;
- SSH private key.

If accidentally committed, rotate the credential.

---

# PART VII — TESTING REQUIREMENTS

## 33. Required Test Types

Use the smallest relevant set:

- unit;
- integration;
- RLS;
- authorization;
- retrieval;
- frontend;
- E2E.

---

## 34. Tests Must Reflect Risk

A CSS tweak does not need database tests.

A workspace access change does.

A retrieval change requires retrieval/security coverage.

---

## 35. Reporting Tests

Pull requests should state:

```text
Tests run:
- ...

Not run:
- ...
```

Agentic tools must be equally explicit.

---

# PART VIII — DOCUMENTATION

## 36. Documentation Is Part of Done

Update relevant documentation when behavior changes.

Examples:

| Change | Document |
|---|---|
| Architecture | `ARCHITECTURE.md` |
| Schema | `DATABASE.md` |
| Endpoint | `API.md` |
| Retrieval | `RAG.md` |
| Security | `SECURITY.md` |
| Deployment | `DEPLOYMENT.md` |
| Tests | `TESTING.md` |
| Delivery phase | `ROADMAP.md` |
| Meaningful completed change | `CHANGELOG.md` |

---

## 37. PROJECT_STATE.md

After substantial work, update project state.

Do not use `PROJECT_STATE.md` as a substitute for canonical documentation.

---

# PART IX — PULL REQUEST REQUIREMENTS

## 38. PR Description Template

Recommended:

```markdown
## Summary
What changed?

## Why
Why is this needed?

## Scope
What is intentionally included/excluded?

## Security Impact
Does this affect authentication, authorization, tenancy, storage, or retrieval?

## Database Impact
Migration required? Yes/No

## RAG Impact
Does this affect parsing, chunking, embeddings, retrieval, reranking, context, or citations?

## Tests
What was run?

## Documentation
Which docs were updated?

## Deployment Notes
Any operator action required?
```

---

## 39. PR Review Checklist

Reviewer should confirm:

```text
[ ] scope is clear
[ ] architecture is preserved
[ ] authorization is correct
[ ] tenant isolation preserved
[ ] tests added
[ ] tests pass
[ ] docs updated
[ ] migration safe
[ ] secrets absent
[ ] no unrelated refactor
```

---

# PART X — REVIEW STANDARDS

## 40. Review for Correctness

Ask:

- does it work?
- are edge cases covered?
- does failure leave coherent state?

---

## 41. Review for Security

Ask:

- can another tenant access this?
- are IDs trusted incorrectly?
- are secrets exposed?
- are signed URLs safe?
- is RLS bypassed?

---

## 42. Review for Maintainability

Ask:

- is responsibility clear?
- is abstraction justified?
- does this duplicate logic?
- can another engineer understand it?

---

## 43. Review for Operability

Ask:

- how is failure observed?
- are logs useful?
- can it be rolled back?
- does deployment require manual steps?

---

# PART XI — DEPENDENCIES

## 44. Adding Dependencies

Before adding a dependency, document why existing tooling is insufficient.

Check:

- maintenance;
- license;
- ecosystem health;
- package size;
- security;
- transitive dependencies.

---

## 45. Avoid Framework Duplication

Do not add:

- second ORM;
- second HTTP framework;
- second UI framework;
- second vector DB;
- second queue;

without strong justification.

---

# PART XII — CONFIGURATION

## 46. Configuration Changes

Any new required environment variable must be added to:

```text
.env.example
```

and documented if operationally important.

---

## 47. Defaults

Safe non-secret defaults may exist.

Secrets must never have real defaults in source.

---

# PART XIII — RELEASE PROCESS

## 48. Before Release

Verify:

- CI green;
- migrations reviewed;
- changelog updated;
- deployment notes documented;
- security blockers resolved;
- smoke test plan ready.

---

## 49. Release Version

Follow changelog/versioning guidance.

---

# PART XIV — HOTFIXES

## 50. Security Hotfix

A security hotfix may bypass normal feature cadence but must still include:

- focused patch;
- tests;
- changelog;
- deployment verification.

---

## 51. Production Hotfix

Avoid broad refactors during urgent production fixes.

Fix the defect first.

Refactor later.

---

# PART XV — AGENTIC CODING SYSTEMS

## 52. Agent Rules

Agents must:

1. read `AGENTS.md`;
2. inspect current state;
3. identify affected docs;
4. plan before editing;
5. keep changes scoped;
6. run tests;
7. report truthfully;
8. update changelog when meaningful.

---

## 53. Agent Commit Behavior

If allowed to commit, agents should use scoped commit messages.

Do not create dozens of meaningless commits.

---

## 54. Agent Reviewability

Agents must avoid massive rewrites unless explicitly requested.

The goal is reviewable changes.

---

# PART XVI — ISSUE REPORTING

## 55. Bug Report Template

Recommended:

```markdown
## Summary

## Environment

## Steps to Reproduce

## Expected

## Actual

## Logs / Request ID

## Security Impact

## Tenant Impact
```

Do not include secrets.

---

## 56. Feature Request Template

```markdown
## Problem

## User Impact

## Proposed Outcome

## Alternatives Considered

## Architecture Impact

## Security Impact

## V1 / Future
```

---

# PART XVII — DEFINITION OF DONE

## 57. General Definition

A contribution is done when applicable:

```text
implementation complete
tests complete
security reviewed
migration included
docs updated
changelog updated
CI passing
deployment impact understood
```

---

## 58. Backend Definition of Done

```text
[ ] typed models
[ ] auth enforced
[ ] errors normalized
[ ] tests pass
[ ] logs appropriate
```

---

## 59. Database Definition of Done

```text
[ ] migration exists
[ ] migration tested
[ ] constraints/indexes reviewed
[ ] RLS impact reviewed
[ ] docs updated
```

---

## 60. RAG Definition of Done

```text
[ ] tenant scope preserved
[ ] source mapping preserved
[ ] evaluation run where available
[ ] failure behavior tested
[ ] docs updated
```

---

## 61. Frontend Definition of Done

```text
[ ] typed
[ ] responsive
[ ] accessible
[ ] loading state
[ ] error state
[ ] tested
```

---

# PART XVIII — DO NOT DO

## 62. Prohibited Contribution Patterns

Do not:

- push directly to main without review;
- mix unrelated refactors with features;
- bypass security checks;
- disable RLS to make code work;
- commit secrets;
- add infrastructure casually;
- claim tests passed if not run;
- change API contracts silently;
- rewrite applied migrations;
- introduce microservices prematurely;
- overrule canonical docs without an ADR.

---

# PART XIX — CONTRIBUTOR CHECKLIST

## 63. Before Coding

```text
[ ] read relevant docs
[ ] identify current roadmap phase
[ ] inspect existing code/tests
[ ] define scope
```

---

## 64. Before Opening PR

```text
[ ] implementation complete
[ ] tests run
[ ] lint/type-check run
[ ] docs updated
[ ] changelog updated
[ ] migration included if needed
[ ] no secrets
```

---

## 65. Before Merge

```text
[ ] review complete
[ ] CI green
[ ] security concerns resolved
[ ] migration order clear
[ ] deployment impact known
```

---

# PART XX — SUMMARY

Bismark AI contributions should optimize for:

```text
clarity
+
security
+
reviewability
+
testability
+
architectural consistency
```

A high-quality contribution is not simply code that works.

It is code that:

```text
fits the product,
preserves tenant boundaries,
is testable,
is documented,
can be safely deployed,
and can be understood by the next engineer or coding agent.
```
