# Deployment register

This register distinguishes executed environment changes from prepared artifacts.
It summarizes retained evidence, not a fresh VPS inventory. No deployment is
performed by adding a row. Product versions follow [versioning](versioning.md);
[CHANGELOG](../CHANGELOG.md) records changes rather than activation.

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

## Prepared — semantic foundation 0005, not deployed

The [foundation publication record and runbook](qh-semantic-consolidation.md#deployment-0004--0005--prepared-not-authorizedexecuted)
identify the reviewed candidate's full source SHA, image ID/OCI label and fresh
no-mount packaging/integration results. Historical candidate results remain dated
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
