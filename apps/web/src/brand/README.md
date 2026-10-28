# Owner-selected QH preview assets

2026-10-18: the product owner selected the geometric red-circle/black-H mark shown
in the approval message. The comparison is closed. This is the sole QH identity
used by the client; no alternate wordmark is invented or reconstructed.

- `qh-logo.png`: faithful crop/render of the same original mark in the supplied
  presentation, page 1, PDF region `[842,225,1134,481]`, at 3× (876×768). Its
  orientation is retained. On 2026-10-28, at the owner’s explicit request, the
  white matte was removed deterministically, including white antialiasing on the
  edges. Geometry and solid artwork colors are preserved; no tracing or redraw.
  The chat attachment is the visual approval reference, not claimed as a locally
  available byte-identical source file. One PNG serves desktop/mobile headers.
- `qh-bubble.png`: the supplied original iridescent artwork, downsampled to 400×300
  with its alpha/proportions intact. Decorative only on welcome/environment.
- `qh-icon.png`: 64×64 whole-mark fit with transparent padding, derived from
  the transparent logo; no glyph cropped or invented.
- `qh-home-sphere.png`: byte-identical copy of the owner-supplied
  `branding/incoming/Interface de bulles _ équilibre de vie.png` (1266×1243).
  Public home artwork, static and fully contained; its labels are part of the image.
  `QH _ Vos contextes, maîtrisés.png` supplies the composition reference only.
- `qh-environment-bubble.png`: byte-identical copy of the latest supplied
  `branding/incoming/qh_bolla_con_ombra.png` (1400×1450 RGBA), reused for the
  environment sphere and its domains. Composition reference:
  `Maquette UX de bulles iridescentes.png`. The supplied shadow and transparency
  remain intact; no artwork redraw or recoloring.

Authorization covers the owner's requested QH product preview/frontend integration
and theme preparation. No general artwork licence is invented. The full source
presentation/mockups remain private. See the versioned asset manifest and
[branding checkpoint](../../../../docs/qh-43-branding-checkpoint.md) for hashes,
transformation details, tests and the separately gated Keycloak activation.

Assets deliberately live under `src/brand`: Vite imports use existing source binds
and HMR. No new public mount, image replacement or VPS configuration is needed.
