"""Guarded management of the existing VPS POC; never manage infrastructure.

Run with Docker permission (e.g. sudo -n make dev-status). No build, migration,
seed, down, volume operation, branch switch or dependency recreation is exposed.
"""
import argparse
from ipaddress import ip_address
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

ROOT = Path('/home/ubuntu/qh')
SERVICES = ('frontend', 'backend')
INFRA = ('postgres', 'neo4j', 'keycloak')


def output(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        # Docker diagnostics can contain interpolated configuration. Fail privately.
        fd, path = tempfile.mkstemp(prefix='qh-dev-error-', suffix='.log')
        with os.fdopen(fd, 'w') as stream:
            stream.write(result.stdout + result.stderr)
        raise RuntimeError('Docker operation failed; protected diagnostics: ' + path)
    return result.stdout


def validate(config, containers, manifest):
    """Fail before app mutation on paths, infrastructure or reviewed image drift."""
    if config.get('name') != 'qh':
        raise ValueError('Expected existing qh project')
    live = {c['Config']['Labels']['com.docker.compose.service']: c for c in containers}
    for name in (*INFRA, 'mcp'):
        c = live[name]
        if c['Config']['Labels']['com.docker.compose.project'] != 'qh' or not c['State']['Running']:
            raise ValueError('Required preserved service unavailable')
    for name in INFRA:
        service = config['services'][name]
        c = live[name]
        env = dict(v.split('=', 1) for v in c['Config']['Env'])
        if any(str(value) != env.get(key) for key, value in service.get('environment', {}).items()):
            raise ValueError('Infrastructure environment drift')
        if service['image'] != c['Config']['Image']:
            raise ValueError('Infrastructure image drift')
        mounts = {(m['Destination'], m.get('Name') if m['Type'] == 'volume' else m['Source'], m['RW']) for m in c['Mounts']}
        expected = {(m['target'], config['volumes'][m['source']]['name'] if m['type'] == 'volume' else m['source'], not m.get('read_only', False)) for m in service.get('volumes', [])}
        if mounts != expected or set(c['NetworkSettings']['Networks']) != {config['networks'][n]['name'] for n in service['networks']}:
            raise ValueError('Infrastructure mounts/networks drift')
    for name, service in config['services'].items():
        if any(p.get('host_ip') != '127.0.0.1' for p in service.get('ports', [])):
            raise ValueError('Non-loopback port refused')
        if name in ('postgres', 'neo4j') and service.get('ports'):
            raise ValueError('Database ports refused')
    pins = {x['component']: x for x in manifest['images']}
    for service, component in [('frontend', 'web'), ('backend', 'api')]:
        if config['services'][service]['image'] != pins[component]['tag']:
            raise ValueError('Unreviewed application image')
        for m in config['services'][service]['volumes']:
            if m['type'] != 'bind' or not Path(m['source']).resolve().is_relative_to(ROOT):
                raise ValueError('Unexpected application source mount')
        ports = {str(p['target']) + '/tcp': [{'HostIp': p['host_ip'], 'HostPort': str(p['published'])}]
                 for p in config['services'][service].get('ports', [])}
        if ports != (live[service].get('HostConfig', {}).get('PortBindings') or {}):
            raise ValueError('Application port drift')
        if set(live[service]['NetworkSettings']['Networks']) != {
                config['networks'][n]['name'] for n in config['services'][service]['networks']}:
            raise ValueError('Application network drift')
    be = config['services']['backend']['environment']
    old = dict(v.split('=', 1) for v in live['backend']['Config']['Env'])
    for key in ('POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
                'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 'OIDC_ISSUER', 'OIDC_JWKS_URL', 'OIDC_AUDIENCE',
                'QH_NATIVE_CONTEXT_ENABLED', 'QH_NATIVE_GRAPH_NAMESPACE'):
        if str(be.get(key)) != old.get(key):
            raise ValueError('Backend database/native/OIDC configuration drift')
    if str(be['QH_NATIVE_CONTEXT_ENABLED']) != 'true' or be['QH_NATIVE_GRAPH_NAMESPACE'] != 'qh-native':
        raise ValueError('Native runtime must retain qh-native')
    if config['services']['frontend'].get('environment',{}).get('VITE_QH_SHARING')=='1':
        frontend=config['services']['frontend']
        address=frontend['networks']['app'].get('ipv4_address')
        actual=live['frontend']['NetworkSettings']['Networks'][config['networks']['app']['name']].get('IPAddress')
        backend=config['services']['backend']
        if (not address or not ip_address(address).is_private or actual and address!=actual or backend['environment'].get('QH_SHARING_ORIGIN')!='https://localhost:5173'
                or backend['command'][-2:]!=['--forwarded-allow-ips',address]
                or 'app.bootstrap:create_sharing_runtime_app' not in backend['command']
                or frontend['environment'].get('QH_WEB_TLS_KEY')!='/run/qh-tls/server.key'):
            raise ValueError('Private HTTPS sharing/proxy binding drift')


def command(compose, action, services=SERVICES):
    if not services or any(name not in SERVICES for name in services):
        raise ValueError('Only frontend/backend may be targeted')
    if action == 'up':
        return compose + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '120', *services]
    if action == 'restart':
        return compose + ['restart', '--no-deps', '--timeout', '40', *services]
    if action == 'stop':
        return compose + ['stop', '--timeout', '40', *services]
    if action == 'status':
        return compose + ['ps', '-a']
    if action == 'logs':
        return compose + ['logs', '--no-color', '--tail', '100', *services]
    raise ValueError('Unsupported operation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('up', 'status', 'logs', 'restart', 'stop'))
    parser.add_argument('--service', choices=SERVICES, help='Target only one existing app; never a dependency')
    args = parser.parse_args()
    services = (args.service,) if args.service else SERVICES
    compose = ['docker', 'compose', '--env-file', str(ROOT / '.env'), '-p', 'qh',
               '-f', str(ROOT / 'infra/docker/docker-compose.yml'),
               '-f', str(ROOT / 'infra/docker/qh-hot-reload.yml')]
    settings=dict(line.split('=',1) for line in (ROOT/'.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
    if settings.get('QH_PRIVATE_SHARING','0') not in ('0','1'):
        raise ValueError('Explicit private sharing flag required')
    if settings.get('QH_PRIVATE_SHARING')=='1':
        compose+=['-f',str(ROOT/'infra/docker/qh-private-sharing.yml')]
    compose+=['--profile','oidc']
    containers = json.loads(output(['docker', 'inspect', *['qh-' + s + '-1' for s in (*SERVICES, *INFRA, 'mcp')]]))
    if args.action in ('up', 'restart'):
        config = json.loads(output(compose + ['config', '--format', 'json']))
        manifest = json.loads((ROOT / 'docs/evidence/qh12-demo-a-20261017/candidate-images.json').read_text())
        # Retain historical evidence; only the explicitly activated backend pin changes.
        backend_pin = json.loads((ROOT / 'infra/docker/qh-backend-image.json').read_text())
        if backend_pin.get('component') != 'api':
            raise ValueError('Explicit backend image pin required')
        manifest['images'] = [backend_pin if pin['component']=='api' else pin for pin in manifest['images']]
        validate(config, containers, manifest)
        for pin in manifest['images']:
            if pin['component'] not in ('api', 'web'):
                continue
            actual = json.loads(output(['docker', 'image', 'inspect', pin['tag']]))[0]
            if actual['Id'] != pin['image_id'] or actual['Config']['Labels'].get('org.opencontainers.image.revision') != pin['oci_revision']:
                raise ValueError('Pinned image ID/revision mismatch')
    if args.action in ('restart', 'stop'):
        for c in containers[:2]:
            known=[str(ROOT/'infra/docker/docker-compose.yml'),str(ROOT/'infra/docker/qh-hot-reload.yml')]
            if c['Config']['Labels'].get('com.docker.compose.project.config_files') not in (','.join(known),','.join([*known,str(ROOT/'infra/docker/qh-private-sharing.yml')])):
                raise ValueError('Refusing operation before verified hot-reload activation')
    result = output(command(compose, args.action, services))
    if args.action == 'restart':
        for _ in range(120):
            apps = json.loads(output(['docker', 'inspect', *['qh-'+s+'-1' for s in services]]))
            if all(c['State'].get('Health', {}).get('Status') == 'healthy' for c in apps):
                break
            time.sleep(1)
        else:
            raise RuntimeError('Applications did not become healthy after restart')
    if args.action in ('up', 'restart', 'stop'):
        after = json.loads(output(['docker', 'inspect', *['qh-' + s + '-1' for s in (*INFRA, 'mcp', *[n for n in SERVICES if n not in services])]]))
        previous = {c['Name']: c for c in containers}
        for current in after:
            old = previous[current['Name']]
            if (current['Id'], current['Image'], current['Mounts'], current['State']['StartedAt']) != (
                    old['Id'], old['Image'], old['Mounts'], old['State']['StartedAt']):
                raise ValueError('Preserved container changed; inspect before any further operation')
    # Protect operational logs; never print raw environment/configuration.
    for c in containers:
        for entry in c['Config']['Env']:
            key, value = entry.split('=', 1)
            if value and any(part in key for part in ('PASSWORD', 'SECRET', 'TOKEN', 'NEO4J_AUTH', 'API_KEY')):
                result = result.replace(value, '[REDACTED]')
    result = re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED]', result)
    result = re.sub(r'([?&](?:code|state)=)[^&\s]+', r'\1[REDACTED]', result)
    print(result, end='')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, KeyError) as exc:
        raise SystemExit(str(exc)) from None
