"""Hermetic browser/OIDC/REST acceptance, no ports, production env or QH volumes.

Creates its own network, tmpfs PostgreSQL and disposable Keycloak. Browser and
Vite share only the test IdP's network namespace, so approved localhost URLs work
without publishing ports or changing the committed realm. Never reads root .env.
"""
import argparse
import json
import os
import re
import shlex
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def sanitized_output(content, values):
    for key, value in values.items():
        if value and ('PASSWORD' in key or key == 'NEO4J_AUTH'):
            content = content.replace(value, '<redacted>')
    content = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '<redacted-token>', content)
    return re.sub(r'([?&#](?:code|state|session_state)=)[^&#\s]+', r'\1<redacted>', content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sudo-docker', action='store_true')
    parser.add_argument('--backend-image', required=True)
    parser.add_argument('--browser-image', required=True)
    parser.add_argument('--frontend-image', help='Serve the exact packaged candidate, with no source mounts')
    parser.add_argument('--understanding', action='store_true', help='QH-12 native retrieval and backup/restore acceptance')
    parser.add_argument('--chat-sessions', action='store_true', help='QH-45 sessions with test-only HTTP-simulated Mistral, never live HTTP')
    parser.add_argument('--qh-login-theme', action='store_true',
                        help='Preview source-only QH theme on this disposable IdP; never alters the VPS realm')
    parser.add_argument('--browser-grep', help='Targeted Playwright recheck; OIDC/outage/restore gates still run')
    parser.add_argument('--focused-browser-only', action='store_true', help='Local focused UI checks only; never a full acceptance verdict')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.focused_browser_only and (not args.browser_grep or os.environ.get('CI')):
        raise SystemExit('Focused mode requires a local explicit filter; CI acceptance cannot use it')
    docker = ['sudo', '-n', 'docker'] if args.sudo_docker else ['docker']
    run_id = ('qh12-browser-' if args.understanding else 'qh11-browser-') + uuid4().hex[:12]
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output.resolve()
    # Refuse mixing prior test artifacts with this run.
    if any(output.iterdir()):
        raise SystemExit('Output must be a new empty test directory')
    resources = []
    network = False

    def run(*command, input=None, capture=True):
        result = subprocess.run([*docker, *command], input=input, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not capture:
            print(sanitized_output((result.stdout or '') + (result.stderr or ''), values), end='', flush=True)
        if result.returncode:
            # Docker/HTTP output could contain secrets or callback URLs.
            diagnostic = sanitized_output(result.stderr or '', values)
            error_path = output / 'docker-error.txt'
            fd = os.open(error_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'w') as stream:
                stream.write(diagnostic)
            raise RuntimeError('Test Docker operation failed: ' + command[0] + '; protected diagnostic retained')
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
            'QH11_BROWSER_TEST': '1', 'QH12_BROWSER_TEST': '1' if args.understanding else '0', 'QH_RUN_OIDC': '1', 'PYTHONPATH': '/workspace/apps/api',
            'QH43_LOGIN_THEME_TEST': '1' if args.qh_login_theme else '0',
            'QH45_SESSION_BROWSER_TEST': '1' if args.chat_sessions else '0',
        }
        if args.understanding:
            values.update(NEO4J_AUTH='neo4j/' + secrets.token_hex(24), NEO4J_URI='bolt://neo4j:7687',
                          NEO4J_USER='neo4j', QH_NATIVE_GRAPH_NAMESPACE=run_id)
            values['NEO4J_PASSWORD'] = values['NEO4J_AUTH'].split('/', 1)[1]
        fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(''.join(key + '=' + value + '\n' for key, value in values.items()))
        graph_env = Path(private) / 'graph.env'
        if args.understanding:
            fd = os.open(graph_env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as stream:
                stream.write('NEO4J_AUTH=' + values['NEO4J_AUTH'] + '\nQH_GRAPH_PASSWORD=' + values['NEO4J_PASSWORD'] + '\n')
        def restricted_env(name, keys):
            path = Path(private) / name
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as stream:
                stream.write(''.join(key + '=' + values[key] + '\n' for key in keys if key in values))
            return path

        pg_env = restricted_env('postgres.env', ['POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD'])
        idp_env = restricted_env('idp.env', ['KC_BOOTSTRAP_ADMIN_USERNAME', 'KC_BOOTSTRAP_ADMIN_PASSWORD',
                                           'KC_HOSTNAME', 'KC_DB', 'FRONTEND_PORT',
                                           'QH_ALICE_PASSWORD', 'QH_BOB_PASSWORD'])
        realm_path = ROOT / 'infra/keycloak/qh-realm.json'
        theme_mounts = []
        if args.qh_login_theme:
            # Copy, never rewrite the readonly persistent realm import. Only the test
            # realm's theme/locale differ; credentials/client/PKCE are intact.
            realm = json.loads(realm_path.read_text())
            realm['loginTheme'] = 'qh'
            realm['internationalizationEnabled'] = True
            realm['supportedLocales'] = ['fr', 'en']
            realm['defaultLocale'] = 'fr'
            realm_path = Path(private) / 'qh-preview-realm.json'
            realm_path.write_text(json.dumps(realm))
            # This is the public fixture with environment placeholders, not resolved
            # credentials. Keycloak's UID differs from the hosted runner's UID.
            realm_path.chmod(0o644)
            theme_mounts = ['--mount', 'type=bind,src=' + str(ROOT / 'infra/keycloak/themes/qh') +
                            ',dst=/opt/keycloak/themes/qh,readonly']
        try:
            run('network', 'create', '--label', 'qh.test.run=' + run_id, run_id)
            network = True
            pg = start('postgres', '--network', run_id, '--network-alias', 'postgres', '--env-file', str(pg_env),
                       '--tmpfs', '/var/lib/postgresql/data:rw', 'postgres:16.8-alpine3.21')
            kc = start('keycloak', '--network', run_id, '--network-alias', 'keycloak', '--env-file', str(idp_env),
                       '--memory', '1g', '--mount', 'type=bind,src=' + str(realm_path) +
                       ',dst=/opt/keycloak/data/import/qh-realm.json,readonly',
                       *theme_mounts,
                       'quay.io/keycloak/keycloak:26.4.7', 'start-dev', '--import-realm')
            wait(['exec', pg, 'pg_isready', '-U', 'qh', '-d', 'qh'], 'Disposable PostgreSQL')
            run('run', '--rm', '-i', '--network', run_id, '--env-file', str(env), '--entrypoint', 'python',
                args.backend_image, '-', input=(ROOT / 'tests/browser/prepare_qh11.py').read_text(), capture=False)
            if args.understanding:
                graph = start('neo4j', '--network', run_id, '--network-alias', 'neo4j', '--env-file', str(graph_env),
                              '--tmpfs', '/data:rw', '--tmpfs', '/logs:rw',
                              '--memory', '2g', '-e', 'NEO4J_server_memory_heap_max__size=256m',
                              '-e', 'NEO4J_server_memory_heap_initial__size=256m',
                              '-e', 'NEO4J_server_memory_pagecache_size=128m', 'neo4j:5.26.5-community')
                # Password stays in the test container environment, never command arguments/logs.
                wait(['exec', graph, 'sh', '-c',
                      'cypher-shell -u neo4j -p "$QH_GRAPH_PASSWORD" "RETURN 1" >/dev/null'], 'Disposable Neo4j')
                prepared = run('run', '--rm', '-i', '--network', run_id, '--env-file', str(env), '--entrypoint', 'python',
                               args.backend_image, '-', input=(ROOT / 'tests/browser/prepare_qh12.py').read_text())
                expected = json.loads(prepared.splitlines()[-1])
                values['QH12_EXPECTED_JSON'] = json.dumps(expected)
                with env.open('a') as stream:
                    stream.write('QH12_EXPECTED_JSON=' + json.dumps(expected) + '\n')
            backend = start('backend', '--network', run_id, '--network-alias', 'backend', '--env-file', str(env),
                            '-e', 'QH_NATIVE_CONTEXT_ENABLED=' + ('true' if args.understanding else 'false'),
                            args.backend_image, 'uvicorn',
                            'tests.browser_session_app:create_app' if args.chat_sessions else 'app.bootstrap:create_runtime_app', '--factory',
                            '--host', '0.0.0.0', '--port', '8000', '--no-access-log')
            for url in ['http://keycloak:8080/realms/qh/.well-known/openid-configuration', 'http://localhost:8000/health']:
                wait(['exec', backend, 'python', '-c',
                      'import urllib.request; urllib.request.urlopen(' + repr(url) + ', timeout=3)'], 'Disposable OIDC/API')
            values['QH_BROWSER_EXTERNAL_SERVER'] = '1' if args.frontend_image else '0'
            browser_env = restricted_env('browser.env', ['QH_ALICE_PASSWORD', 'QH_BOB_PASSWORD',
                                                       'QH12_BROWSER_TEST', 'QH12_EXPECTED_JSON',
                                                       'QH43_LOGIN_THEME_TEST', 'QH45_SESSION_BROWSER_TEST',
                                                       'QH_BROWSER_EXTERNAL_SERVER'])
            with env.open('a') as stream:
                stream.write('QH_BROWSER_EXTERNAL_SERVER=' + ('1' if args.frontend_image else '0') + '\n')
            if args.frontend_image:
                frontend = start('frontend', '--network', 'container:' + kc,
                                 '-e', 'QH_WEB_API_TARGET=http://backend:8000', args.frontend_image)
                wait(['exec', frontend, 'node', '-e',
                      "fetch('http://localhost:5173/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"],
                     'Packaged frontend')
            print('Running real Chromium → Keycloak → production API → disposable PostgreSQL', flush=True)
            browser_command = 'npm run build:web && npm run typecheck && npm run test --workspace apps/web'
            if args.browser_grep:
                browser_command += ' -- --grep ' + shlex.quote(args.browser_grep)
            run('run', '--rm', '--network', 'container:' + kc, '--env-file', str(browser_env),
                '-e', 'QH_WEB_API_TARGET=http://backend:8000', '-e', 'QH_BROWSER_OUTPUT=/results',
                '--mount', 'type=bind,src=' + str(output) + ',dst=/results',
                args.browser_image, 'sh', '-c',
                browser_command, capture=False)
            # Reuse the existing real OIDC/Core/persistence regression, not a duplicate.
            if not args.focused_browser_only:
                run('exec', backend, 'python', '-m', 'pytest', '-q', '/workspace/tests/oidc/test_keycloak.py',
                    '-k', 'test_real_oidc_login_mapping_and_owner_isolation', capture=False)
            if args.understanding and not args.focused_browser_only:
                # Real outage of only this invocation's graph, not a mocked HTTP response.
                run('stop', '--time', '10', graph)
                run('run', '--rm', '--network', 'container:' + kc, '--env-file', str(browser_env),
                    '-e', 'QH12_GRAPH_OUTAGE=1', '-e', 'QH_WEB_API_TARGET=http://backend:8000',
                    '-e', 'QH_BROWSER_OUTPUT=/results/outage',
                    '--mount', 'type=bind,src=' + str(output) + ',dst=/results',
                    args.browser_image, 'npm', 'run', 'test', '--workspace', 'apps/web', capture=False)
                run('stop', '--time', '30', backend)
                code = (ROOT / 'tests/browser/qh12_database.py').read_text()
                before = json.loads(run('run', '--rm', '-i', '--network', run_id, '--env-file', str(env),
                                        '--entrypoint', 'python', args.backend_image, '-', 'snapshot', input=code))
                # Dump/restore into a distinct NEW test DB. No overwrite/downgrade.
                dumped = subprocess.run([*docker, 'exec', pg, 'pg_dump', '-U', 'qh', '-d', 'qh', '-Fc'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
                archive = Path(private) / 'synthetic.dump'
                fd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(dumped)
                subprocess.run([*docker, 'exec', '-i', pg, 'pg_restore', '--list'], input=dumped,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                run('exec', pg, 'createdb', '-U', 'qh', 'qh12_restore')
                subprocess.run([*docker, 'exec', '-i', pg, 'pg_restore', '-U', 'qh', '-d', 'qh12_restore',
                                '--exit-on-error'], input=dumped, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, check=True)
                after = json.loads(run('run', '--rm', '-i', '--network', run_id, '--env-file', str(env),
                                       '-e', 'POSTGRES_DB=qh12_restore', '--entrypoint', 'python',
                                       args.backend_image, '-', 'snapshot', input=code))
                assert after == before, 'Restored table fingerprints differ'
                print('PASS: synthetic pg_dump archive validated/restored; all SQL tables match', flush=True)
                run('start', graph)
                wait(['exec', graph, 'sh', '-c',
                      'cypher-shell -u neo4j -p "$QH_GRAPH_PASSWORD" "RETURN 1" >/dev/null'], 'Restarted test Neo4j')
                run('run', '--rm', '-i', '--network', run_id, '--env-file', str(env),
                    '-e', 'POSTGRES_DB=qh12_restore', '--entrypoint', 'python', args.backend_image, '-',
                    'rebuild', input=code, capture=False)
                run('rm', backend)
                resources.remove(backend)
                backend = start('restored-backend', '--network', run_id, '--network-alias', 'backend',
                                '--env-file', str(env), '-e', 'POSTGRES_DB=qh12_restore',
                                '-e', 'QH_NATIVE_CONTEXT_ENABLED=true', args.backend_image,
                                'uvicorn', 'app.bootstrap:create_runtime_app', '--factory',
                                '--host', '0.0.0.0', '--port', '8000', '--no-access-log')
                wait(['exec', backend, 'python', '-c',
                      "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"],
                     'Restored test API')
                run('run', '--rm', '--network', 'container:' + kc, '--env-file', str(browser_env),
                    '-e', 'QH_WEB_API_TARGET=http://backend:8000', '-e', 'QH_BROWSER_OUTPUT=/results/restored',
                    '--mount', 'type=bind,src=' + str(output) + ',dst=/results', args.browser_image,
                    'npm', 'run', 'test', '--workspace', 'apps/web', '--', '--grep', 'QH-8 rows', capture=False)
            (output / 'verified.json').write_text(json.dumps({
                'ticket': 'QH-12' if args.understanding else 'QH-11', 'browser': 'Chromium', 'oidc': 'Keycloak 26.4.7',
                'api': 'production bootstrap', 'postgres': '16.8 tmpfs test-only',
                'backend_image': run('image', 'inspect', args.backend_image, '--format', '{{.Id}}').strip(),
                'frontend_image': run('image', 'inspect', args.frontend_image, '--format', '{{.Id}}').strip() if args.frontend_image else None,
                'browser_image': run('image', 'inspect', args.browser_image, '--format', '{{.Id}}').strip(),
                'browser_and_contract_checks': 'PASS', 'existing_real_oidc_regression': 'NOT TESTED (focused)' if args.focused_browser_only else 'PASS',
                'native_graph_enabled': args.understanding,
                'qh_login_theme_preview': args.qh_login_theme,
                'qh45_http_simulated_sessions': args.chat_sessions,
                'qh_login_theme_locale': 'fr' if args.qh_login_theme else None,
                'browser_filter': args.browser_grep,
                'real_graph_outage': 'PASS' if args.understanding and not args.focused_browser_only else None,
                'synthetic_backup_restore_rebuild_browser': 'PASS' if args.understanding and not args.focused_browser_only else None, 'published_ports': [], 'live_qh_access': False, 'paid_calls': 0,
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
