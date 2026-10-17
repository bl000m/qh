# Main consolidation and image-only runtime — executed record and historical procedure

**Later decision, 2026-10-17:** the owner authorized the existing VPS POC's
frontend/backend hot reload from the single checkout. See the
[current operating procedure](qh-development-stack.md). This record preserves
the earlier image-only consolidation and rollback identities; it no longer
establishes that branch switching is isolated from running apps.

2026-10-15. The owner subsequently authorized the full sequence in the attached
final-consolidation request. PR #2/#3 are merged and main c723d32 is deployed at
0005; smoke/restart/pending recovery and shared-resource preservation passed.
The permanent checkout is main, with native worktrees removed. The
[deployment register](deployments.md) is current; the procedure below preserves
its earlier preparation gates, now satisfied rather than new permission requests.
No QH-8 or paid provider work was performed.

Historical preparation: this plan follows the owner's consolidation request. No QH-8 work,
merge, branch switch, persistent migration, application replacement or historical
resource removal is authorized by publication approval. The nineteen-entry audit
is closed; its findings are not reopened here.

## First merge gate and ancestry

| Reference | Verified head / relation |
| --- | --- |
| main / origin/main | b1769b6eee5221cc76486f93987b337ff9bf4210 |
| QH-30 / PR #2 | 42a20c78db0dc8537ddf9deea2838a830363c180; 15 commits after main; missing documentation commit now published |
| Semantic foundation before this preparation | 2d8bdd29a35cb4a8b0a1580ad5ed12ec38d16b3d; descends directly from QH-30/42a20c7 |
| Graphiti | Local 77de43c, separate fork from b1769b6; not part of either native branch. Five local commits ahead of its remote are retained in the permanent shared Git repository |

