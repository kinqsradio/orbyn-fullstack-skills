# Code-driven motion implementation

The approved scope extends the existing technical-illustration and UI owners with
one composition clock, trusted source components, source-bound review and optional
vector/audio/3D/simulation/effects/media adapters. The existing nested workspace,
36 skill entrypoints, target instructions and model/provider defaults stay intact.
No external authoring application or hosted rendering service is required.

## Contracts and compatibility

The [motion source guide](../../skills/orbyn-ui-design/examples/spatial-review/motion/README.md)
defines the executable core. New composition version 2 uses rational FPS,
half-open frame ranges, parent-local clocks, explicit transform/property ownership,
custom source registration and side-effect-free sampled seeks. Component readiness
and asynchronous disposal have generation/cancellation ownership. Live UI springs
keep physical velocity while offline export samples an explicit clock.

Film version 1 retains integer FPS; film version 2 explicitly accepts rational
rates. Existing V12 review schema 2 remains readable. A new motion-v1 context uses
the same review schema/store/writer, including source-anchored feedback, typed saved
parameters, reduced motion and frozen review input for export, sealing exact scene/part ranges and source
hashes in the manifest. No stale or inactive anchor is silently remapped.

## Phase ownership and actual evidence surfaces

| Phase | Executable owner | Evidence required before claiming qualification |
| --- | --- | --- |
| P0 compatibility | composition/time/profiles, prepare and existing review bridge | Old film/review reopening; sealed new profile save/reopen; stale/inactive anchors fail |
| P1 authoring/tracks | trusted component registry, keyframes/springs/path tracks, three original example domains | Repeated/reverse/nested/overlap sampling, ambiguous writer refusal, actual capture/export |
| P2 live UI/inspector | transient/commit history, presence, physical spring, pointer ownership, demo | Interrupted controls, keyboard/reduced motion, stale save and teardown races; actual browser review |
| P3 vector/interchange | vector/Lottie adapters | Matching/mismatch, strict supported feature matrix, expression/network refusal before renderer |
| P4 audio/captions | local analysis/alignment and correction adapters | Synthetic timing truth, exact input hashes, unknown/inferred words retained; actual model cells separate |
| P5 generic 3D | conditional Three component/profile | Actual raster/asset/pick/pose checks and disposal; unavailable GPU reported separately |
| P6 simulation | seeded fixed-step world/event/checkpoint adapter | Repeat/reset/backward/membership/collision controls; native/WASM runtime independently observed |
| P7 effects/quality | ordered raster graph and progressive backend | History invalidation, sample completion, loss/cancel/budget controls; WebGL/WebGPU distinguished |
| P8 media/export | local EDL and FFmpeg tools; film/composition exporter | Rational/VFR/cut/stream/frame/decode controls and requested-versus-actual boundaries |

Tests with synthetic data do not qualify an actual GPU, model weight, audio track,
codec build or human artistic quality. Optional cells require a receipt naming
source/profile/fixture/runtime and what was observed. Missing models, devices or
permissions remain explicit; an optional adapter is not a universal guarantee.
Public source does not include ignored reference clones, local media, generated
outputs or a node_modules cache. Component/render code is independently authored;
third-party runtime libraries keep their own versioned notices and terms.

## Research and licensing decisions

Reviewed upstream methods informed the scope, not a blanket source import.
Remotion's custom license and the separate skills repository's absent explicit
license preclude treating those collections as MIT source. OBS and LosslessCut
methods inform lifecycle/EDL behavior without importing GPL implementation code.
FFmpeg binary build flags/codecs determine its own redistribution obligations.
Anime/Motion/Manim/Tweakpane methods inform independent track, geometry and UI
contracts; no copies of those instruction collections are bundled. Lottie input
has a deliberately bounded expression-free feature envelope. Three and optional
rendering/simulation packages are exact-profile dependencies with separate source,
asset/decoder/binary/license closure. Librosa/WhisperX source licensing does not
authorize model weights, tokens, downloads or every language/alignment claim.

The reviewed pinned reference inventory remains local research, excluded from Git.
Shipped dependency locks and notices identify the actual adopted runtime profile;
a default-branch research SHA alone is not an installed-release qualification.

## Bounded runtime qualification

The implementation has been exercised through actual DOM/SVG composition and
rational-FPS film capture, local vector/Lottie rendering, source-bound settings
and feedback saves, local audio analysis and prepared CPU alignment, actual Jolt
WASM worlds, WebGL2 raster/effects and measured-sample WebGL/WebGPU pose export.
These are finite observed fixture/profile cells. Synthetic tests remain distinct
from browser/device/media evidence and from live-agent quality trials. Review
input snapshots and exact exporter/source hashes bind captures; earlier failed
pixel-dimension, CSP and timing controls are retained locally. The final release
receipt must distinguish the frozen candidate from earlier qualified snapshots.

The generic review server's default CSP remains script-src self. Only the explicit
graphics review adapter permits wasm-unsafe-eval for its reviewed local WASM
profile; JavaScript unsafe-eval is not enabled. Custom source modules are trusted
authored code, not a sandboxed data format. Static closure parsing does not prove
computed dependency behavior; actual export also refuses undeclared requests.
