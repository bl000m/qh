COMPOSE = docker compose --env-file .env -f infra/docker/docker-compose.yml

# Existing VPS only: guarded frontend/backend operations, never dependencies.
.PHONY: dev-up dev-status dev-logs dev-restart dev-stop
dev-up:
	python3 scripts/manage_qh_dev.py up $(if $(DEV_SERVICE),--service $(DEV_SERVICE))
dev-status:
	python3 scripts/manage_qh_dev.py status
dev-logs:
	python3 scripts/manage_qh_dev.py logs
dev-restart:
	python3 scripts/manage_qh_dev.py restart $(if $(DEV_SERVICE),--service $(DEV_SERVICE))
dev-stop:
	python3 scripts/manage_qh_dev.py stop $(if $(DEV_SERVICE),--service $(DEV_SERVICE))

.PHONY: config build up down logs ps test smoke verify verify-running verify-infra verify-persistence migrate migration-current test-migrations lock-node lock-python
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
	$(COMPOSE) exec -T backend python -m pytest -q /workspace/tests/quality
	$(COMPOSE) exec -T mcp python -m pytest -q
smoke:
	$(COMPOSE) exec -T frontend npm run build:web
	$(COMPOSE) exec -T frontend npm run typecheck
	$(COMPOSE) exec -T backend python -m pytest -q /workspace/tests/smoke
verify:
	$(MAKE) check-secrets
	$(MAKE) config
	$(MAKE) up
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) smoke
verify-running:
	$(MAKE) check-secrets
	$(MAKE) config
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) smoke
verify-infra:
	$(MAKE) config
	$(COMPOSE) up --no-recreate --no-build -d --wait --wait-timeout 240
	python3 scripts/check_compose.py
	python3 scripts/verify_infra.py
verify-persistence:
	$(MAKE) config
	python3 scripts/verify_infra.py --persistence
migrate:
	$(COMPOSE) exec -T backend alembic -c adapters/postgres/alembic.ini upgrade head
migration-current:
	$(COMPOSE) exec -T backend alembic -c adapters/postgres/alembic.ini current
test-migrations:
	$(COMPOSE) exec -T backend python -m pytest -q tests/test_migrations.py
lock-node:
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace node:22.14.0-bookworm-slim npm install --package-lock-only --ignore-scripts --no-audit --no-fund

.PHONY: lint check-secrets lint-workflows
lint:
	$(COMPOSE) exec -T backend ruff check --no-cache app adapters tests /workspace/tests /workspace/scripts
	$(COMPOSE) exec -T mcp ruff check --no-cache app tests
check-secrets:
	python3 scripts/check_secrets.py
lint-workflows:
	docker run --rm -v "$(CURDIR)/.github/workflows:/workflows:ro" rhysd/actionlint:1.7.7 -color /workflows/quality.yml
lock-python:
	$(COMPOSE) build backend
	$(COMPOSE) run --rm --no-deps -v "$(CURDIR):/workspace" -w /workspace backend uv pip compile apps/api/pyproject.toml --extra dev --python-version 3.12 --universal --generate-hashes --only-binary :all: --output-file apps/api/requirements.lock
	$(COMPOSE) run --rm --no-deps -v "$(CURDIR):/workspace" -w /workspace backend uv pip compile services/mcp-server/pyproject.toml --extra dev --python-version 3.12 --universal --generate-hashes --only-binary :all: --output-file services/mcp-server/requirements.lock

.PHONY: oidc-up oidc-stop test-oidc test-oidc-application seed-oidc-demo
oidc-up:
	python3 scripts/init_oidc_env.py
	$(COMPOSE) --profile oidc up --build -d --wait --wait-timeout 300
	python3 scripts/configure_keycloak.py
oidc-stop:
	$(COMPOSE) --profile oidc stop keycloak
test-oidc:
	python3 scripts/verify_oidc.py
test-oidc-application:
	python3 scripts/verify_oidc.py --application
seed-oidc-demo:
	$(COMPOSE) exec -T backend python -m adapters.postgres.demo_identities
