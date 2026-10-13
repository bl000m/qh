# QH-2 verification — 2026-10-13

Ticket: [QH-2 — Definire confini QH Core e porte adapter](https://contextlab.atlassian.net/browse/QH-2)

**Definition of Done: PASS.** Targeted checks passed before each logical commit;
final integration passed **53 tests**, frontend build/type checks and Compose
validation. The updated backend image also built successfully. Jira was read
through Atlassian MCP; its status remains En cours and no Jira write was made.

## Acceptance checklist

| Requirement | Result | Evidence |
| --- | --- | --- |
| No Graphiti/FastAPI/MCP imports in Core | PASS | AST guard across all inner modules; prohibited, relative, type-only and dynamic import cases tested |
| Core independent of infrastructure | PASS | python -I -S imports all inner contracts without site packages; Neo4j and provider SDK imports also rejected |
| ContextEngine and LLMProvider replaceable | PASS | Two unrelated fakes per port; domain inputs/results and method annotations verified |
| Service contracts and explicit DI | PASS | Four inbound Protocols, immutable ApplicationServices, injected API factory bindings |
| Short ADR consistent with code | PASS | ADR 0001 documents exact methods, locations, dependency direction and deferred behavior |
| Targeted interface/boundary tests | PASS | 15 contract tests, two API composition tests, 28 architecture tests |
| Existing regression suite | PASS | Original FastAPI health, two MCP tests and five live service/DB smoke tests passed |
| Updated backend image build | PASS | docker compose ... build backend exited 0; image sha256:0d30d37bb4b818ee979aab73d983c0e354ef7fd1018999612be866a239b8df20 |
| Fresh start of the rebuilt image | NOT TESTED | Existing backend container retained; new source is tested through bind mounts |

The rebuilt image was not deployed over the running container: preserving
existing containers/volumes was an explicit constraint. This does not affect
contract/import/regression results, but those results do not prove a cold start
of that new image. No resources were removed or pruned.

## Local commit units and checks

| Unit | Commit / message | Checks before commit |
| --- | --- | --- |
| Domain models, inbound contracts, outbound ports and shared test fakes | 585a2b2 — feat(QH-2): define domain contracts and adapter ports | 15 targeted contract tests; staged scope, whitespace and secret checks |
| HTTP composition boundary | 3122116 — refactor(QH-2): inject services at the FastAPI boundary | Two API factory tests plus existing /health test: three passed; staged scope and whitespace checks |
| Architecture guard, ADR and final evidence | test(QH-2): enforce boundaries and document the architecture | 28 architecture tests; backend image build; final 53-test integration, frontend build/type checks, Compose/runtime network checks and staged review |

This report is part of the third unit. Its final hash is available in Git history
and the delivery summary rather than embedded in its own commit content:

```bash
git log --oneline --grep='QH-2'
git show 585a2b2
git show 3122116
```

The approved initial baseline is e91a01b (QH-1/QH-3, 43 files). The permanent
versioning policy is in QH-6 commit 3abeeca. Git was initialized during the
previous preflight; no baseline approval remains pending. No remote push,
force push, destructive reset, secret commit or global runtime installation
was performed.

## Implemented files and boundaries

- apps/api/app/core: immutable domain models, ContextEngine/LLMProvider ports and
  ContextService contract. Port signatures use QH domain values only.
- apps/api/app/policy, projections, chat: feature request/result models and the
  PolicyService, ProjectionService and ChatService inbound contracts.
- apps/api/app/composition.py: explicitly supplied service bindings without
  auto-discovery or default production adapters.
- apps/api/app/api and main.py: FastAPI inbound health route and create_app factory.
- apps/api/adapters/context and llm: reserved implementation namespaces; no
  Graphiti or provider integrations installed.
- apps/api/tests/fakes.py and test_contracts.py: framework-free contract test
  doubles and port/service tests. Test fakes never enter production composition.
- apps/api/tests/test_api_composition.py: framework-specific injection/health tests
  separated from domain contracts so commits remain independently verifiable.
- apps/api/tests/test_architecture.py: import-direction guard and isolated import.
- docs/adr/0001-modular-architecture.md: concise architecture decision.
- AGENTS.md, Makefile, README.md and docs/architecture.md: aligned module rules
  and existing-stack verification command.
- docs/initial-commit-review.md and verification-qh-1.md: historical baseline
  record updated to reflect the user's completed commit.

No production use cases, authorization rules, retrieval, projections, chat
orchestration, Graphiti or Sprint 1 behavior were implemented.

## Executed verification

```bash
# Targeted unit checks, each before the corresponding commit:
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q tests/test_contracts.py
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q tests/test_api_composition.py tests/test_health.py
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q tests/test_architecture.py

# Build, then one full integration pass without replacing containers:
docker compose --env-file .env -f infra/docker/docker-compose.yml build backend
make verify-running
python3 scripts/check_compose.py
```

Final test totals: **46 backend + 2 MCP + 5 live smoke = 53 passed**, zero failed.
This includes 45 QH-2 cases and all eight original cases. Vite built 31 modules;
web/shared TypeScript checks passed. Actual SDK MCP initialize/list_tools/call_tool
and authenticated PostgreSQL SELECT 1 / Neo4j RETURN 1 queries passed.

All five existing services remained healthy. Runtime inspection confirmed
qh_data Internal=true, both DB PortBindings={} and DB network attachments limited
to qh_data. Passwords were never printed. The stack was left running.

Runtime Protocol checks validate shape, not types or future business semantics;
annotation comparison and exercised QH values provide additional contract evidence.
No static Python type checker was added. One existing Starlette/AnyIO
BlockingPortal deprecation warning remains.

## Deferred / not tested

- Cold startup of the newly built image, intentionally avoiding container replacement.
- Database persistence write/restart/read, dedicated hot reload probes and browser UI automation.
- Static Python type checking and the existing dependency warning.
- Concrete services, policy enforcement, validation, provider error mapping,
  richer query operations and adapter integrations belong to subsequent tickets.
