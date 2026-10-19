# QH-45 — RESULT FIRST: scoped live availability

2026-10-19, Europe/Rome. PR #16, branch `feat/QH-45-generative-chat`,
checkout `/home/ubuntu/qh`, baseline `9fdc667`. The owner's attached decision and
subsequent explicit direct confirmation authorize the implementation and controlled
activation below. No merge or Jira DONE is authorized. Earlier 2026-10-18 offline
records remain immutable historical evidence at their pinned commit.

## Decision and boundaries

The usable result is Alice → synthetic Projet pilote → Mistral selection → exact
preview → separate proposed/disclosure consent → question/answer → explicit revoke.
Only `mistral-small-2603`, only the six original proposed revisions, no historical
or other-Space disclosure. The exact internal context hash is pinned privately;
changed data/system context fails closed, with no silent receipt expansion.

Provider authorization lasts a fixed 30 days from activation, without renewal.
Conversation grants remain at most five minutes and never outlive the verified
OIDC token. Same snapshot/scope/model/grant allows follow-up questions without
another administrative manifest gate. New sessions still require in-app consent.
Mock remains the default; no canonical chat persistence or automatic confirmation.

The ledger is created once with purpose QH-45 and explicit historical ledger hashes,
then retained. Default session limits are 3 POST/0.01 USD; cumulative limits are
8 POST/0.20 USD. New sessions, price verification and backend restarts never reset
spend. Codex is authorized at most one real POST; all other requests are for owner
manual testing. No API GET, retry or fallback. Unknown usage/pending/errors stop
calls. USD amounts are conservative list-price estimates, not billing invoices.

## Prices and model availability

