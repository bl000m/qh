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


def test_oidc_route_allowlist_rejects_unknown_endpoints_and_methods():
    from copy import deepcopy
    import importlib.util
    from app.main import create_app
    path = API_ROOT.parents[1]/'tests/oidc/test_keycloak.py'
    spec = importlib.util.spec_from_file_location('qh50_oidc_contract',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    document = create_app().openapi()
    module.check_business_paths(document,spaces_required=True)
    module.check_business_paths(document,spaces_required=False)
    for mutate in ('path','method','development_method'):
        changed = deepcopy(document)
        if mutate=='path': changed['paths']['/unauthorized-feature']={'post':{}}
        elif mutate=='method': changed['paths']['/environment/spaces/{context_id}/open']['get']={}
        else: changed['paths']['/context-spaces/{context_id}/ai/messages']['get']={}
        with pytest.raises(AssertionError):
            module.check_business_paths(changed,spaces_required=True)
        with pytest.raises(AssertionError):
            module.check_business_paths(changed,spaces_required=False)
    module.check_business_paths({'paths':{'/health':{'get':{}},'/auth/me':{'get':{}}}},spaces_required=False)
