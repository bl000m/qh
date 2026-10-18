# QH-43 — selected original identity and login preview

Later owner correction: [central artwork, capsules and primary chat](qh-43-hero-checkpoint.md).
Earlier screenshots/readiness below are dated checkpoints, not acceptance of this iteration.

Later final-verification record: [French isolated login, acceptance mapping and
review readiness](qh-43-final-review.md). The dated draft checkpoint below is
preserved; it does not override the later final-review status.

2026-10-18 (Europe/Rome). PR #15 remains **OPEN / DRAFT**; no merge or Jira DONE.
The owner selected the exact red-circle/black-H geometric mark in their message,
closed the logo comparison and authorized minimal technical adaptations, frontend
integration and login/theme preparation. **Do not offer L1–L8 again.** Historical
comparison artifacts stay private and unchanged. This checkpoint supersedes the
logo-selection gate in the earlier [visual review](qh-43-visual-proposal.md);
[Product Contract](product/QH_PRODUCT_CONTRACT.md) and ADRs 0003–0006 still govern.

## Product decisions and rationale

| Adopted decision | Rationale / alternative | Consequences and limits |
| --- | --- | --- |
| Use only the selected original geometric mark | The owner has chosen it; no new creative/logo variants or recreated vector | Faithfully crop the same original in the supplied PDF; preserve colors/orientation/proportions. Missing standalone SVG does not block the approved raster preview |
| One logo asset, responsive sizing | Avoid divergent desktop/mobile identities | Header on welcome, Mon environnement and every Space; accessible link name remains QH — accueil. Never reinterpret the H/circle arrangement or rotate it |
| Original bubble, compact and decorative | Carry the approved iridescence without competing with content | Welcome/environment only, empty alt and aria-hidden; no bubble above the in-Space question or fake graph/Domain/provider controls |
| White/black structure, restrained red | Match the chosen mark while keeping reading and focus clear | Preserve black focus, text labels and all epistemic/consent safeguards; do not recolor the mark. No remote fonts or new effects |
| Minimal technical favicon | Reuse the whole selected mark, not a new monogram | 64×64 fit with clear padding; PNG in client, same PNG inside theme ICO. No PWA/install capability or new icon family |
| Inherit Keycloak form, add presentation only | Preserve maintained credential/validation/OIDC behavior instead of copying templates or building a login form | Theme sources and actual isolated preview; no persistent realm/import/configuration or IdP restart. Activation requires separate explicit authorization |

## Source and adaptation boundaries

The approval image is a visual reference; no local attachment binary was supplied.
The identical geometric construction exists in the owner's original
`05-presentation-reference.pdf`, page 1. The PNG is a crop/render of that original,
not a hand-reconstruction and not claimed byte-identical to the chat attachment.
Region `[842,225,1134,481]` PDF points at 3× yields 876×768; its original light
background is retained, without heuristic transparency removal. No standalone SVG
is fabricated. A future supplied master can replace this asset without redesign.

The supplied `Bulle de savon irisée transparente.png` is proportionally resampled
from 1448×1086 to 400×300. Alpha remains intact; no illustration is generated.
Header/welcome/environment use the same logo file with CSS sizing. The favicon
fits the whole mark into 64×64; no logo feature is removed to fill the square.
Theme PNG copies equal the frontend files byte-for-byte.

Owner authorization covers this requested product preview/frontend integration
and preparation. It is not recorded as a general artwork licence, final UX sign-off,
production theme activation or permission to publish the presentation/mockups.
Only these selected minimal technical derivatives enter the task PR.

## Implemented surfaces and unchanged contracts

- The common header shows the exact selected mark on desktop/mobile, welcome,
  Mon environnement and Space views. The home link remains keyboard accessible.
- Welcome and Mon environnement show the original compact decorative bubble.
  Existing owned cards/navigation and empty/loading/error states remain real.
- Space stays chat-first: no decorative hero, added onboarding or mandatory search
  before exploration. Consent is unchecked; canonical warnings, exact sources,
  transmitted-context disclosure, revision history and explorer remain available.
- Assets are Vite imports under `apps/web/src/brand`, already source-mounted.
  Existing HMR and loopback ports work without new mounts/restarts/config changes.
- The source-only login theme inherits Keycloak 26.4.7 `keycloak.v2`. CSS/assets
  and header text only; upstream templates/scripts/forms stay inherited. The test
  harness uses a temporary public-fixture copy with only `loginTheme` changed.
  The persistent readonly realm file is never written or theme-selected.

No backend/Core/API/policy/provider/canonical data/schema change, new service,
Domain/sharing capability, dialogue persistence, paid inference or confirmation.

[Asset manifest, actual screenshots, executed checks and acceptance mapping](evidence/qh43-branding-checkpoint-20261018/README.md).
The owner must review this branded checkpoint. Keycloak VPS activation and final
merge/Jira closure remain separate explicit gates.
