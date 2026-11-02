# Selected reanimate source record

This is an inactive provenance record, not an agent entrypoint. Part of this skill derives
from reanimate by Niaz Morshed (MIT) at
<https://github.com/NiazMorshed2007/reanimate/tree/3f7a55a2986a84ca2173e86ee9127eefe31d046d/skills/reanimate>.
The bundled `LICENSE` is the upstream notice, unchanged, and is also at the skill root.
`LICENSE-Orbyn.txt` covers Orbyn adaptations and additions. Use the maintained
`motion-match` skill. `source-manifest.json` lists every skill file with its upstream path
and original and maintained hashes.

## Kept and adapted

`SKILL.md` (rewritten); `references/capture.md`, `analysis.md`, `implementation.md` and
`verify.md`; `scripts/capture.ts`, `compare.ts`, `easing.ts`, `frames.ts`, `lib.ts`,
`sheet.ts` and `inpage/clock.js`, as Node 22 ESM. `inpage/inspect.mjs` is the inspection
code from `capture.ts`, moved out and reduced.

## Original to Orbyn

`scripts/png.mjs`, `scripts/diff.mjs`, `scripts/spec.mjs` and `tests/`.

## Excluded, never copied

- `scripts/gl.ts`, `scripts/inpage/gl-hooks.js` and `references/webgl.md`, with every `--gl`
  option: they trace and extract shader source.
- The `--assets` option: it downloads a page's models, textures, shaders and scripts.
- `scripts/setup.sh`, `scripts/bun.lock`, `scripts/package.json`: installers and dependencies.
- `site/`, `README.md`, `.github/` and any example that names a real company.
- `--playback-rate`, `--gpu`, `--blur`, `--no-video`, `--headed`, `--no-workers`, the CDP worker
  seeding and the recorded video, along with library detection and renderer reporting.
  The virtual clock replaces the first and the worker wait stays.

## Changed

- Rights: a required `--rights` on capture and frames, third-party limits in code, and a rights
  section that leads the entrypoint. Upstream's "clone" and pixel-faithful defaults for any
  reference are gone.
- Runtime: Bun and TypeScript became Node ESM. Playwright, ffmpeg-static, pixelmatch and pngjs
  became a supplied playwright-core and Chrome, system ffmpeg and original code. Nothing is
  installed. `sheet` draws with an original bitmap font and needs no browser.
- `inpage/clock.js` became `clock.mjs`, because the library inventory takes no `.js` files.
  Virtual time now runs from the first script at a fixed instant, and a new animation counts
  from zero, so two captures are identical.
- `compare`: auto-align no longer runs by default and is refused between two captures, because it
  hid late starts. It now uses activity curves. Setup differences and failures exit non-zero.
- `easing`: searches delay and duration together and fits springs.
- Arguments are strict, output stays inside `--root`, and earlier output is not replaced silently.

Upstream install commands and host-specific steps are not imported or activated. Source
identity is not runtime proof.
