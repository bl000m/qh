"""Extend the sealed QH-33 boundary guard without changing its historical bytes."""
from pathlib import Path

import pytest

from tests.test_architecture import API_ROOT, boundary_violations


@pytest.mark.parametrize('module,allowed', [
    ('environment', {'app.core','app.policy','app.environment','app.context'}),
    ('review', {'app.core','app.policy','app.review'}),
])
def test_ux_v2_application_boundaries(module, allowed):
    for path in (API_ROOT/'app'/module).glob('*.py'):
        assert not boundary_violations(path.read_text(),'app.'+module,allowed),str(path)
    assert (Path(API_ROOT)/'app/composition.py').is_file()
