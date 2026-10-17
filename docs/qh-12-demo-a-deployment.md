# Demo A — candidate deployment gate (QH-12)

**Later owner authorization — 2026-10-17:** the owner explicitly chose hot reload
of frontend/backend on the existing VPS project, before PR #13 merge, instead of
this image-only activation. [Executed POC procedure](qh-development-stack.md) and
[deployment register](deployments.md) supersede the pending activation gate only
for that bounded operation. The prepared immutable images and evidence below
remain intact; no migration, realm change, MCP replacement or production release
is implied. QH-12 remains unmerged and Jira open for the owner's browser review.

2026-10-17. Preparation only: **NOT DEPLOYED**. This runbook authorizes no
persistent migration, backup of real data, Keycloak change or container replacement.
The owner must review/merge QH-12 separately and then authorize an exact image set
and maintenance window. Do not use development `make up` or `make migrate` on QH.

## Observed baseline and compatibility

Read-only inspection in this task confirms all six QH services healthy. Application
backend/frontend/MCP images carry OCI revision
`c723d32c5d0825f9232ece560e7e666e69dceb27`; PostgreSQL reports
`0005_retire_legacy_category`. App containers have no source mounts; Keycloak alone
retains the readonly root realm import. Private `.env` and runtime manifest checksums
remain unchanged. Runtime management uses `/home/ubuntu/qh-runtime/current`.
The [deployment register](deployments.md) retains previous activation evidence.

Main after QH-11 is `a5a635fb3200c77a3c1cf2b9e47dcdbb4116da73`.
QH-8/32/33 extraction/evaluation and QH-9/10/11 API/browser changes are merged in
source and **absent from c723d32**. QH-12 adds the read-only Understanding view.
Applied migration files through 0005 and the MCP app remain byte-identical to
c723d32. QH-12 changes no backend/Core/public DTO, policy or canonical schema.
No persistent migration, profile reinterpretation or graph-format change is needed.
Known 0005 startup and old/generic bindings remain mandatory isolated regressions.

## Browser access: approved local POC over SSH forwarding

A remote browser's `localhost` is the operator machine, not the VPS. The approved
Keycloak realm permits `http://localhost:5173/oidc/callback`, and the token issuer
is `http://localhost:8080/realms/qh`. Do not substitute a VPS hostname or add a broad
redirect/CORS allowlist to make the demo work.

The compatible POC access path uses **two SSH local forwards**, once separately
authorized deployment is complete (illustration only, not executed here):

```sh
ssh -N -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:5173:127.0.0.1:5173 \
  -L 127.0.0.1:8080:127.0.0.1:8080 USER@VPS_HOST
# In the operator browser: http://localhost:5173/
```

Both local ports must be free and both forwards must reach the same reviewed VPS.
The callback, discovery, code exchange and end-session use forwarded localhost;
API requests remain same-origin `/api` on the frontend tunnel. The packaged Vite
proxy sends those requests internally to `http://backend:8000`, retaining Bearer
authentication. API JWKS transport remains `http://keycloak:8080/.../certs` while
verifying the public localhost issuer. No browser tunnel to backend 8000 is needed.
No provider secret belongs in Vite's public configuration.

Isolated browser tests exercise these exact browser origins, callback and internal
proxy/backend/IdP topology in a private Docker namespace, with zero published ports.
This establishes contract compatibility, **not an executed SSH/VPS browser session**.
Actual SSH forwarding and post-deployment browser smoke remain NOT TESTED on the VPS.

A public domain/HTTPS reverse proxy, public IdP issuer, persistent BFF session,
external exposure or changed Keycloak allowlists would require a separate reviewed
security/deployment decision. None is necessary for the SSH-only local POC path.
The existing packaged Vite server is retained; this is not production hardening.

## Before asking for deployment authorization

1. Verify QH-12 owner review and actual merge. Fetch main by fast-forward only;
   record exact main SHA and compare executable/configuration trees with the
   tested image source. Stop on drift; build/retest new images if needed.
