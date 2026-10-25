"""Run sealed QH-33 audits against their historical extractor, never live QH.

Only manifest-listed public evidence is materialized in a temporary audit capsule.
No checkout, Git history rewrite, runtime source replacement or paid call occurs.
Current Engine behavior is covered by the ordinary unit/integration gates.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ('docs/evidence/qh33-semantic-20261016/manifest.json',
             'docs/evidence/qh33-v2-20261016/manifest.json')
EXTRACTOR = 'apps/api/app/understanding/extractor.py'
SNAPSHOT = 'docs/evidence/qh51-20261021/qh33-extractor-20261016.snapshot.txt'
SNAPSHOTS = {
    EXTRACTOR: SNAPSHOT,
    'apps/api/tests/test_architecture.py': 'docs/evidence/qh51-20261021/qh33-architecture-test-20261016.snapshot.txt',
}


def materialize(root, destination):
    expected = {}
    for name in MANIFESTS:
        manifest = json.loads((root / name).read_text())
        for relative, fingerprint in manifest['files'].items():
            if relative in expected and expected[relative] != fingerprint:
                raise ValueError('Inconsistent sealed identity: ' + relative)
            expected[relative] = fingerprint
    for relative, fingerprint in expected.items():
        source = (root / SNAPSHOTS.get(relative, relative)).resolve()
        target = (destination / relative).resolve()
        if not source.is_relative_to(root.resolve()) or not target.is_relative_to(destination.resolve()):
            raise ValueError('Historical asset outside audit capsule')
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != fingerprint:
            raise ValueError('Frozen fingerprint mismatch: ' + relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    # The v2 evaluator reuses the unchanged citation resolver; its generated
    # reports must still reproduce byte for byte under the sealed audit.
    for relative in (*MANIFESTS, 'apps/api/app/understanding/citations.py'):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / relative).read_bytes())


def main():
    with tempfile.TemporaryDirectory(prefix='qh33-history-') as directory:
        capsule = Path(directory)
        materialize(ROOT, capsule)
        subprocess.run([sys.executable, str(capsule / 'docs/evidence/qh33-v2-20261016/audit.py')], check=True)
    print('PASS: sealed QH-33 history reproduced; current Engine tested separately')


if __name__ == '__main__':
    main()
