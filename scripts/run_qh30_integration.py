"""Strict isolated integration entry point: unavailable infrastructure or skips fail."""

import os
from pathlib import Path
import sys

import pytest


class RequireExecuted:
    def __init__(self):
        self.skipped = False

    def pytest_runtest_logreport(self, report):
        self.skipped |= report.skipped

    def pytest_collectreport(self, report):
        self.skipped |= report.skipped

    def pytest_sessionfinish(self, session):
        if self.skipped or session.testscollected == 0:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
            print("FAIL: required integration tests skipped or none collected")


def main():
    expected = {
        "QH30_SQL_TEST": "1", "POSTGRES_HOST": "qh30-sql-test",
        "POSTGRES_DB": "qh30_admin",
        "QH30_TEST_NEO4J_URI": "bolt://qh30-native-neo4j-test:7687",
    }
    if any(os.environ.get(k) != v for k, v in expected.items()):
        raise SystemExit("FAIL: explicit dedicated integration configuration required")
    if not os.environ.get("POSTGRES_PASSWORD") or not os.environ.get("QH30_TEST_NEO4J_PASSWORD"):
        raise SystemExit("FAIL: dedicated credentials required")
    root = Path(__file__).resolve().parents[1] / "apps/api"
    os.chdir(root)
    sys.path.insert(0, str(root))
    return pytest.main([
        "-q", "-x", "--tb=short", "-p", "no:cacheprovider",
        "-o", "faulthandler_timeout=60",
        "tests/test_understanding.py", "tests/test_understanding_pipeline.py",
        "tests/test_native_semantics_sql.py", "tests/test_generic_semantics.py",
        "tests/test_projection_outbox.py",
        "tests/test_canonical_graph_pipeline.py", "tests/test_native_runtime.py",
        "tests/test_native_context.py", "tests/test_architecture.py",
        "tests/test_contracts.py", "tests/test_identity_migration.py",
        "tests/test_oidc_security.py", "tests/test_owner_policy.py",
    ], plugins=[RequireExecuted()])


if __name__ == "__main__":
    raise SystemExit(main())
