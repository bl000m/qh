"""Extend the existing boundary guard without editing QH-33's sealed test file."""

from pathlib import Path
import subprocess
import sys

import pytest

from tests.test_architecture import API_ROOT, boundary_violations


@pytest.mark.parametrize('path', sorted((API_ROOT / 'app/context').glob('*.py')))
def test_context_application_dependencies_point_inward(path: Path):
    assert not boundary_violations(path.read_text(), 'app.context',
                                  {'app.core', 'app.policy', 'app.context'})


def test_management_imports_without_framework_or_database_packages():
    source = ('import sys; sys.path.insert(0, sys.argv[1]); '
              'from app.context.service import ManagedContextService; '
              'from app.core.spaces import ContextSpaceRepository')
    result = subprocess.run([sys.executable, '-I', '-S', '-c', source, str(API_ROOT)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
