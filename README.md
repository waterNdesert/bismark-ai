# Bismark AI

Bismark AI is a planned multi-tenant enterprise knowledge intelligence platform
for answering questions against authorized organizational documents with grounded
answers and traceable citations.

**Current phase: Phase 0 — Repository Foundation.** The Next.js and FastAPI
foundations, local Docker/Redis workflow, and validation CI are complete. Product
features, database integration, provider integration and production deployment
remain out of scope until Phase 1 or later.

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
make docker-build
make docker-up  # http://localhost:8000 and Redis inside Docker only
make docker-down
make docker-logs
make docker-ps
```

The frontend remains a local pnpm process. The API runs locally with uvicorn or
via Docker Compose, while Redis is a container-internal dependency reachable as
`redis:6379` from the API container. The API is reachable at
`http://localhost:8000` when running through Docker.

Stop development servers with Ctrl-C. Validation:

```sh
make check
make api-check
make web-check
make format-check
```

`make check` runs the complete backend and frontend validation suite without
starting Docker. Frontend formatting uses Prettier via `make web-format-check`;
`make web-format` applies formatting. CI runs these checks on pull requests and
pushes to `main`. Docker Compose syntax can be checked separately with
`docker compose -f infra/docker/compose.dev.yaml config`.

See [API settings and commands](apps/api/README.md) and
[frontend commands](apps/web/README.md). No provider credentials are needed.
Backend settings read process environment variables; no dotenv file is loaded
implicitly. The frontend currently consumes no environment variables.

## Repository layout and status

`apps/api` contains settings, health/readiness routes and tests. `apps/web` contains
the minimal Next.js App Router page and Tailwind/tooling setup. Infrastructure,
root scripts/tests and evaluation directories still contain placeholders; backend
tests live in `apps/api/tests`.

Follow [ROADMAP.md](ROADMAP.md) one phase at a time. Phase 0 is complete and CI
runs validation on pull requests and pushes to `main`. Git uses main with no
remote. The environment template describes planned settings as well as current
ones; it is not a production configuration.
Retrieval, authorization and citations remain documented requirements.
