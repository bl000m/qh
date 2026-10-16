"""Verify QH-33 frozen lineage and reproducibility, not semantic truth."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
manifest = json.loads((HERE / 'manifest.json').read_text())
for name, expected in manifest['files'].items():
    path = ROOT / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit('Fingerprint mismatch: ' + name)
with tempfile.TemporaryDirectory() as temp:
    out = Path(temp) / 'recomputed'
    subprocess.run([sys.executable, str(ROOT / 'scripts/evaluate_qh33.py'),
                    '--out', str(out), '--prepare-protocol'], check=True)
    for name in ['metrics.json', 'review-template.json', 'review-packet.md',
                 'source-only.md', 'future-protocol.json']:
        actual = (out / name).read_bytes()
        if name.endswith('.md'):
            actual = actual.rstrip() + b'\n'
        if actual != (HERE / name).read_bytes():
            raise SystemExit('Reproduction mismatch: ' + name)
before, after = [json.loads((HERE / name).read_text()) for name in
                 ['before-engine-probes.json', 'after-engine-probes.json']]
for name in ['benchmark_sha256', 'temporal_probes_sha256', 'cases', 'provider_calls']:
    if before[name] != after[name]:
        raise SystemExit('Comparison input/result mismatch: ' + name)
if after['extractor_sha256'] != hashlib.sha256(
        (ROOT / 'apps/api/app/understanding/extractor.py').read_bytes()).hexdigest():
    raise SystemExit('Current extractor identity mismatch')
if before['extractor_sha256'] != manifest['baseline_extractor_sha256']:
    raise SystemExit('Baseline extractor identity mismatch')
if before['provider_calls'] or after['provider_calls']:
    raise SystemExit('Unexpected provider consumption')
print('PASS: artifact hashes/reproduction and comparable probe inputs; no human validation asserted')
