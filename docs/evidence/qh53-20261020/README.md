# QH-53 browser and visual evidence

Actual Chromium captures of **synthetic disposable data**, with a 1672 × 941
viewport unless labelled otherwise. Full-page PNGs include any vertical overflow;
`captures.json` records their actual pixel dimensions. The frontend uses normal product mode: no mock selector.
Provider HTTP is simulated in the isolated API factory. No paid inference or
live canonical write was executed to create these captures.

The [reference catalogue](reference-catalog.json) identifies all 15 supplied images
by content, dimensions and SHA-256. Private originals are not republished. Six
current operational images were compared side by side with the actual UI at
native width; the conversation-started requirement has no separate final supplied
image and is checked against the owner's explicit textual specification.

| View | Actual capture | Review |
| --- | --- | --- |
| Discussion, empty | [Screenshot](discussion-empty.png) | Shared header/tab line, original orb, two CTA and bottom composer |
| Discussion, started | [Screenshot](discussion-started.png) | Messages, selected-message memory rectangle before composer, no overlap |
| Éléments | [Screenshot](elements.png) | Three real expandable sections and working intake |
| Modèle, available | [Screenshot](model-available.png) | Compact real model/budget cards, administrative disclosure closed |
| Modèle, unavailable | [Screenshot](model-unavailable.png) | Honest availability, no fake provider or budget |
| Conseils | [Screenshot](advice.png) | Three editable question starters; mandated tab order |
| Context settings | [Screenshot](context-settings.png) | Description, primary domain and actual rename/assignment actions |
| Global settings | [Screenshot](global-settings.png) | Four sections; existing controls only, secondary account details |
| Mobile | [Screenshot](discussion-mobile.png) | 390 × 844 viewport, reflow and reachable composer |
| Zoom 200% | [Screenshot](discussion-zoom200.png) | CSS zoom 2, no horizontal document overflow |
| Short viewport | [Screenshot](discussion-keyboard.png) | 390 × 450 viewport simulating reduced keyboard space |

Visual corrections after actual comparisons included shared header spacing,
hero/CTA scale, the three context-settings cards, global settings proportions,
readable action/composer typography and flex wrapping at zoom. The original QH orb
and logo are reused. Unsupported controls illustrated by a reference are absent:
Delete, editable profile name, notifications, language/theme and model selectors.
The mandatory single tab order takes precedence over inconsistent reference tabs.

Available model values belong to the actually authorized isolated Projet pilote.
The new budget Space remains outside the allowlist. Its unavailable-state capture
is included separately; no fixture or live allowlist was widened for a screenshot.
Budget is reread after a response and checked against the exact API capability
values. Started-chat text explicitly identifies the offline simulation; this does
not demonstrate live Mistral semantic quality.

Final six side-by-side originals and hashes are retained in the protected local
archive `.local-archive/qh53-ux-20261020/comparison-product-final/`. Public
`captures.json` binds each actual PNG to its dimensions and SHA-256. Review is
visual, not a claim of pixel identity across unsupported features or synthetic data.

## Reproduction and test evidence

Images built from the candidate with existing Dockerfiles:

```sh
sudo -n docker build -f apps/api/Dockerfile.dev -t qh53-api:review .
sudo -n docker build -f apps/web/Dockerfile.browser -t qh53-browser:review .
sudo -n docker build -f apps/web/Dockerfile.dev -t qh53-web:review .
sudo -n docker run --rm --network none --entrypoint npm qh53-browser:review \
  --workspace @qh/web run lint
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh53-api:review --browser-image qh53-browser:review \
  --frontend-image qh53-web:review --understanding --chat-sessions \
  --product-mode --browser-grep 'QH-53 complete|QH-53 consent|QH-52 product' \
  --focused-browser-only --output /tmp/new-empty-qh53-evidence
```

Local targeted results:

| Evidence | Result | What it establishes |
| --- | --- | --- |
| `foundation-targeted.log` | PASS, 6 tests and TypeScript | Tab keyboard/draft/memory, narrow 200% text, session limits and logout |
| `ui-regressions.log` | 25 PASS / 4 initial FAIL | Scoped retrieval, history, provenance/review, isolation, mobile and provider safety; failures retained honestly |
| `corrected-regressions.log` | 3 PASS / 1 residual FAIL | Both canonical proposal-warning cases and maquette actions corrected; residual missing collection link subsequently fixed |
| `navigation-final.log` | PASS, 2 tests | New Space, identity/account navigation, metadata, foreign denial; actual domain editing, back/forward and unclassified navigation |
| `lint-final3.log` | PASS | Application and test TypeScript |
| `product-final.log` | PASS, 4 browser tests + 1 real OIDC protocol test | Normal UI, description/domain/proposal persistence, Bob denial, distinct preview/consent/send, real budget, selected memory and OIDC renewal |

Each runner owns its private Docker network and tmpfs data services, never reads
the root `.env`, publishes no ports and removes only its own test resources.
Real isolated Keycloak rotation/replay/revocation is separate from simulated HTTP
provider generation. The one complete hosted CI campaign is linked on the PR at
its exact HEAD; focused runs are not substituted for that campaign.

Physical Mac password-manager/OS keyboard behavior and owner visual acceptance are
**NOT TESTED** here. The [criterion-by-criterion report](../../qh-53-definitive-ux.md)
separates implemented/tested behavior, these limits, excluded paid/provider work
and pending PR review/merge/Jira closure.
