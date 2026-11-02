# Selected Stageshow support source record

This is an inactive provenance record, not an agent entrypoint. Selected kit, example,
playground and verification source derives from Stageshow by Benji Taylor (MIT) at
<https://github.com/benjitaylor/skills/tree/802057409787133703c56001080169e347305572/stageshow>.
The bundled `LICENSE` is the upstream notice, unchanged. `LICENSE-Orbyn.txt` covers Orbyn
adaptations and additions. Use the maintained `product-illustration` skill.
`source-manifest.json` lists every file with its upstream path and original and
maintained hashes.

## Selected

`kit/` (except `kit/brands/`), `teaching/`, `scripts/`, `playground/`, `LICENSE`,
`NOTICE.md` (rewritten), `README.md` (rewritten), `package.json`, and these examples:
ai-cards, ai-chat, annotations, backgrounds, bento, calendar, chart-scrub, choreography,
chrome, close-up, controls, corner-chip, cursor-morph, cursor-resize, cursors, dark-bento,
dark-hero, device-pair, dynamic-island (renamed status-island), fade-crop, form-error,
freeform-drag, glass, hero-demo, hero-grid, kit-extras, loading, looks, many-of-one,
messages, opposite-corners, overlap, panel-annotation, parts, payout-flow, phone-touch,
phones, presence, reorder, ruled-bento, share, stacked-cards, staggered-bento, static-card,
story, subscriptions, swipe, table-edit, tilted-stack, upload, window-row.

The upstream guides in `references/` are maintained one level up, beside the skill's
entrypoint, in `../../` (see `guides.json`). Upstream `SKILL.md` is replaced by the
skill entrypoint and `../../gold-examples.md`.

## Excluded, never copied

- `assets/app-icons.ts`: upstream's notice says app bundle artwork is outside its MIT grant.
- `kit/brands/`: third-party marks, `SOURCES.md` and their licence files.
- `examples/brand-marks`, `examples/monochrome`.
- Real-product studies: `examples/figma`, `linear`, `slack`, `raycast`, `finder`,
  `finder-glass`, `spotify`, `notion`, `gmail`, `google-calendar`, `google-docs`,
  `powerpoint`, `excel`, `wikipedia` (with its photographs), `telegram`, `imessage`.
- `.github/assets/stageshow.png`, `package-lock.json`, the optional `portless`
  dependency, upstream `AGENTS.md` and install instructions.

## Changed

- `BrandMark` displays a logo the consumer supplies; there is no bundled registry.
- Real company and product names became invented ones; URLs use the reserved
  `.example` domain. Named-device and OS API values became generic: `ios.tsx` is
  `keyboard.tsx`, `frame="android"` is `punch`, `app="imessage"` is `native`,
  `tone="ios"` is `monogram`, `faceid` is `facescan`, `Mac*` cursors are `Sys*`.
- Status bar glyphs and the desktop arrow were redrawn from plain geometry, replacing
  paths upstream describes as taken or measured from a platform kit.
- Named font stacks became `system-ui` and `ui-monospace`.
- `examples/looks/radix.css` became `technical.css`, with original token values.
- `hero-demo` replaces a real terminal product's welcome box and copied toolbar icons
  with an invented tool and Lucide icons. Its faults against upstream's own gate were
  fixed, including a new compact layout.
- `annotations` replaces a photograph with an original vector drawing.
- `scripts/dev.mjs` runs plain Vite on 127.0.0.1. The selection-drift warning in
  `kit/act.ts` now applies only to I-beam drags, as its message says.
- `scripts/film-checks.mjs` keeps a list of real company names as detection data only.

Upstream install commands and host-specific steps are not imported or activated. Source
identity is not runtime proof.
