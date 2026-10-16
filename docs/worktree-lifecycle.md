# Single-checkout development and preserved worktree history

The mandatory rules live in [AGENTS.md](../AGENTS.md#single-checkout-development-policy)
and its [task/Done policy](../AGENTS.md#task-execution--definition-of-done-policy).
The owner's later 2026-10-16 single-checkout decision supersedes sibling-worktree
creation. All new development uses `/home/ubuntu/qh`, one task branch, Jira ticket
and PR at a time. Existing #5/#7 directories are paused transition exceptions.
Historical records below preserve earlier actions; they are not current commands
or instructions to create worktrees. This change does not merge any PR or deploy.

## Safe manual bootstrap in the single checkout

1. Read `/home/ubuntu/qh/AGENTS.md`, relevant skill, Jira objective/acceptance,
   dependencies/comments and the existing PR. Propose a verifiable DoD if missing.
   Confirm the previous task is closed, or record the owner's explicit exception.
2. Inspect `git status --short --branch`, staged/unstaged diffs, untracked and
   ignored files, and editor buffers. Save/commit approved work; preserve private
   configuration and evidence. Never hide changes with an automatic stash/reset.
3. Inspect active sessions, build/test/reload processes, open files and container
   bind mounts. Confirm no process depends on the current source tree. Check the
   target branch retains the exact readonly realm import bytes/path and does not
   overwrite private files. Stop if any safety fact is unknown or incompatible.
4. Fetch `origin/main`, select `main` only when safe, then fast-forward only and
   verify equality with fetched `origin/main`. Stop on divergence; no reset/rebase.
   Create the one authorized task branch from there, or select its existing branch
   after reviewing base/local commits/PR. An attached legacy branch blocks ordinary
   switching until its separately verified migration; never use force flags.
5. Work, test and commit only in `/home/ubuntu/qh`. Publish to the existing task PR
   as authorized. Corrections stay in that branch; no replacement PR or new task.

The steps are review gates, not an unconditional shell script. Do not switch during
an active editor save/build/test or while another coding session owns the tree.
The old `scripts/start_task_worktree.py` is disabled: no arguments, old plan mode,
`--create`, old hashes and directory options all fail without mutation; `--help`
only explains the change. No automatic replacement performs hidden switches,
fetches, runtime actions or task creation.

Development `make up`/generic Compose must not manage the persistent stack. Keep
production on the frozen `/home/ubuntu/qh-runtime/current` bundle. Switching Git
is not migration/deployment or permission to use production credentials in tests.

## Readiness, closure and reporting

- **IN PROGRESS:** implementation is underway or technical criteria remain unmet.
- **READY FOR REVIEW:** technical acceptance verified, PR published and unmerged.
- **DONE:** every Jira acceptance verified, PR reviewed and merged, Jira updated.

Green tests alone are insufficient. Report every criterion with evidence and
implemented/tested, implemented/unverified, not implemented or out-of-scope status.
Correct safe in-scope failures with regression tests; propose prioritized solutions
for unrelated issues. Jira writes and merge require explicit approval. If merge
succeeds but Jira closure is pending, say so and do not report DONE. Never start
the next task automatically. For this non-ticket policy maintenance, Jira is not
assigned: do not fabricate a key or claim an issue update.

## Executed non-destructive transition of PR #6 — 2026-10-16

Before switching, a read-only inventory found backend/frontend/MCP with no mounts,
using the frozen c723d32 release bundle. Database volumes were independent of Git.
The sole checkout bind was `infra/keycloak/qh-realm.json`, readonly and identical
between `main/f1e0ae6` and `b76b567`. Privileged process/open-file inspection found
shell/editor activity, no source-dependent app/test/reload process and no unreadable
processes. No branch change modified Compose, the realm, credentials or runtime.
These observations permit this transition, not arbitrary future branch switches.

Both checkouts were clean and fetched `main` equaled `origin/main/f1e0ae6`.
The existing #6 checkout `/home/ubuntu/qh-worktree-lifecycle-policy` was detached
normally at preserved `b76b567`; then the same `docs/worktree-lifecycle-policy`
branch was selected normally in `/home/ubuntu/qh`. No force, directory move or
removal occurred. `b76b567` remains an ancestor of the updated PR. The old directory
is a retained detached snapshot, not an active development checkout.

The #5 and #7 worktrees/HEADs remain unchanged at `5a604f6` and `f62bd8e`.
Their tracked/ignored contents, frozen capture/reference, authoritative ledger,
private configuration, runtime bundle and container identities are checked against
protected before/after inventories in
`/home/ubuntu/qh-finalization-evidence/single-checkout-20261016/`.
No private inventory or credential is committed. Historical PR #1 is untouched.

## Proposed integration order — one review/merge at a time

This is a procedure requiring the appropriate later approvals, not authorization
to push other branches, merge, change Jira, remove directories or start QH-33.

1. **PR #6:** review the published single-checkout delta and exact-head CI. After
   explicit merge approval, preserve ancestry with a merge commit, verify GitHub's
   result, then safely switch the clean primary checkout to `main` and fast-forward
   to fetched `origin/main`. Confirm `b76b567` and its successor are reachable.
   Record review/merge and the non-ticket Jira mapping; do not call CI success DONE.
2. **PR #5:** after closing #6, reconcile its description with its actual head.
   The local head `5a604f6` contains `1ee72f1`, `a167aaf`, `5a604f6` beyond remote
   `2acf84e`; these exact commits are already on remote #7. Do not cherry-pick,
   regenerate captures or discard them as duplicates. Before editing #5, inspect
   the whole legacy directory (including ignored files), sessions and mounts; make
   verified durable copies of important evidence/private configuration. Release
   the clean legacy checkout by ordinary detach at retained `5a604f6`, then select
   its existing branch in `/home/ubuntu/qh`; compare HEAD/tree and original files.
   Read the integrated policy with `git show origin/main:AGENTS.md` before selecting
   an older branch, and incorporate updated `main` into that branch by a reviewed
   ordinary merge if needed to retain the new instructions. No force/rebase.
   After authorization, publish the preserved baseline commits on #5, resolve only
   actual documentation conflicts, rerun relevant/hosted checks and review that
   exact head. Integrate #5 only after review/merge approval; then synchronize main.
   QH-8's completed offline acceptance stays closed; the separate experiment's
   mixed semantic findings and provisional reference must remain explicit.
3. **PR #7 / QH-32:** only after #5 integration, retarget the existing #7 to `main`
   and verify its diff contains the intended follow-up, not duplicated baseline.
   Migrate its legacy branch to the primary checkout using the same saved-state,
   evidence/process/mount and ordinary-detach checks; retain `f62bd8e` and every
   original artifact. Incorporate integrated main if required; no history rewrite.
   Resolve real README/changelog conflicts without changing frozen evidence.
   Link the existing QH-32 instead of implementing it again; confirm each criterion
   and CI on the final head, obtain review/merge approval, then update Jira only
   when authorized. No QH-33 work starts automatically; its independently reviewed
   semantic reference is still a prerequisite, not supplied by locator tests.

Keep each legacy directory until its actual integration or a verified safe
migration. Subsequent removal requires the separate legacy retirement checks in
AGENTS: all commits preserved, ignored files/evidence recoverable, no sessions or
mount/path dependencies, ordinary `git worktree remove` without force. An open,
unmigrated worktree must stay. Do not delete the primary checkout or historical
PR #1 refs. Shared README/changelog paths may need normal conflict resolution;
no conflict is assumed or bypassed in advance.

## Verification scope

Legacy-bootstrap tests exercise old API/CLI entry points, old creation flags and
help in synthetic checkout directories, checking unchanged HEAD/ref sentinels,
local files and absence of created checkout paths. No Git executable is required
by the disabled entry point or these focused regressions. A network-disabled Docker run plus lint,
link/whitespace checks and configured-secret guard provide the focused local gate.
Hosted quality/OIDC/native checks apply only to their exact tested head; record
actual results in PR #6. No persistent database tests, paid inference, application
replacement, cleanup or new product functionality is part of this workflow change.

Focused local execution passed: three legacy-bootstrap tests in a network-disabled,
readonly Docker container (temporary test directory only), Ruff lint/format,
actionlint, Git whitespace, 30 local file/anchor links, exact DONE wording and
verbatim preservation of the historical audit. Before/after inventories confirmed
all existing container IDs/images/start times/mounts/networks, private configuration,
runtime/realm/ledger and complete #5/#7 checkout contents/HEADs unchanged. No test
credentials or persistent database connection were used. The initial Git-dependent
test fixture was replaced with file/ref sentinels because the backend image lacks
Git and the disabled bootstrap must no longer need it. Hosted results are recorded
in the PR after publication, never inferred from earlier green heads.

## Historical worktree policy execution — superseded, retained evidence

The following is the earlier dated audit verbatim. Its sibling-worktree bootstrap,
primary-on-main assumptions and test results describe that earlier policy only;
current development must follow the single-checkout sections above and AGENTS.

## Actual directory audit — 2026-10-16

Recursive `.git` marker discovery under `/home/ubuntu/`, registered-worktree
porcelain inventory and GitHub PR reads found only the primary QH repository there
before maintenance; the two QH-8 worktrees were under `/tmp`. The final full scan
also covered hidden directories with no unreadable directories: the separate
`/home/ubuntu/.codex/.tmp/plugins` repository is tool-managed, has its own Git
common directory and is not a QH worktree; it was left untouched. The existing
`qh-worktrees` directory was empty. Runtime and evidence directories are not
worktrees. No extra nested worktrees were discovered.

| Directory | Classification | Action / result |
| --- | --- | --- |
| `/home/ubuntu/qh` | Primary repository | Retained on `main`, `f1e0ae6`, clean; private `.env` and readonly realm import preserved |
| `/home/ubuntu/qh-runtime` | Runtime/deployment | Left intact; release bundle, symlink and file hashes/modes unchanged |
| `/home/ubuntu/qh-worktrees` | Other: empty former worktree parent | Left intact; no registered or nested checkout, no forced directory cleanup |
| `/home/ubuntu/qh-cutover-evidence` | Evidence archive | Left intact |
| `/home/ubuntu/qh-finalization-evidence` | Evidence archive | Existing archives retained; new protected maintenance/evidence subdirectory added |
| `/home/ubuntu/qh8-mistral-evaluation` | Active development worktree, PR #5 OPEN | Moved from `/tmp` with `git worktree move`; kept all tracked/ignored contents and local commits; no push |
| `/home/ubuntu/qh8-understanding-extractor` | Worktree of merged PR #4 | Moved from `/tmp`, verified, then safely removed; local branch deleted with `-d` |
| `/home/ubuntu/.codex/.tmp/plugins` | Other: separate tool-managed Git repository | Left intact; unrelated to QH common Git directory or PR cleanup |
| `/home/ubuntu/qh-worktree-lifecycle-policy` | Active policy task worktree | Created from `origin/main`, branch `docs/worktree-lifecycle-policy`; dedicated review PR |

### Relocation and removal evidence

Before mutation, both destinations were absent. Full file inventories included
tracked, untracked and ignored paths, symlink targets, SHA-256, modes, ownership and
Git branch/HEAD/status/diff. After each move, these compared equal (excluding only
the `.git` pointer whose location Git necessarily updates). HEADs were unchanged:

- Mistral: `a167aaf332a40a8555233792bab285355e34e074`,
  `feat/QH-8-mistral-evaluation`, no tracked/untracked changes, one ignored bytecode
  file retained. The report and all four committed captures were present.
- Understanding: `29d57fe5cf3abc2f9e661eb29b1f7a6097d3d080`,
  `feat/QH-8-understanding-extractor`, no tracked/untracked/ignored changes.

Process inspection covered cwd, command path references and open file descriptors
across accessible `/proc`, with no unreadable processes in the preflight. Running
and stopped Docker configurations had no mounts dependent on either checkout.
No matching systemd or inspected local configuration path references were found;
tracked source/configuration files contained neither old worktree absolute path.
These are local observations, not a claim to observe every remote editor session.
Processes/open files/container mounts were rechecked immediately before removal.

[PR #4](https://github.com/bl000m/qh/pull/4) is actually merged, with result
`f1e0ae6f46eac54477c3bacf263a002fee97dea0` on freshly fetched `origin/main`.
`git merge-base --is-ancestor 29d57fe origin/main` succeeded. Its source commit is
thus reachable without squash/rebase ambiguity. Important verification artifacts
were persisted, and a private branch bundle was created and `git bundle verify`
succeeded before removal. `git worktree remove` succeeded without force; prune
preview had no extra candidate; prune and `git branch -d` succeeded. Remote branches
and the preserved historical Graphiti ancestry were not deleted or rewritten.
PR #5 is OPEN, so its worktree and all unpublished commits are retained.

### Persistent evidence and path dependencies

Private audit storage:
`/home/ubuntu/qh-finalization-evidence/worktree-lifecycle-20261016/` (protected).
It holds before/after inventories, relocation/removal proofs, branch bundle and:

- `mistral-evidence/`: original private experiment artifacts, including the one
  authoritative `live-initial/ledger.json`. Verified inventory equal after moving.
- `understanding-verification/`: original QH-8 verification files, verified equal.
- `historical-qh8-helpers/`: verbatim copies of historical helper/report files; not
  active runtime scripts and not permission to repeat paid calls/deployments.

The old `/tmp/qh8-mistral-evidence` and `/tmp/qh8-verification` are compatibility
symlinks to these persistent directories. They do not create independent ledgers.
The old worktree paths have no compatibility symlinks and are no longer registered.
Frozen captures/manifests/historical commands retain their original path strings.
Mistral's active report documents the persistent paths in local documentation-only
commit `5a604f6`; no policy change was put in experimental PR #5 and it was not pushed.

### Verification and review boundary

- PASS: Git baseline/primary `main`, live GitHub merged/open state and main protection.
- PASS: exact worktree contents/modes/ownership and Git-state comparisons after moves;
  report/capture presence, archive equality and verified bundle before removal.
- PASS: final Git inventory/status, no registered worktree in `/tmp`, no extra nested
  checkout under audited directories; only merged PR #4 removed without force.
- PASS: unchanged production container identities/images/start times/mounts/networks,
  frozen runtime tree, root private `.env` and readonly IdP import hashes/modes.
  No database connection, migration, provider call or deployment was performed.
- PASS: six hermetic Git bootstrap tests in disposable synthetic repositories:
  `python3 -m unittest discover -s tests -p test_worktree_bootstrap.py -v`.
  These are tooling fixtures, never the QH development worktrees or data.
- PASS: bootstrap refuses the real primary checkout before policy integration;
  no branch/worktree is created by this expected rejection.
- PASS: Ruff, whitespace, local file links, sealed Mistral manifest hashes and
  staged configured-secret guard. No application test/build rerun is claimed.
- NOT TESTED: policy bootstrap on the future merged primary checkout; no automatic
  merge or primary fast-forward was performed. Review/merge and a safe subsequent
  primary `git pull --ff-only` remain manual, subject to current main instructions.

The policy task's exact commit/PR and final worktree HEADs are reported in its PR
and delivery message to avoid self-referential commit IDs in this record.
