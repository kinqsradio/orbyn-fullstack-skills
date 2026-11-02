# Stageshow kit (adapted)

The kit, examples, playground and verification tools behind the
`product-illustration` skill, adapted from Stageshow by Benji Taylor. Start with
the skill's `SKILL.md`; this file covers running the folder.

## Preview

Requires Node 20.19 or later. Copy this folder outside the library first, so its
`node_modules` never lands in the skill tree. Then, in the copy:

```sh
npm install --ignore-scripts
npm run dev
```

Vite serves on 127.0.0.1; open the local URL it prints.

The playground includes the gold examples, visual styles and labeled bad/good
teaching pairs. Pause, replay, slow down, or advance one frame. Phone changes the
available width to 358px; Reduced motion shows each scene's still.

## Use the kit

Copy `kit/` into your React project. Its components import their own CSS:

```tsx
import { Stage, Window, type Act } from './kit'
```

Copy an example as a starting point. Keep its relative kit imports and adapt the
composition and look to your product. These are authored illustrations: a scripted
`a.click()` draws feedback; `a.set()` changes the scene.

The kit supports React 18 and later and needs no third-party animation runtime. The
playground uses Vite; filming uses `playwright-core` and locally installed Chrome
(or `CHROME_PATH`). Those tools are not runtime dependencies of a demo.

## Verify

```sh
npm run typecheck
npm run check:css
node scripts/film.mjs '<your URL>' --select '.your-demo' --gate
node scripts/film.mjs '<your URL>' --select '.your-demo' --width 390 --gate
node scripts/film.mjs '<your URL>' --select '.your-demo' --states --gate
```

For the bundled viewer, use `?capture=hero-demo` as the filming URL and `#example`
as the selector. No automated clean result replaces watching the motion.

## Contents

- `kit/`: portable React source and styles.
- `examples/`: gold scenes and reference specimens.
- `teaching/`: explicitly flawed/corrected pairs, separate from gold.
- `scripts/`: verification tools, independent of the host's markup.
- `playground/`: the standalone local viewer.

`SOURCE.md` records what was selected, excluded and changed. See `NOTICE.md` for notices.
