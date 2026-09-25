.PHONY: api-install api-dev api-test api-lint api-format-check api-typecheck api-check db-check db-upgrade db-current db-history web-install web-dev web-build web-format web-format-check web-lint web-typecheck web-check check format-check docker-build docker-up docker-down docker-logs docker-ps
api-install:
	cd apps/api && uv sync --locked
api-dev:
	cd apps/api && uv run --locked uvicorn app.main:app --reload --host 127.0.0.1
api-test:
	cd apps/api && uv run --locked pytest
api-lint:
	cd apps/api && uv run --locked ruff check .
api-format-check:
	cd apps/api && uv run --locked ruff format --check .
api-typecheck:
	cd apps/api && uv run --locked mypy app tests
api-check: api-lint api-format-check api-typecheck api-test
db-check:
	cd apps/api && uv run --locked python ../../scripts/run_with_env.py ../../.env python -m app.db.health
db-upgrade:
	cd apps/api && uv run --locked python ../../scripts/run_with_env.py ../../.env alembic upgrade head
db-current:
	cd apps/api && uv run --locked python ../../scripts/run_with_env.py ../../.env alembic current
db-history:
	cd apps/api && uv run --locked python ../../scripts/run_with_env.py ../../.env alembic history
web-install:
	pnpm --dir apps/web install --frozen-lockfile
web-dev:
	pnpm --dir apps/web dev --hostname 127.0.0.1
web-build:
	pnpm --dir apps/web build
web-format:
	pnpm --dir apps/web format
web-format-check:
	pnpm --dir apps/web format:check
web-lint:
	pnpm --dir apps/web lint
web-typecheck:
	pnpm --dir apps/web typecheck
web-check: web-format-check web-lint web-typecheck web-build
check: api-check web-check
format-check: api-format-check web-format-check
docker-build:
	docker compose -f infra/docker/compose.dev.yaml build

docker-up:
	docker compose -f infra/docker/compose.dev.yaml up --build -d

docker-down:
	docker compose -f infra/docker/compose.dev.yaml down

docker-logs:
	docker compose -f infra/docker/compose.dev.yaml logs -f

docker-ps:
	docker compose -f infra/docker/compose.dev.yaml ps

.PHONY: api-dev-env web-test
api-dev-env:
	cd apps/api && uv run --locked python ../../scripts/run_with_env.py ../../.env uvicorn app.main:app --reload --host 127.0.0.1
web-test:
	pnpm --dir apps/web test:e2e