2. Inspect candidate backend/frontend/MCP immutable IDs and OCI revision labels;
   preserve old c723d32 IDs and the frozen bundle. Reusing a commit-shaped tag alone
   is insufficient. No registry push/tag/release or VPS activation is implied.
3. Recheck all running/stopped container IDs, mounts, environment/config fingerprints,
   health, ports and networks. Privately render the candidate image-only Compose
   from a new frozen bundle with the existing project `qh`, networks/volumes,
   namespace `qh-native` and private configuration. No `--project-directory`
   override. Preserve readonly realm bytes and all DB/IdP services/volumes.
4. Recheck schema 0005, registered profile definitions and unknown/non-ready intents;
   verify authorized old Space reads against retained smoke IDs. Stop on any
   unexpected data/schema/profile/format drift. Never reset epochs or rewrite rows.
5. Confirm the deployment needs **zero migrations** and no realm changes. Freeze
   canonical/manual/external writers for a consistent backup and cutover. Prepare
   a private backup destination with adequate disk space and mode 600 access.
6. Present exact source/image identities, isolated test results, pending VPS checks,
   backup plan and image rollback pins to the owner. **STOP for explicit approval**
   before any production backup, service stop, configuration write or replacement.

## Authorized-window backup and restore verification — future steps only

- With writers paused and the old backend stopped under explicit authorization,
  capture canonical/source/revision/provenance/current-pointer/registry/outbox
  fingerprints and the actual DB version. Retain exact smoke IDs privately.
- Create a restricted `pg_dump -Fc` of the actual current DB using its existing
  protected credentials; never print them or put them in command arguments/logs.
  Validate the archive listing and checksum. Preserve DB/Neo4j/IdP volumes.
- Restore into a **new isolated database on dedicated test infrastructure**, never
  over QH. Compare all canonical tables and immutable IDs/content/provenance, plus
  operational/outbox state at the stopped-writer snapshot. Verify native graph
  recovery from canonical data with the candidate, exact-ID retrieval and auth.
- Keep the backup/private inventory at a durable protected destination. Temporary
  scratch success is not evidence that a durable production backup exists.

The test harness rehearses this sequence with entirely synthetic data: valid
archive, distinct restored DB, exact table fingerprints, new graph rebuild without
extraction, candidate restart and real browser retrieval of the same revision IDs.
It does not back up or restore the VPS. Executed results belong to the QH-12 report.

## Activation/smoke/rollback boundary — future authorized window

Only after owner approval: use a new frozen bundle with reviewed image pins and
no source mounts. Replace only authorized app services with `--no-deps --no-build`;
leave PostgreSQL, Neo4j, Keycloak, their volumes/networks and the readonly realm
unchanged. Preserve `qh-native` and queue state. No migration or bootstrap reseeding.
Keep production configuration atomic/scoped and private; retain the previous bundle.

Acceptance requires actual forwarded browser login, correct QH identity, create/
open/back, explicit current/proposed/history queries, source/relation/revision IDs,
empty versus unavailable behavior and Alice/Bob denial; then restart **only the
candidate backend** and verify the same retained IDs without replay/extraction.
Do not claim live synthetic Understanding acquisition from the UI: there is no
public ingestion flow. Prefer retained authorized source data; any new persistent
synthetic pipeline import needs explicit owner authorization and must be retained.
Verify prior smoke Spaces, all service mounts/IDs, scope readiness and no leaks.

Rollback is **images/configuration only**, to the retained matching c723d32 bundle,
if compatibility checks permit. Stop writers first. The old UI/API loses the new
features but the database stays at 0005 with all committed data retained. Never
restore the old DB over newer content, downgrade 0005, delete new Spaces/revisions,
clear outbox intents or reset the graph to hide a failure. If old code cannot safely
read new content, keep writers stopped and diagnose/repair forward with review.
Do not automatically start fd50/0004 code against 0005. Record actual outcome and
new IDs/checks in deployments.md only after execution; reopening writers is gated
on successful smoke/readiness, not health alone.

No actual VPS backup/restore, SSH test, replacement, schema/realm edit or rollback
has been performed by QH-12 preparation. Pending authorization remains visible.