The fixed official [Mistral Small 4 model page](https://docs.mistral.ai/models/mistral-small-4-0-26-03)
is fetched over HTTPS without key or QH content. Parse explicit input/output USD
per-million records; reject retired/unknown/conflicting/tiered/increased prices,
redirects, oversized pages, HTTP errors or parse failures. Cache a successful check
for less than 24 hours; refresh automatically on subsequent use after expiry.
A failed refresh disables paid disclosure; no stale fallback. No new owner receipt
approval is needed inside the existing 30-day authorization. Lower prices do not
increase limits: cost accounting retains the conservative pinned ceilings.

No API model/quota lookup is performed. The historical QH-13 success identifies the
workspace/key path but does not prove today's quota; the single authorized real
smoke is the concrete billed-workspace/model availability check. If unavailable,
stop without retry and report the exact outcome.

## Narrow activation and rollback

Protected private archive `.local-archive/qh45-live-20261019/` holds original `.env`,
hot-reload override, backend inspect and canonical/configuration inventories.
Private receipt/ledger live under ignored `.local-archive/qh45-runtime/`, mounted
only into the backend at `/run/qh-chat`. Key is injected only into the backend
process environment. No secret enters Git, client bundle, screenshots or logs.

The owner authorizes default-off source plumbing in the existing hot-reload
override, `QH_CHAT_SESSIONS_ENABLED=true` in private configuration, and guarded
`sudo -n make dev-up DEV_SERVICE=backend`. Guard validates original DB/OIDC/native
configuration, images, loopback ports and mounts. Only backend may be recreated;
all non-target container IDs/images/start times/mounts must remain equal. No
PostgreSQL/Neo4j/Keycloak/MCP/frontend lifecycle, migration or canonical write.

Fast revoke: change private `authorization.json` to `owner_authorized=false` (or
remove it); receipt fingerprint checks deny new/existing grants without extending
expiry. Preserve ledger. Normal rollback: set private flag false, then run the
same backend-only guarded up command; validate mock and disabled capability.
Full pre-activation configuration restore uses the protected originals and the
same backend-only operation; never delete/reset the ledger, restore a database,
recreate Keycloak or run generic Compose lifecycle commands.

## Verification and operational result

**MISTRAL AVAILABLE IN THE QH CLIENT: YES**, only Alice / Projet pilote,
while scope, prices, provider availability and remaining budget stay valid.

- Activation receipt: 2026-10-19 04:30:42 UTC (06:30:42 Europe/Rome).
- Fixed expiry: **2026-11-18 04:30:42 UTC / 05:30:42 Europe/Rome**. The daylight-
  saving change explains the different local hour; duration is 30 × 24 hours.
- One actual browser POST completed: provider and QH HTTP 200, Italian overview,
  four exact references from six supplied proposed revisions, canonical warnings.
  Prompt 3,609 / completion 93 tokens; estimated USD **0.00059715**, QH generation
  **2.20 seconds**. Reservation was USD 0.0024. No API GET, retry or extra inference.
- Codex smoke grant explicitly revoked; subsequent preview also revoked without
  generation. Real mode remains enabled for the owner. Remaining at checkpoint:
  **7 cumulative POST / USD 0.19940285**, 3 POST/0.01 USD maximum per new session.
- Every canonical table and all five non-backend containers are unchanged. Backend
  image, ports, networks and pre-existing DB/OIDC/native environment retained;
  only the authorized private mount/settings and backend recreation differ.
- Actual Alice/Bob owned-space capabilities, foreign denial, default mock, two
  consents, exact preview, canonical warnings and revocation **PASS**. Separate
  post-smoke checks made zero generation requests. Historical ledgers/assets/realm
  import unchanged; private API-key bytes unchanged and absent from browser/logs/Git.

[Sealed real response, screenshots, allowance and preservation receipts](evidence/qh45-live-20261019/README.md).

### Try immediately from the owner's Mac

1. Keep the existing SSH forwarding for 5173/8000/8080. Open
   `http://localhost:5173`, sign in as Alice and open **Projet pilote** (or the
   existing `/context-spaces/eb122625-1830-4557-b805-473d3b66132a` URL).
2. Explicitly check “Inclure explicitement les propositions non confirmées”, enter
   the question, then choose **Mistral — consentement requis**.
3. Select “Examiner les données avant envoi”; inspect the six actual revisions,
   sources and supplier messages. Check the separate external-disclosure consent,
   then “Autoriser cette session Mistral”. Preview/consent consume no generation.
4. “Envoyer la question” uses the real provider. Follow-up questions use the same
   grant/snapshot without another consent, subject to the displayed expiry and
   limits. Expand sources/provided context to inspect provenance.
5. “Révoquer la session” ends it. Login token remains 300 seconds from authentication;
   a late consent may leave little time. Reauthenticate and consent anew if expired:
   this never replenishes the seven-request global remainder.

### Quality and POC limits

The actual answer addresses the overview question in Italian but does not explicitly
qualify support as proposed; both deterministic warnings remain mandatory. “Pausa
reversibile da prendere” can sound more committed than the source's possibility.
Citation selection includes Alex's entity/evidence quote rather than the main pilot
item. Exact aliases do not establish ideal citation relevance or entailment. One
success is not general semantic, prompt-injection, quota or 30-day uptime proof.
Unknown costs/provider errors stop further sends; there is no retry/fallback.
Bounded non-ranked retrieval, short OIDC session and memory-only grants remain.

### Acceptance and technical checks

| Current Jira/owner criterion | Classification and result |
| --- | --- |
| Usable Alice/Projet pilote real chat with actual exact preview and separate consents | Implemented and tested — PASS, real browser/client single POST and subsequent zero-inference availability |
| Other owners/Spaces excluded, canonical hydration/graph/snapshot/aliases/warnings | Implemented and tested — PASS, actual Alice/Bob, sealed scope/response plus isolated regressions |
| Fixed 30-day availability distinct from five-minute/token grants and fresh prices | Implemented and tested — PASS, exact receipt, expiry/price failure/revocation/max-duration offline tests; automatic fixed official source, no model API GET |
| Session/global budget, no reset/retry/fallback, ledger/cost | Implemented and tested — PASS, actual single settled ledger attempt, seven remaining, isolated multi-session/concurrency/crash/error guards |
| No canonical writes; preserve data, other containers, historical ledgers and rollback | Implemented and tested — PASS, fourteen-table equality, five-container exact identity/config comparison, backend-only guard and retained private rollback inputs. Actual rollback not executed because activation succeeded |
| Functional/browser/OIDC regressions and final exact-HEAD CI | Targeted 127 PASS, backend-management 16 PASS, TypeScript/build/Ruff PASS; full native/browser/quality/OIDC execution and immutable final run are reported in PR #16's final review summary, separately from local image counts |
| General semantic correctness or future persistence/session redesign | Not demonstrated / out of scope; QH-39/QH-42 and all other tickets not started |
| Owner review, merge and Jira DONE | Not performed; PR #16 remains open, no DONE claim |

No further Codex inference is authorized: its one smoke allowance is consumed.
The remaining owner manual calls remain authorized within the unchanged receipt,
consent, scope, budget and expiry. Future unavailability or format/price drift must
fail closed without silently changing the receipt, extending time or resetting costs.

The sealed prior offline archive's source fingerprints belong to commit `9fdc667`;
run its audit at that revision. The new live archive records later source/operational
lineage rather than changing historical hashes or claiming an earlier disabled
runtime is still the current activation state.
