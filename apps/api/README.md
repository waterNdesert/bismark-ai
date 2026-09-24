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
Readiness is process-only; no external dependencies are checked.

Settings read process environment variables: APP_ENV, APP_NAME, APP_VERSION,
LOG_LEVEL, FRONTEND_URL, and comma-separated CORS_ORIGINS. Local defaults require
no secrets. Origins must be explicit HTTP(S) origins without paths, wildcards or
credentials. CORS credentials are disabled. No dotenv file is loaded implicitly;
export variables in the shell. No database, authentication or product API exists.
