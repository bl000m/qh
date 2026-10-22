# QH51 — ordinary development AI, owner correction22 October2026

The latest owner correction supersedes the initial Essai IA activation/preview
proposal. Envoyer authorizes the submitted chat request; Proposer avec Mistral
authorizes the selected-source UUM request. No activation, provider checkbox,
economic confirmation, preview approval or Space/conversation grant.

One private development account is pinned by canonical QH user ID and SHA256 of
the verified OIDC issuer/subject. The verifier supplies this identity after RS256,
issuer/audience/scope/role, expiry and database mapping checks. Backend CHAT/owner
policy runs before private reads, immediately before disclosure and after response.
Only the current owned Space is read; confirmed-current by default, proposed opt-in.
No inference at startup/page load, no automatic memory or fact confirmation.

The private receipt has an additive development_account field; its original
purpose, expiry2026-11-18T04:30:42.744367Z and all historical grants remain recorded.
The exact model is mistral-small-2603 at the pinned Mistral chat endpoint. Official
price verification is public and carries neither key nor context. Unknown prices
fail closed. Credential presence, valid receipt, remaining global budget and price
verification determine availability; a successful call establishes current model
access/quota, never a promise about future quota.

The original QH45 ledger remains the sole economic authority.8 calls/USD0.20 total,
including4 historical calls/USD0.00239730 at baseline. No session counter in this
mode, no refill/renewal/transfer. UTF8-bound input<=12000 and output<=1000 tokens;
maximum reservationUSD0.0024. flock+fsync prevents concurrent overspend; pending or
failed calls block further calls. Budget shortage returns HTTP402 and the exact
French plafond message before HTTP. No retry/fallback. One synthetic paid smoke
maximum for Codex; repetitive checks use HTTP MockTransport. Original ledger rows
are preserved; only the authorized smoke may append a new row.

app/chat/development.py coordinates the existing ContextualChatService and
ConversationEnrichment through explicit composition. It introduces no second
Engine, repository, schema, model registry or consent/grant storage. The same
UumExtractionProvider/QH32 resolves exact evidence and validates the entire batch;
Source/proposed/outbox publication remains atomic. Runtime receipts say
uum-mistral/3. Replayed source operations do not call the provider again.

Additive POST /context-spaces/{id}/ai/messages accepts the existing ChatInput.
POST .../ai/proposals accepts the existing EnrichmentInput with semantic mode.
No client owner/model/price/budget field. Both authenticate the verified identity.
Legacy session endpoints remain for historical/offline contracts; a configured
development account cannot spend through them. UI capabilities carry automatic
and plafond_reached; ordinary actions bypass all legacy provider modals.

Operational activation uses a private receipt backup and guarded app-only start,
without schema, Keycloak, images, canonical data, backup or PR19 changes. Revoke by
removing the development_account configuration/turning off scoped availability;
a receipt hash change denies in-flight or subsequent results. Original private
receipt is retained for rollback; the ledger must never be rolled back.

The binding radial references and same-Space visual lifecycle remain independent
acceptance criteria. PR23 remains open, unmerged; no Jira write is authorized.


## Owner amendment — diagnostic POC envelope, 22 October 2026

The owner now authorizes **100 aggregate API attempts / EUR5 maximum**, shared by
ordinary chat and UUM extraction for the same exact verified development account.
Use USD2.50 with the existing conservative EUR2/USD accounting bound: 2.50 × 2 =
EUR5, including all historical spend. ECB reference on 22 October: EUR1 = USD1.1205
([official reference](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.eu.html));
this is a reference, not a guaranteed transaction rate. The EUR2/USD bound supplies
substantial margin; do not expand USD based on a more favorable spot rate.
Original expiry, exact model, all old calls/charges and failure/pending guards remain.
No refill, session ceiling, automatic retry/fallback or new real Codex inference.
The private receipt explicitly records this additive budget amendment; the original
ledger gets new ceiling metadata and an append-only amendment record, never a reset
or alteration of historical calls. Old limits above are historical for this mode.

Private development diagnostics capture provider response JSON before last_exchange
cleanup and application validation results independently of economic completion.
Store only response + safe attempt/check/accounting metadata, never request prompts,
authorization headers or credentials. Exact known-key echoes are redacted and flagged.
Storage is private (0700/0600), outside Git/canonical SQL, expires after one hour,
and is pruned on operations plus every thirty seconds while the app runs. Stopped
apps cannot execute housekeeping; startup purges expired content before serving.
Owner/verified principal/current token/work session/Space CHAT gates every read/delete;
price verification and remaining budget are unnecessary for reading old diagnostics.
The Modèles panel exposes scoped authenticated reads and individual controlled delete.
No raw content in ordinary logs, CI artifacts or repository. Repetitive tests use
synthetic transport only. Validation admission rules are unchanged; the proposed
[functional contract and audit](qh-51-validation-audit.md) await owner approval.
