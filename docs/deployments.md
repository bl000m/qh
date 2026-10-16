# Deployment register

This register distinguishes executed environment changes from prepared artifacts.
It summarizes retained evidence, not a fresh VPS inventory. No deployment is
performed by adding a row. Product versions follow [versioning](versioning.md);
[CHANGELOG](../CHANGELOG.md) records changes rather than activation.

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
