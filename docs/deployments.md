# Deployment register

This register distinguishes executed environment changes from prepared artifacts.
It summarizes retained evidence, not a fresh VPS inventory. No deployment is
performed by adding a row. Product versions follow [versioning](versioning.md);
[CHANGELOG](../CHANGELOG.md) records changes rather than activation.

**Status alignment — 2026-10-17:** QH-8, QH-32 and QH-33 code/evidence are merged
on `main`; QH-33 PR #8 merged as `a7a2da3e43fca3fbcd54dd743956c14e0fa599e2` and
its approved technical scope is DONE. Independent human validation remains open
in QH-38, with null human metrics. These merges are **not deployments**: the VPS
backend/frontend/MCP still run images from
`c723d32c5d0825f9232ece560e7e666e69dceb27`, persistent schema 0005, without
application source mounts. Application image revision/mounts were rechecked
read-only for this alignment; no new schema probe or activation was performed.
The artifact identities and executed deployment records below are preserved.

## QH-11 browser candidate — 2026-10-17 (not deployed)

The existing frontend now has a candidate Space-management UI, tested with real
Chromium/PKCE against temporary Keycloak/PostgreSQL and the QH-9/10 API. Test-only
images and reproduction are in [QH-11](qh-11-mon-environnement.md). Its approved
session stores tokens only in memory and adds no backend service, schema or realm
change. This code is not on the VPS; the c723d32 frontend/API remain untouched.
Demo A activation belongs to separately authorized QH-12 work.

QH-10 PR #11 has since merged as `24c9f4f8c065bb78b7d62da46b33a2078ccecc6e`
and Jira is DONE. Its preserved artifacts below still represent tests, not deployment.

## QH-10 scoped retrieval candidate — 2026-10-17 (not deployed)

Final compatibility checkpoint: executable/test OCI revision
`e47a295fe5b9528571779d838286a55318846e51`, image
`qh10-retrieval:e47a295fe5b9528571779d838286a55318846e51`, immutable ID
`sha256:c93049dcc6b73938c7af6da7ea23db32e3c504d3772ca8463a973339241c2169`.
The historical JSON citation-property fix retains the existing schema and public
DTO; recognized QH-8 receipts retain strict locator validation. This supersedes
the test artifact below for current reproduction, without replacing its evidence.
No persistent environment or data change is performed.

Prior checkpoint retained:

Executable/test OCI revision `48cbb60627d1947092ec74607222af0e689ea0ca`, test image
`qh10-retrieval:48cbb60627d1947092ec74607222af0e689ea0ca`, immutable ID
`sha256:6fb804a03725037703797f0c1318e82713b0d3a90cf6b7f020f8965e99f2ea48`.
Built from Git archive; tests use dedicated disposable SQL/Neo4j and offline QH-8
fixtures, with no paid provider, source mounts in the packaged run, or persistent
QH write. Mandatory view selection and canonical hydrated responses belong to the
[QH-10 candidate contract](qh-10-scoped-retrieval.md). No schema/dependency change;
VPS images remain c723d32/schema 0005. This artifact is not a deployment window.

## QH-9 metadata REST candidate — 2026-10-17 (not deployed)

Executable/OCI revision `2f8386aa2efb8d74e30ceb589ab4abc1a6d45c76`, test image
`qh9-context-spaces:2f8386aa2efb8d74e30ceb589ab4abc1a6d45c76`, immutable ID
`sha256:7f5de34d7194d15646291fb6963c0ac20c8ede3974f4999bc79c6f7406a8460b`.
Built from Git archive with the existing hash-locked development image recipe;
no source bind/private configuration in the test container. The new metadata routes
reuse OIDC/PolicyService and existing SQL tables. Tests use unique disposable
databases, never the persistent QH database; schema 0005 on the VPS is unchanged.
See [contract and verification](qh-9-context-spaces.md). This is a local test
artifact, not Demo A deployment; that window belongs to QH-12 and requires
separate authorization. The VPS continues running the c723d32 application images.

## Offline personal-review package — QH-33 v2, 2026-10-16 (not deployed)

