# Demo A planning rehearsal — 2026-10-17

[Operational plan](../../qh-13-demo-a-plan.md). This is new planning evidence,
separate from the sealed QH-13 execution archive and QH-8 original captures.
No network, credentials, SQL/Neo4j connection, Alice identity or persistent write.
The script's in-memory repository and allowing policy are simulation stubs;
they cannot establish real ownership, immutable SQL replay or worker correctness.

[rehearse.py](rehearse.py) exercises existing fixture generation, strict validation,
explicit QH-32 resolver derivation, deterministic revision IDs, pure Context Builder
and mock output/reference decoder. [rehearsal.json](rehearsal.json) preserves raw
fixture-file SHA-256, canonical conversation/items hashes and derived fingerprints.
Every UUID is explicitly **simulation-only**, not a persistent target. Created-at
is a fixed 32-character placeholder. Source/context hashes depend on those UUIDs.
There is no new seed command or production code in this artifact.

Reproduce from `/home/ubuntu/qh` with the existing dependency image, no environment
files or connection to a QH network:

```bash
sudo -n docker run --rm --network none --read-only --tmpfs /tmp \
  -e PYTHONPATH=/workspace/apps/api \
  --mount type=bind,src=/home/ubuntu/qh,dst=/workspace,readonly \
  -w /workspace/apps/api --entrypoint python \
  qh12-api:d70626bbe50c070c428b02564d22dec42b3b22b0 \
  /workspace/docs/evidence/qh13-demo-plan-20261017/rehearse.py \
  > /tmp/qh13-demo-rehearsal.json
cmp docs/evidence/qh13-demo-plan-20261017/rehearsal.json /tmp/qh13-demo-rehearsal.json
```

Observed: 6/6 valid proposed revisions per fixture, 18 total; resolver changes zero
output citations; repeated checkpoint yields identical IDs. Each simulated Space
supplies 5/6 records, declares partial coverage and the mock references three.
`chat_omitted_local_ids` identifies the excluded record. Actual ordering and selected
IDs can change with real Space UUIDs/timestamps or longer dialogue; these are byte
bounds, not tokenizer measurements or charges. No new Mistral call or ledger usage.
Source-level Alice/Bob/worker/SQL/Chromium evidence is in the existing
[QH-13 report](../../qh-13-contextual-chat.md); the proposed populated persistent
demo and personal Mac verification remain **NOT TESTED**.

Executed addendum checks: deterministic rehearsal reproduced byte-for-byte;
existing offline `tests/test_understanding.py`, `tests/test_citations.py` and
`tests/test_chat_context.py`: **89 passed**, 0.63 s, network disabled. Ruff on the
rehearsal script passed. Changed Markdown: **104 local links/anchors** and balanced
fences checked; Git whitespace passed. No application/configuration change against
`7279f33`; sealed experiment/evaluation archives and ledgers are unchanged.
Latest-head hosted CI must be checked separately on PR #14; historical measurements
in the original report are not new test executions for this planning addendum.
