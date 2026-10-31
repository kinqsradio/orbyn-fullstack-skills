# Code-driven motion support

This is reusable source owned by technical-illustration and orbyn-ui-design, not a
new skill, provider or mandatory installation. Keep the consuming project's own
brand, design owner, instructions, existing stack and review files. The outer
library/nested-target layout is unchanged.

## Core authoring

`composition.mjs` accepts inert version-2 data with rational `fps`, a source
revision, integer frame duration and bounded clips. `examples.mjs` contains three
independently authored domains: engineering delivery, an orbital diagram and a
greenhouse study. Register new trusted components in source through
`createRegistry().register(id, component)`; the examples are not a closed set.
There are no saved import paths, JavaScript expressions, HTML strings or eval.

Each component provides pure `sample(clip)`, synchronous `mount(host,state)` and
`update(handle,state)`, awaitable `ready(handle,signal)` and awaitable
`dispose(handle)`, plus its explicit dependency records. Sampling cannot fetch,
mutate world state, play audio or invoke callbacks. Readiness owns fonts, images,
models, shaders and backend completion; returning a promise is not evidence that a
backend was actually qualified. Dispose must settle pending owned work and free
resources. `createPlayer().seek(frame)` awaits readiness, aborts the previous
request, serializes mount/unmount ownership and rejects stale results. Await
`player.dispose()` before retiring an export or GPU surface.

Clip `start` and `duration` are half-open frame intervals in its parent's local
clock. The root uses project frames. A child receives `(parentFrame-start)*rate +
offset`; parents gate visibility. Positive rates are bounded to .001–1000; signed
offsets permit pre-roll. Parent transforms compose as 2D affine matrices and
parent opacity multiplies. Siblings use explicit zIndex, then stable ID order.
Sampling at durationFrames is an explicit terminal request displaying the final
frame; export emits only frames 0 through durationFrames-1. Repeated, backward and
out-of-order seeks do not execute events. `reducedMotion` reaches every custom
component as well as its tracks; a component owns its meaningful static state.

`tracks.mjs` supports scalar keyframes, linear/smooth/in/out easing, analytically
sampled under/critical/over-damped springs with initial velocity, length-based
polyline paths, stagger and label resolution for trusted source authoring.
`resolveLabels` converts labels to numbers before constructing inert clips. Track
times use local seconds. A property has one highest-priority replacement writer;
equal-priority replacements fail. Explicit additive scalar writers can contribute.
A path owns both transform x and y, so simultaneous x/y writers fail. No implicit
blending, world-space write conversion or transform-order guessing occurs.

`time.mjs` reduces rational rates, computes direct frame/time addresses and uses
BigInt arithmetic for integer audio-sample addresses. Rounding is explicit:
frame selection defaults to floor, audio samples to nearest with ties upward.
Use direct addresses rather than repeatedly rounding one-frame increments. The
existing film model keeps version 1 with integer FPS; version 2 explicitly accepts
rational FPS and the same shot/primitive envelope. A composition is a separate
version-2 contract, not a silent reinterpretation of a film spec.

## Preview, interaction and durable review

From the library root with existing Python 3.11+ and Node:

```sh
python3 skills/orbyn-ui-design/examples/spatial-review/prepare.py --destination /ABS/CONSUMER/docs/design/motion-review --motion-example 0
python3 /ABS/CONSUMER/docs/design/motion-review/serve.py --package /ABS/CONSUMER/docs/design/motion-review
```

Open the reported loopback address followed by `motion/demo.html`. Examples 0–2
are selectable at preparation. Source previews without a bridge can switch all
three, but cannot claim durable saves. A prepared review binds one composition;
changing its source requires a fresh review round rather than retargeting comments.
No npm cache, node_modules, hidden file, output cache or test fixture is copied.
Unselected source-authoring study inputs and optional setup/CLI tools stay in the
outer library; a selected custom module and project are copied and sealed explicitly.
Optional graphics dependencies and Python audio/model setup tools are prepared
separately with their reviewed profiles; the normal UI package does not copy model
download/setup scripts or their environment requirements.

Source-declared `bindings` name a known clip property, numeric range/step, color
or enum and default. Saved `parameters` must match exactly; unknown paths, out-of-
range values, track-writer conflicts and timing changes to parent clocks fail.
Radius, type size, orbit rate and color are real saved examples. Values update the
sampled clip, undo/reset and existing source-bound review, never executable imports.

The demo has frame scrub/play/pause, responsive DOM/SVG, drag and keyboard camera
takeover, reduced motion, interrupted presence, undo/redo/reset and save/reopen.
The live spring preserves velocity when its target changes. The export sampler
is independent of that wall-clock interaction. One pointer owns a drag;
interrupted exits use generation tokens; hidden controls restore focus to their
trigger. `inspector.mjs` separates transient edits from committed history and
rejects a save completion when newer edits exist. These helpers do not replace a
consumer framework's focus, routing or accessibility requirements.

Existing V12 review schema-2 documents and film version-1 packages retain their
old validators. New motion packages explicitly use prototype ID
`motion-composition-v1` and context profile `motion-v1`, while retaining the same
schema-2 `review.json`, loopback writer, revision conflict protocol and design
reconciliation. FPS, scene/part ranges and anchor identity are in fingerprinted
targets; `motion-project.json` is hash-bound. Stale or inactive parts are rejected;
no fuzzy anchor migration or second persistence store is introduced. Feedback
captures exact part/frame/camera/parameters and reduced-motion preference on first
input; posting, durable save/reopen and paused restore use the same pending/comments
records. A submitted review is immutable and uses the existing decision reconciler.

