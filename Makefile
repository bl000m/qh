COMPOSE = docker compose --env-file .env -f infra/docker/docker-compose.yml

.PHONY: config build up down logs ps test smoke verify verify-running verify-infra lock-node lock-python
config:
	$(COMPOSE) config --quiet
build:
	$(COMPOSE) build
up:
	$(COMPOSE) up --build -d --wait --wait-timeout 240
down:
	$(COMPOSE) down
logs:
	$(COMPOSE) logs --tail=100 -f
ps:
	$(COMPOSE) ps
test:
	$(COMPOSE) exec -T backend python -m pytest -q
	$(COMPOSE) exec -T mcp python -m pytest -q
smoke:
	$(COMPOSE) exec -T frontend npm run build:web
	$(COMPOSE) exec -T frontend npm run typecheck
	$(COMPOSE) exec -T backend python -m pytest -q /workspace/tests/smoke
verify:
	$(MAKE) config
	$(MAKE) up
	$(MAKE) test
	$(MAKE) smoke
verify-running:
	$(MAKE) config
	$(MAKE) test
	$(MAKE) smoke
verify-infra:
	$(MAKE) config
	$(COMPOSE) up --no-recreate --no-build -d --wait --wait-timeout 240
	python3 scripts/check_compose.py
	python3 scripts/verify_infra.py
lock-node:
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace node:22.14.0-bookworm-slim npm install --package-lock-only --ignore-scripts --no-audit --no-fund
lock-python:
	$(COMPOSE) build backend
	$(COMPOSE) run --rm --no-deps -v "$(CURDIR):/workspace" -w /workspace backend uv pip compile apps/api/pyproject.toml --extra dev --python-version 3.12 --universal --generate-hashes --only-binary :all: --output-file apps/api/requirements.lock
	$(COMPOSE) run --rm --no-deps -v "$(CURDIR):/workspace" -w /workspace backend uv pip compile services/mcp-server/pyproject.toml --extra dev --python-version 3.12 --universal --generate-hashes --only-binary :all: --output-file services/mcp-server/requirements.lock
