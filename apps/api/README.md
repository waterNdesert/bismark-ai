# API development foundation

Use Python 3.12 and uv. This conservative runtime baseline avoids assuming future
parser/AI dependencies support the host Python 3.14. Those dependencies remain
unselected. uv installs a single managed 3.12 runtime if needed.

From this directory:

```sh
uv sync --locked
uv run --locked uvicorn app.main:app --reload --host 127.0.0.1
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy app tests
make db-current
make db-history
make db-upgrade
make db-check
```

The backend can also be started through Docker Compose for the local Phase 0
baseline:

```sh
cd ../..
make docker-build
make docker-up
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ready
make docker-down
```

The containerized Redis service is internal to Docker only and is not published to
`localhost:6379`.

GET /health returns {"status":"ok"}; GET /ready returns {"status":"ready"}.
`/health` and `/ready` are process checks. `/ready/database` performs a generic
`SELECT 1` check and returns `{"status":"ready"}` or HTTP 503 without exposing
database details.

Settings read process environment variables, including secret-typed Supabase and
database settings. Database operations require `DATABASE_URL`; local database
commands load the ignored repository `.env` for the child process. The Phase 1B
schema foundation contains only profiles, organizations, organization_members,
workspaces, and workspace_members. Authentication, storage, RLS, worker, and RAG
implementation remain deferred.

The verified `DATABASE_URL` uses the Supabase Session Pooler connection mode,
which supports the Phase 1A Alembic DDL migration. The URL remains local-only
and is never committed or logged.
