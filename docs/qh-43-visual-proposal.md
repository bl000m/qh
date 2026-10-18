# QH-43 — asset selection and functional UX checkpoints

2026-10-18. Owner approved plan commit `41ee02f` and authorized the asset-independent
layout in PR #15. **Branding selection awaits review; no theme source or activation.**
[Approved plan](qh-43-ux-branding-plan.md),
[Jira QH-43](https://contextlab.atlassian.net/browse/QH-43),
[PR #15](https://github.com/bl000m/qh/pull/15).


## Selected identity — later owner decision, 2026-10-18

The owner has now selected the precise geometric original mark and **closed the
comparison**. Do not propose L1–L8 again. Minimal technical derivatives, frontend
preview and source-only Keycloak preparation are authorized; the following review
gates are historical checkpoints, superseded for that preview by the
[selected identity record](qh-43-branding-checkpoint.md). No general artwork licence,
VPS theme activation, final UX acceptance, merge or DONE is inferred.

## Second checkpoint — owner direction and private logo gate, 2026-10-18

The owner accepted the first functional layout as a **working base, not final UX**.
The seven files in `QH-design 2/` are confirmed as the intended reference delivery;
there is **no remaining ZIP prerequisite**. Earlier archive observations below are
historical evidence, not a request to supply or reconstruct an archive.

The approved visual direction is the original standalone bubble as compact
noninteractive decoration in Mon environnement/welcome, white/black structure,
red accents and restrained iridescence. Portrait illustrations and future-feature
mockups must not become product controls. Final public branding is still gated:
**select the actual logo variant and confirm public usage rights first**. Keycloak
theme source preparation waits for that selection; no realm/theme activation.

The private comparison board is
`/home/ubuntu/qh/.local-archive/branding/logo-review-20261018/logo-board.html`
(and `logo-board.png` beside it). Options L1–L3 show the mockup wordmarks, L4–L7
the presentation's construction/orientation variants, and L8 the chat mockup's
small application. Each is explicitly labelled a **simple crop**, with original
file SHA, region, PDF page where applicable and derived hash in `logo-options.json`.
No mark is redrawn, retyped, rotated or heuristically reconstructed. PDF crops are
rasterized, not standalone original masters. All 24 pages are privately available
as a contact sheet; repeated embedded applications are not treated as new brands.
The original seven files remain unchanged and private. Missing: an authoritative
standalone SVG/master, official variants/spacing, palette/typography and usage
rights. No crop, board, PDF or original image enters Git or the client bundle.

### Second iteration: adopted decisions and rationale

| Decision | Rationale / alternative | Consequences and limits |
| --- | --- | --- |
| Put the question ahead of implementation explanations | Reduce the first-screen reading burden instead of requiring technical onboarding | Bounded/unranked retrieval, ephemeral dialogue, history exclusion and reset behavior remain in `Fonctionnement et limites`, after the composer |
| Keep consent and applicable canonical warnings visible | Disclosure must not obscure authorization or epistemic state | Proposal inclusion stays unchecked; unconfirmed availability and both deterministic response warnings stay outside collapsed sections |
| Distinguish the user's question and provider output visually | Establish conversational rhythm instead of an administrative form | Pending state shows the actual submitted question plus loading status, never a simulated response; exact extractive mock label remains |
| Make technical sources secondary, but inspectable | Readable dialogue should lead without losing auditability | Declared references and provided context retain separate disclosures and the existing complete canonical renderer; explorer stays visible before any question |
| Make the skip link first in keyboard order and explicitly transfer focus | A screenshot of focused UI must not imply a permanent overlay | Clipped off-focus, visible on focus, activation focuses main and removes the overlay; no token/session/navigation contract changes |

[Second-iteration evidence, comparisons and test boundaries](evidence/qh43-ux-iteration2-20261018/README.md).
This remains **IN PROGRESS / owner checkpoint**, with PR #15 OPEN and DRAFT.
Branding selection/rights, final visual approval and theme source preparation are
not implemented or verified; merge and Jira DONE are not authorized.

## First checkpoint — historical record

## Actual delivery and integrity

The named `qh-design-references.zip` is absent. The intake instead contains
`QH-design 2/` with **seven already-extracted files**: five PNGs, one PDF and README.
No ZIP was created or extraction fabricated; archive integrity remains **NOT TESTED**.
The individual file sizes/SHA-256/dimensions are in the
[asset inventory](evidence/qh43-ux-checkpoint-20261018/asset-inventory.json).
All five PNG chunk CRCs/boundaries pass. The PDF opens, is unencrypted and has 24
pages of 1440 × 810 points; all page text was read and relevant pages rendered
privately. Originals are unchanged; hash-identical private copies are retained in
`.local-archive/branding/review-20261018/originals/`.

The PDF and mockups remain private references. They are not installed into public
assets, copied into application bundles, or presented as implemented features.
No original SVG/standalone logo, exact brand token sheet or font licence was supplied.

## Selection proposed for owner approval

| Original reference | Observation / selected use | Excluded interpretation |
| --- | --- | --- |
| `01-mobile-mon-environnement.png`, 1086 × 1448 | White space, compact QH mark and glass visual anchor inform the welcome/environment hierarchy | No provider shortcuts, projection actions, native mobile shell or fake menu features |
| `02-chat-projection-sante.png`, 1086 × 1448 | Clear question/answer rhythm and expandable evidence inform the existing scoped chat | It depicts a guest health projection, not Alice's implemented owner chat. No medical content, guest access or synthetic intelligent answer is imported |
| `03-projection-autorisations.png`, 1086 × 1448 | Future sharing/permission concept only; no UI control selected | No link generation, recipient/provider permissions, write access or European-provider policy toggles |
| `04-illustration-bulles.png`, 1122 × 1402 | Editorial/marketing reference; omit from functional screens | Portraits do not become owners, avatars, navigation controls or product data |
| `Bulle de savon irisée transparente.png`, 1448 × 1086, RGBA | Propose this exact original as a small decorative environment/welcome accent. Keep its proportions and do not derive interactive meaning from it | Not a graph visualization, completeness score, Domain object or Space selector |
| `05-presentation-reference.pdf`, 24 pages | Page 1: brand intent; 9–12: environment/understanding; 19–21: conceptual access modes and projections. Distinguish persistent understanding from a transcript | Domains, ongoing conversational acquisition, sharing, guest links, MCP/export and agent actions remain future ticket scope |

The mockups show a red-circle/black-letter wordmark; page 1 also explores rotated
HQ/QH variants. That is **not a sufficiently unambiguous brand master**. No raster
logo crop or reconstructed vector is approved or implemented. The existing plain
QH text remains in the working client until the owner supplies/selects the master.

## Proposed composition — private design, not the running implementation

Private preview:
`/home/ubuntu/qh/.local-archive/branding/review-20261018/visual-proposal.html`.
Rendered review image:
`/home/ubuntu/qh/.local-archive/qh43-implementation-20261018/visual-proposal.png`.
It uses the original bubble and an explicitly labelled missing-logo placeholder;
it is a proposal, not an application screenshot or a replacement logo.

- **Environment:** approved original logo in the header; Mon environnement and
  short orientation copy; small bubble alongside the title on desktop, reduced
  on mobile so the owned-Space list remains immediately discoverable. Actual
  Space names/status lead; technical IDs stay in disclosures. No Domain grouping.
- **Space:** compact breadcrumb and Space title, then the existing chat, with
  proposal choice/warnings and source panels preserved. No large decorative hero
  above the composer. Explorer remains a visible disclosure below it.
- **Welcome/Keycloak:** same eventual original mark and restrained bubble artwork,
  with readable login/error controls. Keycloak remains the credential collector;
  theme preparation begins only after asset selection approval, activation later.
- **Style:** white/black structure, restrained red accent and the supplied bubble's
  iridescence outside text surfaces. Preview red is illustrative, not a claim of
  an authoritative supplied hex palette. Do not use color alone for epistemic state.

### Explicit review decisions

1. Approve or correct the compact decorative use of the standalone bubble for
   environment/welcome, with no editorial portraits or projection mockups in the app.
2. Approve or correct the screen composition and restrained white/black/red direction.
3. Supply the authoritative logo SVG (and available light/dark/icon variants), resolve
   PDF/mockup wordmark variants, and confirm palette/typography plus public asset rights.
4. Confirm that the already-extracted seven files are the intended reference delivery,
   or provide the ZIP if archive-level verification is required. Current file hashes
   identify exactly what was analyzed; no ZIP verification is claimed.

The first two decisions do not authorize a fabricated logo. Source PDF/mockups stay
private even after design approval; only specifically approved minimal derivatives
would enter the public client/theme assets.

## Functional layout implemented independently of branding

- A valid OIDC callback now always lands on Mon environnement. PKCE/state/nonce,
  in-memory token lifetime and existing logout/identity/policy contracts are unchanged.
- Owned cards emphasize name, lifecycle status and modification date; administrative
  metadata and account identity are expandable. Lifecycle `active` is not understanding
  confirmation. Existing bounded ordering/pagination and create API remain unchanged.
- Space heading/breadcrumb identify the current Space. Chat is open and primary,
  without an automatic POST or proposal opt-in. Native explorer disclosure lazily
  mounts the same Understanding renderer on first expansion and retains it while
  folded. Escape returns focus; changing Space resets it and temporary conversation.
- The existing full canonical fields, source citations, exact relation anchors,
  descriptor certainty, history, search and graph-readiness checks remain available.
  Declared sources and provided context stay distinct. Both deterministic proposed
  warnings remain mandatory, independently of the model's prose.
- Layout supports keyboard/skip navigation, mobile reflow and enlarged text using
  the existing neutral styling. **No final palette, logo, bubble or Keycloak theme
  has been applied to the running application.**

No API/backend/Core/policy/schema/provider/infra/dependency change. No Domain,
sharing/projection, human validation/editing, synthesis or QH-39/QH-44 feature.

## Verification and remaining gates

Executed commands, counts and actual screenshots are recorded in the
[checkpoint evidence](evidence/qh43-ux-checkpoint-20261018/README.md).
The initial isolated run found two issues: its new reauthentication helper assumed
that every login presents a password form, and real 320px/200%-text overflow.
The helper now accepts either the genuine Keycloak form or validated SSO completion;
flex wrapping/intrinsic text wrapping correct reflow without clipping content or
weakening the assertions. Original security/denial tests remain intact; Bob now
navigates explicitly after the intentional login-to-environment change.

This is an **IN PROGRESS implementation checkpoint** for owner review, not full
QH-43 READY FOR REVIEW/DONE. Asset choice, original SVG/rights, final visual checks
and theme-source preparation are pending. Live theme activation requires separate
explicit authorization. General accessibility certification or live model semantic
correctness is not claimed by layout tests or by the owner's QH-13 POC acceptance.

### First-checkpoint Jira acceptance mapping (historical)

| Jira criterion | Checkpoint classification / evidence | Missing portion |
| --- | --- | --- |
| Login/reload environment; invalid tokens/logout/isolation | Implemented and tested — PASS: real Code+PKCE/SSO, callback/PKCE tampering, expiry/reload and Alice/Bob browser regressions | Final owner UX review |
| Owned overview; no fake Domains/sharing | Implemented and tested — PASS: owned list, pagination, metadata disclosure and foreign access denial; no API/schema change | Final branded appearance |
| Primary chat with consent/reset/epistemic safeguards | Implemented and tested — PASS: no automatic POST, canonical warnings, mock labels, three-Space reset/late response and source checks | No general model comprehension claim |
| Accessible expandable full exploration | Implemented and tested — PASS: native keyboard disclosure, retained draft/choice, focus return, canonical source/history/anchor regressions | Final visual review with selected assets |
| Original traceable graphics and responsive readability | Partially implemented/tested: neutral desktop/mobile/reflow PASS; file-level asset integrity PASS | Branding selection, authoritative SVG/rights, final palette/contrast/visual acceptance; ZIP integrity unavailable |
| Keycloak presentation/security | Existing OIDC preserved/tested — PASS; theme NOT IMPLEMENTED / NOT TESTED / NOT ACTIVATED | Sources only after asset approval; VPS activation separately authorized |
| TypeScript/build/browser/OIDC/CI | Local frontend/build, 43 browser/contracts, OIDC/outage/restored-ID checks PASS; latest hosted CI belongs to PR #15 HEAD | Verify current hosted run separately; counts are not combined |
| Owner review, merge and Jira closure | NOT DONE; implementation checkpoint only, PR remains draft | Owner asset/implementation review and explicit merge/DONE authorization |
