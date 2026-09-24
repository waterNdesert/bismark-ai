# Bismark AI

Bismark AI is a planned multi-tenant enterprise knowledge intelligence platform
for answering questions against authorized organizational documents with grounded
answers and traceable citations.

**Current phase: Phase 0 — Repository Foundation.** Minimal Next.js and FastAPI
application foundations exist. Product features, database integration, Docker,
Redis and CI remain unimplemented. This is not a production-ready product.

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

## Development

Prerequisites: Node.js 24, pnpm 10.33.2, uv, Python 3.12 and Make.
Python 3.12 is a conservative compatibility baseline for future parser/AI
packages, which remain unselected. uv obtains one managed 3.12 runtime if needed.
Dependencies are locked per app; no monorepo orchestrator is required.

```sh
make api-install
make web-install
make api-dev    # http://127.0.0.1:8000
make web-dev    # http://127.0.0.1:3000, in another terminal
```

Stop development servers with Ctrl-C. Validation:

```sh
make api-test
make api-lint
make api-format-check
make api-typecheck
make web-lint
make web-typecheck
make web-build
```

See [API settings and commands](apps/api/README.md) and
[frontend commands](apps/web/README.md). No provider credentials are needed.
Backend settings read process environment variables; no dotenv file is loaded
implicitly. The frontend currently consumes no environment variables.

## Repository layout and status

`apps/api` contains settings, health/readiness routes and tests. `apps/web` contains
the minimal Next.js App Router page and Tailwind/tooling setup. Infrastructure,
root scripts/tests and evaluation directories still contain placeholders; backend
tests live in `apps/api/tests`.

Follow [ROADMAP.md](ROADMAP.md) one phase at a time. Docker/Redis and CI remain
Phase 0 work. Git uses main with no remote. The environment template describes
planned settings as well as current ones; it is not a production configuration.
Retrieval, authorization and citations remain documented requirements.
