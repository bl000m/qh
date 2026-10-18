"""Verify immutable historical evidence and the later owner-approved CSS delta."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = 'b1d721a642a815d82493c7d1cb5ebe2608a91ebd'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    old = HERE.parent / 'qh43-keycloak-live-20261018'
    for name, digest in json.loads((old / 'manifest.json').read_text())['files'].items():
        assert sha((old / name).read_bytes()) == digest, name
    result = json.loads((old / 'results.json').read_text())
    historical = dict(result['source_hashes'])
    historical.update({'infra/keycloak/themes/qh/' + n: h for n, h in result['theme_files'].items()})
    for name, digest in historical.items():
        assert sha(subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=REPO)) == digest
    for name, digest in json.loads((HERE / 'manifest.json').read_text())['files'].items():
        assert sha((HERE / name).read_bytes()) == digest, name
    now = json.loads((HERE / 'results.json').read_text())
    for name, digest in now['source_hashes'].items():
        assert sha((REPO / name).read_bytes()) == digest, name
    assert now['actual_vps'] and len(now['checks']) == 2
    assert all(c['welcome_centered'] and c['environment_centered'] and c['login_bubble_full_grid'] and c['actual_login'] == 'PASS' for c in now['checks'])
    assert now['realm_writes'] == now['qh_writes'] == now['paid_calls'] == 0
    print('PASS: historical evidence immutable; actual VPS centering and current CSS lineage')


if __name__ == '__main__':
    main()
