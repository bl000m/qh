"""Hermetic Git checks: no QH checkout, network, Docker or remote writes."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/start_task_worktree.py"
spec = importlib.util.spec_from_file_location("worktree_bootstrap", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WorktreeBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="qh-worktree-test-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "qh"
        self.repo.mkdir()
        self.run_git("init", "-b", "main")
        (self.repo / "AGENTS.md").write_text(
            module.SECTION + "\nSynthetic test policy.\n"
        )
        self.run_git("add", "AGENTS.md")
        self.run_git(
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "Synthetic policy",
        )
        self.before = self.run_git("rev-parse", "HEAD")

    def run_git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], text=True, stderr=subprocess.DEVNULL
        ).strip()

    def plan(self, branch="feat/QH-9-context-graph", **kwargs):
        return module.bootstrap(self.repo, branch, emit=lambda value: None, **kwargs)

    def test_plan_is_read_only_and_create_reports_sibling_state(self):
        plan = self.plan()
        target = self.repo.parent / "qh9-context-graph"
        self.assertEqual(plan["destination"], str(target))
        self.assertFalse(target.exists())
        self.assertEqual(self.run_git("branch", "--list"), "* main")
        created = self.plan(create=True, policy_sha256=plan["policy_sha256"])
        self.assertEqual(created["head"], self.before)
        self.assertIn("feat/QH-9-context-graph", created["status"])
        self.assertEqual(self.run_git("status", "--porcelain"), "")
        self.assertEqual(self.run_git("branch", "--show-current"), "main")

    def test_rejects_stale_or_unreviewed_policy_before_mutation(self):
        for digest in (None, "incorrect"):
            with self.assertRaisesRegex(ValueError, "read-only plan"):
                self.plan(create=True, policy_sha256=digest)
        self.assertEqual(self.run_git("branch", "--list"), "* main")

    def test_rejects_attached_branch_without_recreating_it(self):
        plan = self.plan()
        self.plan(create=True, policy_sha256=plan["policy_sha256"])
        with self.assertRaisesRegex(ValueError, "already has a worktree"):
            self.plan(name="qh9-another-name")

    def test_reuses_existing_unattached_branch_without_recreating(self):
        self.run_git("branch", "feat/QH-10-existing")
        plan = self.plan("feat/QH-10-existing")
        self.assertEqual(plan["base"], "existing branch")
        created = self.plan(
            "feat/QH-10-existing", create=True, policy_sha256=plan["policy_sha256"]
        )
        self.assertEqual(created["head"], self.before)

    def test_rejects_occupied_symlink_and_paths_outside_sibling(self):
        (self.repo.parent / "qh9-context-graph").symlink_to("missing-target")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.plan()
        for name in ("/tmp/qh-new", "../qh-new", "nested/qh-new", "other"):
            with self.assertRaisesRegex(ValueError, "sibling directory"):
                self.plan(name=name)

    def test_requires_integrated_primary_instructions_and_main(self):
        (self.repo / "AGENTS.md").write_text("No lifecycle policy yet.\n")
        with self.assertRaisesRegex(ValueError, "not integrated"):
            self.plan()
        (self.repo / "AGENTS.md").write_text(module.SECTION + "\nUncommitted change.\n")
        with self.assertRaisesRegex(ValueError, "differs from committed main"):
            self.plan()
        self.run_git("checkout", "-b", "other")
        with self.assertRaisesRegex(ValueError, "must be on main"):
            self.plan()


if __name__ == "__main__":
    unittest.main()
