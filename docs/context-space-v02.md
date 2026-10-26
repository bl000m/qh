# Context Space V0.2

Implementation for the owner's 26 October 2026 request, without an assigned Jira
ticket. Browser acceptance with a real model remains outstanding; offline fixtures
verify wiring and invariants, never semantic quality.

The Space opens directly into Discussion. Elements, Overview, Sources, History,
Review and Advice are removed from its navigation. Understanding is a secondary,
closed-by-default, expandable panel; model selection is compact. Rename,
organization and existing governed sharing remain in secondary settings.

The existing UUM Engine, atomic format, exact citation resolver, canonical writer,
projection outbox, graph-verified retrieval, verified OIDC and Mistral cost gates
are reused. No changes to Keycloak, provider configuration, ledgers or `.env`.
Machine consolidation never advances human-confirmed pointers. Existing controlled
sharing still excludes unconfirmed proposals by default.

Additive migration `0010_context_consolidation` introduces immutable intake,
immutable consolidated versions and a per-Space operation state. Owner/Space
checks precede reads and writes. The existing canonical writer publishes original
source, the complete proposed batch, outbox and version in one transaction. Claims
serialize concurrent submissions before paid work; an unchanged successful batch
is replayed without generation. Empty/failed analyses retain pending intake and
the previous version. Browser reload reads persisted intake and versions; it does
not infer. Chat uses the exact last consolidated revision IDs through existing
retrieval and retains backend-produced response attribution; citations are
reauthorized when opened. New dialogue remains pending until explicit memory.

TXT/Markdown retain their exact text. Portable `qh.context-space/1` JSON uses
strict fields, provenance/uncertainty and flattened import ancestry, never a table
dump or credentials. Import does not dereference foreign IDs or confirm imported
assertions. An owner export can contain the owner's original quoted content.

Known limits:

- PDF extraction is unavailable and explicitly refused. No new dependency or fake
  document success was added.
- The existing atomic UUM format produces synthesized statements grouped by its
  six dimensions, not a new free-form summary or entity/relation extraction engine.
  Actual semantic correction/merge quality needs the real-model manual test below.
- All original intake is replayed, including previous support. The previous
  machine understanding is supplied separately as unverified reference data,
  never substituted for the original citable evidence. This is bounded to
  500 entries and 800 KB of stored JSON; each upload is at most 500 KB. The original
  Engine source ceiling still applies. There is no silent truncation.
- Existing chat context formatting remains bounded (40 revisions / 8 KB), with
  partial-coverage warnings. This is no new RAG or semantic ranking engine.
- A process crash during an in-flight consolidation leaves the job running. It
  must be checked by an operator before release, preventing an automatic paid
  retry. Normal failures release the claim for an explicit retry.
- Legacy canonical proposals are retained but are not presented as a fabricated
  consolidated version. Previously recorded material needs an explicit import or
  new intake to enter this new workflow.
- Persistent schema activation, real-model browser acceptance and green Full
  Verification of the final candidate are separate from the local checks.
  Historical browser assertions about the removed navigation need adaptation.

Activation is not performed by this change. AGENTS.md requires explicit approval
and verified backup/rollback safeguards for a persistent migration. After owner
approval, a scoped operator operation must back up and verify the current database,
apply only the additive 0010 migration, verify schema/runtime compatibility and
preserve existing data, IdP, mounts, ledgers, snapshots and private configuration.
Rollback must retain new intake/version history: do not downgrade/drop the tables;
return to the compatible candidate, or restore a verified backup only with explicit
data-loss authorization. No generic Compose lifecycle or `make migrate` on the VPS.

Manual acceptance after authorized activation:

1. Log in with the already approved development account; open/create a Space.
   Verify Discussion occupies the width and Understanding is closed.
2. Enter several messages; use Envoyer to converse. Attach a TXT or Markdown file.
   Verify the pending count. Verify a PDF gives an explicit refusal.
3. Click Mémoriser once. Verify a real `mistral-small-2603` request, structured
   understanding opening automatically, version/date and exact source quotations.
   No per-item/dimension confirmation is required.
4. Reload. Verify discussion, sources and version survive; ask a question about
   the consolidated content and inspect that answer's exact authorized sources.
5. Add an explicit correction. The previous version stays until successful memory;
   memorize and assess that the new version handles the correction/uncertainty.
6. Export JSON. Open a second owned Space; import that JSON. Check it is pending
   until Mémoriser; consolidate, reload and export again. Inspect retained origin
   identity, evidence and uncertainty in ancestry.
7. In an independent second account, verify both private Spaces, intake, exports
   and citations remain inaccessible. No guest rights are widened.

Automatic checks use offline providers and disposable infrastructure exclusively.
No real-provider test or inference is run on load/CI. User-triggered ordinary
Envoyer/Mémoriser retains the existing model and aggregate accounting contract.