Executable/OCI revision `f745db5e62f65f35fd7960f93e367ff6fbeaa7f7`, image
`qh33-v2-review:f745db5e62f65f35fd7960f93e367ff6fbeaa7f7`, immutable ID
`sha256:684d040c124af536ba6ed13f9e6fc738e0278354f9c5c60eb4259ba04ab969d0`.
Built from Git archive; 19 v1/v2 accounting/review tests pass without network,
provider key or source bind. D1–D5 are approved rubric/POC decisions, not personal
review attestations. All 74 unit decisions remain pending. No migration, deployment,
canonical publication or inference. V1 artifacts, outputs and ledger remain sealed.
[Personal review matrix](evidence/qh33-v2-20261016/review-matrix.it.md).

## Offline evaluation artifact — QH-33, 2026-10-16 (not deployed)

Executable/OCI revision `16c280f373e9842c311188d147bb33abedba900e`, image
`qh33-semantics:16c280f373e9842c311188d147bb33abedba900e`, immutable ID
`sha256:757883a007c92c4ce134e6640e3858e04f156d1558d7f4e974621d1debbfeb62`.
Built from Git archive for offline benchmark/probe and disposable integration tests.
No runtime replacement, persistent migration, new provider request or local model.
Semantic labels remain provisional pending independent owner review. The separate
candidate prompt is prepared only, with no live/default instruction change.
[QH-33 report](qh33-semantic-evaluation.md).

## Offline follow-up artifact — QH-8 citations, 2026-10-16 (not deployed)

The owner authorized only frozen-capture offline resolution and an architectural
record, with no new paid inference or persistent QH change. Exact source/OCI revision
`1446a26e9821470f8619c08d3dba40e0662034ed`, tag
`qh8-citations:1446a26e9821470f8619c08d3dba40e0662034ed`, immutable image ID
`sha256:67bcad2b7160102652878e009bda29bc25d1e5484bb5878b21387d7d442b8a82`.
Built from Git archive without ignored configuration; test/replay runs have no
application source bind mount or provider key, only disposable SQL/Neo4j targets.
No schema version/migration, service deployment or model installation. Subsequent
report/evidence commits do not change executable code or this image identity.
[Follow-up report](qh8-citation-followup.md).

## Experiment artifact only — QH-8, 2026-10-16 (not deployed)

Owner-authorized four synthetic Mistral extractions ran on disposable test SQL/Neo4j.
First three used existing source `e2fde579b1bef86b8bfbf9fb0c12b476f998849a`.
Harness ordering correction and fourth request/offline personal replay used
`qh8-mistral:1ee72f18f1b6cfef7755f2ae5b34a3c09a393dd8`, OCI revision identical,
image ID `sha256:e3528ebc399e3a6391a5e742bf502e8b6b8c4b0fc9f40e85d77ab73d4a8b3aba`,
built from Git archive and executed without application source mounts. No QH
service replacement, persistent migration/provisioning, product release or schema
change. Live personal harness assertion and successful offline replay are separate
results. [Report and captures](qh8-mistral-evaluation.md).

## Executed — consolidated native foundation, 2026-10-15

