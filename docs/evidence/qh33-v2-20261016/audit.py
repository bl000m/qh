"""Offline identity/reproduction audit; no human validation or QH writes."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
manifest = json.loads((HERE / "manifest.json").read_text())
for name, expected in manifest["files"].items():
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit("Fingerprint mismatch: " + name)
with tempfile.TemporaryDirectory() as temp:
    out = Path(temp) / "recomputed"
    subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_qh33_v2.py"), "--out", str(out)], check=True)
    for name in manifest["generated_files"]:
        if (out / name).read_bytes() != (HERE / name).read_bytes():
            raise SystemExit("Reproduction mismatch: " + name)
    metrics = json.loads((out / "metrics.json").read_text())
    review = json.loads((out / "review-template.json").read_text())
    assert metrics["human_review"]["metrics"] is None
    assert metrics["human_review"]["accepted_units"] == 0
    assert metrics["inventory"]["review_units"] == 74
    assert metrics["inventory"]["active_source_propositions"] == 44
    assert review["reviewer"] is None and review["reviewed_at"] is None
    assert review["independent_of_assistant_author"] is None
    assert review["reference_completeness_checked"] is False
    assert review["candidate_payloads_checked"] is False
    assert all(row["decision"] == "pending" and all(v is None for v in row["ratings"].values()) for row in review["units"])
subprocess.run([sys.executable, str(ROOT / "docs/evidence/qh33-semantic-20261016/audit.py")], check=True)
print("PASS: sealed v1 plus reproducible v2; 74 IDs/44 active propositions; personal attestations absent and metrics null")
