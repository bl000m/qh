# QH-12 — structured Context Space view and Demo A preparation

## Current scope — browse-first amendment, 2026-10-17

The owner approved a navigable Context Space experience and a genuine read-only
browse operation before PR #13 merge. [ADR 0005](adr/0005-browse-first-context-understanding.md)
supersedes the earlier search-required UX recorded below, without rewriting that
checkpoint or changing QH-10 POST selector semantics. This remains the same
QH-12 branch, checkout and PR. Owner visual review, merge and Jira closure remain pending.

## Product decisions and rationale

“QH does not require users to know what to search for before showing them what
their Context Space understands. Browsing is the primary experience; search is a
complementary capability.”

The [ADR decision matrix](adr/0005-browse-first-context-understanding.md#product-decisions-and-rationale)
records motivations, alternatives, architectural/UX consequences and open points
for all eight owner decisions. The [Product Contract](product/QH_PRODUCT_CONTRACT.md#browse-first-understanding--owner-amendment-2026-10-17)
is the functional authority. Canonical content, open annotations, entity/relation
shape, immutable source/revision provenance and epistemic validation remain distinct.

The overview requests bounded current/proposed/history pages and displays existing
literal excerpts as `Aperçu structuré`, never validated synthesis or importance
ranking. Navigation uses exact canonical filters, with groups explicitly scoped to
loaded pages. No global facet counts or complete summary are inferred. A canonical
summary selection convention is not approved; a summary-labelled record is ordinary
content, not an automatically selected/validated synthesis. Generative synthesis,
interactive confirmation/editing and advanced graph navigation remain future work.

`GET /context-spaces/{id}/understanding` reuses the QH-10 canonical revision page.
View is mandatory; limit 1–100, UUID cursor, descriptor/tentative, kind/unclassified,
item/revision and explicit related-item filters are documented in ADR 0005.
The existing service/policy, owned canonical selection, exact Neo4j assertion
verification, hydration and freshness checks apply. No SQL-only bypass. Search
remains in `Rechercher dans ce contexte`; it still uses the unchanged QH-10 POST.

## Owner-approved acceptance criteria

1. Opening an owned populated Space renders `Aperçu structuré` without a search request; literal excerpts, ordering and partial coverage are explicit, with no invented narrative or ranking.
2. Current confirmed understanding, proposed content and retained history are visibly distinct. Proposed-only, historical-only and truly empty Spaces are distinguishable; no automatic confirmation.
3. New read-only GET `/context-spaces/{id}/understanding` requires explicit view and bounded UUID keyset pagination; optional exact navigation filters apply before LIMIT. QH-10 POST still requires its original selector.
4. OIDC internal identity and the shared PolicyService authorize before private reads and before disclosure on every page; missing/foreign Spaces yield uniform 404. Known IDs/cursors and arbitrary headers are not capabilities.
5. Canonical candidate IDs go through native graph verification, common canonical hydration/provenance/anchors and repeated readiness checks. Pending, missing/corrupt graph and concurrent changes fail closed with 503, including empty selections; no SQL-only fallback.
6. Open/multiple/tentative/absent descriptors and all three structural kinds remain navigable. Facets/counts derived from loaded pages never claim global coverage; subsequent pages are explicit user actions.
7. Shared revision renderer supports readable detail, exact relation predicate/endpoints, source provenance/literal quotes, temporal unknowns, item history and incident explicit relations; no inferred entity/relation or changed state.
8. Progressive disclosure and secondary search preserve keyboard/mobile usability. Loading, failed/late responses, changed filters and changed Spaces disclose no stale private content.
9. Real isolated Chromium/Keycloak/PostgreSQL 0005/Neo4j tests, native/OIDC/Core/QH-9/10 regressions, lint and complete latest-head CI pass with executed evidence, not static claims.
10. English ADR 0005, Product Contract amendment, architecture and QH-12 Product decisions and rationale record adopted choices, motivations, alternatives, consequences, limits and open questions with cross-links.
11. Existing single-checkout hot reload remains operational on original ports, with no infrastructure/MCP/realm/volume recreation, migration, paid call or persistent demo import. Empty Alice Spaces remain empty; a populated VPS demo requires separate write consent.
12. PR #13 remains the only task PR, unmerged for owner visual review; Jira stays open until reviewed merge and authorized closure. QH-13 is not started.

## Execution status for this amendment

Local acceptance is verified against exact source/image revision
`799c64ce5b615d42f6119c6d187b1f26d96f7237`, with no source mounts or inference
in the isolated runs. Later documentation/evidence commits have no executable or
configuration drift. [Separate archive](evidence/qh12-browse-20261017/README.md),
[measured results](evidence/qh12-browse-20261017/verification.json),
[image identities](evidence/qh12-browse-20261017/test-images.json).

| Criteria | Classification / executed evidence | Limits |
| --- | --- | --- |
| 1–2: immediate overview, explicit epistemic views | Implemented and tested, PASS: populated preview without POST query, separate current/proposed, empty/proposed-only/historical-only real browser controls | Literal excerpts, not semantic synthesis; proposed includes all retained proposed revisions, not a curated active approval queue |
| 3: bounded no-selector contract and unchanged search | Implemented and tested, PASS: view-before-LIMIT, full keyset traversal, exact item/anchor filters, invalid/duplicate/unknown parameters; QH-10 regressions | Stable UUID order, not importance/chronological ranking or a multi-request snapshot |
| 4–5: policy, isolation, integrity, freshness | Implemented and tested, PASS: Alice/Bob API denial, revocation on next page, missing graph assertion/marker/pending and empty-scope outage; changed-during-hydration rejection even for empty results | No guest/write grant or SQL-only fallback |
| 6–7: open navigation, detail/provenance/history | Implemented and tested, PASS: novel Unicode/multiple/tentative/unclassified controls, all kinds, exact endpoints, literal citations and same stable item's retained revisions | Facets local to loaded pages; no global descriptor count/ontology, source-body API or inferred concepts |
| 8: disclosure and usability | Implemented and tested, PASS: late responses, failed pagination clears rows, keyboard Enter/navigation, 375px layout; QH-11 session/loading/error regressions | No advanced graph canvas or new persistence/session model |
| 9: integrated verification | Implemented and tested locally, PASS: strict **532 native tests, zero skips, 760.17 s**; packaged **29 browser/contract checks, 1.7 min**; real OIDC regression **1 PASS/1 live-only deselected**, real graph outage **1 PASS**, restored-ID browser **1 PASS**; Ruff, strict app/test TypeScript and private-file/whitespace guards PASS | Counts overlap and are not summed. Complete hosted quality/native/browser/OIDC checks are required and attached to the exact latest head of [PR #13](https://github.com/bl000m/qh/pull/13) after publication |
| 10: recoverable product decisions | Implemented and checked, PASS: English ADR decision matrix, dated Product Contract amendment, architecture/report/AGENTS links; Jira criteria appended with original wording preserved (Markdown line-break whitespace normalized by Jira) | Decision approval is not owner acceptance of the UI |
| 11: existing VPS and write boundary | Implemented and tested, PASS: real Chromium opens existing Alice empty Space and explores using only GETs; all six container IDs/images/mounts/config and protected .env/realm/frozen manifest unchanged | No populated persistent demo; personal Mac session is not attested |
| 12: review workflow | PR #13 remains open/unmerged on the same branch; Jira remains En cours; no QH-13 | Owner review/merge and authorized Jira closure remain outstanding; never DONE on tests alone |

Exact reproduction (dedicated test credentials only):

```sh
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  -w /workspace/apps/api --entrypoint python \
  qh12-browse-api:799c64ce5b615d42f6119c6d187b1f26d96f7237 \
  -u /workspace/scripts/run_qh30_integration.py
```

The reused browser harness command is in the archive README. It verifies backup,
restore, exact canonical hashes, graph reconstruction and reopening without
another extractor call. Existing Starlette/AnyIO deprecation and empty-new-graph
property notices remain non-blocking. The earlier missing test-fixture import and
gated network-free probe were corrected; final strict execution has no skips.
Preliminary/targeted counts are not added to the full suite. Original QH-8 and
QH-33 archive audits pass; no reference, ledger, source or semantic judgment is
rewritten. These tests establish navigation/integrity behavior, not general LLM
semantic correctness or independent human validation.

## Historical pre-browse implementation and evidence (preserved)

The following report describes the earlier selector-based contract. Statements
that browsing was excluded or required new approval belong to that earlier scope;
the owner's later decision and ADR 0005 above now govern the new implementation.


2026-10-17. [QH-12](https://contextlab.atlassian.net/browse/QH-12) uses the existing
React client, ephemeral OIDC session, QH-9 metadata routes and QH-10 canonical
retrieval. No backend/Core/public contract, schema, policy or provider change.
Initial preparation was **NOT DEPLOYED**. A later explicit owner decision on
2026-10-17 authorized [VPS hot-reload activation](qh-development-stack.md) before
merge. That executed transition is separate from the sealed-image tests below.
Owner browser review, merge and Jira closure remain pending; green tests alone
do not make this task DONE.

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

## Optional populated VPS demo plan — NOT EXECUTED

The live Alice Spaces remain empty and are not reassigned historical understanding.
The real VPS smoke opens the existing retained Space through Code+PKCE, observes
`Aperçu structuré` and the honest empty state without a search, then explores using
only GET requests. No Space, identity, source, understanding or outbox intent is
created by this browse increment. Populated examples are isolated test screenshots.
The owner's own Mac/forwarding session is not attested by VPS Chromium.

If the owner later wants interactive populated content, obtain separate explicit
persistent-write consent first. A minimal plan would use one conspicuously named
synthetic demo Space with stable import/source/revision IDs, an immutable fixture
fingerprint/checkpoint, one synthetic source and six generic proposed QH-8 fixture
revisions (including entity/relation and exact citations). Resolve Alice through
existing internal QH identity; never rebind old owners or infer write permission
from READ_CONTEXT. Replay identical IDs/content idempotently; stop on any conflict.
Use the existing internal fixture import/extractor/publisher and native worker,
without LLM calls, schema/profile changes or deployment. Preserve proposed state,
null confirmed pointer and every created artifact/row. No confirmed examples or
human actor assertions without a distinct explicit validation authorization.
Verify exact IDs/provenance and Bob denial; retain the demo instead of deleting it.
This plan is not an authorized command, a seeded dataset or part of technical Done.
