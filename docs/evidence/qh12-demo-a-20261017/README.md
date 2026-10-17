# QH-12 — isolated Demo A proof, 2026-10-17

Real Chromium/Keycloak → separately packaged Node22 frontend → production FastAPI
→ canonical PostgreSQL 0005/native worker → Neo4j. Fresh test-only containers,
no published ports, application source mounts, real-data write or inference.

- [Observed verification](verified.json), [immutable image IDs](candidate-images.json).
- [Readonly Compose preflight](compose-preflight.json): no activation/realm/schema change.
- [History/source view](qh12-history.png), [relation anchors](qh12-relation.png),
  [real graph outage](qh12-graph-unavailable.png).

Six unchanged QH-8 fixture proposals plus five distinct revision/time/legacy controls
are synthetic, not new Mistral outputs or independent semantic validation. The
confirmed/rejected control actor is a test identity. All original captures, ledger
and QH-33/QH-38 evidence remain untouched. Screenshots contain synthetic post-login
content only; no password/token, trace, HAR or login/session export is published.

The test performs real outage, a protected synthetic pg_dump/new-DB restore with
all-table fingerprints, graph rebuild without an extractor and real browser
re-open of retained IDs. None is a VPS operation or production backup.
[Report and exact reproduction](../../qh-12-context-understanding.md).
