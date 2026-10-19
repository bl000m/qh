# QH-45 — actual private-VPS Mistral client acceptance

2026-10-19, Europe/Rome. This is an **actual** QH browser → Keycloak Code+PKCE →
existing backend → scoped session → Mistral Small 4 response. It is not a mock,
adapter-only invocation or evidence of general semantic accuracy. The owner approved
30-day availability and at most one Codex POST; that one call is now consumed.
No further Codex inference or Mistral API GET was performed.

[Result and remaining allowance](result.json) · [Exact public QH response](qh-response.json) ·
[Subsequent zero-inference Alice/Bob availability checks](availability.json).

| Actual response | Desktop | Mobile |
| --- | --- | --- |
| One authorized generation, then grant revoked | [Screenshot](live-desktop.png) | [Screenshot](live-mobile.png) |
| New unconsented preview, seven cumulative requests remain, then preview revoked | [Screenshot](available-desktop.png) | [Screenshot](available-mobile.png) |

The response screenshots were taken as the answer appeared, before asynchronous
budget-status refresh. The subsequent preview screenshots show settled global
allowance. The ledger/result records the authoritative observed usage and cost;
visual refresh never controls server budget enforcement. Availability screenshots
use Europe/Rome; the initial response capture used the test browser's UTC timezone.

## Observed outcome

Provider and QH HTTP 200, six authorized proposed revisions, four exact declared
canonical references, mandatory proposed-only warnings visible. One POST, 3,609 input
and 93 output tokens, estimated USD 0.00059715; QH generation 2.20 seconds, not an
independent raw provider-latency measurement. Remaining QH-45 envelope: seven POSTs /
USD 0.19940285. Per-session limit remains three POSTs / USD 0.01 and token-bounded
five minutes. No daily/session/price-check reset.

The answer is in Italian and responds to the overview question. It preserves the
possible waiting-time benefit and unanswered measurement question. It does not
state in prose that the support is unconfirmed; deterministic canonical UI warnings
remain mandatory. “Una pausa reversibile da prendere” is less carefully conditional
than “We can take a reversible pause”; retain this as a phrasing limitation rather
than claiming all semantic risks resolved. The model declares an Alex entity revision
instead of the main pilot-decision item for that part of the summary; its exact
source quote includes the pilot choice. Valid identity/source location does not
prove ideal citation selection or entailment. No automatic confirmation follows.

All fourteen canonical tables/rows are unchanged; the three Alice demo Spaces,
closed historical ledgers, realm import/original assets and five non-backend
containers are retained. Only backend was recreated, retaining image, ports,
networks and original DB/OIDC/native environment, adding the private session mount
and five backend-only environment settings. Host `.env` changed only the two chat
flags; key bytes are unchanged. No key/token/password/receipt or private configuration
is included here. Browser receives only demo login credentials, never the API key.

## Integrity and lineage

`manifest.json` seals the public synthetic archive and pins executable source commit
`b07037565e62bceca87c6406f9e50af4382706de`. `audit.py` checks archive hashes, pinned
source bytes and prior fixture/experiment evidence against `9fdc667`; it never calls
a provider or uses credentials. Run `python3 docs/evidence/qh45-live-20261019/audit.py`.
Private activation manifest/authorization and historical-ledger hashes are retained
under ignored protected `.local-archive/qh45-live-20261019/`; the live ledger remains
under `.local-archive/qh45-runtime/` and must evolve, never be restored/reset from
this checkpoint. Its checkpoint hash is lineage, not an assertion that future owner
calls leave it unchanged.

[Activation, rollback, acceptance mapping and limits](../../qh-45-live-activation.md).
Final exact-HEAD quality/browser/native/OIDC CI is linked in PR #16; local image
results and hosted final-tree results are distinct, not combined test totals.
