"""Plan/create a QH task worktree after reviewing committed primary instructions.

No network, publication, cleanup, runtime changes or provider calls. Use the primary
checkout's copy after the lifecycle policy has been integrated into main.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

PRIMARY = Path("/home/ubuntu/qh")
SECTION = "## Git Worktree Lifecycle Policy"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def bootstrap(repo, branch, name=None, *, create=False, policy_sha256=None, emit=print):
    repo = Path(repo).resolve()
    # Read instructions before any branch/worktree mutation, including on create.
    policy = (repo / "AGENTS.md").read_bytes()
    if SECTION.encode() not in policy:
        raise ValueError("Lifecycle policy is not integrated in the primary checkout")
    if git(repo, "branch", "--show-current") != "main":
        raise ValueError(
            "Primary checkout must be on main; do not switch it automatically"
        )
    committed = subprocess.check_output(
        ["git", "-C", str(repo), "show", "HEAD:AGENTS.md"]
    )
    if committed != policy:
        raise ValueError("Primary AGENTS.md differs from committed main; review first")
    digest = hashlib.sha256(policy).hexdigest()
    emit(policy.decode())
    if create and policy_sha256 != digest:
        raise ValueError(
            "Run the read-only plan, review instructions and supply its policy SHA-256"
        )
    git(repo, "check-ref-format", "--branch", branch)
    fields = git(repo, "worktree", "list", "--porcelain", "-z").split("\0")
    if "branch refs/heads/" + branch in fields:
        raise ValueError(
            "Branch already has a worktree; inspect its session before reuse"
        )
    if name is None:
        name = re.sub(r"^QH-", "qh", branch.rsplit("/", 1)[-1], flags=re.I).lower()
        if not name.startswith("qh"):
            name = "qh-" + name
    if not re.fullmatch(r"qh[a-z0-9._-]+", name):
        raise ValueError(
            "Use a qh-prefixed sibling directory name without path separators"
        )
    destination = repo.parent / name
    if os.path.lexists(destination):
        raise ValueError("Destination already exists, including possible symlink")
    exists = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "show-ref",
            "--verify",
            "--quiet",
            "refs/heads/" + branch,
        ],
        check=False,
    )
    if exists.returncode not in (0, 1):
        raise ValueError("Could not inspect existing branch")
    args = ["worktree", "add"]
    if exists.returncode == 1:
        args += ["-b", branch, str(destination), "main"]
    else:
        args += [str(destination), branch]
    result = dict(
        mode="create" if create else "plan",
        primary=str(repo),
        branch=branch,
        destination=str(destination),
        policy_sha256=digest,
        base="main" if exists.returncode == 1 else "existing branch",
        command=["git", "-C", str(repo), *args],
    )
    emit(json.dumps(result, indent=2))
    if create:
        subprocess.run(["git", "-C", str(repo), *args], check=True)
        result.update(
            head=git(destination, "rev-parse", "HEAD"),
            status=git(destination, "status", "--short", "--branch"),
        )
        emit(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("branch")
    parser.add_argument("--name")
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--policy-sha256")
    args = parser.parse_args()
    try:
        bootstrap(
            PRIMARY,
            args.branch,
            args.name,
            create=args.create,
            policy_sha256=args.policy_sha256,
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Worktree bootstrap stopped: {exc}\n")


if __name__ == "__main__":
    main()
