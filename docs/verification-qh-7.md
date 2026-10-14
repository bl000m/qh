# QH-7 verification

Branch: `feat/QH-7-graphiti-context-engine`. Baseline: `b1769b6`, clean `main`
with no prior QH-7 implementation or verification report. Session completed local
verification on 2026-10-15 (Europe/Paris). Ticket and dependencies QH-2/QH-3 were
read through Atlassian MCP; QH-7 had zero comments. No Jira writes occurred.
Product Contract, architecture, ADR 0001 and canonical persistence ADR 0002 apply.

**Current verdict: QH-7 is not Done — live smoke FAIL.** The authorized bounded
Mistral experiment completed semantic ingestion/retrieval in space A, but space B
had no retrievable fact. It stopped after seven new requests, before either limit
(30 requests, 0.05 USD). No automatic retry/rerun was performed. Detailed outcome
and token ledger are recorded below; the earlier local/UUID sections describe
pre-live verification stages. Model reliability remains unapproved.

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
| Neo4j and Graphiti operational; real ingest + retrieval through ContextEngine | FAIL (live experiment) | Index initialization PASS; live ingestion/retrieval PASS for A, but B has no retrievable fact due to incomplete entity extraction. No end-to-end success is claimed. |
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


## UUID correction and VPS activation — 2026-10-15

The real Neo4j preflight exposed a gap in the earlier mocked ingestion check:
Graphiti 0.30.2 interprets `add_episode(uuid=...)` as an existing-episode lookup.
A new deterministic ID raised `NodeNotFoundError` before the provider boundary.
Installed source inspection of `Graphiti.add_episode` and
`EpisodicNode.get_by_uuid` confirmed that behavior. The previous hosted CI success
at commit `3ed53db` did not cover this real API behavior.

The adapter now creates only the missing derived EpisodicNode via its Graphiti
API before requesting extraction. Existing episode content, scope, descriptor,
type and reference time must match; conflicting reuse fails before provider
access. No Core contract, architecture, canonical PostgreSQL persistence or QH-8
workflow changes. A denied extraction may leave a partial derived episode; full
ingestion idempotence and concurrent conflicting writers are not claimed.

Executed checks:

- Regression test calls the real installed `Graphiti.add_episode`, with in-memory
  episode storage and the real SDK/approval transport. New UUID and matching reuse
  reach two separate denied approvals; conflicting text never reaches approval
  or overwrites the stored episode. No network is available. The same new test
  fails against the original adapter at its missing-approval assertion, confirming
  it detects the regression rather than reproducing the implementation.
- Targeted adapter, architecture and contract tests: **63 PASS** both in an
  isolated network-less image with current source and after backend activation.
  Running command: `sudo -n docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q -p no:cacheprovider tests/test_graphiti_context.py tests/test_architecture.py tests/test_contracts.py`.
- Backend Ruff check: **PASS** before build and in the recreated backend.
- `sudo -n docker compose --env-file .env -f infra/docker/docker-compose.yml build backend`:
  **PASS**, only backend image built. Dependency lock unchanged.
- `sudo -n docker compose --env-file .env -f infra/docker/docker-compose.yml up -d --no-deps --no-build --force-recreate --wait --wait-timeout 120 backend`:
  **PASS**, only backend recreated. Before/after container ID and mount comparison
  confirms the other five container IDs and every mount unchanged. No volumes or
  existing data deleted; no migrations executed.
- Installed backend version: **0.30.2**, confirmed with importlib.metadata;
  installed-source UUID semantics verified with inspect.getsource. Required
  Mistral/Neo4j settings all nonempty; no key printed, changed or validated externally.
- Actual Neo4j preflight inside the updated backend: **PASS**, fresh UUID and its
  reuse both reach the HTTP approval boundary. Both approvals deliberately denied;
  an additional in-memory HTTP transport would fail any attempted send. **Zero
  external requests sent**. One partial synthetic episode retained in scope
  `qh7-uuid-probe-e6362c64a5f0446f93dedc340be1278e`; existing data untouched.
- First pending request observed: Mistral Cloud, POST
  `https://api.mistral.ai/v1/chat/completions`, model `ministral-3b-2512`, entity
  extraction for `Ada founded Cedar Observatory.`, 5056-byte serialized request,
  max output 4096 tokens. This was denied, not executed. Actual live payload/hash
  must be reviewed again before single-request authorization.
- Backend local `/health`: **HTTP 200**. One non-failing upstream Pydantic Config
  deprecation warning remains in targeted tests.

The full 139-test baseline was previously executed; this limited adapter fix uses
63 targeted checks plus the actual Neo4j/HTTP-boundary probe, without repeating
unaffected migration/frontend/MCP/OIDC suites. Real semantic extraction, embedding
and end-to-end retrieval remain **NOT TESTED** and QH-7 remains **not Done**.
The environment is ready for the individually authorized live smoke; no real
Mistral API call, remote push, merge, CI rerun or Jira write was performed.
The correction is a new local `fix(QH-7)` commit; existing commits are unchanged.


## Authorized bounded Mistral smoke — 2026-10-15

