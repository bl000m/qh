# QH-43 — Demo A UX and original branding plan

2026-10-18. **Initial plan at `41ee02f`, preserved below.** The owner has since
approved asset-independent implementation; see the dated gates and current checkpoint.
[Jira QH-43](https://contextlab.atlassian.net/browse/QH-43) is the sole next task;
checkout `/home/ubuntu/qh`, branch `feat/QH-43-demo-a-ux-branding`, based on updated
main `cc6f421b54966f0c1dd302a3da4958d1be6e245f`. Its dedicated PR initially contains
this plan and documentation only; it now includes the authorized functional checkpoint.
Jira QH-43 has not been transitioned.

## Owner-approved implementation gates — 2026-10-18

The owner approved this plan at `41ee02f` and authorized asset-independent layout
implementation in the same PR #15: environment landing, owned overview, primary
chat, expandable explorer, navigation/reflow and canonical/epistemic preservation.
Final branding needs approval of the original-asset selection and visual proposal;
Keycloak theme sources follow that approval, with VPS activation separately gated.
The initial planning text/NOT TESTED matrix below remains its historical checkpoint,
not the current implementation result. See the [asset proposal and checkpoint](qh-43-visual-proposal.md)
for actual files, executed evidence, remaining gates and explicit owner decisions.
No merge, DONE, public Mistral, realm change or canonical write is authorized.

## Start gate and accepted QH-13 boundary

[PR #14](https://github.com/bl000m/qh/pull/14) is merged, without squash/rebase,
as `cc6f421b54966f0c1dd302a3da4958d1be6e245f`; reviewed HEAD
`f543dcb6f03dfa0058b9ad3bb6077442e348d8f9` remains its second parent. QH-13 DONE
was verified on Jira **after** merge. Its reviewed-head
[CI](https://github.com/bl000m/qh/actions/runs/39100631663) passed quality, browser,
OIDC and native integration (665 tests, zero skips). The existing gate/first-trial/
second-trial audits passed again before closure; no new inference was performed.

The owner accepted the POC limit: generated prose may omit the unconfirmed
qualification, but UI warnings derived from verified canonical states remain
mandatory. [The second trial](qh-13-mistral-alias-experiment.md) returned provider/QH
200 with exact aliases, **not** proof of general semantic correctness. The public
provider stays mock; both experiment ledgers remain closed and preserved.

Guarded `dev-stop` preceded the checkout switch; main fast-forwarded and `dev-up`
restored the same frontend/backend containers. All fourteen QH table inventories,
three Alice demo Spaces, protected ledgers/configuration, six container IDs/images/
mounts and infrastructure/MCP uptime match the closure baseline. Only the two app
start times changed. Ports 5173/8000/8080 returned 200. Private before/after evidence
is in ignored `.local-archive/qh13-closure-20261018/`; no credentials are published.

## Product decisions and rationale

Reuse the [Product Contract's approved Demo A amendment](product/QH_PRODUCT_CONTRACT.md#demo-a-experience--owner-amendment-2026-10-17)
and [ADRs 0003](adr/0003-native-context-engine.md),
[0004](adr/0004-unified-understanding-engine.md),
[0005](adr/0005-browse-first-context-understanding.md) and
[0006](adr/0006-scoped-contextual-chat.md). This plan changes presentation priority,
not the Engine, canonical model, policy, public API or OIDC security contract.

| Decision proposed for implementation | Rationale / alternative | Consequence and boundary |
| --- | --- | --- |
| Every successful login lands at `/`, Mon environnement | Orient the owner instead of restoring an old Space | Change application return navigation after the validated OIDC callback; retain state/verifier/nonce checks. Authenticated in-app Space links still work |
| Overview shows existing owned Space cards | Start with available capabilities rather than the presentation's future hierarchy | No Domain grouping/filter, Domain API, sharing control or invented summary/count. Space lifecycle status is distinct from understanding validation |
| Open chat is primary inside a Space | Make the existing interaction immediately usable, instead of putting it below a large explorer | Opening the page sends no question and grants no proposal/provider consent; mock remains explicitly extractive |
| Explorer is visible and collapsed initially | Progressive disclosure avoids overwhelming the page without requiring a search | One visible keyboard-operable control; complete existing browsing/history remains reachable without asking a question |
| Use only owner-approved original graphics | Preserve QH identity instead of approximating its logo | Final artwork/palette/type choices wait for intake; no generated or invented logo. White/black/red and restrained iridescence are direction, not fabricated exact brand specifications |
| Prepare a Keycloak-hosted visual theme, separate from activation | Coherent identity without a second login/session system | No realm modification, theme selection, IdP restart or persistent configuration change under this plan. Activation remains a separate owner gate |

The durable browse-first guarantee remains: users can inspect what the Space
understands before knowing what to search or ask. Chat-first placement does not
hide canonical understanding, turn previews into validated synthesis or make a
mock appear to comprehend a question.

## Proposed screens and interactions

| Screen / route | Concrete layout and behavior | Existing components/contracts reused |
| --- | --- | --- |
| Signed-out QH welcome, `/` | Approved QH mark and restrained glass artwork, short French introduction, one `Se connecter` action; no private Space preview. Session-expired/login-error messages remain readable | `App` sign-in state, `BrowserSession.login`, existing `Notice`; hosted Keycloak redirect |
| Keycloak-hosted sign-in | Same approved mark, typography and colors around the existing username/password, error and login controls; the SPA never takes the password | Current Keycloak login form and inherited theme; existing Code+PKCE client. Theme source preparation and isolated verification only after plan approval |
| `Mon environnement`, `/` after login | Page heading, existing create action and owned Space grid. Cards emphasize name, human-readable lifecycle status and last modification; UUID/admin fields move into expandable metadata. Existing `Afficher plus`, empty/loading/retry states remain | `App.Environment`, `Spaces`, `Metadata`, `QhApi.list/create`; same bounded list API. No understanding query for every dashboard card |
| Space, `/context-spaces/{id}` | Breadcrumb back to Mon environnement, selected Space name, folded metadata. Chat is the first usable section, open initially, with question/composer, loading/error/model and ephemeral-dialogue notice | `Detail`, `Chat`, same scoped POST/CHAT gate and canonical DTOs; distinct React keys per Space/component |
| `Explorer la compréhension`, same Space | Visible closed disclosure below chat; keyboard opens existing overview, current/proposed/history, descriptor groups, entities/relations and complementary search. Load on first expansion, retain while collapsed, reset on Space change | `Understanding`, existing bounded `usePage`, `SearchUnderstanding` and no-selector browse API. No new global counts/facets or taxonomy |
| Revision/source detail, within explorer or chat sources | Readable claim and validation state first; exact source quote/turn, relationship endpoints, time and history remain available. IDs/full JSON are secondary expandable details | `Revision`, canonical source/citation rendering, exact anchor/history navigation; unavailable full source text is not invented |

The app shell should show `Mon environnement` as the root page heading and the
actual Space name as the Space heading; a breadcrumb gives orientation. Do not
present a Domain breadcrumb when no Domain exists. Responsive order is unchanged:
Space identity → chat → explorer, one column on narrow screens, no horizontal
page overflow. No new interaction panel is required for unavailable capabilities.

Chat requirements remain visible near the composer: confirmed-current default;
unconfirmed proposals require the existing unchecked opt-in; proposed-only/empty/
unavailable states differ; mock says **Extraits de démonstration — sans compréhension
de la question**. Preserve the per-answer proposed-support and all-proposed-context
warnings even when model prose contradicts or omits status. Keep **Sources utilisées**
(declared references) separate from **Contexte fourni et limites** (transmitted set).
No automatic provider invocation on opening a Space, login or disclosure control.

Changing Space, proposal choice, logout or expired identity clears temporary
conversation as before; stale async results cannot populate another Space. Toggling
the explorer must not erase chat or opt in to proposals. Closing a disclosure while
focus is inside returns focus to its control. Preserve exact revisions, graph trust,
partial-coverage warnings and fail-closed error handling throughout.

## Reuse and intended implementation surface — not changed now

| Surface | Intended minimal change after review |
| --- | --- |
| `apps/web/src/App.tsx` | Root/Space heading, card metadata disclosure, primary chat then explorer wrapper; preserve API access/owner handling |
| `apps/web/src/auth.ts` | Successful authentication routes to `/` rather than restoring `user.state`; retain callback validation, in-memory tokens, temporary PKCE state and logout behavior |
| `apps/web/src/Chat.tsx` | Primary/open placement and visual composition; reuse all messages, warnings, source panels, reset and no-retry logic |
| `apps/web/src/Understanding.tsx`, `Revision.tsx` | Reuse renderer and navigation, adapt heading/focus hierarchy only where needed; no reinterpretation or relabeling of canonical data |
| `apps/web/src/styles.css`, `index.html`, `public/brand/` | Approved visual tokens/assets/favicon, responsive spacing and focus; no new UI framework or dependency expected |
| Future `infra/keycloak/themes/qh/` | Proposed source-only inherited login theme and documentation; no live realm/import/Compose change |
| Existing frontend tests / isolated browser harness | Extend current suites, not a new infrastructure or parallel VPS stack |

A successful callback currently restores a validated Space return path. The new
owner-approved landing deliberately changes that UX expectation. In
`apps/web/tests/browser.spec.ts`, Bob's foreign deep link must now first land at the
environment after login, then explicitly navigate to Alice's Space to verify the
same denial. Do not drop the denial assertion or weaken callback/open-redirect
checks just to accommodate the new landing. Reuse `apps/web/tests/contracts.spec.ts` for
navigation contracts and existing chat/browse/understanding/graph-outage suites.

## Original asset intake and design-reference analysis

Intake directory: **`/home/ubuntu/qh/.local-archive/branding/incoming/`**.
It was absent at preflight and has been prepared empty, mode 700, for the owner's
handoff. No package was found or analyzed; no logo was generated. `.local-archive`
is Git-ignored and Docker-build-excluded. The owner may transfer files through
VS Code Remote or SCP; only approved distributable derivatives will enter Git.

| Needed reference | Preferred delivery | Use / decision still pending |
| --- | --- | --- |
| Original QH logo | SVG with viewBox/vector paths; transparent PNG 1024–2048 px fallback | Approved primary mark, clear space and minimum size; do not redraw |
| Logo variants | Light/dark, horizontal/compact/icon variants if original versions exist | Choose supplied variants per background; do not invent absent variants |
| Glass sphere artwork | Original PNG/WebP/AVIF, alpha if intended, high-resolution master | Restrained decorative placement; cannot obscure text, warnings or controls |
| Product presentation/mockups | PDF/PPTX and selected screenshots | Visual/composition reference only; not proof of implemented Domains, sharing, ingestion, summaries or graph UI |
| Palette and logo rules | Exact supplied color values and usage guide | Translate to a small shared client/theme token sheet after review |
| Typography | Font names and licences; WOFF2 only with redistribution permission | Prefer existing system fallback until approved, no remote font tracking |
| Rights/provenance | Ownership/licence and permission to publish chosen derivatives | Asset manifest with original SHA, selected derivative, purpose and licence; source deck stays private |

After delivery: inventory names/formats/dimensions/SHA-256 without executing embedded
content; inspect originals visually; map each reference screen to **existing**, **QH-43
presentation change**, or **future capability**. Return a compact selection/contact
sheet and capability matrix for owner review before importing public assets. Check
SVG scripts/external references and export static safe derivatives if needed,
preserving the original private files and documenting transformations. No source
presentation, private metadata or unapproved artwork is published by default.

Brand direction: white/black for structure, red as a deliberate accent, quiet
iridescence/glass away from reading surfaces. Confirmation/proposal/error states
must retain explicit text and sufficient contrast, never color alone. Keep focus
rings, visible labels and reduced-motion behavior; no decorative animation is
required. Exact palette, composition and logo proportions await originals.

## Keycloak boundary and isolated theme verification

Follow official [Keycloak theme guidance](https://www.keycloak.org/ui-customization/themes):
extend a bundled theme instead of editing it. Prefer images/CSS/properties over
replacing login form templates; inheritance details must match the actual pinned
Keycloak version. This is a preparation recommendation, not activation instructions
or permission to change the running realm.

After plan/assets approval, prepare theme sources using only approved artwork;
validate their appearance and the unchanged Code+PKCE flow through the existing
isolated Keycloak/browser harness. Keep issuer, client, redirect allowlist,
state/verifier/nonce, token-memory boundary, passwords, identities and policy intact.
No CDN, external scripts or second authentication/session backend. Do not alter
`infra/keycloak/qh-realm.json`, select a live theme or change the VPS IdP container.

Prepared theme sources and isolated screenshot/OIDC evidence can satisfy the
**preparation** portion of QH-43. A branded login actually visible on the VPS needs
separate explicit runtime authorization and a reviewed activation/rollback plan.
It must remain **NOT ACTIVATED**, not be called delivered live, until that gate.

## Acceptance matrix and verification plan

The rows below map the actual Jira criteria; proposed checks are **NOT EXECUTED for
QH-43**, and no UX criterion is claimed implemented by this document.

| Jira criterion | Observable acceptance / planned evidence | Current state |
| --- | --- | --- |
| Login/reload lands in Mon environnement | Real Chromium + Keycloak fresh login, protected deep-link login, reload/reauthentication and session-expiry recovery end at `/`; authenticated navigation still opens selected Spaces. Invalid state/token, logout and token-free Web Storage regressions retained | NOT IMPLEMENTED / NOT TESTED |
| Owned overview; no fake Domains/sharing | Alice sees only owned cards with bounded pagination; Bob sees no Alice cards or metadata and is denied explicit foreign URL/API access after login. No fabricated Domain controls, global totals or synthesis | NOT IMPLEMENTED / NOT TESTED |
| Chat primary; state/consent preserved | Composer precedes explorer; no automatic POST. Proposed-only/current/mixed/empty states, explicit opt-in/reset, Space/identity switch, late response and provider failures pass; both deterministic proposal warnings remain | NOT IMPLEMENTED / NOT TESTED |
| Expandable complete exploration | Tab + Enter/Space opens/closes explorer; focus is meaningful and visible. Existing no-query overview, open descriptors, item/entity/relation details, exact quotes/endpoints and revision history remain accessible; partial pages do not claim completeness | NOT IMPLEMENTED / NOT TESTED |
| Original traceable graphics, responsive/readable | Owner-selected asset manifest/licences, desktop and 390px mobile screenshots, 320px reflow and 200% zoom checks; text contrast >=4.5:1, large text/UI boundaries/focus >=3:1; warnings never rely on color; keyboard/reduced-motion checked | ASSETS PENDING / NOT TESTED |
| Keycloak visual coherence preserves OIDC | Inherited source theme reviewed with approved assets; real isolated OIDC/browser checks and error-state screenshots. Runtime activation reported separately and requires owner authorization | NOT PREPARED / NOT TESTED / NOT ACTIVATED |
| TypeScript/build and regressions | Existing Docker frontend lint/build, Chromium suites including updated landing expectation, auth/owner/browse/chat/graph failure regressions and relevant hosted CI; no paid calls or VPS test seed | NOT EXECUTED for implementation |
| Owner review, merge, Jira closure | Owner approves this plan/assets, then reviews the implemented single PR; merge and DONE only under explicit authorization with every required criterion evidenced | PENDING; draft planning PR is not technical READY FOR REVIEW or DONE |

Use existing isolated fixture Spaces for destructive/error scenarios. On the live
VPS, limit any later smoke to existing three synthetic Alice Spaces and read/mock
chat operations; no create/rename/reseed, canonical write, graph outage or IdP change
without separate authorization. Do not duplicate the existing Docker test stack.

## Review gate and sequence within this same ticket

1. **Now:** publish this planning-only draft PR and stop for owner review.
2. Owner delivers originals; inspect them and obtain approval of plan, asset selection
   and final visual choices. Missing graphics do not authorize a substitute logo.
3. Only after approval, implement coherent client navigation/composition and approved
   asset styling in this same branch/PR; prepare the theme separately from activation.
4. Execute the matrix using existing fixtures/harness, publish screenshots and exact
   results, and request implementation review. No automatic merge/DONE.

No new ADR is required for this planning-only step: responsibilities are unchanged
and the product direction is already recorded in the approved Contract amendment.
Any later structural contradiction would require an explicit decision before work.

**Out of scope:** Domain model, sharing, advanced graph UI, editing/interactive human
confirmation, generated synthesis, QH-39 ingestion, QH-34/QH-44 Context Delta/export
work, local models, semantic retrieval or paid/public Mistral activation. No new
service, public API, migration, canonical write or automatic confirmation. QH-44's
roadmap note is acknowledged only; no work or ticket changes are performed on it.
