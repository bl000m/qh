# Task worktrees and lifecycle audit

The mandatory rules live in [AGENTS.md](../AGENTS.md#git-worktree-lifecycle-policy).
This document records the bootstrap procedure and the 2026-10-16 maintenance.
The policy is proposed separately from experimental PR #5. Because `main` is
protected, it becomes the committed primary-checkout policy only after the owner
reviews/merges its dedicated PR and the primary checkout is safely fast-forwarded.
This maintenance does not merge it or update deployed images.

## Bootstrap from the primary checkout

Read `/home/ubuntu/qh/AGENTS.md` and task-specific instructions before creating any
branch/worktree. After the policy PR is integrated and the primary `main` checkout
is updated, use its bootstrap script (Python standard library + existing Git only):

```bash
python3 /home/ubuntu/qh/scripts/start_task_worktree.py feat/QH-9-context-graph
```

The default is a read-only plan: it prints the committed primary instructions,
branch/destination, Git command and policy SHA-256. Read the instructions and
satisfy their task-specific requirements. Then pass the returned digest:

```bash
python3 /home/ubuntu/qh/scripts/start_task_worktree.py feat/QH-9-context-graph \
  --create --policy-sha256 <digest-returned-by-plan>
```

The script re-reads committed primary instructions before mutation. If the policy
has changed, run the plan and review again; do not substitute a digest without
reading the instructions. It refuses unintegrated/modified instructions, primary
checkout off `main`, an attached branch, occupied destination (including dangling
symlinks), invalid Git branch or a non-sibling directory name. Existing unattached
branches are checked out without recreation. It never fetches, switches `main`,
publishes, removes a worktree or touches runtime resources.

An explicit `--name qh9-descriptive-name` can select another direct sibling.
All safety/approval requirements in AGENTS/task instructions still apply; a
successful path preflight is not approval for unspecified product decisions.
For cleanup, perform the mandatory merged-PR/archive/session checks in AGENTS,
then use ordinary `git worktree remove`, reviewed `prune` and safe `branch -d`.
No automatic cleanup hook is installed.

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
