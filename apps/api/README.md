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
workspaces, and workspace_members. Authentication and profile bootstrap are implemented. Storage, RLS, worker,
tenant authorization and RAG remain deferred.

The verified `DATABASE_URL` uses the Supabase Session Pooler connection mode,
which supports the Phase 1A Alembic DDL migration. The URL remains local-only
and is never committed or logged.

## Authentication development

Set `SUPABASE_URL` (HTTPS project origin), `SUPABASE_ANON_KEY` (public key),
and `DATABASE_URL` in the ignored root `.env`. Start from the repository root
with `make api-dev-env`. Use `CORS_ORIGINS` matching the actual browser origin.
`make api-dev` still starts without loading a dotenv file. Health routes work
without auth credentials; authenticated routes fail closed with 503 when missing.

GET `/api/v1/me` reads the verified user's profile. POST `/api/v1/me` initializes
it idempotently. Both require a Supabase access token; no supplied user ID is
trusted. No service-role key or local JWT signing secret is needed. Read the
implemented contract in `docs/API.md` and security limits in `docs/SECURITY.md`.
