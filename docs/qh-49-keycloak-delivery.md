# QH-49 — durable theme delivery and actual VPS activation

2026-10-19. The owner explicitly authorized image selection in Compose/private
configuration, a Keycloak-only stop, protected cold backup/verification and
replacement, plus rollback to the prepared previous-theme image if needed.
QH-50 and PR #17 remain open for owner review; no merge or Jira DONE is authorized.
This operational dependency is delivered in the existing checkout/PR to preserve
QH-50 work without switching branches or stopping the source-bound applications.

## Cause and selected mechanism

The VPS still served the seven QH-43 theme files in its container writable layer.
QH-50's two FreeMarker overrides and new CSS were only in source/isolated tests.
The actual realm already selected `qh`, French default and fr/en: changing realm
settings or the authentication contract was unnecessary. The preflight captured
the OLD login through the real QH welcome path, not a direct isolated theme URL.

The new image bakes the exact public theme from `1a103d1c472d8d9325ac8ceb54a4db305e9eaef7`
onto the **same pinned Keycloak 26.4.7 base**. It has no runtime secrets, realm/user
export, DB data, new extension or application code. Unlike a source bind or writable-
layer installation it survives recreation and branch switches without mutable
checkout assets. The original logo/bubble/favicon bytes are unchanged.

| Artifact | Exact identity |
| --- | --- |
| Active tag | `qh-keycloak:26.4.7-qh-1a103d1` |
| Active image ID | `sha256:21451375143c0d31397f1d23cbb38aca9a872e220bd74c94d89f815635b43954` |
| Public-theme manifest | `sha256:7a9eace5814e474dca51ffa8ecbc15a01a7f5f2c3c912f1fd6284bc37e0d8e4a` |
| Previous-theme rollback tag | `qh-keycloak:26.4.7-qh43-rollback-20261019` |
| Rollback image ID | `sha256:945dc5567d3aa113fc88fadfe3f45d1342f83cd3861f0e09088d3c2888e46d69` |
| Saved two-image archive | `sha256:8137185034bd925ddb7aa8f48b766896fea398bd9010a2a48cf3b61167d4f367` |

The [release manifest](../infra/keycloak/qh-theme-release.json) pins base, source,
all twelve public files and both image IDs. The [Dockerfile](../infra/keycloak/Dockerfile.theme)
and [packaging guide](../infra/keycloak/README.md) document rebuilding into a new
candidate tag. Fresh builds verify payload hashes; no false claim of identical
build/provenance metadata is made. The saved archive preserves exact existing IDs.
No image/credential was pushed to a registry during this operation.

## Executed delta and recovery

The only effective Compose change is `services.keycloak.image`. Base Compose now
accepts `QH_KEYCLOAK_IMAGE`, retaining upstream 26.4.7 when unset for fresh local
installs. The private VPS selector chooses the sealed active image. No theme mount,
new service/port/network/volume, realm PUT, user/client/credential/policy or session
setting change was made. Start command, memory, healthcheck, `qh_app`, loopback 8080,
`qh_keycloak_data` and the root readonly realm import are preserved.

Only Keycloak was gracefully stopped and replaced. Before replacement its stopped
H2 volume was archived read-only, hashed, extracted into a new isolated volume and
compared file-for-file. The restored copy was subsequently started as an isolated
Keycloak, with no host ports/live volume; administrative Code login proved the same
realm/client/user configuration digest. This establishes recovery beyond merely
creating a tar file. The private archive contains IdP data/credential hashes and
must never enter Git/logs. Normal authentication updates sessions/events; this is
not a claim that active H2 bytes remain static after login.

Measured stop-to-readiness was **40.04 seconds**. Other five containers retained
IDs, image, start time, environment hash, ports, mounts and networks. Read-only SQL
checks preserve canonical tables, identities, demo Spaces/revision states, graph/
outbox progress and triggers; ledger/provider configuration is unchanged. The
existing app-only guard validates the new image selection without being weakened.
A repeat of the identical Keycloak-only apply kept the same container ID: no
second interruption/recreation occurred. The prior isolated test separately proved
actual container replacement on the same synthetic store and old-theme rollback.

The reviewed apply command targets only Keycloak, after checking exact image ID,
backup, configuration equivalence and the authorization boundary:

