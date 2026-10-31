## Mise à jour POC autorisée —23 octobre2026

Le plafond courant est EUR10 au total, historique inclus: USD5 avec le bound
conservateur EUR2/USD conservé. Aucun quota de requêtes/session dans ce mode.
Les requêtes ordinaires n'envoient pas max_tokens; la réservation avant HTTP
couvre le pire coût de la fenêtre combinée du modèle. Mémoriser → Continuer
analyse toute la conversation via le même Engine, publication atomique de source
et propositions non confirmées, puis Voir la proposition. Aucun appel payé pour
les vérifications de cet incrément; les contrats ci-dessous restent historiques.

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

### Private UUM performance diagnostics — 29 October 2026

Consolidations add numeric metadata to the same private, scoped, one-hour records.
`input_tokens`/`output_tokens` reuse validated ledger usage reported by Mistral;
they cover the entire request, not an independently verified invoice or isolated
source tokenization. `source_tokens` is unavailable (`null`); no tokenizer estimate
is presented as billed usage. Missing measurements remain missing, never zero.
`provider_ms` reuses the existing monotonic transport timing (after reservation,
through response receipt/JSON capture). `consolidation_ms` measures entry into
consolidate, including authorization, context preparation, provider, validation and
publication/error cleanup, up to diagnostic finalization. Replays without a new
provider call do not create an artificial generation diagnostic.

`source_chars` includes the original source's speaker prefixes and separators;
`source_disclosed_chars` counts its nonoverlapping transmitted segments. Both use
Unicode code points. `request_message_chars` covers all message bodies, including
instructions/previous machine state; `request_schema_chars` measures the compact
output schema. `catalogue_chars` measures compact passage metadata plus segment
reference labels, excluding source text. These normalized JSON sizes are not HTTP
wire byte measurements. `output_json_chars`/`output_json_bytes` measure the actual
provider message content in code points/UTF-8 bytes before canonical expansion.
`atomic_items`, `passage_references` (occurrences, not distinct IDs),
`atomic_text_chars` and compact `evidence_json_chars` describe returned output,
including a candidate subsequently rejected by the Engine. They imply no semantic
support or confirmation. Invalid JSON retains available sizes without invented counts.

Four simple advisory flags are independent of admission and budgets:

- Output tokens > 3 × input tokens, with output >= 2,000 tokens.
- At least 8 atomics and more than 1 atomic per 100 source characters.
- Compact evidence/reference arrays > 50% of actual output characters, with output >= 2,000 characters.
- Catalogue metadata > 2 × source characters, with catalogue >= 4,000 characters.

Ratios are indicative comparisons (including normalized field sizes where stated),
not proof of an error. Long requested procedures can legitimately trigger them.
No flag changes validation, token ceilings, timeouts, retries or persistence.
The existing payload carries source text once; catalogue descriptors contain no
copied quotes. Previous understanding is separately labelled unverified machine
data. No context compaction is introduced.

A future passage selector can fit between the authorized Engine packet and
`PassageReferences` construction in `UumExtractionProvider.generate`. It must keep
original source IDs/offsets and relevant facts, constraints, negation, contradictions,
chronology and user/assistant/external attribution, with sufficient surrounding
context. Existing access checks and canonical citation validation remain mandatory;
selection must not turn missing evidence into an assertion. This is not implemented.


## Contratto di risposta approvato — 22 ottobre 2026

L'owner approva il contratto dell'audit con `support_basis` obbligatorio:

| Valore | Condizioni controllate sugli input effettivamente inviati |
| --- | --- |
| dialogue | Messaggio utente esplicito non vuoto; nessun alias citato; insufficient_context=false. Può esistere contesto canonico disponibile ma non dichiarato come supporto |
| canonical | Almeno un alias esatto, distinto e risolvibile fra quelli trasmessi; insufficient_context=false |
| mixed | Condizioni canonical più presenza del dialogo utente effettivamente inviato; insufficient_context=false |
| insufficient | insufficient_context=true; eventuali riferimenti devono comunque essere validi e possono indicare supporto pertinente ma inadeguato |

Il backend verifica packet/snapshot/record/alias e presenza del dialogo, **non**
entailment o verità del testo. Il frontend verifica il DTO rispetto allo Space,
alla selezione ricevuta e al dialogo della richiesta. La dichiarazione del modello
non è una prova autonoma; nessuna riconciliazione o correzione euristica. Canonical
indica revisioni persistite autorizzate, anche proposte se esplicitamente incluse:
non significa automaticamente conoscenza confermata o verità. Stati epistemici e
avvisi su proposte/copertura parziale rimangono indipendenti.

UI: appui déclaré leggibile e avviso per dialogue/mixed: informazioni conversazionali
non confermate/registrate, nessuna memorizzazione automatica. UUM rimane un'azione
distinta; Source/proposte/outbox e review QH46 restano invariati. Autorizzazione,
provenance, struttura JSON, snapshot e plafond restano bloccanti. Nessun fallback
al vecchio protocollo: campo assente o incoerente viene respinto. Le evidenze storiche
non vengono riscritte. Il precedente divieto di implementazione era un gate ora
soddisfatto, non una regola funzionale permanente.

La sola verifica reale autorizzata da questo mandato usa il modello pinned
mistral-small-2603 e l'endpoint già approvato, una richiesta sintetica entro il
plafond residuo, prenotazione massima USD0.0024, zero retry/fallback. Nessuna
inferenza di startup o test automatico/CI; payload e JSON sanitari fittizi rimangono
privati. Le altre prove usano provider simulato. Non estende disponibilità o budget.
