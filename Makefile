.PHONY: api-install api-dev api-test api-lint api-format-check api-typecheck web-install web-dev web-build web-lint web-typecheck
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
web-install:
	pnpm --dir apps/web install --frozen-lockfile
web-dev:
	pnpm --dir apps/web dev --hostname 127.0.0.1
web-build:
	pnpm --dir apps/web build
web-lint:
	pnpm --dir apps/web lint
web-typecheck:
	pnpm --dir apps/web typecheck
