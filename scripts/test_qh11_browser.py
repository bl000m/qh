"""Hermetic browser/OIDC/REST acceptance, no ports, production env or QH volumes.

Creates its own network, tmpfs PostgreSQL and disposable Keycloak. Browser and
Vite share only the test IdP's network namespace, so approved localhost URLs work
without publishing ports or changing the committed realm. Never reads root .env.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sudo-docker', action='store_true')
    parser.add_argument('--backend-image', required=True)
    parser.add_argument('--browser-image', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    docker = ['sudo', '-n', 'docker'] if args.sudo_docker else ['docker']
    run_id = 'qh11-browser-' + uuid4().hex[:12]
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output.resolve()
    # Refuse mixing prior test artifacts with this run.
    if any(output.iterdir()):
        raise SystemExit('Output must be a new empty test directory')
    resources = []
    network = False

    def run(*command, input=None, capture=True):
        result = subprocess.run([*docker, *command], input=input, text=True,
                                stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE if capture else None)
        if result.returncode:
            # Docker/HTTP output could contain secrets or callback URLs.
            raise RuntimeError('Test Docker operation failed: ' + command[0])
        return result.stdout or ''

    def start(service, *arguments):
        name = run_id + '-' + service
        run('run', '-d', '--name', name, '--label', 'qh.test.run=' + run_id, *arguments)
        resources.append(name)
        return name

    def wait(command, description):
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            result = subprocess.run([*docker, *command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                return
            time.sleep(1)
        raise RuntimeError(description + ' did not become ready')

    with tempfile.TemporaryDirectory(prefix=run_id + '-') as private:
        env = Path(private) / 'test.env'
        values = {
            'POSTGRES_HOST': 'postgres', 'POSTGRES_PORT': '5432', 'POSTGRES_DB': 'qh', 'POSTGRES_USER': 'qh',
            'POSTGRES_PASSWORD': secrets.token_hex(24),
            'QH_ALICE_PASSWORD': secrets.token_hex(20), 'QH_BOB_PASSWORD': secrets.token_hex(20),
            'KC_BOOTSTRAP_ADMIN_USERNAME': 'qh-admin', 'KC_BOOTSTRAP_ADMIN_PASSWORD': secrets.token_hex(24),
            'KC_HOSTNAME': 'http://localhost:8080', 'KC_DB': 'dev-file', 'FRONTEND_PORT': '5173',
            'OIDC_ISSUER': 'http://localhost:8080/realms/qh',
            'OIDC_JWKS_URL': 'http://keycloak:8080/realms/qh/protocol/openid-connect/certs',
            'OIDC_AUDIENCE': 'qh-api', 'QH_NATIVE_CONTEXT_ENABLED': 'false',
            'QH11_BROWSER_TEST': '1', 'QH_RUN_OIDC': '1', 'PYTHONPATH': '/workspace/apps/api',
        }
        fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(''.join(key + '=' + value + '\n' for key, value in values.items()))
        try:
            run('network', 'create', '--label', 'qh.test.run=' + run_id, run_id)
            network = True
            pg = start('postgres', '--network', run_id, '--network-alias', 'postgres', '--env-file', str(env),
                       '--tmpfs', '/var/lib/postgresql/data:rw', 'postgres:16.8-alpine3.21')
            kc = start('keycloak', '--network', run_id, '--network-alias', 'keycloak', '--env-file', str(env),
                       '--memory', '1g', '--mount', 'type=bind,src=' + str(ROOT / 'infra/keycloak/qh-realm.json') +
                       ',dst=/opt/keycloak/data/import/qh-realm.json,readonly',
                       'quay.io/keycloak/keycloak:26.4.7', 'start-dev', '--import-realm')
            wait(['exec', pg, 'pg_isready', '-U', 'qh', '-d', 'qh'], 'Disposable PostgreSQL')
            run('run', '--rm', '-i', '--network', run_id, '--env-file', str(env), '--entrypoint', 'python',
                args.backend_image, '-', input=(ROOT / 'tests/browser/prepare_qh11.py').read_text(), capture=False)
            backend = start('backend', '--network', run_id, '--network-alias', 'backend', '--env-file', str(env),
                            args.backend_image, 'uvicorn', 'app.bootstrap:create_runtime_app', '--factory',
                            '--host', '0.0.0.0', '--port', '8000', '--no-access-log')
            for url in ['http://keycloak:8080/realms/qh/.well-known/openid-configuration', 'http://localhost:8000/health']:
                wait(['exec', backend, 'python', '-c',
                      'import urllib.request; urllib.request.urlopen(' + repr(url) + ', timeout=3)'], 'Disposable OIDC/API')
            print('Running real Chromium → Keycloak → production API → disposable PostgreSQL', flush=True)
            run('run', '--rm', '--network', 'container:' + kc, '--env-file', str(env),
                '-e', 'QH_WEB_API_TARGET=http://backend:8000', '-e', 'QH_BROWSER_OUTPUT=/results',
                '--mount', 'type=bind,src=' + str(output) + ',dst=/results',
                args.browser_image, 'sh', '-c',
                'npm run build:web && npm run typecheck && npm run test --workspace apps/web', capture=False)
            # Reuse the existing real OIDC/Core/persistence regression, not a duplicate.
            run('exec', backend, 'python', '-m', 'pytest', '-q', '/workspace/tests/oidc/test_keycloak.py',
                '-k', 'test_real_oidc_login_mapping_and_owner_isolation', capture=False)
            (output / 'verified.json').write_text(json.dumps({
                'ticket': 'QH-11', 'browser': 'Chromium', 'oidc': 'Keycloak 26.4.7',
                'api': 'production bootstrap', 'postgres': '16.8 tmpfs test-only',
                'backend_image': run('image', 'inspect', args.backend_image, '--format', '{{.Id}}').strip(),
                'browser_image': run('image', 'inspect', args.browser_image, '--format', '{{.Id}}').strip(),
                'browser_and_contract_checks': 'PASS', 'existing_real_oidc_regression': 'PASS',
                'published_ports': [], 'live_qh_access': False, 'paid_calls': 0,
            }, indent=2) + '\n')
        finally:
            for name in reversed(resources):
                # Only containers created successfully by this invocation, never qh-* runtime.
                label = run('inspect', name, '--format', '{{index .Config.Labels "qh.test.run"}}').strip()
                if label != run_id:
                    raise RuntimeError('Test ownership mismatch; resources retained')
                run('stop', '--time', '10', name)
                run('rm', name)
            if network:
                run('network', 'rm', run_id)


if __name__ == '__main__':
    main()
