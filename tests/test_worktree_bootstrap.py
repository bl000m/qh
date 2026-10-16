"""Disabled entry points preserve checkout/ref sentinels without requiring Git."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/start_task_worktree.py"
spec = importlib.util.spec_from_file_location("worktree_bootstrap", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DisabledWorktreeBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="qh-bootstrap-test-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "qh"
        self.repo.mkdir()
        # Sentinels cover both clean tracked content and unsaved/private files.
        # The disabled entry point must not even need Git installed.
        (self.repo / ".git/refs/heads").mkdir(parents=True)
        (self.repo / ".git/HEAD").write_text("ref: refs/heads/main\n")
        (self.repo / ".git/refs/heads/main").write_text("a" * 40 + "\n")
        (self.repo / "AGENTS.md").write_text("Synthetic single-checkout policy.\n")
        (self.repo / ".private-sentinel").write_bytes(b"preserve local content\n")
        self.before = self.snapshot()

    def snapshot(self):
        return {
            "files": {
                str(p.relative_to(self.repo.parent)): p.read_bytes()
                for p in self.repo.parent.rglob("*")
                if p.is_file()
            },
            "directories": sorted(
                str(p.relative_to(self.repo.parent))
                for p in self.repo.parent.rglob("*")
                if p.is_dir()
            ),
        }

    def test_legacy_plan_create_and_options_never_mutate(self):
        for args in [
            [],
            ["feat/QH-9-example"],
            ["feat/QH-9-example", "--create", "--policy-sha256", "old-hash"],
            ["feat/QH-9-example", "--name", "qh9-legacy", "--create"],
            ["--unknown-option"],
        ]:
            with self.subTest(args=args):
                result = subprocess.run(
                    ["python3", str(SCRIPT), *args],
                    cwd=self.repo,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("disabled", result.stderr)
                self.assertIn("/home/ubuntu/qh", result.stderr)
                self.assertEqual(self.snapshot(), self.before)

    def test_imported_legacy_api_rejects_without_reading_repository(self):
        for repo in [self.repo, self.repo / "missing"]:
            for create in (False, True):
                with self.subTest(repo=repo, create=create):
                    with self.assertRaisesRegex(ValueError, "disabled"):
                        module.bootstrap(
                            repo,
                            "feat/QH-9-example",
                            create=create,
                            name="qh9-legacy",
                            policy_sha256="old-hash",
                        )
                    self.assertEqual(self.snapshot(), self.before)

    def test_help_explains_disabled_single_checkout_without_mutation(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--help"],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Disabled legacy bootstrap", result.stdout)
        self.assertIn("/home/ubuntu/qh", result.stdout)
        self.assertEqual(self.snapshot(), self.before)


if __name__ == "__main__":
    unittest.main()
