# QH-7 verification

Branch: `feat/QH-7-graphiti-context-engine`. Baseline: `b1769b6`, clean `main`
with no prior QH-7 implementation or verification report. Session completed local
verification on 2026-10-15 (Europe/Paris). Ticket and dependencies QH-2/QH-3 were
read through Atlassian MCP; QH-7 had zero comments. No Jira writes occurred.
Product Contract, architecture, ADR 0001 and canonical persistence ADR 0002 apply.

**Verdict: QH-7 is not Done.** Local implementation and checks pass; real Mistral
ingestion plus semantic retrieval is **NOT TESTED**, pending explicit authorization
for each external request. No Mistral or other paid provider request was executed.
Final extraction model selection is deferred until authorized live verification.

## Delta and boundaries

Added the replaceable Python Graphiti adapter, explicit Mistral factory and
per-HTTP-request authorization gate. Graphiti 0.30.2 and transitive dependencies
are hash-locked; Core signatures and imports remain unchanged. Deterministic
space scopes and derived episode source/revision descriptors normalize search
results to QH values without canonical PostgreSQL writes or human validation.
Mistral Small is only a candidate; see [compatibility analysis and operating
instructions](qh-7-graphiti.md). No QH-8 source persistence or canonical mapping,
Understanding Items, projections, client or MCP features were implemented.

AGENTS.md now contains one permanent cost-authorization section. Each single
HTTP attempt requires separate consent; embedding batches are split into
single-text requests, Graphiti/SDK retries are disabled and paid reranking is
disabled in favor of local RRF. Factory construction performs no database index
writes, provider requests or telemetry. Index initialization is explicit.

Git author was configured only in this repository as Mathia Pagani,
`mathiapagani@gmail.com`, using the explicitly supplied identity. No global Git
configuration or previous commit was changed. No push or merge occurred.

## Definition of Done evidence

| Ticket criterion | Verdict | Executed evidence / limits |
| --- | --- | --- |
| Neo4j and Graphiti operational; real ingest + retrieval through ContextEngine | NOT TESTED | Local pinned Graphiti index initialization PASS; 33 indexes ONLINE on existing Neo4j. Real extraction/embeddings/retrieval were not invoked. Mocks do not satisfy this criterion. |
| Core API exposes no Graphiti types and Core imports no provider/framework SDKs | PASS | Architecture AST/import tests, contract tests and complete backend suite pass; Core files unchanged. |
| Separate technical scope for two Context Space IDs; authorization remains backend/Core | PASS (mock/static scope) | Adapter tests verify deterministic distinct scopes, explicit multi-space filters, rejection of foreign edges/episodes and missing provenance. No new public route or policy bypass. Real two-space retrieval remains NOT TESTED as part of live smoke. |
| Targeted tests executable in Docker; harmless data and no existing DB deletion | PASS | 12 adapter tests, 139 complete backend tests and 10 secret-guard tests pass in Docker. Synthetic fixture keys and text only; existing containers, volumes and application data preserved. Existing migration tests create and clean only their own isolated test DBs. |

## Commands and observed results

Docker socket access for the session user was denied; `sudo -n docker` works.
The execution sandbox also failed to initialize (`bwrap` loopback permissions),
so approved commands ran outside it. No runtime or package was installed globally.

- `sudo -n docker build -f apps/api/Dockerfile.dev -t qh-backend:qh7 .`:
  PASS, hash-locked dependencies installed in the image. Final build output was
  captured to `/tmp/qh7-final-build.log`. Existing containers were not replaced.
- `sudo -n docker run --rm --network qh_data --env-file .env -e POSTGRES_HOST=postgres -e POSTGRES_PORT=5432 -e MISTRAL_API_KEY= qh-backend:qh7 python -m pytest -q -p no:cacheprovider tests`:
  PASS, **139 passed**, 21.74 seconds, final built image without source mounts.
  Provider key overridden empty; internal data network only. Two non-failing
  upstream warnings: Starlette/AnyIO deprecation and Pydantic class Config deprecation.
- Targeted `tests/test_graphiti_context.py` with the rebuilt dependency image,
  current source mounted read-only and `--network none`: PASS, **12 passed**.
  Real Graphiti/OpenAI SDK request serialization was exercised only with an
  in-memory HTTP peer, covering JSON Schema, 1024-dimensional embedding handling,
  separate approvals, denied defaults/models/endpoints/batches and no retry.
- `sudo -n docker run --rm --network none qh-backend:qh7 ruff check --no-cache app adapters tests /workspace/tests /workspace/scripts`:
  PASS, all checks passed on the final built image.
- Quality tests `/workspace/tests/quality` in the dependency image with current
  tests/scripts mounted read-only and `--network none`: PASS, **10 passed**.
- `sudo -n docker compose --env-file .env -f infra/docker/docker-compose.yml config --quiet`
  and `python3 scripts/check_compose.py`: PASS; five base services, internal data
  network, no published DB ports, loopback application ports, persistent volumes.
- Local Neo4j index check: temporary `qh-backend:qh7` container on `qh_data`,
  existing `.env` credentials, explicit Neo4j URI/user, synthetic Mistral key/model,
  default deny approval. Executed `create_graphiti_engine()`, asserted driver
  `_init_task is None`, awaited `adapter.initialize()`, then queried
  `SHOW INDEXES YIELD name, state RETURN name, state`: PASS, **33 ONLINE**.
  Closed adapter and SDK. No ingestion/search, source inserts, deletes or provider calls.
- Noninteractive `make smoke-graphiti` with stdin from `/dev/null`: PASS rejection,
  stops before the Docker command. The real interactive smoke is **NOT TESTED**.
- `git diff --check`, `git diff --cached --check` and
  `python3 scripts/check_secrets.py`: PASS before implementation commit.
  Guard reports no sensitive values. The real VPS `.env` was not edited or printed.
- Final `docker ps`: all six existing services, including optional Keycloak,
  remain healthy. No container recreation, database reset, volume deletion or
  canonical application migration was performed by QH-7.

The first complete-suite invocation omitted `POSTGRES_PORT`: 105 passed, 2 failed,
32 setup errors from the missing variable. This was an invocation error; rerunning
with the explicit Compose-equivalent port passed all 139 tests. An initial offline
factory test revealed a pending coroutine from Graphiti's automatic driver index
initialization; construction outside the running loop removed that behavior and
warning. A final full suite followed integration; targeted checks covered the
single-input embedding change. Frontend/MCP builds and live OIDC flows were not
rerun because those sources/contracts were unchanged. Hosted CI was not triggered.

## Local commits

| Commit | Message | Purpose and checks |
| --- | --- | --- |
| `f9ae568` | `docs(QH-7): require authorization for every billable request` | Permanent per-call rule; staged diff review and whitespace checks. |
| `5afc8e7` | `feat(QH-7): integrate Graphiti with per-request Mistral approval` | Adapter, guarded factory, manual smoke, configuration and contracts; Docker build, 139 backend + 10 guard tests, 12 focused tests, Ruff, Compose, Neo4j index initialization, secret/index/diff review. |

The final documentation commit adds this report; its hash is available in
`git log -3 --oneline` and the delivery summary. Checks: documentation/reference
review, staged whitespace and secret guard. No further provider call is authorized
by these implementation or verification results.
