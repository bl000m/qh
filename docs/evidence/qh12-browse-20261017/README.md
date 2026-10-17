# QH-12 browse-first isolated evidence — 2026-10-17

Exact executable/test source: `799c64ce5b615d42f6119c6d187b1f26d96f7237`,
built from Git archive, with no credentials or host-source mounts in the tests.
Images and OCI revisions: [test-images.json](test-images.json).

[Browser result](browser-verified.json) records real Chromium/Keycloak/SQL/Neo4j,
29 browser/contract checks, the existing real OIDC regression, real isolated graph
outage and a separate restored-ID browser replay. PostgreSQL/graph restoration
compares all SQL tables and canonical identities without another extraction.
Screenshots show actual synthetic canonical history and relation detail, not
illustrative data or independent semantic validation. Prior 24-browser/503-native
and Mistral archives remain untouched; counts from different checkpoints overlap.

The isolated fixture preserves the six original QH-8 proposals and eleven total
main-Space controls, then adds separate empty, proposed-only and historical-only
Spaces for this navigation increment. These are synthetic test-only actors and
states, not owner attestations. The live Alice Spaces remain empty; no fixture
was imported into persistent QH and no inference or migration was performed.

Reproduce the browser run from the single checkout with the three exact images:

```sh
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh12-browse-api:799c64ce5b615d42f6119c6d187b1f26d96f7237 \
  --browser-image qh12-browse-browser:799c64ce5b615d42f6119c6d187b1f26d96f7237 \
  --frontend-image qh12-browse-web:799c64ce5b615d42f6119c6d187b1f26d96f7237 \
  --understanding --output /tmp/qh12-browse-new-run
```

Output must be a new empty directory. The reused harness owns and normally removes
only its labelled test containers/network. No persistent QH target, .env, volume,
public port, paid provider, approval/confirmation or deployment command is used.
The real VPS read-only empty-state smoke is reported separately, with private
runtime inventory/credentials kept outside Git. See the [QH-12 acceptance report](../../qh-12-context-understanding.md)
and [ADR 0005](../../adr/0005-browse-first-context-understanding.md).
