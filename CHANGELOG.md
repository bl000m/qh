# Changelog

Changes to QH are recorded here by product outcome. This file is not a deployment
record or evidence of a published release. See [versioning](docs/versioning.md)
and the [deployment register](docs/deployments.md). No product release/tag has
been created; existing 0.1.0 package metadata belongs to development scaffolding.

## Unreleased — semantic foundation (QH-30)

### Owner-approved browse-first QH-12 evolution — 2026-10-17

- New scoped read-only canonical browsing alongside unchanged QH-10 search:
  explicit revision view, bounded keyset pages, exact navigation filters, native
  graph/canonical validation, shared policy and fail-closed freshness.
- Deterministic structured preview and page-local open descriptor grouping lead
  to readable detail, exact relation anchors and item history. No LLM synthesis,
  semantic taxonomy, editing or confirmation. English ADR 0005/Product Contract
  amendment and criterion-by-criterion QH-12 scope preserve previous history.
- Verification for this increment is recorded separately in the QH-12 report;
  the previous 503-native/24-browser checkpoint is not proof of browsing.

### Owner-authorized VPS development POC — 2026-10-17

- Existing project `qh`: activate QH-11/12 frontend and QH-9/10 backend from the
  single checkout with Vite/Uvicorn reload, preserving loopback ports, schema 0005,
  native worker/namespace, DB/Neo4j/IdP/MCP containers and volumes. Add guarded
  app-only `make dev-*` commands, drift regressions and updated switch safeguards.
- Real protected PostgreSQL dump restored in isolation; all 14 table fingerprints
  match. Separately authorized Alice/Bob identity provisioning fixes missing links;
  browser smoke conserves two empty synthetic Spaces (one unintended duplicate
  from the temporary smoke script, retained without deletion). Historical rows/evidence remain.
- Real VPS PKCE, same-origin API, Space UI, revision views, Bob denial and React/
  Python reload verified. Historical provenance checked readonly; populated Alice
  provenance and personal Mac verification remain pending. QH-12 PR #13 stays open;
  no merge, Jira transition, migration, realm edit or paid inference.

Earlier status entries below describe their checkpoints, before this explicit
runtime transition. The immutable bundle/images remain preserved for rollback.

### Status alignment — 2026-10-17

- QH-11 PR #12 owner-reviewed and merged with history as
  `a5a635fb3200c77a3c1cf2b9e47dcdbb4116da73`; Jira DONE, four green head jobs.
  QH-12 source/UI and Demo A preparation remain distinct from VPS activation.


- QH-10 owner-reviewed PR #11 merged with history preserved as
  `24c9f4f8c065bb78b7d62da46b33a2078ccecc6e`; Jira QH-10 is DONE. Its final
  head CI passed quality/OIDC and 503 native tests without skips. No activation.


- QH-33 technical scope closed: PR #8 merged as
  `a7a2da3e43fca3fbcd54dd743956c14e0fa599e2`, Jira DONE with the approved scope
  addendum. Reproducible v2 benchmark, separate provisional metrics, offline
  comparisons and integrity checks are merged; independent human review of all
  74 units remains open in QH-38, with null human metrics and no attestations.
- Roadmap follows the already updated Jira scope: Demo A QH-9–12; chat QH-13 and
  conversation-to-understanding QH-39; guest-link Demo B QH-40 with manual selection
  (QH-17 optional); complete MCP demo QH-26. These are planned flows, not shipped
  capabilities. Product Contract and ADRs 0003/0004 remain authoritative.
- Merged code/evidence is distinct from VPS activation: application images still
  use `c723d32`, persistent schema 0005. Documentation only; no new deployment,
  inference, migration, feature, release/tag or rewrite of frozen evidence.
  Earlier preparation entries below retain their historical scope; this dated
  status and the deployment register describe current activation.

### Added

- QH-12 candidate read-only Understanding view: explicit revision views, text/open
  descriptor selection, bounded pages, distinct validation/certainty/time/provenance
  and exact relation anchors. Real browser/native/SQL/graph outage and synthetic
  backup/restore/rebuild proof. Immutable images and Demo A deployment plan only;
  no browse-all API, schema/realm change, persistent operation or deployment.


- QH-11 candidate `Mon environnement`: existing React/TypeScript/Vite client with
  real OIDC Code + PKCE, ephemeral tokens, Space list/create/detail, bounded pages,
  retry/empty/expired/denied states and keyboard/mobile navigation. Backend remains
  the owner-policy enforcement point. Test-only Chromium/Keycloak/PostgreSQL proof
  and CI reuse existing API/identity fixtures; no new production service or schema.
  No Understanding UI, deployment or claim of complete Demo A.


- QH-10 candidate canonical retrieval via `POST /context-spaces/query`: explicit
  owner-authorized scopes, mandatory current/proposed/history view, native substring
  search or exact open-descriptor selection, bounded UUID pagination and verified
  PostgreSQL hydration after Neo4j lookup. Canonical payloads retain structural
  shape, registered profile/version, proposed/confirmed/rejected state, current
  pointer, exact source revisions, citations, relation anchors and temporal bounds.
  Pending/stale/missing graph state fails closed. No temporal/as-of filters,
  generation, canonical writes, new schema or deployment.

- QH-9 candidate REST metadata management: authenticated create/list/detail and
  name-only update, existing owner policy/identity mapping, bounded UUID pagination
  and canonical PostgreSQL persistence. Foreign/missing IDs share a uniform denial;
  SQL owner predicates fence stale permissions. No lifecycle/delete, schema change,
  Understanding retrieval, UI or deployment. Isolated HTTP/SQL/reopen regressions.

