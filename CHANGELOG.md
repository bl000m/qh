# Changelog

Changes to QH are recorded here by product outcome. This file is not a deployment
record or evidence of a published release. See [versioning](docs/versioning.md)
and the [deployment register](docs/deployments.md). No product release/tag has
been created; existing 0.1.0 package metadata belongs to development scaffolding.

## Unreleased — semantic foundation (QH-30)

### Added

- Three explicitly provisioned generic profiles: item, entity, relation. Optional
  open value/certainty descriptors and authorized exact descriptor selection with
  canonical hydration; specialized immutable schemas/rules remain supported.
- Isolated regressions for 0004/0005, strict PostgreSQL–Neo4j CI, actual backend
  process restart/recovery and packaging without source mounts.
- Release/versioning discipline, logical Jira milestone plan and deployment register.

### Changed

- One registered canonical representation throughout native projection/retrieval;
  fixture category mapping and duplicate temporal/endpoint decoding retired.
- Standalone snapshot reconciliation/full-scope query checks retired. Incremental
  outbox is the normal path; explicit worker rebuild retains its generation publisher.
- Instructions distinguish active 0004/fd50 from the undeployed semantic foundation.
- Prepared opt-in image-only Compose for the existing three app services; isolated
  startup/smoke/restart verified, without changing shared DB/IdP resources. Main
  consolidation and removal of live source mounts remain separately gated.

### Migration boundary

- Prepared forward-only `0005_retire_legacy_category` removes only a null legacy
  column/check, aborting on non-null history. Applied 0001–0004 and historical
  type bindings remain unchanged. Provisioning is separate from migration/startup.
- **Not deployed.** fd50 must not run against 0005; activation requires a reviewed
  compatible image/mounts, backup, explicit migration target and owner authorization.
- Extraction, embedding/cache, vector/hybrid search, Source Vault and Domain Packs
  remain future work. No public ingestion or descriptor-query API is introduced.

## 2026-10-15 — native cutover, unversioned deployment (QH-30)

- PostgreSQL advanced explicitly from 0002 through 0003 to 0004; native backend
  fd50b1b and incremental worker activated. Synthetic provenance/isolation smoke
  and controlled restart passed; shared services and six Graphiti nodes retained.
- This records an authorized environment change, not a retrospective 0.1.0 release.
  Exact artifact identity and evidence are in the [deployment register](docs/deployments.md).

Earlier milestones retain their original dated reports and ADRs; this changelog
starts from the recorded native cutover and does not invent past release versions.
