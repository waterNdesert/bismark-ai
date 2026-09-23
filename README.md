# Bismark AI

Bismark AI is a planned multi-tenant enterprise knowledge intelligence platform
for answering questions against authorized organizational documents with grounded
answers and traceable citations.

**Current phase: Phase 0 — Repository Foundation.** This repository contains
architecture and planning documents plus an empty directory skeleton. It is not
a runnable product: frontend, backend, dependencies, tests, and deployment
configuration have not been implemented.

## Intended stack

- Frontend: Next.js, TypeScript, React, Tailwind CSS, shadcn/ui; hosted on Vercel.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic; a modular monolith.
- Compute: Hostinger KVM 2, Docker Compose, Caddy, Redis, and a Python worker.
- Data: Supabase PostgreSQL, Auth, private Storage, pgvector, and PostgreSQL FTS.
- RAG: structured parsing, hybrid retrieval with RRF, Voyage embeddings and
  reranking, and an external LLM behind an application-owned provider interface.

Parser, worker framework, and specific AI models remain open decisions.

## Project documentation

- [Product requirements](PRD.md)
- [Agent operating guide and canonical authority order](AGENTS.md)
- [Verified project state and open issues](PROJECT_STATE.md)
- [Roadmap](ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database](docs/DATABASE.md)
- [API](docs/API.md)
- [RAG](docs/RAG.md)
- [Security](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Testing](docs/TESTING.md)
- [Accepted architecture decisions](docs/decisions/)
- [Contribution guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Environment template](.env.example)

## Repository layout

`apps/web` and `apps/api` reserve the application locations. `infra/docker` and
`infra/caddy` reserve infrastructure configuration locations. `scripts`, `tests`,
and `evals` reserve operational tooling, test suites, and evaluation assets.
These directories currently contain only `.gitkeep` placeholders.

## Development status

Follow [ROADMAP.md](ROADMAP.md) one phase at a time. Complete and verify Phase 0
before beginning Phase 1. There are no install, run, or test commands configured
yet. Git is initialized on `main`; no remote is configured.

The environment template contains placeholders and development examples, not
production-ready configuration. Keep real credentials in ignored local files or
a secret store. Never expose server-side credentials through `NEXT_PUBLIC_*`.

Retrieval must enforce organization/workspace permissions inside both database
search paths. Citations may refer only to evidence actually supplied to the LLM.