## Export and inspect

```sh
node skills/orbyn-ui-design/examples/spatial-review/motion/export-composition.mjs --package /ABS/CONSUMER/docs/design/motion-review --output /ABS/CONSUMER/output/fresh-export --playwright /ABS/EXISTING/playwright/index.mjs --chrome /ABS/EXISTING/chrome
```

The caller supplies existing tools. This path captures the same registered DOM/SVG
scene after readiness, uses exact rational FFmpeg rate strings, verifies source
hashes before/after, probes the encoded frame count/time and fully decodes output.
It refuses existing output and records failure/cancellation separately from
success. It exports a silent scene sequence; audio/footage use the explicit media
adapter. An existing regular `review.json` is frozen, copied and hashed as
`review-input.json`; its validated settings are restored through the same trusted
preview API before capture. Concurrent later review writes do not silently retarget
the export. `--from-frame N --frames COUNT` selects a bounded source window without
retiming the project, and receipts distinguish source frame addresses from output
frame numbers. Graphics profiles additionally require explicit `--fps RATE` and
`--mode raster|effects|pathtrace|webgpu`; each progressive frame records its actual
completion/sample receipt and canvas size. A pose sequence is not a full-film claim. Existing film export remains available for music-led primitive films.
System fonts and actual GPU/audio/media profiles need separate qualification.
A successful encode does not establish aesthetics, accessibility or product parity.

`statechart.mjs` samples the exact supplied numbered occurrences, including
revisits, and requires each incoming edge to connect those consecutive records.
Its SVG and full text records retain labels/guards and evidence boundaries. Feed
actual chart/replay output; do not manufacture a checker verdict from an animation.

Run core tests without optional dependencies:

```sh
node --test skills/orbyn-ui-design/examples/spatial-review/motion/core.test.mjs
python3 -m unittest discover -s tests -p test_motion_composition.py
```

Optional vector, audio, media and graphics modules have their own explicit
supported envelope, tests and qualification receipts. Ordinary UI work never
waits for an optional GPU, ASR model, native simulation or authoring app.

## A new consumer domain

```sh
python3 skills/orbyn-ui-design/examples/spatial-review/prepare.py --destination /ABS/CONSUMER/docs/design/coast-review --motion-project /ABS/CONSUMER/coast.json --component-source /ABS/CONSUMER/coast.mjs
```

The JSON uses the same inert composition schema. The separately selected trusted
module exports `registerCustomComponents(registry)` and returns that registry.
`custom-domain.example.json` and `custom-domain.example.mjs` demonstrate a fourth
independent coastal domain, numeric/color/enum controls and a packaged local clock
import. The helper copies and hashes reviewed source; Node's VM parser checks its
static module closure without evaluating the module. Static imports must resolve
to packaged local `.mjs` files; missing, foreign or bare imports fail. This is not
a JavaScript sandbox and cannot prove computed fetch/import behavior. Review the
trusted source and its declared assets; actual export also rejects undeclared
runtime network requests. No import path or code is accepted from saved JSON.

## Optional graphics review

Build the explicitly selected local graphics profile using its own library helper,
then pass `--graphics-profile /ABS/BUILT_PROFILE` to prepare a fresh package. The
helper verifies the reviewed release lock, exact module/sidecar hashes and bounded
size, and retains notices plus the lock in `motion/graphics-profile/`. It does not
install dependencies. The graphics-v1 context uses the same schema-2 review writer
for exact picked part, camera projection, timeline/mode and four bounded material/
light controls. Body-membership anchors follow actual tick/event order, including
removal and recreation; inactive/stale picks refuse to save. Raster, progressive
WebGL and WebGPU qualify separately with their observed device/profile.

For local audio analysis, prepared alignment models, reviewed corrections and
music-led source artifacts, use [the audio workflow](audio-workflow.md).

## Vector authoring and bounded interchange

[vector.mjs](vector.mjs) samples independently authored contours, aligned morphs
and mathematical explainers. [lottie.mjs](lottie.mjs) exposes the executable
`LOTTIE_SUBSET` supported/refused feature matrix: supported vector shape/keyframe
data is sampled without an expression-capable player, while expressions, remote
assets, unsupported masks/mattes/text/font features and excessive budgets refuse
before rendering. This is a bounded interchange route, not every Lottie feature.
The original `vector-study.json` and trusted `vector-study.mjs` remain in the outer
library as source-authoring inputs; select them explicitly for a fresh package:

```sh
python3 skills/orbyn-ui-design/examples/spatial-review/prepare.py --destination /ABS/CONSUMER/docs/design/vector-review --motion-project /ABS/LIBRARY/skills/orbyn-ui-design/examples/spatial-review/motion/vector-study.json --component-source /ABS/LIBRARY/skills/orbyn-ui-design/examples/spatial-review/motion/vector-study.mjs
```

For supplied footage, non-destructive EDLs, audio/stream selection, captions,
measured loudness and exact requested-versus-actual cut behavior, use
[repo-owned media editing](MEDIA.md). This remains separate from authoring a scene.