[Draft PR #2](https://github.com/bl000m/qh/pull/2) remains open/mergeable.
[Hosted run 38769832583](https://github.com/bl000m/qh/actions/runs/38769832583)
passed quality, oidc and native-integration on **42a20c7**. The native job executed
**178 tests, zero skips**, 70.52 s; inspected logs confirm actual SQL/Neo4j execution.
Main currently has no branch-protection rule; no repository rules are changed here.
The required manual recheck before each authorized merge remains essential.
The quality gate has environment-gated skips; its color alone is not that evidence.
The workflow uses disposable GitHub-hosted runners and generated credentials, no
VPS deployment/SSH/production migration hooks. No deployment secret is consumed.

**Stop before merge.** After explicit approval, make #2 ready and use GitHub's
**create merge commit**, preserving all 15 source commits including 42a20c7.
Do not squash or rebase this already published history. Recheck its exact head,
current main and green checks immediately before the authorized merge.

Only after that merge, fetch main and publish `refactor/QH-30-semantic-foundation`
with a normal push, then open its separate PR **against main**. Verify:

```bash
git fetch origin main feat/QH-30-native-context-engine
git merge-base --is-ancestor 42a20c78db0dc8537ddf9deea2838a830363c180 origin/main
git merge-base origin/main refactor/QH-30-semantic-foundation
git log --oneline origin/main..refactor/QH-30-semantic-foundation
git diff --stat origin/main...refactor/QH-30-semantic-foundation
```

With the prescribed merge commit, the shared base is 42a20c7; the semantic PR diff
contains foundation changes and this bounded deployment preparation, without
reintroducing QH-30. The branches currently form a straight native line, so no
ancestry conflict exists. If main advances incompatibly, stop and present conflicts;
never force-push or silently rewrite history. Run all hosted quality/OIDC/native
jobs on the semantic PR (261 native cases expected for unchanged application code),
inspect no-skip native evidence, then **stop again before its merge**. The semantic
PR is intentionally not created before #2 merges; its hosted results are pending.
No Graphiti branch is merged, pushed or deleted by this procedure.

## Current filesystem dependencies — read-only verification

| Running service | Actual dependency | Consequence |
| --- | --- | --- |
| backend | Five source/test/script mounts under /home/ubuntu/qh-worktrees/qh-30; fd50 image | Retain checkout until authorized replacement and verified zero application mounts |
| frontend | Four mounts from /home/ubuntu/qh: apps/web source, index/config, shared source | Do not switch root branch while these source mounts are active |
| MCP | Two app/test mounts from /home/ubuntu/qh | Same branch-switch restriction |
| Keycloak | readonly /home/ubuntu/qh/infra/keycloak/qh-realm.json plus qh_keycloak_data | Preserve service, file/path/content and volume. Realm Git blob is identical across Graphiti and the semantic branch; recheck against final main before switching |
| PostgreSQL / Neo4j | Named qh_postgres_data, qh_neo4j_data, qh_neo4j_logs on qh_data | No checkout source dependency; preserve IDs, volumes, networks and data |

All six QH containers were inspected without printing environment credentials.
Root tracked/untracked status is clean, with ignored mode-600 .env and bytecode;
QH-30 is clean; semantic foundation has only its ignored Ruff cache. Surreal's
checkout retains five untracked spike files plus ignored .env/bytecode. No ignored
file was removed or copied into an image/Git. The initial sanitized mount inventory
is retained locally at /tmp/qh-main-consolidation-mounts.json. No root branch switch
or worktree removal has occurred.

## Optional image-only Compose override

Use [qh-immutable.yml](../infra/docker/qh-immutable.yml) **only for an authorized
activation**. It overrides the existing frontend/backend/MCP services: required
reviewed image pins, no build configuration, zero app volumes, no backend/MCP
reload. Default development Compose remains unchanged; no service/broker is added.
Compose must support `!reset` (local tested version 5.6.0). Render with the deployed
Compose version before approval; do not silently fall back to bind-mounted sources.

The frontend keeps its existing Vite server packaged in the image; this does not
claim a new hardened production web-serving architecture. Keycloak's readonly
configuration bind is retained deliberately; it is not an application source mount.
Comparing resolved configs including profile oidc showed PostgreSQL, Neo4j and
Keycloak service definitions, credentials, named volumes and networks unchanged.
Application ports remain loopback-only and database ports unpublished.

### Isolated executed proof

Executed against only qh30-sql-test (tmpfs, unique qh30_immutable_* database) and
qh30-native-neo4j-test (unique qh30-immutable-* namespace), plus three newly created
test app containers on isolated networks, without published ports. No QH volume,
network membership or container was changed. Only test-owned resources are removed
at teardown; the shared native regression servers are retained.

- Backend image: qh-semantic-candidate:95b3a8f8cdcd6c8133ac7d1252fe3d81d35a2fc4,
  ID sha256:dbae3e5701725c1bbcf99d1a0cc25f025e3df488adef8a7ae2f08a7e0ef34c2f.
- Frontend and MCP images built from git archive of 2d8bdd2 with matching OCI label:
  frontend ID sha256:a128d96fcd63ba551e71aa6e785982842f786e45c852083a84afb6f1cda361e5;
  MCP ID sha256:709f7093b4926eb7725dcda3a13daf51aaad96311e478fb3d7ce83ad092a9e00.
- PASS actual mount inspection: all three app containers have zero mounts; Python
  servers have no reload process. Backend → frontend HTTP and MCP /health succeed.
- PASS empty disposable install through 0005, explicit generic provisioning,
  source → outbox → actual backend worker → graph → text/descriptor retrieval,
  exact provenance, proposed state and foreign-owner denial; four synthetic items.
- PASS backend-only controlled restart: same scope/owner/item/source IDs retrieved
  read-only. PASS frontend build and TypeScript checks; MCP 2 tests passed.
- Prior full packaging proof remains 261 native tests without mounts on the 95b3a8f
  image; this configuration-only experiment is additional evidence, not a new full
  suite or proof of the not-yet-created final main artifact.

Reproduce by building the three images from reviewed Git archives, rendering base
plus immutable override, and using a test-only final override with ports reset,
backend dependencies reset, dedicated SQL/graph addresses/credentials, a unique
new database and namespace, and data network qh30-native-test. Run explicit 0005
and provisioning before starting only frontend/backend/MCP with --no-deps; inspect
actual mounts, run the existing smoke CLI, restart backend and verify retained IDs.
Never substitute QH addresses. The executed temporary harness/result are retained
at /tmp/qh_immutable_probe.py and /tmp/qh-immutable-probe-result.json; 43 local
Markdown links/anchors, Git whitespace and the staged credential guard passed. Credentials
remain mode 600 outside Git. This harness is evidence, not a production entry point.

## Post-merge 0005 cutover — separately authorized maintenance

Both Git merges and hosted acceptance precede this deployment. Build **all three
application images from the reviewed final main commit**, with its full OCI revision
and inspected immutable IDs; do not treat 95b3a8f as the final consolidated release.
Record the actual main/image IDs and fresh packaging checks before asking for
activation approval. An illustrative management invocation after those pins exist:

```bash
# After final main/image review; values come from the reviewed deployment record.
QH_IMAGE_ONLY_COMPOSE=(sudo -n env
  "QH_NATIVE_BACKEND_IMAGE=$QH_NATIVE_BACKEND_IMAGE"
  "QH_FRONTEND_IMAGE=$QH_FRONTEND_IMAGE"
  "QH_MCP_IMAGE=$QH_MCP_IMAGE"
  QH_NATIVE_CONTEXT_ENABLED=true QH_NATIVE_GRAPH_NAMESPACE=qh-native
  docker compose --env-file /home/ubuntu/qh/.env -p qh
  -f /home/ubuntu/qh-worktrees/qh-semantic-foundation/infra/docker/docker-compose.yml
  -f /home/ubuntu/qh-worktrees/qh-semantic-foundation/infra/docker/qh-immutable.yml)
"${QH_IMAGE_ONLY_COMPOSE[@]}" config --quiet
```

Preserve the [0005 transaction/backup/guard/smoke runbook](qh-semantic-consolidation.md#deployment-0004--0005--prepared-not-authorizedexecuted),
substituting the final reviewed main images and this immutable invocation. Never
execute its earlier worktree-mounted activation as a parallel deployment option.
Recheck live 0004, actual non-null category count and retained synthetic data;
freeze writers, stop only backend, take/validate restricted pg_dump of actual data,
apply explicit 0005 via the compatible one-off image and --no-deps, compare canonical
and operational hashes/constraints/triggers, provision exact generic profiles.
Start only backend/frontend/MCP with --no-deps --no-build. Replacement of all three
app containers is required to remove their current source mounts and requires
explicit approval, beyond the earlier backend-only activation authorization.

Keep PostgreSQL/Neo4j/Keycloak containers, credentials, volumes and networks exactly
as found. Compare IDs/mounts before/after, confirm six Graphiti nodes/fingerprint,
run authorized synthetic provenance/isolation/descriptor smoke and backend restart;
retain synthetic IDs and append the actual [deployment register](deployments.md).
If 0005 fails, verify transactional rollback before considering resumption. After
0005 commits, keep writes stopped on later failure; never restart fd50, downgrade,
restore over newer data, clear intents or delete smoke data. Repair forward with a
reviewed compatible artifact. No automated paid call or QH-8 extractor is involved.

## One permanent checkout and historical resources — after successful deployment

1. Reconfirm no running or stopped QH application container has a bind source under
   a soon-to-change/remove checkout; stopping a container alone does not remove its
   configuration dependency. Preserve the root .env and exact realm import bytes.
   Compare all ignored/local files with the pre-switch inventory; archive anything
   needed before changing branches, without exposing secrets.
2. After verified image-only activation and explicit checkout authorization, switch
   /home/ubuntu/qh to main and fast-forward its local ref to the approved origin/main.
   No force/reset. Keep its common .git, Graphiti local/remote branch refs and PR #1.
   Recheck Keycloak import file is identical to its retained blob; do not recreate
   Keycloak. Repeat app health, sync/read-only retrieval and mount inventory.
3. Use main's absolute base + immutable Compose paths for all later management.
   Old container Compose working-directory/config labels are historical metadata,
   not live filesystem mounts; record them before removal. Existing DB/IdP labels
   already refer to root. Do not run default make up on the VPS: it is the bind-
   mounted development path. Persist only reviewed image pins in ignored .env
   through an authorized scoped update, preserving all credentials.
4. Once merged ancestry, clean/ignored-file checks, runtime detachment and archive
   acceptance are satisfied, separately authorize native git worktree removal:
   `git worktree remove /home/ubuntu/qh-worktrees/qh-30` and
   `git worktree remove /home/ubuntu/qh-worktrees/qh-semantic-foundation` from root.
   Keep branch refs/remotes; no --force, directory deletion or clean. If Git refuses
   because of generated/ignored files, stop and obtain the scoped archive/cleanup
   authorization rather than forcing removal.
5. Surreal: use the [existing archive/stop plan](qh-30-plan.md#surrealdb-archive-and-stop-plan--prepared-not-executed).
   Preserve five untracked spike files/results, restricted .env and Git refs;
   validate exports/offline graph archives before separately approved graceful stop
   of exactly the three spike containers. Stop retains volumes/images. Only after
   archive acceptance and separate approval remove its worktree with git worktree
   remove; never force/remove unarchived local files. No new resource audit is needed.
6. Resource deletion/disk recovery is a later approval: ~667 MB spike persistence,
   ~481 MB exclusive Surreal image and container layers at the prior measurement;
   shared PostgreSQL/Neo4j images/layers are excluded. Stop alone mainly recovers
   ~606 MiB measured RAM, not volume/image space. Historical Graphiti images/6 nodes
   and shared root/DB/IdP resources remain preserved according to that inventory.

## Remaining approvals

- First: ready/merge PR #2 by merge commit at verified 42a20c7, after rechecking main
  and checks. Publishing authorization alone is not merge authorization.
- Then: after separate semantic PR, verified hosted CI and clean diff, its own merge.
- Then: exact final-main application image pins, 0005/provisioning/backup/retained-
  synthetic-smoke writes, backend/frontend/MCP replacement without source mounts.
- After acceptance: root checkout switch/fast-forward, local archive operations and
  individually reviewed git worktree removals; no branch deletion implied.
- Historical exports/stop, then any container/volume/image/network removal need
  their separate archive/retirement authorization. Jira writes/tags/releases remain
  outside this request. No QH-8 implementation before consolidation/acceptance.


## Final execution outcome

Both PRs merged by merge commit with green hosted checks; consolidated runtime
source c723d32 is deployed at 0005. All three final images passed new checks and
run without app mounts from a frozen release bundle outside the Git checkouts.
Protected backup restore, exact old-row integrity, descriptors/provenance/isolation,
identical-ID restart and durable pending recovery passed. Shared services and the
six Graphiti nodes are unchanged. `/home/ubuntu/qh` is the only worktree, on main.

All three spike containers and its empty network are removed after verified exports/
cold recovery. The exclusive Surreal volume and four unused historical images were
archived/recovered/removed; PG/Neo4j/Keycloak volumes are deliberately retained.
Surreal's five sources are in historical commit 39b542a, preserved by all-ref Git
bundle restoration. Root private settings, archive checksums, exact IDs and results
are protected outside Git. No remaining consolidation PR, forced history change,
prune, paid call or QH-8 implementation. See the exact deployment register above.
