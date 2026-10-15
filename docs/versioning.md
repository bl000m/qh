# Versioning and milestone discipline

QH uses one product version `MAJOR.MINOR.PATCH`, separate from Git commits, Alembic
revisions and registered semantic type versions. The planned first product milestone
is **0.1.0**; it is not released. Current package manifests already say 0.1.0 as
scaffolding metadata; this does not establish a tag, release or deployed artifact.
This task changes no manifest or lockfile.

## Product and artifact identifiers

- Before 1.0, a minor increment identifies an intentionally incompatible product
  contract; a patch is a compatible correction. From 1.0, incompatible public
  changes increment major, compatible capabilities minor, corrections patch.
- Keep work in [CHANGELOG Unreleased](../CHANGELOG.md#unreleased--semantic-foundation-qh-30)
  until a release is explicitly approved. Then agree the version and align intended
  package metadata/locks, move those entries to a dated version and validate it.
  Do not manufacture historical versions from deployment dates.
- Git uses conventional messages with Jira keys. A proposed product tag is `vX.Y.Z`,
  created only with explicit authorization; GitHub Release and push need approval
  too. This document creates none of them.
- A deployable backend is identified by full source SHA, OCI revision label and
  Docker-inspected immutable image ID (registry digest too if later published).
  A commit-named tag is a convenience, not immutability proof. Fail preflight if its
  inspected ID/label differs. Do not claim a registry digest for a local-only image.
- Build from `git archive` of the reviewed commit, excluding local credentials.
  Test that exact image without source mounts. A later documentation-only evidence
  commit may follow it; prove no executable/configuration drift against the image
  source. Any runtime change requires a new artifact and relevant verification.
- Record schema targets independently (`0004_projection_outbox`, prepared 0005).
  They are not product versions. Semantic profile IDs/versions are immutable data;
  product releases must never reinterpret an existing registered version.

## Logical Jira milestones — document plan only

The table groups existing work for the planned V0.1. No Jira version, milestone,
fixVersion, issue link/status or estimate is created or changed by this document.
The owner must authorize remote changes and choose Jira's target-version metadata.
Do not infer ticket completion from a deployment or this plan.

| Logical checkpoint | Existing ticket scope | Evidence / exit boundary |
| --- | --- | --- |
| Native context infrastructure | QH-30 | Native runtime active at 0004/fd50; dated cutover evidence. Semantic-foundation publication, hosted CI and separately authorized 0005/provisioning/deployment still pending |
| First complete understanding flow | QH-8 | Future conversational source → interchangeable extractor → proposed canonical understanding/exact evidence → native retrieval. No implementation started by this preparation |
| Product access/selection flows | QH-9, QH-10 | Follow their approved contracts and dependency gates; internal selectors do not establish new public write/disclosure contracts |
| Original-source vault | QH-31 | Future original-byte storage/access/lifecycle. Outside the current foundation and not claimed complete |

A possible Jira target version is **0.1.0**, pending explicit owner approval to
create/assign it. These checkpoints do not promise that every future QH-31 feature
belongs to that first release; its release scope needs a separate owner decision.

## Publication and deployment records

For each verified unit, link its SHA and test command/result in the existing
foundation evidence. Before publication, require a clean branch, secret/index
checks, coherent changelog and no runtime drift from the tested image. Hosted CI
is a separate result recorded only after an authorized push/run.

For each authorized activation, append to [deployments](deployments.md): date/target,
authorization, code/image SHA and immutable ID, backend source mounts/configuration,
schema before/after, namespace, test/evidence references and recovery outcome.
A prepared candidate is explicitly undeployed. Keep prior deployment rows; never
replace historical results with later candidate tests. Private backups, credentials
and sensitive inventories stay outside Git. Release approval does not itself
permit migration, resource retirement or destructive rollback.
