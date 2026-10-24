"""Historical identities stay sealed while the current Engine evolves."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.audit_qh33_history import ROOT, SNAPSHOT, SNAPSHOTS, EXTRACTOR, materialize


class HistoricalAuditTests(unittest.TestCase):
    def test_historical_capsule_preserves_runtime_and_exact_sealed_source(self):
        before = (ROOT / EXTRACTOR).read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            capsule = Path(directory)
            materialize(ROOT, capsule)
            for target, source in SNAPSHOTS.items():
                self.assertEqual((capsule / target).read_bytes(), (ROOT / source).read_bytes())
        self.assertEqual((ROOT / EXTRACTOR).read_bytes(), before)

    def test_modified_frozen_snapshot_or_evidence_rejected(self):
        original = Path.read_bytes
        for relative in (SNAPSHOT, 'docs/evidence/qh33-semantic-20261016/metrics.json'):
            with self.subTest(asset=relative), tempfile.TemporaryDirectory() as directory:
                def changed(path):
                    raw = original(path)
                    return raw + b'\nmodified' if path == (ROOT / relative).resolve() else raw
                with patch.object(Path, 'read_bytes', changed):
                    with self.assertRaisesRegex(ValueError, 'Frozen fingerprint mismatch'):
                        materialize(ROOT, Path(directory))