- QH-33 offline proposition benchmark, separate draft metrics and blank independent
  review packet; synthetic positive/mutated controls expose remaining semantic
  gaps. Complete literal temporal-evidence tokens now reject timestamp prefixes
  atomically. No claim of improved LLM comprehension or human-validated accuracy;
  candidate prompt and bounded future protocol remain unexecuted.

- QH-8 explicit offline citation derivation: unique exact quote matches in original
  Unicode turn spans, separate hashed audit/checkpoint, unchanged strict whole-batch
  publication and no live-provider change. Missing/ambiguous/foreign evidence fails
  closed; deterministic correction does not repair semantic assertions.

- Owner-approved single Understanding Engine with QH-client extraction and future
  authorized MCP proposal input; source-verifiable and externally declared provenance
  remain distinct. ADR 0004 adds no public API, permission, service or migration.

- QH-8 optional official Mistral Small 4 adapter, strict request/token/cost ledger,
  four independent synthetic inputs and frozen pre-call reference, isolated manual
  evaluation and mock HTTP/native-pipeline CI regressions. After two historical HTTP 429s, four authorized full-conversation
  extractions returned HTTP 200 on 2026-10-16; 7/8 cumulative requests retain
  USD 0.012 uncertain historical holds plus USD 0.00395415 conservative ledger
  accounting (USD 0.00392283 cache-aware calculated new usage).
  Captured 37 candidates: 23/34 citation spans exact, three relations lack evidence,
  one of four batches accepted. Frozen reference remains provisionally assessed
  by the implementing assistant, without independent human validation.

- QH-8 offline conversation import, interchangeable fixture/replay extractor,
  exact Unicode citation validation and conservative relation resolution. Generic
  proposed items commit through the existing canonical outbox; isolated owner,
  structured retrieval, restart/pending/rebuild regressions. Not deployed; no real
  LLM extraction, external calls or new public API.

- Three explicitly provisioned generic profiles: item, entity, relation. Optional
  open value/certainty descriptors and authorized exact descriptor selection with
  canonical hydration; specialized immutable schemas/rules remain supported.
- Isolated regressions for 0004/0005, strict PostgreSQL–Neo4j CI, actual backend
  process restart/recovery and packaging without source mounts.
- Release/versioning discipline, logical Jira milestone plan and deployment register.

### Changed

- QH-8 evaluation harness checks the revision matching its retrieval query rather
  than assuming PostgreSQL snapshot order matches publication order. No extraction
  instructions, reference, provider, or application behavior changed.

- Single-checkout development in `/home/ubuntu/qh`, one task branch/ticket/PR
  at a time; legacy worktree bootstrap disabled. Explicit technical readiness
  versus reviewed/merged/Jira-updated DONE. Existing experiment worktrees and
  frozen evidence retained under safe transition/retirement checks. Runtime
  resources and persistent QH data are unchanged.

- One registered canonical representation throughout native projection/retrieval;
  fixture category mapping and duplicate temporal/endpoint decoding retired.
- Standalone snapshot reconciliation/full-scope query checks retired. Incremental
  outbox is the normal path; explicit worker rebuild retains its generation publisher.
- Instructions distinguish active 0004/fd50 from the undeployed semantic foundation.
- Prepared opt-in image-only Compose for the existing three app services; isolated
  startup/smoke/restart verified, without changing shared DB/IdP resources. Main
  consolidation and removal of live source mounts remain separately gated.

### Migration boundary

- Applied forward-only `0005_retire_legacy_category` removes only a null legacy
  column/check, aborting on non-null history. Applied 0001–0004 and historical
  type bindings remain unchanged. Provisioning is separate from migration/startup.
- **Deployed to the VPS on 2026-10-15 with owner authorization.** The tested final-main
  images have no application source mounts; the backup was restored before migration.
  fd50 must never run against 0005.
- Extraction, embedding/cache, vector/hybrid search, Source Vault and Domain Packs
  remain future work. No public ingestion or descriptor-query API is introduced.

## 2026-10-15 — consolidated foundation, unversioned deployment

- PR #2/#3 merged with merge commits; main runtime source c723d32. Hosted quality,
  OIDC and 261 real native tests passed; final backend image packaging 6 tests passed.
- PostgreSQL advanced from 0004 to 0005 after protected backup/actual restore. Three
  generic profiles registered alongside eleven historical versions; existing data,
  71 constraints, 24 triggers and six Graphiti nodes preserved.
- Backend/frontend/MCP deployed as versioned images without source mounts. Exact-ID
  restart, descriptor/provenance/isolation smoke and stopped-worker intent recovery
  passed. Main is the permanent root checkout; technical history remains preserved.
- Historical resource/archive outcomes are recorded in [deployments](docs/deployments.md).
  This environment activation is not a public product release; no tag was created.

## 2026-10-15 — native cutover, unversioned deployment (QH-30)

- PostgreSQL advanced explicitly from 0002 through 0003 to 0004; native backend
  fd50b1b and incremental worker activated. Synthetic provenance/isolation smoke
  and controlled restart passed; shared services and six Graphiti nodes retained.
- This records an authorized environment change, not a retrospective 0.1.0 release.
  Exact artifact identity and evidence are in the [deployment register](docs/deployments.md).

Earlier milestones retain their original dated reports and ADRs; this changelog
starts from the recorded native cutover and does not invent past release versions.
