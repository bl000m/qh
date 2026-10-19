# QH-50 — official maquette implementation and typed-name confirmation

2026-10-19. Same branch/PR #17, after verified `4c3b888`. Earlier commits, reports,
CI and captures are preserved. This increment changes frontend presentation and
reuses owner organization APIs; it adds no backend, migration or canonical mutation.
The Product Contract and [ADR 0008](adr/0008-personal-organization-and-owner-review.md#later-owner-amendment--three-official-maquettes-2026-10-19)
record the owner decision. It does not authorize merge or Jira DONE.

## Verified visual reference

The images were opened and identified by their actual content, not just filenames.
They remain in the owner's private `branding/incoming/QH-design 2` directory.

| Private file | Verified page | Layout reference |
| --- | --- | --- |
| Image ChatGPT 19 oct. 2026, 14_50_18-1.png | Mon environnement | White header/settings, strong left title, bordered domain/resume panels, equal cards, round arrows, compact sorting/create controls |
| Image ChatGPT 19 oct. 2026, 14_50_21-2.png | Domain | Breadcrumb, large centered original bubble and title, responsive Space cards, Ouvrir action, sort/create header |
| Image ChatGPT 19 oct. 2026, 14_50_23-3.png | Context Space | Bubble/title/actions, primary chat, secondary Sources/Compréhension/Détails column, bottom composer and compact provider controls |

The original approved bubble/logo bytes are unchanged. Discreet CSS hue/tint variation
is presentation only. Domain/Space names, membership, response references, validation
states and source content come from authorized data. The screenshots use the existing
disposable browser harness; populated comparison domains do not write VPS demo data.

## Actual functional boundaries

`SpaceActions` stages primary/secondary memberships in a native accessible dialog and
saves through the same owner-scoped organization version. A true 409 leaves the dialog
open, explains non-publication and offers explicit reload. No automatic retry/overwrite.
The first opening can materialize virtual organization version 0 as version 1; the client
now loads the editor only after the authorized Space opening event settles, avoiding a
false conflict without weakening server concurrency checks. No backend change is needed.

The desktop support column offers actual answer-specific sources, the existing lazy
canonical explorer/review and Space metadata. Mobile support is a separate view; it hides
rather than unmounts the conversation. Choosing an answer's sources still opens the exact
canonical response modal, distinct from all supplied revisions. No new semantic inference,
retrieval, provider availability or persisted conversation follows this presentation.

## Supprimer: exact name, no destructive backend

[QH-9's lifecycle boundary](qh-9-context-spaces.md#deletion-and-lifecycle-boundary)
provides neither DELETE nor archive/status mutation. The confirmation names the target,
requires the full literal name and explains that no content is removed. Empty/partial,
case-changed, extra-space or Unicode-normalized alternatives do not count as an exact
match. Enter never submits a destructive request. Even an exact match leaves final
execution disabled because no approved lifecycle/backend exists. Cancel/Escape restore
focus, and switching Spaces resets the dialog. This is prepared UX, **not implemented
deletion**, and never displays fake success.

Before enabling execution the owner must choose recoverable archive versus deletion,
retention and reconstruction guarantees, impacts on Sources/revisions/graph/outbox/shares,
policy actions and concurrent target/name checks. A recoverable archive is a candidate,
not an approved lifecycle; inactive-row test fixtures do not define its access semantics.
No new ticket or destructive endpoint is created by this increment.

## Visual comparison and honest differences

Desktop captures use 1448×1086, matching the references; mobile uses 390×844, with
additional 320px/200% text checks. Private side-by-side material retains original reference
images and untouched actual screenshots, with page mapping, hashes and layout bounds.
These are developer comparisons, not a fabricated owner acceptance or numerical pixel score.

Known intentional differences:

- Real Space counts/names and actual mock/provider output replace illustrative examples.
  No fake health advice, additional demo Space, avatar initials or canonical description
  is inserted. The current metadata API has no description field, so descriptions are omitted.
- Required proposal opt-in and canonical epistemic warnings remain visible even where the
  mockup omits a control or presents an illustrative answer. Mock output is explicitly labeled.
- Arial/Helvetica/system fallback is used with available bold metrics; the original mockup's
  font source was not supplied. No unapproved external font download is introduced.
- Header logout remains a real accessible action rather than an invented named profile.
  Technical identity/metadata and operational limits remain available by disclosure.
- Supprimer opens the complete guarded confirmation, but execution is deliberately unavailable.
  This is the only requested action awaiting an approved backend lifecycle.

Executed checks and exact PR CI outcomes are recorded below/at publication. Existing native,
OIDC, review and historical audit evidence is retained; only affected local checks are repeated.
The unmodified required workflow still checks every published HEAD. The Keycloak theme/runtime,
provider settings, persistent canonical data and ledgers are outside this visual increment.

## Executed refinement verification

The final focused run used the existing disposable browser harness, real Keycloak/PKCE,
PostgreSQL and Neo4j, with HTTP-simulated provider paths only:

```bash
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh50-api:review --browser-image qh50-browser:maquette \
  --frontend-image qh50-web:maquette --understanding --qh-login-theme --chat-sessions \
  --browser-grep 'approved maquettes|chat follows latest|narrow mobile|chat composer leads' \
  --focused-browser-only --output .local-archive/qh50-maquettes-final
```

| Criterion | Classification / observed result |
| --- | --- |
| Three reference pages and actual content | Implemented/tested, PASS: six captures; desktop 1448×1086 and mobile 390×844; all seven home domain cards fit the desktop viewport and the domain hero is centered within 2px |
| Primary/secondary domain assignment | Implemented/tested, PASS: real isolated PUT, primary selection, simulated 409, explicit reload, keyboard-focus restoration, successful versioned save and origin breadcrumb |
| Named counter-confirmation | Implemented/tested, PASS: partial/exact input, Enter and Escape, zero DELETE requests; literal Unicode/case/space regressions in the pure helper test |
| Destructive execution | Not implemented: final action remains disabled even after an exact name match; approved lifecycle/backend is a prerequisite, not bypassed by the UI |
| Conversation, sources and mobile support | Implemented/tested, PASS: latest-answer follow, deliberate manual scroll, answer-specific source modal and focus, support navigation retaining the answer, no accidental overflow at 320px/200% text |
| Empty domain and isolation | Implemented/tested, PASS: one empty-state CTA, actual Bob login denied access to Alice's Space and no assignment/delete controls disclosed |
| Build/static | PASS: Docker TypeScript app/test checks and production Vite build; 2 no-network helper/reflow tests, 4.6s |
| Final focused browser run | PASS: 4 tests, 51.3s; omitted full OIDC/outage/restore phases explicitly NOT TESTED by this focused invocation |
| Prior affected checks | PASS in earlier refinement runs: immutable QH-46 confirm/reject/correct, complete hierarchical navigation/owner editing/recent-used ordering; counts overlap and are not summed |
| Mandatory published-HEAD CI | Unmodified quality/native-integration/browser/OIDC jobs remain required; the PR rollup and delivery comment record the exact final run and outcome |
| Preservation | PASS: read-only original SQL-row hashes, identities, Spaces, graph/outbox state, triggers, six existing containers/configuration hashes, protected files and unchanged Mistral ledger |
| Owner acceptance, merge and Jira closure | Pending: this is a technical review delivery, not owner approval or DONE |

The first focused comparisons exposed an organization-version race on first opening and
an overlarge intrinsic card width that hid the seventh domain. Both were corrected in
the frontend and verified in the final run. A mobile support toggle initially pushed the
composer below its established leading-position limit; it now follows the chat while the
support view retains the conversation. No server concurrency or security guard was relaxed.

Private review material is indexed at
`.local-archive/qh50-maquette-comparison-20261019/README.md`; `comparison.html` contains
unaltered originals and final screenshots side by side, and `manifest.json` seals their
hashes. The previous review index/captures remain preserved. No private image is published
in Git or uploaded as a hosted CI artifact.

Observed residual differences are explicit: the domain page is shorter without the
mockup's unavailable description; the chat can be taller due to mandatory opt-in, honest
mock labeling and actual response provenance; controls use real available actions and
owner data rather than the reference's sample profile/answers. Layout/type spacing was
refined after viewing the original and actual captures. The exact original bubble stays
unchanged; CSS tint cannot reproduce a different photographic source/lighting, and no
replacement brand image was generated. These limits remain for owner visual review.

### Required-CI regression correction

The first updated-HEAD CI (`09e1fe0`, run `39260364922`) passed quality, OIDC and
745 native integration tests with zero skips, but its browser phase correctly failed
three checks (65 passed). Two tests needed exact breadcrumb matching and attachment
synchronization before selecting the mobile support view. A real initial organization
hydration race could also reset the first Space page after pagination: initial listing
now waits for that metadata read. The regression explicitly holds/releases both requests,
requires exactly one initial page request, preserves both pages and verifies cursor exhaustion.
No timeout was raised and no assertion/job was dropped.

The four affected/recovery browser checks then passed locally, **4 PASS / 33.9s**,
with production TypeScript/build checks, real isolated OIDC/SQL/graph, mobile browse,
Alice/Bob and sanitized API failures. Artifacts are retained in
`.local-archive/qh50-maquette-ci-regressions/`. No layout/asset/canonical/backend change
follows this correction; the final visual captures above remain representative.
Only the final published HEAD's complete mandatory rollup can establish CI readiness.
