# DEPLOYMENT.md — Bismark AI Deployment and Operations Guide

**Project:** Bismark AI  
**Document Type:** Canonical Deployment Specification  
**Status:** V1 Deployment Baseline  
**Version:** 1.0  
**Audience:** DevOps, Backend Engineering, Frontend Engineering, Security, QA, and Agentic Coding Systems

---

## 1. Purpose

This document defines how Bismark AI V1 is deployed, configured, operated, upgraded, and recovered.

It covers:

- Vercel frontend deployment;
- Hostinger KVM 2 backend deployment;
- Docker Compose;
- Caddy;
- Supabase;
- Redis;
- domains and DNS;
- TLS/SSL;
- environment variables;
- secrets;
- deployment workflow;
- health checks;
- backups;
- restore procedures;
- rollback procedures;
- logging;
- monitoring;
- scaling;
- incident operations.

Documentation authority follows the canonical order in [AGENTS.md §2](../AGENTS.md#2-documentation-authority).
`PROJECT_STATE.md` reports current implementation state and does not override architectural decisions.

It must remain aligned with:

- `docs/DATABASE.md`
- `docs/API.md`
- `docs/RAG.md`
- `docs/TESTING.md`

---

## 2. Deployment Summary

Bismark AI V1 uses the following production topology:

```text
                        Internet
                           |
                 +---------+---------+
                 |                   |
                 v                   v
             Vercel              Hostinger VPS
             Next.js                Caddy
                 |                   |
                 | HTTPS             v
                 +--------------> FastAPI
                                     |
                           +---------+---------+
                           |                   |
                           v                   v
                        Worker               Redis
                           |
                           +---------------------------+
                           |            |              |
                           v            v              v
                       Supabase      Voyage AI      LLM Provider
```

Supabase provides:

- PostgreSQL;
- Auth;
- Storage;
- pgvector.

Hostinger provides:

- compute for FastAPI;
- worker;
- Redis;
- parser dependencies;
- Caddy.

Vercel provides:

- frontend hosting;
- preview deployments;
- CDN;
- frontend TLS.

---

## 3. Environment Model

Bismark AI should use separate environments.

Recommended:

```text
development
staging
production
```

Each environment should have separate:

- Supabase project;
- database;
- storage bucket;
- API secrets;
- frontend environment variables;
- backend environment variables;
- domains;
- provider keys where practical.

Production data must never be reused casually in development.

---

## 4. Development Deployment

Recommended local development:

```text
Developer Machine
├── Next.js dev server
├── FastAPI dev server
├── Docker Redis
└── optional local parser dependencies

External:
├── Supabase development project
├── Voyage test key
└── LLM development key
```

The entire stack does not need to be fully containerized locally on day one.

---

## 5. Staging Deployment

Staging should mirror production as closely as possible.

Suggested:

```text
staging-app.bismark.ai
staging-api.bismark.ai
```

Staging should include:

- Vercel frontend;
- Hostinger or equivalent backend environment;
- separate Supabase project;
- separate storage bucket;
- test provider credentials;
- representative documents.

---

## 6. Production Deployment

Suggested public domains:

```text
app.bismark.ai
api.bismark.ai
```

Optional future domains:

```text
status.bismark.ai
docs.bismark.ai
```

Do not expose internal Docker services directly.

---

# PART I — HOSTINGER KVM 2

## 7. Initial VPS Class

Recommended starting point:

```text
Hostinger KVM 2
2 vCPU
8 GB RAM
100 GB NVMe
```

This is suitable because:

- PostgreSQL is external;
- file storage is external;
- embeddings are external;
- reranking is external;
- LLM inference is external.

The VPS mainly handles:

- API requests;
- parsing;
- queueing;
- chunking;
- temporary files;
- streaming;
- orchestration.

---

## 8. VPS Operating System

Recommended:

```text
Ubuntu LTS
```

Use a currently supported LTS release.

The server should be kept minimal.

---

## 9. VPS Directory Layout

Recommended:

```text
/opt/bismark/
├── app/
├── infra/
├── env/
├── backups/
├── logs/
└── temp/
```

Alternative repository deployment path is acceptable if consistent.

---

## 10. Required Server Software

Install:

```text
Docker Engine
Docker Compose plugin
Caddy container or image
Git
UFW
unattended-upgrades
```

Optional:

```text
fail2ban
```

Do not install PostgreSQL locally for production V1.

---

# PART II — FIREWALL

## 11. UFW Baseline

Default:

```text
deny incoming
allow outgoing
```

Allow:

```text
22/tcp
80/tcp
443/tcp
```

If Caddy HTTP/3 is intentionally used:

```text
443/udp
```

Everything else should remain blocked publicly.

---

## 12. Internal Ports

Do not publicly expose:

- FastAPI container port;
- Redis;
- worker;
- parser service;
- internal metrics endpoint.

Only Caddy should face the internet for backend traffic.

---

# PART III — SSH

## 13. SSH Security

Production SSH requirements:

- key authentication;
- password authentication disabled;
- root password login disabled;
- limited sudo-capable admin account;
- minimal authorized keys.

Do not distribute the same private SSH key widely.

---

## 14. SSH Example Hardening

Expected settings conceptually:

```text
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin prohibit-password
```

Exact configuration must be validated before restarting SSH.

---

# PART IV — DOCKER

## 15. Production Docker Services

Initial Docker Compose services:

```text
caddy
api
worker
redis
```

---

## 16. Recommended Compose Topology

```text
caddy
  |
  v
api

worker
  |
  v
redis

api
  |
  +--> redis
  +--> Supabase
  +--> Voyage
  +--> LLM
```

---

## 17. Docker Networks

Recommended:

```text
proxy
internal
egress
```

Example concept:

```text
caddy -> proxy
api -> proxy + internal
worker -> internal + egress
redis -> internal
```

Redis must not attach to a public network unnecessarily.

---

## 18. Docker Volumes

Persistent local volumes should be minimal.

Potential volumes:

```text
caddy_data
caddy_config
redis_data
```

User source files should not use local persistent volumes.

---

## 19. Temporary Processing Storage

Worker may use:

```text
/tmp/bismark
```

or a mounted temp directory.

Files must be deleted after:

- successful processing;
- failed processing;
- timeout cleanup.

---

## 20. Container User

Run application containers as non-root where practical.

---

## 21. Image Versioning

Production images should be tagged.

Avoid deploying only:

```text
latest
```

Recommended:

```text
bismark-api:<git-sha>
```

or:

```text
bismark-api:1.0.0
```

---

# PART V — EXAMPLE DOCKER COMPOSE STRUCTURE

## 22. Conceptual Compose

```yaml
services:
  caddy:
    image: caddy:2
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./infra/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - proxy

  api:
    image: bismark-api:${APP_VERSION}
    restart: unless-stopped
    env_file:
      - ./env/production.env
    expose:
      - "8000"
    networks:
      - proxy
      - internal
    depends_on:
      - redis

  worker:
    image: bismark-api:${APP_VERSION}
    restart: unless-stopped
    env_file:
      - ./env/production.env
    command: ["<worker-command>"]
    networks:
      - internal
      - egress
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - internal

volumes:
  caddy_data:
  caddy_config:
  redis_data:

networks:
  proxy:
  egress:
    driver: bridge
  internal:
    internal: true
```

Exact worker command will depend on chosen job library.

The worker reaches Redis over the isolated `internal` network. Its separate
`egress` bridge permits outbound HTTPS to Supabase, Voyage, and the LLM provider
when required by a job. The worker publishes no ports and is not a Caddy upstream;
outbound access does not make it a public HTTP service. Redis remains attached
only to `internal` and publishes no ports. The API uses `proxy` for outbound
connectivity and `internal` for Redis. Host firewall policy must preserve required
outbound connectivity while restricting inbound traffic.

This is conceptual documentation only; no runnable Compose configuration exists yet.

---

# PART VI — CADDY

## 23. Caddy Role

Caddy provides:

- TLS;
- HTTPS;
- reverse proxy;
- HTTP to HTTPS redirect;
- API edge.

---

## 24. Caddy Example

Conceptual:

```caddy
api.bismark.ai {
    reverse_proxy api:8000
}
```

Optional headers may be added after testing.

---

## 25. TLS

Caddy should obtain and renew certificates automatically.

Requirements:

- correct DNS;
- public port 80;
- public port 443;
- domain resolves to VPS.

---

## 26. Certificate Persistence

Persist:

```text
/data
/config
```

for Caddy.

Do not lose Caddy certificate state on every container recreation.

---

# PART VII — DNS

## 27. Suggested Records

Frontend:

```text
app.bismark.ai
```

managed according to Vercel's required records.

Backend:

```text
api.bismark.ai -> VPS public IP
```

Exact A/CNAME configuration depends on DNS provider.

---

## 28. DNS Validation

Before enabling production traffic:

```bash
dig +short app.bismark.ai
dig +short api.bismark.ai
```

Then test:

```bash
curl -I https://api.bismark.ai/health
```

---

# PART VIII — VERCEL

## 29. Frontend Deployment

Vercel hosts:

```text
apps/web
```

Recommended workflow:

```text
GitHub push
→ Vercel build
→ preview deployment
→ production promotion
```

---

## 30. Vercel Environments

Use:

```text
Development
Preview
Production
```

with separate variables.

---

## 31. Frontend Variables

Typical public variables:

```text
NEXT_PUBLIC_APP_URL
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

Never expose:

```text
SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL
VOYAGE_API_KEY
LLM_API_KEY
```

---

## 32. Vercel Build

Expected:

```text
pnpm install
pnpm build
```

or repository-specific equivalent.

Lock package manager version.

---

# PART IX — SUPABASE

## 33. Supabase Responsibilities

Supabase provides:

```text
Auth
PostgreSQL
Storage
pgvector
```

---

## 34. Supabase Projects

Use separate projects for:

```text
development
staging
production
```

---

## 35. Database Migrations

Production database changes must run through version-controlled migrations.

Preferred order:

```text
required PostgreSQL extensions (including pgvector)
→ application tables and columns
→ dependent functions and RLS policies
→ indexes after their prerequisite objects
```

Exact implementation may use Alembic plus controlled SQL migration files.
Order individual migrations by dependency: enable pgvector before creating any
vector columns or vector indexes; create functions before policies that use them.

---

## 36. pgvector

Enable pgvector before creating vector columns.

Do not manually change vector dimension in production.

---

## 37. Storage Bucket

Recommended private bucket:

```text
bismark-documents
```

Environment-specific naming is acceptable.

Bucket must not be public.

---

# PART X — REDIS

## 38. Redis Role

Redis is used for:

- job queue;
- transient worker coordination.

It is not the source of truth for product state.

---

## 39. Redis Persistence

A small persistent volume may be used.

However, durable job state should exist in PostgreSQL where required.

---

## 40. Redis Exposure

Redis must not publish port 6379 publicly.

---

# PART XI — ENVIRONMENT VARIABLES

## 41. Backend Core Variables

Expected:

```text
APP_ENV
APP_NAME
APP_VERSION
LOG_LEVEL

APP_URL
API_URL
FRONTEND_URL
CORS_ORIGINS
```

---

## 42. Supabase Variables

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET
DATABASE_URL
```

---

## 43. Voyage Variables

```text
VOYAGE_API_KEY
VOYAGE_EMBEDDING_MODEL
VOYAGE_EMBEDDING_DIMENSION
VOYAGE_RERANK_MODEL
```

---

## 44. LLM Variables

```text
LLM_PROVIDER
LLM_MODEL
LLM_API_KEY
LLM_BASE_URL
```

`LLM_BASE_URL` may be optional.

---

## 45. Redis Variables

```text
REDIS_URL
```

---

## 46. RAG Variables

```text
RAG_VECTOR_CANDIDATES
RAG_KEYWORD_CANDIDATES
RAG_FUSED_CANDIDATES
RAG_RERANK_CANDIDATES
RAG_FINAL_EVIDENCE_COUNT
RAG_MAX_CONTEXT_TOKENS
RAG_CONVERSATION_TURNS
RAG_CHUNK_TARGET_TOKENS
RAG_CHUNK_OVERLAP_TOKENS
```

---

## 47. Upload Variables

```text
MAX_UPLOAD_SIZE_MB
SIGNED_URL_TTL_SECONDS
```

---

## 48. Security Variables

```text
RATE_LIMIT_CHAT_PER_MINUTE
RATE_LIMIT_UPLOAD_PER_HOUR
TRUSTED_PROXY_COUNT
```

---

## 49. Worker Variables

Potential:

```text
WORKER_CONCURRENCY
JOB_MAX_RETRIES
JOB_TIMEOUT_SECONDS
PARSER_TIMEOUT_SECONDS
```

---

# PART XII — SECRET MANAGEMENT

## 50. Production Secrets

Production secrets should be stored outside Git.

Possible storage locations:

- host environment file with restricted permissions;
- CI/CD secrets;
- Vercel environment variables.

---

## 51. Environment File Permissions

If using:

```text
/opt/bismark/env/production.env
```

set restrictive permissions:

```bash
chmod 600
```

and owner appropriately.

---

## 52. Secret Rotation

After key rotation:

1. update secret store;
2. restart/redeploy affected service;
3. verify health;
4. revoke old key.

---

# PART XIII — CI/CD

## 53. Recommended CI Pipeline

On pull request:

```text
lint
type-check
unit tests
integration tests
security checks
build frontend
build backend image
```

---

## 54. Recommended CD Pipeline

On approved production release:

```text
tag/version
→ build image
→ push image
→ migrate database
→ deploy backend
→ health check
→ deploy/promote frontend
→ smoke test
```

Exact order may vary if backward compatibility requires frontend first.

---

## 55. Database Migration Rule

Do not deploy application code that requires a schema not yet applied.

Use backward-compatible migrations where possible.

---

# PART XIV — MANUAL DEPLOYMENT FLOW

## 56. Initial Backend Deployment

Conceptual:

```bash
cd /opt/bismark
git pull
docker compose build
docker compose run --rm api alembic upgrade head
docker compose up -d
docker compose ps
```

If production images are built in CI:

```bash
docker compose pull
docker compose run --rm api alembic upgrade head
docker compose up -d
```

---

## 57. Verify Backend

Check:

```bash
docker compose ps
docker compose logs --tail=100 api
docker compose logs --tail=100 worker
```

Then:

```bash
curl -fsS https://api.bismark.ai/health
curl -fsS https://api.bismark.ai/ready
```

---

# PART XV — HEALTH CHECKS

## 58. Liveness

Endpoint:

```text
/health
```

Expected:

```json
{"status":"ok"}
```

---

## 59. Readiness

Endpoint:

```text
/ready
```

Should verify critical dependencies as appropriate:

- database;
- Redis.

External AI providers should not necessarily make readiness fail unless product behavior depends on it at startup.

---

# PART XVI — LOGGING

## 60. Docker Logs

Use Docker logging with rotation.

Recommended:

```text
driver: local
```

with bounded file size.

---

## 61. Application Logs

Use structured JSON logs where practical.

Include:

- timestamp;
- level;
- request ID;
- service;
- error class;
- entity IDs where safe.

---

## 62. Log Retention

Do not allow unbounded local logs.

Use rotation.

Future versions may ship logs to external observability.

---

# PART XVII — MONITORING

## 63. Initial Monitoring

At minimum monitor:

- API availability;
- readiness;
- disk usage;
- memory usage;
- CPU usage;
- container restarts;
- worker failures;
- queue depth;
- database errors;
- provider errors.

---

## 64. Alert Candidates

Alert when:

- API unavailable;
- disk > 80%;
- repeated worker crashes;
- queue depth continuously rising;
- Redis unavailable;
- database unavailable;
- high provider error rate;
- certificate failure.

---

# PART XVIII — BACKUPS

## 65. Backup Philosophy

Critical durable data lives primarily in Supabase.

Backups must cover:

- PostgreSQL;
- source documents;
- deployment configuration;
- secrets recovery process;
- repository.

---

## 66. PostgreSQL Backups

Use Supabase backup capability appropriate to the selected plan.

Document:

- automatic backup frequency;
- retention;
- restore process.

---

## 67. Manual Database Export

Before risky migrations, consider manual logical backup.

Conceptual:

```bash
pg_dump "$DATABASE_URL" > /opt/bismark/backups/pre_migration.sql
```

Do not expose backup files publicly.

---

## 68. Source Document Backup

Supabase Storage is separate from PostgreSQL.

Do not assume a database backup contains source files.

Future policy may use:

- storage replication;
- periodic export;
- provider-native backup.

---

## 69. VPS Backup

The VPS should not contain irreplaceable application data.

Still back up:

- Caddy config;
- deployment config;
- environment configuration securely;
- operational scripts.

Source code is recoverable from Git.

---

# PART XIX — RECOVERY

## 70. Recovery Objectives

V1 should aim for practical recoverability rather than formal enterprise RTO/RPO.

Recovery priorities:

1. restore database;
2. restore storage access;
3. restore backend;
4. restore frontend;
5. verify tenant access;
6. verify RAG retrieval.

---

## 71. VPS Loss Recovery

If VPS is lost:

1. provision replacement VPS;
2. install Docker;
3. restore firewall;
4. restore deployment files;
5. restore environment secrets;
6. point DNS if IP changed;
7. start containers;
8. verify Caddy TLS;
9. run health checks.

Because durable user data is external, no application data should depend solely on the lost VPS.

---

## 72. Frontend Recovery

If Vercel deployment fails:

- roll back to prior deployment;
- verify API compatibility;
- restore production alias.

---

## 73. Database Recovery

Before restoring production:

- identify restore point;
- confirm backups;
- restore to safe target if possible;
- validate tenant data;
- validate migrations;
- verify application compatibility.

---

# PART XX — ROLLBACK

## 74. Backend Rollback

Use immutable image tags.

Example:

```text
bismark-api:abc123
bismark-api:def456
```

Rollback:

```text
change APP_VERSION
docker compose pull
docker compose up -d
```

---

## 75. Migration Rollback

Do not assume every database migration is safely reversible.

Prefer forward-fix migrations.

For destructive changes:

- backup first;
- document rollback.

---

## 76. Frontend Rollback

Vercel should support promotion of a previous successful deployment.

---

# PART XXI — ZERO-DOWNTIME PRACTICES

## 77. Backward Compatibility

When possible:

1. deploy additive database migration;
2. deploy backend;
3. deploy frontend;
4. remove deprecated structure later.

---

## 78. API Compatibility

Avoid frontend and backend requiring simultaneous exact deployment.

Use backward-compatible API responses during transitions.

---

# PART XXII — SCALING

## 79. Initial Capacity

KVM 2 is intended for MVP and early production.

Expected initial services:

```text
1 API container
1 worker
1 Redis
1 Caddy
```

---

## 80. First Scale Step

When measured need appears:

```text
increase worker concurrency
increase API process count
upgrade KVM
```

---

## 81. KVM 4 Upgrade

Consider KVM 4 when:

- document processing queues grow;
- CPU is consistently saturated;
- memory pressure is high;
- concurrent streaming load becomes significant.

Do not upgrade only because user count grows if external services remain the primary compute consumers.

---

## 82. Future Horizontal Scaling

Possible later:

- multiple API replicas;
- multiple workers;
- managed Redis;
- separate worker host;
- load balancer.

Requires architecture review.

---

# PART XXIII — DEPLOYMENT SECURITY

## 83. Production Checklist

Before go-live verify:

```text
[ ] HTTPS works
[ ] HTTP redirects to HTTPS
[ ] UFW active
[ ] SSH key-only
[ ] Redis not public
[ ] API internal port not public
[ ] secrets not in Git
[ ] Supabase bucket private
[ ] service-role key backend-only
[ ] CORS restricted
[ ] rate limiting configured
[ ] backups configured
[ ] logs rotated
[ ] health checks pass
```

---

# PART XXIV — DOMAIN CHANGE

## 84. Domain Migration

If production domain changes:

1. update DNS;
2. update Caddy;
3. update Vercel domain;
4. update `APP_URL`;
5. update `API_URL`;
6. update `FRONTEND_URL`;
7. update CORS;
8. update Supabase redirect/auth URLs;
9. verify signed links;
10. test login and chat.

---

# PART XXV — DEPLOYMENT FILES

## 85. Expected Repository Files

Recommended:

```text
infra/
├── caddy/
│   └── Caddyfile
├── docker/
│   ├── api.Dockerfile
│   └── web.Dockerfile (optional)
└── scripts/
```

Root:

```text
docker-compose.yml
.env.example
```

---

## 86. Dockerfile Expectations

Backend Dockerfile should:

- use pinned Python base version;
- install dependencies reproducibly;
- use non-root user where practical;
- expose only internal API port;
- define healthcheck if useful;
- avoid copying secrets;
- avoid development packages in final image where possible.

---

# PART XXVI — RELEASE PROCESS

## 87. Release Candidate Flow

Recommended:

```text
feature branch
→ pull request
→ CI
→ staging
→ smoke tests
→ production approval
→ production deployment
→ verification
```

---

## 88. Release Notes

Significant releases should update:

```text
CHANGELOG.md
```

Include:

- features;
- fixes;
- security changes;
- migrations;
- deployment notes.

---

# PART XXVII — SMOKE TESTS

## 89. Minimum Smoke Test

After production deployment:

1. load frontend;
2. log in;
3. create/read workspace;
4. list documents;
5. upload small document;
6. verify processing;
7. ask question;
8. receive citation;
9. reopen conversation;
10. verify source access;
11. verify logs;
12. verify no cross-tenant leakage in test accounts.

---

# PART XXVIII — DISASTER SCENARIOS

## 90. VPS Disk Full

Action:

1. inspect Docker logs;
2. inspect temp files;
3. clean safe caches;
4. verify log rotation;
5. restore free space;
6. restart affected services if required.

---

## 91. Redis Failure

Impact:

- ingestion queue may stop;
- chat should remain available if not queue-dependent.

Action:

- restart Redis;
- verify queued jobs;
- reconcile durable ingestion jobs.

---

## 92. Supabase Outage

Impact:

- auth;
- database;
- storage;
- retrieval.

Action:

- fail safely;
- do not accept fake success;
- monitor provider status;
- resume after recovery.

---

## 93. Voyage Outage

Impact:

- new embeddings;
- semantic retrieval;
- reranking.

Possible behavior:

- existing keyword retrieval may technically remain possible;
- production fallback must be explicitly configured and tested.

Default is safe failure over silent degradation.

---

## 94. LLM Provider Outage

Impact:

- answer generation.

Action:

- preserve user message;
- mark assistant response failed;
- allow retry.

---

# PART XXIX — DEPLOYMENT ACCEPTANCE CRITERIA

## 95. V1 Deployment Is Acceptable When

1. frontend deploys through Vercel;
2. backend runs in Docker on Hostinger;
3. Caddy serves HTTPS;
4. Redis is private;
5. Supabase is external;
6. source storage is private;
7. database migrations are reproducible;
8. environment variables are documented;
9. secrets are not committed;
10. health endpoint works;
11. readiness endpoint works;
12. logs rotate;
13. backups are defined;
14. restore procedure exists;
15. rollback procedure exists;
16. production CORS is restricted;
17. firewall is enabled;
18. only intended public ports are open;
19. worker survives restart;
20. application can recover from VPS replacement using external durable data.

---

# PART XXX — INITIAL DEPLOYMENT SEQUENCE

## 96. Phase 1 — Provision Infrastructure

Provision:

```text
Hostinger KVM 2
Supabase development/staging/production
Vercel project
```

---

## 97. Phase 2 — Harden VPS

Configure:

```text
SSH
UFW
automatic updates
Docker
directories
```

---

## 98. Phase 3 — Configure DNS

Set:

```text
api.bismark.ai
app.bismark.ai
```

---

## 99. Phase 4 — Deploy Backend Skeleton

Deploy:

```text
Caddy
FastAPI
Redis
worker
```

Verify:

```text
/health
/ready
```

---

## 100. Phase 5 — Configure Supabase

Enable:

```text
Auth
Storage
pgvector
RLS
```

Run migrations.

---

## 101. Phase 6 — Deploy Frontend

Deploy Next.js to Vercel.

Set environment variables.

Verify API connectivity.

---

## 102. Phase 7 — Configure Providers

Add:

```text
Voyage
LLM provider
```

Verify secrets and provider connectivity.

---

## 103. Phase 8 — End-to-End Test

Test:

```text
signup
organization
workspace
upload
ingestion
retrieval
chat
citation
conversation
feedback
```

---

# PART XXXI — DO NOT DO

## 104. Prohibited Deployment Shortcuts

Do not:

- run production PostgreSQL on the same VPS without an ADR;
- expose Redis publicly;
- store user documents permanently on VPS;
- put secrets in Docker images;
- use wildcard CORS in production;
- use `latest` tags only for production;
- skip database backup before risky migration;
- deploy destructive migrations casually;
- open unnecessary firewall ports;
- expose internal parser ports;
- use root containers by default;
- deploy directly from unreviewed local changes;
- rely on a single undocumented `.env` file;
- assume database backup includes object storage;
- disable HTTPS for convenience.

---

## 105. Summary

The Bismark AI V1 deployment model is:

```text
Frontend:
Next.js
Vercel

Backend:
FastAPI
Worker
Redis
Caddy
Hostinger KVM 2
Docker Compose

Data:
Supabase PostgreSQL
Supabase Auth
Supabase Storage
pgvector

AI:
Voyage embeddings
Voyage reranking
External LLM
```

The architecture intentionally keeps durable state outside the VPS so the application can recover quickly from server replacement.

Production deployment should remain simple, reproducible, secure, and observable.

The first operational goal is not maximum infrastructure sophistication.

It is:

```text
reliable deployment
+
secure tenant isolation
+
recoverable data
+
repeatable releases
+
fast iteration
```
