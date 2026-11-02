# Capturing a reference

The goal is a numbered set of frames of exactly the thing to match, at a known rate, plus any ground truth the source gives. The same capture, run later on ours, is the verification.

Settle the rights first. Pass `--rights own`, `licensed` or `third-party` on every capture and every `frames.mjs` run. The decision is yours and the skill's table sets what follows; the flag records it and turns on the limits below.

| With `--rights third-party` | Why |
| --- | --- |
| `--out` must be ignored by Git, or outside any repository | Raw captures stay local |
| `--pre-js` is refused | Capture only what a normal visitor sees |
| `inspect.json` holds timing, easing and distance only | Text, fonts, colours, class names, sources and stylesheet code stay out of it |
| A sign-in redirect or a visible password field stops the run | A login wall stays closed |
| `compare.mjs` writes no diff images and refuses `--fidelity pixel`, when either side is third-party | Only the written numbers carry forward |

Selectors you pass are written into `capture.json`, `track.json`, `spec.json` and `check.md`, so a class name you type can reach those files. Use neutral selectors such as `main > section:nth-child(2)` for someone else's page, because the spec is the file that carries forward.

A page that answers 200 with a soft wall, such as "Subscribe to read" or "Verify you are human", is not detected. Read the frames, and stop if the page is not what a normal visitor sees.

On any page, HTTP 400 and above stops the run, and so does leaving the requested site. A login wall, paywall or bot check stays closed. Ask the user for a screen recording instead, and never work around one with cookies, a changed user agent or a different browser.

## A web page

Check the site's terms before capturing someone else's page.

```bash
node <skill>/scripts/capture.mjs --url https://example.com --out output/motion-match/<name>/ref \
  --rights third-party --viewport 1440x900 --selector "section.hero" --trigger load --duration 3000 \
  --track "section.hero h1, section.hero p, section.hero .cta"
```

Pass `--playwright` and `--chrome`, or set `PLAYWRIGHT_CORE` and `CHROME_PATH`. Both must already exist; nothing is installed. Prefer selectors by role or a stable class. Generated class names can change between loads.

| Motion starts when | `--trigger` | Notes |
| --- | --- | --- |
| the page loads | `load` | t = 0 is navigation |
| the section scrolls into view | `scroll` | starts just below the fold; keep `--scroll-steps` and `--scroll-ms` the same on ours |
| the page reaches a scroll position | `scroll --scroll-to 1800` | compare by `scrollY` in `track.json` |
| the pointer enters an element | `hover --target ".card"` | `--hover-at 0.2,0.8` picks the spot |
| the pointer leaves | `leave --pre-hover ".card"` | hovers first, then moves to `--leave-to` |
| something follows the pointer | `move --target ".card" --path "0.1,0.1;0.9,0.1"` | `--path-ms` per leg |
| something is dragged | `drag --target ".rail" --path "0.3,0.5;0.7,0.5"` | released while moving, so fling velocity is not zero |
| something is clicked | `click --target "button[aria-label=Menu]"` | add `--pre-js` on our own page to reach the state first |
| it loops | `none` | capture two or three periods and measure the period |

Useful options:

- `--clock virtual` is the default. The page runs on a clock advanced frame by frame, so every frame is exact at any `--fps`, for CSS and JavaScript motion alike, and two captures of one page are identical. `--seed N` seeds `Math.random`.
- `--clock real` writes `track.json` only, no frames. Use it to check that timing on the real clock agrees.
- `--reduced-motion reduce` shows the reduced path. Match that too when the project cares.
- `--clip x,y,w,h` when the element moves outside its resting box. `--pad 24` keeps shadows and overshoot in the crop.

A canvas on our own page is verified by frames the same way: the virtual clock drives its `requestAnimationFrame` loop, so the same seed gives the same picture. This skill reads no shader or scene data.

| File | Use |
| --- | --- |
| `inspect.json › animations` | CSS, transition and Web Animations timing with keyframes. For CSS animations `timing.easing` is `linear`, and the real easing sits on each keyframe. A finished animation with no fill is gone by the time this runs, so read `track.json` too. |
| `inspect.json › nodes` | Own or licensed pages only: rect and computed styles of up to 150 nodes |
| `track.json` | One sample per page frame per tracked selector: `x y w h opacity transform`. Feed it to `spec.mjs` and `easing.mjs`. |
| `frames/`, `frames.json` | The pictures; `triggerFrame` is where t = 0 sits |
| `capture.json` | The settings, read by `compare.mjs` to refuse a mismatched pair |

Limits: iframes are not inspected, and workers run on the real clock without a seed.

## A video, screen recording or gif

Use a file the user supplied. `frames.mjs` reads local files and refuses web addresses, so it can never download a video. A streaming link, or anything behind DRM, needs a screen recording from the user, and the same rights apply to it.

```bash
node <skill>/scripts/frames.mjs --in ref.mp4 --probe
node <skill>/scripts/frames.mjs --in ref.mp4 --out output/motion-match/<name>/ref/frames --rights third-party \
  --fps 25 --start 0:12 --end 0:15.5 --crop 320,180,1280,720
node <skill>/scripts/sheet.mjs filmstrip --frames output/motion-match/<name>/ref/frames --out output/motion-match/<name>/ref/sheets
```

- Extract a few frames at 2 fps to choose the range and crop, then re-extract at 25 to 30 fps. A gif uses its own rate, which `--probe` prints.
- Crop out browser chrome, cursors and recorder overlays. Use `--width` so both sides end up the same size.
- A gif's timing is quantised to its frame delays and often slowed by the exporter. Treat it as plus or minus one frame.
- A screen recording may have a non-integer scale. Convert distances with `distance_css = distance_video × (viewport_width / crop_width)`.

## Prototype and animation files

A Lottie file holds its layers, keyframes and bezier handles, so read those numbers for a file you may use. For a Figma or similar prototype, export a video and use the video path. A video made with the [code-only rule](../../technical-illustration/references/code-only.md) may not embed any of these files.

## Capturing ours

Reuse the reference command exactly, changing only `--url`, `--out` and, where it differs, `--rights`. Keep `--fps`, `--duration`, `--pre-roll`, the trigger, `--clock` and `--seed` identical. `compare.mjs` fails its setup gate otherwise. If the reference was a video, choose a viewport that makes the cropped element the same pixel size, or pass `--rescale` to `compare.mjs`, which is slightly lossy.
