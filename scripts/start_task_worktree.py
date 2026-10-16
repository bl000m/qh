"""Disabled legacy bootstrap: QH develops only in /home/ubuntu/qh.

Read AGENTS.md and docs/worktree-lifecycle.md for the manual single-checkout
preflight. No invocation creates a branch, worktree or directory, switches Git,
accesses the network or changes runtime. Legacy --create is also disabled.
"""

import argparse

DISABLED_REASON = (
    "Worktree bootstrap is disabled. Develop only in /home/ubuntu/qh; "
    "read AGENTS.md and docs/worktree-lifecycle.md before a manual branch switch. "
    "No changes performed."
)


def bootstrap(*_args, **_kwargs):
    """Reject legacy callers before inspecting or changing any checkout."""
    raise ValueError(DISABLED_REASON)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_known_args(argv)
    parser.exit(2, DISABLED_REASON + "\n")


if __name__ == "__main__":
    main()