```text
docker compose --env-file /home/ubuntu/qh/.env -p qh \
  -f /home/ubuntu/qh/infra/docker/docker-compose.yml \
  -f /home/ubuntu/qh/infra/docker/qh-hot-reload.yml --profile oidc \
  up -d --no-deps --no-build --pull never --wait --wait-timeout 180 keycloak
```

This execution is not blanket permission for future recreation. Ordinary `make dev-*`
remains frontend/backend-only. Keep the selector when checking out future branches;
a branch missing this configuration must fail preflight rather than silently select
an old image. Do not recreate Keycloak with generic up/down or overwrite its data.

If an authorized rollback is needed, verify the sealed previous-theme image, set
only `QH_KEYCLOAK_IMAGE` to that rollback tag, then use the same guarded Keycloak-only
apply. The old QH-43 files are baked into that image, so it does not depend on the
destroyed writable layer. Keep the same existing data volume, realm selection and
OIDC configuration. No live H2 restore/overwrite is part of normal theme rollback.
Unexpected DB damage requires a separately reviewed recovery; never replace user
data silently. Rollback was rehearsed in isolation and was **not needed on the VPS**.

## Actual VPS verification and Definition of Done

The verifier used the normal `http://localhost:5173` Welcome → Se connecter →
Keycloak → Mon environnement path. It blocked non-GET QH API requests; only existing
Alice/Bob credentials were passed privately to the browser. No Understanding,
organization, review, chat/provider or canonical write was performed.

| Ticket criterion | Classification / observed result |
| --- | --- |
| Tracked theme/base/image identity and repeatable delivery | Implemented/tested — PASS: release manifest, sealed archive, exact file checks, image-only effective delta, repeat apply retains container ID |
| Same-volume recreation survives without source mount | Implemented/tested — PASS in isolation: persisted sentinel, Alice/Bob subjects and theme/CSS hashes survive replacement; previous-image rollback also passes |
| NEW login actually served on VPS, not only isolated preview | Implemented/tested — PASS: French/English actual screenshots desktop 1280×900 and mobile 390×844, original assets, rounded controls, no old large title, Continuer |
| Real auth, invalid password, logout/new auth and isolation | Implemented/tested — PASS: Alice reads three six-proposal demo Spaces; Bob's six foreign reads denied; invalid password, mobile auth, logout/fresh login and anonymous denial pass |
| OIDC invariants | Implemented/tested — PASS: Code+S256 verifier, state/nonce, memory-only tokens and actual state/nonce/PKCE negative controls; realm/client/user digest and 300-second setting unchanged |
| Backup and rollback | Implemented/tested — PASS: cold restore file equality AND isolated restored-Keycloak startup/config check; sealed previous-theme image rollback rehearsed. Live rollback NOT EXECUTED because no regression occurred |
| Canonical/runtime/provider preservation | Implemented/tested — PASS: unchanged other five services, canonical rows and states, root import, graph/outbox and ledger; zero new paid calls |
| Natural 300-second expiry timing | Prior executed evidence reused; not timed again in QH-49 because expiry/session behavior did not change |
| Owner visual review, reviewed merge and Jira closure | Pending; no automatic DONE, merge or next task |

The earlier complete QH-50 CI on `1a103d1` remains historical evidence. The companion
configuration/docs commit must pass its own required PR rollup; exact final run is
recorded in PR/Jira, not inferred from previous green checks. Targeted packaging,
configuration and guard checks cover this delta without another local full campaign:

- Network-disabled Docker pytest of `test_dev_management.py` and `test_secrets.py`:
  **27 passed**, with Ruff passing on the changed test.
- `Dockerfile.theme` built successfully with `--network none` into the separate
  `qh-keycloak:qh49-recipe-verification` tag. All twelve packaged file hashes and
  the manifest match the frozen theme. The live image/tag was not replaced by this
  verification build.
- Local Markdown file links, code fences and `git diff --check` verified before
  publication. Full required GitHub CI is checked separately on the final commit.

[Sanitized live receipt](evidence/qh49-keycloak-live-20261019/summary.json).
Actual BEFORE/AFTER desktop/mobile screenshots, raw private receipts, cold backup
and rollback materials remain under `.local-archive/qh49-durable-theme-20261019/`;
actual activation evidence is in `activation-20261019T202301Z/`. No raw realm,
credentials, H2 files, authentication URLs or private image upload is published.
The original QH-43 activation/source-only QH-50 reports remain historical records.