The owner explicitly authorized the complete synthetic two-space experiment:
maximum **30 new Mistral requests**, estimated budget **0.05 USD**, models
`ministral-3b-2512` and `mistral-embed`, no automatic retries or concurrent sends.
The grant supersedes per-call prompts for this experiment only. AGENTS.md was
updated to allow such bounded grants while keeping default deny, scope checks,
accounting and stop-on-error. No new model/provider, architecture, QH-8 behavior,
public endpoint or canonical persistence was introduced.

The temporary runner `/tmp/qh7-bounded-smoke.py` was executed once with
`--run-authorized-experiment` inside the backend. It creates a new ledger directory
exclusively and refuses an automatic restart. Offline `--validate-only` checks
confirmed rejection before network send for exhausted count/budget and forbidden
models. The existing approval transport lock serializes each complete response;
an additional in-flight assertion prohibits overlapping sends. SDK and transport
retries are zero and Graphiti's retry wrapper remains overridden. Invalid HTTP,
JSON/schema/vector results and budget risks abort rather than silently continuing.

Each send reserves a conservative estimated token allowance based on full UTF-8
request bytes plus 1024 framing tokens and the actual max output (including the
16384-token edge extraction override). Both allowed model tariffs used are
0.10 USD per million input tokens and, for the LLM, 0.10 USD per million output
tokens. Response usage is reconciled after every call. All responses here were
HTTP 200 with valid JSON schemas/vector dimensions; semantic validity failed later.

Previously obtained entity extraction and Ada embedding were reused. A cache of
identical embedding inputs avoided repeated paid calls during persistence/internal
candidate searches and across spaces. These are temporary smoke optimizations,
not production Core behavior. Prior results are counted separately below.

| Functional criterion | Result | Evidence |
| --- | --- | --- |
| Source A, `Ada founded Cedar Observatory.` | PASS | Two entities and the FOUNDED fact persisted in derived state. ContextEngine returns `Ada founded Cedar Observatory` with exact QH source/revision provenance. |
| Source B, `Bea founded Cedar Observatory.` | FAIL | Entity extraction returned only Cedar Observatory. Edge extraction named Bea, which was absent from the node list; Graphiti dropped that edge. Neo4j confirms one entity and zero facts. |
| Semantic retrieval B | FAIL | Same semantic query, scope restricted to B, returned no hits. This is the stop condition. |
| Full isolation between two populated semantic spaces | NOT VERIFIED | A's returned hit has correct scope/provenance and no B content, but B has no semantic fact, so a complete two-sided isolation success cannot be claimed. |
| Response quality | FAIL | The B summary also introduced `Founded by Bea in 2023.` although the source contained no date. The data remains derived, without any approved Understanding Item or canonical PostgreSQL write. |
| Limits / no retries / serial sends | PASS | Seven new requests, estimated 0.0004597 USD, no HTTP failures/retries/parallel sends. No additional external calls after the missing-B-result stop. |

Schema validation does not imply semantic correctness: the incomplete entity list
and the reference to an unextracted entity were syntactically valid. The gap was
identified by final search and then explained using saved responses and local
Neo4j reads only. Do not treat Graphiti returning from add_episode as proof that
all source facts were retained. Future work before another live attempt should
add offline checks for missing expected synthetic entities, invalid edge endpoints
and unsupported summary content, then review the model/prompt behavior. No further
paid call or fallback model was attempted after this failure.

### Request and token accounting

The full key-free [response/usage ledger](evidence/qh7-mistral-smoke.json) includes
payload hashes, per-request output caps, tokens, validated results and costs.
It contains synthetic data only, no key, request headers or full prompts.

| New request | Model / purpose | Input tokens | Output tokens |
| --- | --- | ---: | ---: |
| 1 | mistral-embed — Cedar Observatory | 7 | 0 |
| 2 | ministral-3b-2512 — A edge extraction | 1406 | 99 |
| 3 | mistral-embed — A fact vector | 10 | 0 |
| 4 | ministral-3b-2512 — B entity extraction | 932 | 44 |
| 5 | ministral-3b-2512 — B edge extraction | 1391 | 103 |
| 6 | ministral-3b-2512 — B entity summary | 564 | 33 |
| 7 | mistral-embed — semantic search query (reused for both spaces) | 8 | 0 |
| **New experiment total** | **7 requests: 4 LLM + 3 embeddings** | **4318** | **279** |

New experiment: **4597 tokens**, estimated **0.0004597 USD**. Prior separately
authorized requests: entity extraction 932 input + 73 output, Ada embedding 4 input;
**2 requests**, **1009 tokens**, estimated **0.0001009 USD**. Combined smoke history:
**9 real requests**, **5254 input + 352 output = 5606 tokens**, estimated
**0.0005606 USD**. These are tariff-based estimates, not billing-invoice amounts.
All ledger counts and token sums were reconciled offline. No further API call was
made to fetch billing or verify the key. Synthetic scopes and derived data remain
available for inspection; no existing data/volumes were deleted.

Only offline read-only diagnosis and documentation continued after the stop.
No remote push, merge, CI rerun or Jira write was performed. No model reliability
approval or successful QH-7 completion is claimed. Local commit purposes/checks:
`docs(QH-7): allow explicitly bounded paid experiments` updates the permanent rule;
the following evidence commit records this failed live outcome and usage.
Both use staged diff/whitespace review and the secret guard; code/tests/dependencies
were unchanged by this experiment, so the prior 63-test adapter evidence is reused.
