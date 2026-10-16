# Offline derived citations — 2026-10-16

These are **derived artifacts**, not new model outputs. Originals remain byte-identical
in [the frozen Mistral capture](../qh8-mistral-20261016/README.md), from local baseline
`5a604f62fd7dfabf77a618e5d40cdee5572da38b`. Nothing in that directory is overwritten.

`before-results.json` and `after-results.json` come from actual original/derived
replay on disposable PostgreSQL/Neo4j with exact code/image `1446a26` and no provider
key or application source mount. `image.json` identifies the immutable image.

Each successful case has `derived-output.json`, a new-key `checkpoint.json`,
`citation-resolution.json` with original/derived hashes and offsets, and `canonical.json`
with the temporary proposed revisions/retrieval results. `source.json` and
`validation.json` record the replay source and outcome. No claim is made that a
corrected locator fixes meaning or independently validates the reference.

The multilingual case has source/validation/rejection diagnostics only, **no derived
output, checkpoint or canonical export**: three relation candidates lack evidence,
so its entire batch stays unpublished with desired/applied versions zero. No valid
sibling is promoted. Temporary databases/namespaces were removed by the harness;
these exports preserve the executed evidence.

`audit.py` independently checks original file hashes, exact unique Unicode matches,
o changes except evidence start/end and a distinct extraction key, derivation
hashes, proposed/unconfirmed revisions, recorded retrieval/denial results and the
complete multilingual rejection. It uses standard library only, no runtime or API:

```bash
python3 docs/evidence/qh8-citation-resolution-20261016/audit.py
```

`metrics.json` is that executed audit output. `manifest.json` hashes the derived
archive and identifies the original evidence tree and source revision. Private
full test/replay logs and temporary replay inputs persist under
`/home/ubuntu/qh-finalization-evidence/qh8-citation-followup-20261016/`.
The original experiment ledger remains elsewhere unchanged; no new budget was
created and no Mistral request occurred. See the [follow-up report](../../qh8-citation-followup.md).
