# QH-12 — structured Context Space view and Demo A preparation

2026-10-17. [QH-12](https://contextlab.atlassian.net/browse/QH-12) uses the existing
React client, ephemeral OIDC session, QH-9 metadata routes and QH-10 canonical
retrieval. No backend/Core/public contract, schema, policy or provider change.
Deployment is a separate gate: **NOT DEPLOYED**. Owner review, merge and Jira
closure are pending; green tests alone do not make this task DONE.

QH-11 was closed first: owner-reviewed PR #12 merged with history as
`a5a635fb3200c77a3c1cf2b9e47dcdbb4116da73`; Jira QH-11 is DONE.
QH-12 starts from that updated main in `/home/ubuntu/qh`, branch
`feat/QH-12-context-understanding`. QH-13 is not started.

## What the browser displays

The existing Space detail retains QH-11 name/metadata and adds **Compréhension du
contexte**. It has explicit **Confirmé** (`current`), **Propositions** (`proposed`)
and **Historique** (`history`) views. Every POST names the view; no hidden fallback.
Current means confirmed-current, not the latest proposal. Confirmed historical
revisions and rejected/proposed rows retain their IDs/state in history.

Users submit either literal substring text or arbitrary descriptors, one per line.
Multiple descriptors use exact any-of semantics, case/whitespace preserved. Tentative
assignments are opt-in and disabled for text selection. Page sizes are bounded
5/20/50; cursors come unchanged from QH-10 after its view filter. Each request is
freshly checked; pages do not promise a transactionally frozen multi-page snapshot.
Changing selection/view cannot show a late historical result under a current label.
An error discards visible pages, including a failed subsequent-page request.

Each revision displays content (text or JSON fallback), structural shape,
open descriptor assignments and certainty, epistemic state, revision number/ID,
current-confirmed indicator, registered type/version, stable item ID, predecessor,
validation actor/time and separate temporal bounds. No dates are inferred from
creation time. An asserted assignment never implies content truth or confirmation.
Relations show the exact predicate and both stable item/revision endpoint anchors,
including older immutable anchors. There is no graph viewer or revision editing.

Provenance exposes authorized source IDs, revision IDs/numbers and origin/locator
JSON when supplied. Recognizable QH-8 receipt/locator payloads become literal quotes
with their original Unicode code-point bounds; no JavaScript UTF-16 slicing,
normalization, quote repair or semantic inference. Historical free-form `citations`
properties remain JSON, not verified quotation claims. No source body/name/description
is fabricated when absent from the DTO. Literal support is not semantic entailment.
The metadata API has no free-form Space description field; no new one is invented.

## Deliberately unchanged public contract

The owner required QH-10 selectors to remain authoritative. An initial instruction
asks for a view and a selector; **no API request is made to pretend to browse all
revisions**. No blank text, wildcard or hardcoded list of meanings is used.
Unclassified revisions can be retrieved by text; the entity control proves it.
A genuine browse-all mode would require a separately approved bounded public
contract, owner checks, view filtering before pagination and the same fail-closed
hydration. It is unnecessary for this selector-based acceptance and is not added.

PostgreSQL remains canonical, Neo4j derived/rebuildable, and PolicyService remains
the one backend gate. The UI adds no owner permission, confirmation action,
frontend extractor, ontology, membership, projection, sharing, MCP or paid inference.
[Product Contract](product/QH_PRODUCT_CONTRACT.md) and ADRs
[0003](adr/0003-native-context-engine.md)/[0004](adr/0004-unified-understanding-engine.md)
are unchanged. Session persistence/BFF remains future QH-42, not implemented here.

## Real isolated proof and fixtures

The reused [QH-11 harness](../scripts/test_qh11_browser.py), `--understanding`,
adds a new Neo4j 5.26.5 container and native worker to its own labelled network,
tmpfs PostgreSQL 16.8, disposable Keycloak 26.4.7 and real Chromium. It creates no
published ports and uses no production `.env`, network, volume or endpoint.
Credentials are generated in mode-600 temporary files and scoped to the containers
that need them; frontend receives no database/IdP passwords. Child output redacts
passwords, JWTs and callback values, including failed test logs. No traces/HAR,
login screenshots, session/token exports or LLM HTTP are used.

Setup reuses the unchanged QH-8 project fixture and actual internal extractor with
the deterministic **FixtureUnderstandingProvider**, not a new Mistral generation.
Its six original proposed revisions remain unchanged. Separate synthetic controls
add three decision revisions (confirmed/proposed/rejected), one reported-timestamp
entity and one historical structured payload with opaque bibliography: **11 revisions**.
Confirmed/rejected fixtures explicitly use the synthetic actor; they are not owner
attestations, real approvals or rewrites of original proposals. Human benchmark
review QH-38 and frozen QH-8/QH-33 artifacts/ledgers remain untouched.

Browser requests go through the actual packaged frontend same-origin proxy,
production FastAPI bootstrap, real JWKS/identity/PolicyService, canonical PostgreSQL
and the real Neo4j worker. Expected IDs/anchors are exported from the setup's
canonical SQL and compared with actual API payloads/DOM. Screenshots document those
runs; they do not substitute fixtures or screenshots for application behavior.
QH-11 regression scenarios remain included. UI-only fault/delay simulation is
explicitly separate from real owner denial and real graph outage.

Recovery stages stop **only the test graph**, prove real HTTP 503/unavailable
rather than empty, stop test writers, create/validate a protected synthetic pg_dump,
restore it into a distinct new DB, compare every table's count/hash, rebuild a new
graph from restored canonical rows without extraction, restart the exact candidate
backend, and repeat real browser retrieval of the same retained revision IDs.
Canonical table fingerprints remain unchanged across rebuild. Only successfully
created/labeled resources are stopped/removed normally; no forced cleanup or QH
volume deletion. The archive is test scratch, not a durable production backup.

## Reproduction and immutable candidates

Final executable/configuration source: `d70626bbe50c070c428b02564d22dec42b3b22b0`.
Backend, frontend, MCP and browser test images are built from its Git archive with
that OCI revision label. [Image manifest](evidence/qh12-demo-a-20261017/candidate-images.json)
records immutable local IDs, not a registry digest/release or deployment.
Later report/artifact commits have no executable/configuration drift.

```sh
python3 scripts/test_qh11_browser.py --sudo-docker --understanding \
  --backend-image qh12-api:d70626bbe50c070c428b02564d22dec42b3b22b0 \
  --frontend-image qh12-web:d70626bbe50c070c428b02564d22dec42b3b22b0 \
  --browser-image qh12-browser:d70626bbe50c070c428b02564d22dec42b3b22b0 \
  --output /tmp/qh12-evidence-new
```

Use a new/empty output directory. Omit `--sudo-docker` where unnecessary. To rebuild,
pipe `git archive` of that exact source to Docker using the existing API/frontend/MCP
recipes and `apps/web/Dockerfile.browser`, with the same revision label. The test
browser drives the separately packaged Node22 frontend, with no source mount.
No global host runtime/dependency installation is required.

## Definition of Done and checkpoint boundaries

| Jira/owner criterion | Required observable result / classification |
| --- | --- |
| Real detail with structured QH understanding | Actual Alice OIDC → Space → real scoped REST revisions; shape/content/descriptors/state/revision distinct |
| Decision/hypothesis/question/new meaning and unclassified | Exact open any-of descriptors and text selection, tentative opt-in; no fixed UI vocabulary |
| Current/proposed/history and pagination | Confirmed-current versus proposals/rejected history, exact IDs/cursors, late-response guard |
| Sources and relations | Source-revision IDs, original quotes and immutable relation anchors match SQL; opaque bibliography stays opaque |
| Missing/empty/errors/authorization | Instruction before search; current-empty, failed/denied and unavailable are distinct; Bob URL + direct scoped REST denied |
| Login/session/accessibility/navigation | Reused real PKCE/state/expiry/logout, keyboard/mobile/back/forward regressions and TypeScript build |
| 0005 compatibility and packaged recovery | New isolated 0005 install, real native engine, backup/restore fingerprint equality, graph rebuild and exact-ID browser re-open |
| Immutable candidate and preflight | Exact-source images/labels, readonly Compose render: same DB/IdP images/volumes/networks/realm; no app mounts |
| Actual VPS activation | NOT TESTED / NOT DEPLOYED. Separate owner authorization mandatory; conditional operational criterion is not claimed satisfied |
| Task DONE | Pending owner review, authorized QH-12 merge and Jira closure; ticket remains En cours |

Executed results from the sealed run are recorded below. Hosted final-head CI is
reported on the task PR; local success is not evidence of a hosted result.

## Demo A deployment readiness and limits

See the [separate preflight/backup/restore/rollback/smoke plan](qh-12-demo-a-deployment.md)
and [sanitized Compose preflight](evidence/qh12-demo-a-20261017/compose-preflight.json).
Read-only VPS checks observed healthy c723d32 images and schema 0005. Root realm,
private configuration, container/image/start/mount state and frozen evidence are
preserved. No migration is required; none is executed on QH.

The deployment access path is SSH forwarding of frontend 5173 and IdP 8080, preserving
the approved localhost issuer/callback and internal same-origin API proxy. Isolated
origins/proxy compatibility is tested; actual SSH/VPS browser smoke, real-data
backup/restore and replacement remain **NOT TESTED**. Public HTTPS/issuer/realm
changes would require a new decision; they are unnecessary for this local POC.

Technical candidate readiness is separate from permission to deploy. The current
VPS cannot show this source increment until a separately reviewed/authorized
activation. Existing acquisition is internal only: the UI cannot populate an empty
Space with Understanding. Any persistent synthetic import for a deployed demo
requires explicit authorization and retention of its IDs/data.

Chromium/mobile viewport/keyboard checks are not Safari/Firefox or a formal WCAG
audit. Semantic correctness and event-time entailment are not improved/validated
by rendering. Independent human semantic review remains QH-38. No new prompt
experiment, chat/ingestion or QH-13 work is performed.

## Initial executed verification — sealed source 50061be

| Check | Observed verdict |
| --- | --- |
| Packaged Node22 frontend build + strict TypeScript (app/tests) | PASS |
| Real packaged browser/native acceptance + contract/negative UI checks | PASS — 23 tests, zero skips, 57.1 s |
| Existing selected real OIDC/Core/SQL/reopen regression | PASS — 1 passed, 1 deliberately deselected live-only case, 14.45 s |
| Real Neo4j outage via test-container stop | PASS — 1 browser test, 3.8 s; 503/unavailable, zero misleading empty results |
| Synthetic backup → new-DB restore → all-table comparison | PASS — exact counts/hashes before operational rebuild |
| New graph rebuild and candidate backend restart | PASS — canonical table hashes unchanged, no extractor |
| Browser against restored data | PASS — 1 repeated exact-ID/provenance/history case, 14.1 s |
| Unchanged MCP image transport regressions | PASS — actual local Uvicorn server in network-disabled test container, 2 passed |
| Child-log redaction, Ruff/actionlint/whitespace/links/secret guard | PASS; log guard 1 passed, image-wide Ruff passed |
| Candidate Compose render | PASS — same DB/IdP image/volume models, networks, namespace, readonly realm; zero app mounts, loopback ports |
| Actual VPS schema/health/config preservation | PASS read-only — 0005, c723d32 app images healthy, retained container/mount/private-file fingerprints |
| Latest-head hosted quality/browser/OIDC/native CI | Recorded on task PR after publication; do not infer from this local table |
| Actual VPS backup/SSH login/deployment/post-cutover smoke/rollback | NOT TESTED / NOT DEPLOYED; explicit authorization required |
| Owner review, QH-12 merge, Jira DONE | Pending; task remains En cours / READY FOR REVIEW only after hosted checks |

Counts overlap previous targeted/preliminary runs and are not summed. The restored
browser case repeats an existing case under a different DB/graph lifecycle.
The existing Starlette/AnyIO deprecation and initial empty-graph missing-property
notifications during rebuild remain non-blocking; they are not graph health claims
for the VPS. First setup failures were corrected within test scope: insufficient
Neo4j tmpfs memory budget, an invalid fixture origin outside the existing enum,
and assertions incorrectly requiring a Z spelling instead of the returned canonical
ISO offset. One preliminary restored-browser run exhausted its 30 s budget during
competing builds; the sequential sealed run passes without retries or relaxed checks.
No product schema/rule or original capture was altered to make the fixture pass.

The initial source/configuration checkpoint was 50061be. Final correction d70626b
recognizes only descriptor assignments conforming to the approved value/certainty
contract, preserving other historical JSON without object-to-string coercion.
This fixes a reproducible rendering failure for an opaque legacy certainty object.
Nine targeted contract tests and strict TypeScript pass; the final packaged run
and current-head CI are recorded below/on the task PR. Initial metric/image
records remain in the evidence archive with an `-initial` suffix. Later
documentation commits are checked for zero executable drift against d70626b. Proposed next action is owner review
of the QH-12 PR and image/runbook evidence. No QH-13 work or automatic deployment.

## Final executed verification — source d70626b

The final packet supersedes the initial checkpoint for current reproduction,
preserving its `-initial.json` records. Exact-image Node22 build/typecheck PASS;
**24 frontend/Chromium checks PASS, zero skips, 55.7 s**, including the new actual
legacy JSON rendering control. Real OIDC/Core/persistence regression PASS (1 passed,
1 live-only case deselected, 14.46 s). Real graph outage PASS (1 test, 3.7 s).
Synthetic dump/new-DB restore, all-table fingerprints and canonical-preserving
rebuild PASS; real browser re-open of the same restored IDs PASS (1 repeated case,
14.5 s). Final MCP image/actual server: 2 tests PASS. Initial and final counts are
not summed. Latest-head hosted CI is recorded on [PR #13](https://github.com/bl000m/qh/pull/13).

All UI acceptance rows above are implemented and tested. Conditional deployment
rows stay NOT TESTED / NOT DEPLOYED, and owner review/merge/Jira closure remain
pending. The final candidate is **READY FOR DEPLOYMENT / NOT DEPLOYED** in the
technical preparation sense, subject to review/merge and a separate authorization
of exact image pins, access method and maintenance window. No permission is inferred.
