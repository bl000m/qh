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

Execution results, activation/expiry, remaining allowance, smoke response, exact
CI and preservation verdicts will be filled after the corresponding operations.
No planned check in this section is a claimed PASS.

The sealed prior offline archive's source fingerprints belong to commit `9fdc667`;
run its audit at that revision. The new live archive records later source/operational
lineage rather than changing historical hashes or claiming an earlier disabled
runtime is still the current activation state.
