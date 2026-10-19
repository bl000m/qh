# ADR 0008 — Personal organization and explicit owner review

2026-10-19. Accepted by the product owner for QH-50, referencing QH-46.
Builds on ADRs 0003, 0004, 0005 and 0007; their historical decisions remain intact.

## Decision and rationale

Personal domains organize access to existing Spaces; they are not semantic types,
canonical understanding, security scopes or a replacement Context Engine. One
owner-bound PostgreSQL metadata document stores editable domains and many-to-many
Space memberships, with optimistic version checks. Seven French defaults are
returned without creating canonical Spaces or classifying private content. Profile
and preferences remain transversal. Membership never grants permission. Every
referenced Space must pass the existing PolicyService and SQL ownership fence.

The owner explicitly approved one metadata-only migration, tested in isolation
before its narrowly scoped VPS application. Sources, Understanding revisions and
existing demo content must remain unchanged. Client-only storage was rejected
because organization must survive browser changes; canonical domain entities were
rejected because navigation must not impose an ontology.

Owner review uses the existing canonical publisher and outbox, not a new database
or engine. Explicit confirmation/rejection of a pending proposal creates a new
immutable revision with the same identity, profile, shape, sources and relation
anchors. Confirmation alone advances the confirmed-current pointer atomically;
rejection preserves the previous pointer. A text correction creates a human
proposal, never an implicit confirmation. Original extraction and history remain.
Independent propose/confirm policy actions are owner-only. Concurrency conflicts
fail closed; an identical operation key replays the same result and a conflicting
reuse fails. Review receipts are immutable revision metadata, not a second table.

The pending inbox distinguishes proposals with review successors. Existing public
`proposed` and `history` retrieval retain their historical meaning. A confirmed
hypothesis is still a hypothesis. Source quotation, interpretation, human acceptance
and external truth remain separate. Tests of review mutations use disposable data;
Codex must not confirm the VPS demo proposals.

## UX consequences and limits

Chat stays primary, with a temporary conversational viewport and an accessible
answer-specific sources panel. Technical records remain available by disclosure.
Groups use literal asserted descriptors only; unknown meanings remain visible.
Revision lineage/current pointers can explain explicit evolution, but do not prove
contradiction, semantic replacement or matching. Advanced reconciliation (QH-47),
semantic retrieval (QH-48), conversation ingestion (QH-39) and session redesign
(QH-42) remain separate. No provider calls or new disclosure are authorized here.

The application adds organization/review contracts, outbound PostgreSQL adapters
and inbound REST routes, assembled in composition. Core stays framework independent.
No Keycloak, OIDC lifetime, provider budgets or consent changes follow this ADR.

## Owner dashboard clarification — 2026-10-19

The two dashboard shelves are horizontal carousels: Mes domaines and Reprendre
mes Context Spaces. Domain selection filters the server-paginated Space list;
Tous les domaines and Non classés are explicit. Titles remain centered and full
names accessible. Sorting uses recorded opening time or opening count, never
`updated_at`. One bounded request-local opening event records server time/count
in the same owner document, without conversation text. A bounded deduplication
window handles duplicate React effects; this is navigation activity, not analytics
or proof of use before this feature existed. Organization updates cannot forge
or erase server-authored activity and do not race its version unnecessarily.

The UX creation route requires one primary domain and atomically creates the
Space and its membership; further memberships are editable. Legacy QH-9 REST
creation remains compatible and yields an unclassified Space, like pre-existing
Spaces. New dashboard creation cannot bypass its required primary-domain choice.
No automatic assignment is applied retroactively. Removing a domain only changes
organization; it does not delete Spaces or their understanding.

## Later owner refinement — hierarchical navigation, 2026-10-19

This later decision supersedes **home filtering** in the earlier dashboard clarification;
its persistence, owner fences, opening activity and primary-domain rules still apply.
Mon environnement presents two compact independent shelves. Selecting a domain opens
`/domains/{domain_id}`, with only that owner's associated Spaces and a creation action
preselecting that primary domain. Settings hold domain editing; secondary collection
views expose all/unclassified Spaces. The home has no remembered domain filter.

Explicit domain-origin navigation uses `/domains/{domain_id}/context-spaces/{space_id}`.
A breadcrumb uses that origin only after the owner's organization confirms membership;
it never infers origin from the primary domain. Direct/resume Space links have no domain.
Renaming preserves IDs; missing/deleted domains fail with an inaccessible-domain state.
No new backend API, metadata schema or canonical write is necessary for routing.
An explicitly requested domain URL survives an OIDC reauthentication through validated
transaction state; ordinary login and plain Space login still land at Mon environnement.
Token memory storage, expiry, PKCE, nonce and state verification remain unchanged.

Alternatives rejected: leaving all shelves visible while filtering does not communicate
entry into a domain; inferring primary membership as navigation origin misrepresents
multi-domain navigation; session/local storage of a last Space silently resumes context.
The tradeoff is an explicit nested route, plus a graceful home-only breadcrumb when
its former domain/membership is no longer available. Membership never grants access.

The owner-selected login mockup refines the existing Keycloak theme with small real
FR/EN locale links and native credential controls. Versioned template overrides retain
upstream authentication/session/error/optional-flow branches, with pinned upstream
maintenance documented in the theme. No custom credential endpoint or realm change
is introduced. Prepared source and isolated rendering do not activate the live theme;
QH-49 owns durable image/mount delivery before any ordinary Keycloak recreation.