| Field | Verified outcome |
| --- | --- |
| Authorization | Owner's final-consolidation attachment explicitly authorized both merges, CI, persistent 0005/provisioning, three application replacements, root checkout update, verified archive/retirement and native worktree removal |
| Git | PR #2 merge 8e5df3d30cfdf571e023871caf5585a076564c84; PR #3 merge **c723d32c5d0825f9232ece560e7e666e69dceb27**. Merge commits preserve 42a20c7, aabeced and all intermediate foundation commits. Graphiti is not merged |
| Image source / OCI revision | c723d32c5d0825f9232ece560e7e666e69dceb27; built from exact Git archives. Later execution-record changes are Markdown only |
| Backend | `qh-backend:c723d32c5d0825f9232ece560e7e666e69dceb27`; `sha256:29acb1370d9af489997c24c35c5becdb9d4d53bbfd348c4e28249df8fdc550f5` |
| Frontend | `qh-frontend:c723d32c5d0825f9232ece560e7e666e69dceb27`; `sha256:61733a41bc3a8a9dc63db6f28fbb71fb090db57833d2886fb33e898ec852d8e5` |
| MCP | `qh-mcp:c723d32c5d0825f9232ece560e7e666e69dceb27`; `sha256:5b7a54d1994fe864390edf6197506a203206381bf35667f1b9c980b16e51c8bf` |
| Hosted acceptance | [PR #2](https://github.com/bl000m/qh/actions/runs/38769832583): quality/OIDC/native green, 178 native cases; [PR #3](https://github.com/bl000m/qh/actions/runs/38774150451) and [consolidated main](https://github.com/bl000m/qh/actions/runs/38774841579): all three jobs green, **261 native tests, zero skips** |
| Final-image checks | Backend **6 packaging/runtime tests passed**, 89.02 s, no mounts; actual three-image isolated startup/0005/provisioning/smoke/restart passed, frontend build/typecheck and 2 MCP tests passed |
| Backup | Protected pg_dump custom archive at `/home/ubuntu/qh-finalization-evidence/qh-before-0005.dump`, SHA256 `db084b8e266a9c2e18830b21cfaff18746a95a8261b905f0cee53aefc274c45e`. Actual restore on dedicated PostgreSQL verified every canonical/operational row hash and trigger. Three restored CHECK deparses used equivalent elementwise varchar→text casts; exact equivalence was verified before migration |
| Schema | 0004 → explicit **0005_retire_legacy_category**. No database/volume recreation, no category value deletion. All old row hashes, 71 validated constraints, 24 enabled triggers and outbox/state preserved exactly during migration |
| Registered semantics | 3 exact qh.generic profiles explicitly provisioned; 11 historical registry entries retained (14 total). No old binding/revision rewritten |
| Persistent acceptance | Both historical qh.decision/1 scopes readable without rebuild; four generic synthetic proposals, exact source evidence, text/descriptor retrieval and foreign/mixed-scope denial passed. Backend restart returned identical IDs. A fifth generic revision committed with worker stopped remained pending and was recovered after startup; original IDs unchanged |
| Final data checkpoint | 5 synthetic users, 3 spaces/sources/source revisions, 6 stable items, 7 proposed item revisions/provenance/bindings, 7 ready outbox intents; 3 scopes synchronized, zero failed/pending. No automatic confirmation/current-pointer update |
| Shared preservation | PostgreSQL/Neo4j/Keycloak container IDs, mounts, credentials, qh_app/qh_data IDs and volumes retained. Six Graphiti nodes/four relationships retain fingerprint f604509c02424ecd613ae965e873ec4ba880461b37c122c3757a14c1ff032f32; no native cross-links |
| Runtime independence | Backend/frontend/MCP have **zero mounts**, no Python reload. Frozen reviewed Compose bundle `/home/ubuntu/qh-runtime/releases/c723d32c5d0825f9232ece560e7e666e69dceb27`, pointer `/home/ubuntu/qh-runtime/current`; readonly Keycloak root import path and bytes retained |
| Checkout | One permanent checkout `/home/ubuntu/qh` on main. QH-30, semantic and Surreal worktrees removed using git worktree remove without force. All branch refs retained; Graphiti unpublished commits and spike source commit 39b542a92a71f33f8cc65f6b18dafcd6d83746eb verified through a restored all-ref Git bundle |
| Retirement | 3 spike containers, exclusive Surreal volume (1809153 allocated bytes), empty spike network and 4 unused old Graphiti/fd50/Surreal images removed only after recoverable archive checks. No global prune. **All PostgreSQL/Neo4j/Keycloak volumes preserved**, including the spike PG/Neo stores and anonymous Neo log volume |

Exact synthetic scope/owner/item/source IDs are retained privately in
`persistent-generic-smoke.json`, `persistent-after-restart.json`,
`persistent-pending-recovery-intent.json` and `persistent-recovered-pending.json`
under `/home/ubuntu/qh-finalization-evidence`. They were not deleted. Original fd50 smoke evidence remains under
/home/ubuntu/qh-cutover-evidence. No LLM/embedding/extraction call occurred.

Surreal source/private settings, logical database exports and complete cold stores
were archived. PostgreSQL row hashes, both Surreal logical imports and cold restore
(persistent root metadata/schema/records/auth; runtime node/load metrics excluded),
and Neo4j cold graph/auth restore all passed on isolated copies. Docker save archives
were actually loaded and configs/layers compared before removing unused image tags.
Backups and private manifests are retained, mode-restricted, outside Git. Retained
PG/Neo spike volumes are intentionally protected by the owner's explicit limit,
not operational alternative implementations. Shared regression servers/base images
remain in use and were not classified as obsolete.

Management (no source worktree needed):

```bash
sudo -n docker compose --env-file /home/ubuntu/qh/.env -p qh \
  -f /home/ubuntu/qh-runtime/current/infra/docker/docker-compose.yml \
  -f /home/ubuntu/qh-runtime/current/infra/docker/qh-immutable.yml \
  -f /home/ubuntu/qh-runtime/current/infra/docker/qh-idp-path.json config --quiet
```

Do not use development `make up` for this VPS. Never restart archived fd50 against
0005, downgrade, clear outbox or restore over newer content. Future modifications
still require their own task/authorization. The current record is an unversioned
development deployment, not a new tag/release or Jira status change. QH-8 has not
started; extraction, embeddings and advanced semantic retrieval remain future work.

## Executed — VPS native cutover, 2026-10-15

| Field | Recorded result |
| --- | --- |
| Authorization | Owner explicitly authorized controlled 0003/0004 activation and backend-only replacement; resumed with corrected Compose invocation omitting project-directory override |
| Product release | Unversioned development deployment; no retrospective tag/release |
| Source / OCI revision | `fd50b1ba67061ea95285a2ffce122939524ab93f` |
| Image tag | `qh-native-backend:fd50b1ba67061ea95285a2ffce122939524ab93f` |
| Docker image ID | `sha256:0d30a854117eefebb14f83ec2ffcf892f7d9c383a6d9c66576d66d9067547e45` |
| Schema before → after | `0002_oidc_identities` → explicit `0003_native_semantics` → `0004_projection_outbox` |
| Backend source | Five bind mounts: apps/api app, adapters and tests, plus root tests/scripts under `/home/ubuntu/qh-worktrees/qh-30`; image identity alone does not certify mounted source |
| Runtime / graph | Native engine and backend-local incremental worker; namespace `qh-native`; existing `qh_app`/`qh_data` and database volumes retained |
| Acceptance | Synthetic canonical write/outbox/worker/retrieval/provenance, owner/mixed-scope denial and controlled backend restart PASS; two retained synthetic revisions/scopes, no auto-confirmation |
| Preservation / recovery | Shared services unchanged; six Graphiti nodes and their relationship fingerprint preserved. No destructive downgrade or historical-resource retirement |
| Evidence | [Executed cutover](qh-30-plan.md#persistent-cutover-execution-and-read-only-historical-inventory); restricted exact evidence/backups under `/home/ubuntu/qh-cutover-evidence`, not in Git |

## Historical prepared candidate — superseded by executed main activation

The [foundation publication record and runbook](qh-semantic-consolidation.md#deployment-0004--0005--prepared-not-authorizedexecuted)
identify the reviewed candidate's fresh no-mount packaging/integration results.
Prepared image source is `95b3a8f8cdcd6c8133ac7d1252fe3d81d35a2fc4`, tag
`qh-semantic-candidate:95b3a8f8cdcd6c8133ac7d1252fe3d81d35a2fc4`, Docker image ID
`sha256:dbae3e5701725c1bbcf99d1a0cc25f025e3df488adef8a7ae2f08a7e0ef34c2f`,
with matching OCI revision. The later evidence commit changes documentation only;
this is not the currently deployed fd50 image. Fresh strict integration passed
**261 tests, zero skips**, 316.60 s, entirely in that image without source mounts;
its six packaging/runtime cases are included in that run. Historical candidate results remain dated
there and do not certify the latest image. Runtime remains 0004/fd50 until separate
activation authorization; a green hosted CI will not constitute that authorization.

0005 requires stopped writers/backend, a verified logical backup of actual 0004
data, explicit 0005 target, before/after canonical/guard/outbox comparison, controlled
generic-profile provisioning and a compatible new backend with matching mounts.
After acceptance append an executed row with actual image/source/schema/namespace,
retained synthetic IDs, restart result and any repair. Never restart fd50 against
0005, remove history, delete synthetic data or restore over newer data as fallback.
No target migration, profile provisioning, backend replacement or resource cleanup
has occurred in this preparation.

The owner's subsequent [main consolidation plan](main-consolidation.md) supersedes
the worktree-mounted activation: merge QH-30 and semantic foundation through their
separate approval gates, then build/review final-main images and deploy the three
app services without source mounts. The 95b3a8f candidate remains verified baseline
evidence, not the final consolidated release. No new executed deployment is added.
