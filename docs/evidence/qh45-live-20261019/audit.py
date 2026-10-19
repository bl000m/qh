"""Read-only sealed actual-client evidence audit; never activates or infers."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def git_bytes(commit, name):
    return subprocess.check_output(['git', 'show', commit+':'+name], cwd=ROOT)


def main():
    manifest = json.loads((HERE/'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        path = (HERE/name).resolve()
        assert path.is_relative_to(HERE) and path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    for name, digest in manifest['source_hashes'].items():
        assert hashlib.sha256(git_bytes(manifest['implementation_commit'], name)).hexdigest() == digest, name
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    subprocess.run(['git', 'merge-base', '--is-ancestor', manifest['implementation_commit'], 'HEAD'], cwd=ROOT, check=True)
    for prefix in ['docs/evidence/qh8-mistral-20261016',
                   'docs/evidence/qh13-mistral-chat-trial-20261018',
                   'docs/evidence/qh13-mistral-alias-gate-20261018',
                   'docs/evidence/qh45-provider-sessions-20261018',
                   'apps/api/tests/fixtures']:
        assert not subprocess.check_output(['git', 'diff', '9fdc667', '--', prefix], cwd=ROOT), prefix
    r = json.loads((HERE/'result.json').read_text())
    assert r['real_mistral_posts'] == 1 and r['mistral_api_gets'] == 0 and r['canonical_writes'] == 0
    assert r['qh_http'] == r['provider_http'] == 200
    assert r['remaining_calls'] == 7 and r['smoke_grant_revoked'] == 'PASS'
    assert r['mock_default'] and r['scoped_provider_still_enabled'] and not r['merge'] and not r['jira_done']
    assert all(v == 'PASS' for v in r['checks'].values())
    assert r['preservation']['canonical_14_tables'] == r['preservation']['other_five_containers_unchanged'] == 'PASS'
    answer = json.loads((HERE/'qh-response.json').read_text())
    rows = {row['revision_id']: row for row in answer['provided_revisions']}
    assert len(rows) == 6 and all(row['validation_state'] == 'proposed' and not row['is_current_confirmed'] for row in rows.values())
    refs = [row['revision_id'] for row in answer['references']]
    assert len(refs) == len(set(refs)) == 4 and set(refs) <= rows.keys()
    availability = json.loads((HERE/'availability.json').read_text())
    assert availability['new_paid_requests'] == 0 and all(v == 'PASS' for v in availability['checks'].values())
    print('PASS: one actual client inference, exact canonical scope, revoked smoke, seven remaining, immutable history')


if __name__ == '__main__':
    main()
