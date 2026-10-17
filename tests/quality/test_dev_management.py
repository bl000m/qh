"""Runtime command regressions: app-only scope and infrastructure drift refusal."""
from copy import deepcopy
from pathlib import Path
import runpy

import pytest

DEV = runpy.run_path(str(Path('/workspace/scripts/manage_qh_dev.py')))


def fixture():
    services = {}
    containers = []
    for name in ('postgres', 'neo4j', 'keycloak', 'mcp', 'backend', 'frontend'):
        services[name] = {'image': name, 'environment': {}, 'networks': {'app': {}}, 'volumes': []}
        containers.append({'Config': {'Image': name, 'Env': [], 'Labels': {
            'com.docker.compose.project': 'qh', 'com.docker.compose.service': name}},
            'State': {'Running': True}, 'Mounts': [], 'NetworkSettings': {'Networks': {'qh_app': {}}}})
    env = {key: 'unchanged' for key in ('POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER',
                                      'POSTGRES_PASSWORD', 'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD',
                                      'OIDC_ISSUER', 'OIDC_JWKS_URL', 'OIDC_AUDIENCE')}
    env.update(QH_NATIVE_CONTEXT_ENABLED='true', QH_NATIVE_GRAPH_NAMESPACE='qh-native')
    services['backend']['environment'] = env
    containers[4]['Config']['Env'] = [f'{k}={v}' for k, v in env.items()]
    return ({'name': 'qh', 'services': services, 'volumes': {}, 'networks': {'app': {'name': 'qh_app'}}},
            containers, {'images': [{'component': 'api', 'tag': 'backend'}, {'component': 'web', 'tag': 'frontend'}]})


def test_app_mutations_cannot_target_dependencies_or_build():
    command = DEV['command']
    for action in ('up', 'restart', 'stop'):
        args = command(['docker', 'compose'], action)
        assert args[-2:] == ['frontend', 'backend']
        assert not any(x in args for x in ('mcp', 'postgres', 'neo4j', 'keycloak', '--build', 'down', '-v'))
    assert '--no-deps' in command([], 'up') and '--no-build' in command([], 'up')
    assert '--no-deps' in command([], 'restart')
    with pytest.raises(ValueError):
        command([], 'down')


def test_guard_accepts_unchanged_runtime():
    DEV['validate'](*fixture())


@pytest.mark.parametrize('change', ['password', 'image', 'network', 'mount', 'public_port', 'database_port',
                                    'foreign_source', 'app_image', 'namespace', 'native_disabled', 'missing_infra',
                                    'app_port', 'app_network'])
def test_guard_refuses_resource_and_configuration_drift(change):
    config, containers, manifest = deepcopy(fixture())
    services = config['services']
    if change == 'password':
        services['postgres']['environment']['POSTGRES_PASSWORD'] = 'different'
    elif change == 'image':
        services['postgres']['image'] = 'new-postgres'
    elif change == 'network':
        containers[0]['NetworkSettings']['Networks'] = {'preview_data': {}}
    elif change == 'mount':
        containers[0]['Mounts'] = [{'Destination': '/data', 'Type': 'volume', 'Name': 'new', 'RW': True}]
    elif change == 'public_port':
        services['frontend']['ports'] = [{'host_ip': '0.0.0.0', 'published': '5173'}]
    elif change == 'database_port':
        services['postgres']['ports'] = [{'host_ip': '127.0.0.1', 'published': '5432'}]
    elif change == 'foreign_source':
        services['frontend']['volumes'] = [{'type': 'bind', 'source': '/tmp/preview', 'target': '/workspace'}]
    elif change == 'app_image':
        services['frontend']['image'] = 'untested'
    elif change == 'namespace':
        services['backend']['environment']['QH_NATIVE_GRAPH_NAMESPACE'] = 'preview'
    elif change == 'native_disabled':
        services['backend']['environment']['QH_NATIVE_CONTEXT_ENABLED'] = 'false'
    elif change == 'missing_infra':
        containers[0]['State']['Running'] = False
    elif change == 'app_port':
        services['frontend']['ports'] = [{'host_ip': '127.0.0.1', 'published': '5174', 'target': 5173}]
    elif change == 'app_network':
        containers[5]['NetworkSettings']['Networks'] = {'preview_app': {}}
    with pytest.raises(ValueError):
        DEV['validate'](config, containers, manifest)
