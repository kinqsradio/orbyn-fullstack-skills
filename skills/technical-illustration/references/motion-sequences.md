# Review deterministic motion across scenes and tasks

Choose motion for the task: an interface transition explains a state change; an
onboarding/explainer guides attention; a data reveal conveys an actual comparison;
a 3D sequence explains a spatial relationship; a kinetic film carries a timed
message. Reuse the UI, chart, illustration or media owner. Motion does not require
Scenario, generated music, a video export or the same visual style everywhere.

## Specify time, content and interruption

Keep a pure `sample(time, scenario, reducedMotion)` model with explicit duration,
scene intervals, transition/easing, camera/part/layer state, captions and the actual
content/data revision. The render consumes that model. Never accumulate transforms
from prior seeks or use random/real wall time without a recorded seed/input.
Define cut boundaries (which scene owns the exact boundary), backward seeking,
repeated seek, end/loop and missing media. Test them, including a bad discontinuity
or stale asset control. A mechanical angle cycle alone is not a multi-scene story.

Interaction takes over playback; pause and release the owned animation task before
scrubbing, annotation or a new command. A restored review starts paused. Pause on
background/page exit and clean up owned frames/listeners. Reduced motion uses a
meaningful static alternative/manual seeking, without blocking information or
essential controls. Do not autoplay audio. Honour the target's accessibility needs;
fast cutting or constant movement is a style decision, not a universal quality gate.
Check flashing, movement-triggered discomfort, focus, readable dwell and pause/stop.

For text, wait for actual font readiness, fit every intended aspect/viewport, reserve
safe areas for captions and keep reading order and contrast. Do not treat a measured
fraction of moving frames as accessibility or readability evidence. Captions must
follow the real spoken/audible content when audio exists; the V12 example's silent
explanatory text is not evidence of captioning an audio track. Provide transcript
and meaningful content without relying on motion or sound alone.

## Persist and qualify the actual delivery

Use [durable review](../../orbyn-ui-design/references/review-packages.md). Save source,
settings, model/media hashes, scene/time/part/camera/layers, comments, dispositions
and design decisions with the consuming repo's actual design owner. A screenshot
coordinate cannot identify a moving 3D part. The
[original spatial example](../../orbyn-ui-design/examples/spatial-review/README.md)
provides four small executable motion modes and source-bound 3D review/replay;
it does not implement a general media editor or full video export.

For a chosen film delivery, declare actual frame rate/duration/resolution/aspect,
frame count, codec/container, audio sync/loudness and caption/transcript requirements.
If using subframe samples/motion blur, sample within valid scene bounds and inspect
cuts; blur must not blend unrelated scenes or hide wrong text/geometry. Keep image,
font, music and media rights/source hashes. Generation, paid providers and external
uploads need the applicable task authority; no source research enables them.

Use bounded render workers, frame/time budgets, cancellation and retained first
failures. Inspect opening, cuts, text, relevant error states and the final frame;
qualify encode/decode/playback with the actual installed runtime and intended
consumer. A DOM preview is not proof of a finished video, audio correctness, WebGL,
native rendering or complete accessibility. State unperformed export/platform
cells. Existing behavior/a11y/pixel tests remain the regression owners; never
blindly accept newly generated baselines.

Reviewed inspiration: Scenario's [kinetic film method](https://www.scenario.com/explorations/kinetic-film/),
ZIP SHA-256 `2217ab5dbd452185a5c3c1509994da46b1ac20d2ebeaa888536244372ce73ebf`
reviewed 30 October 2026. No license was found in the reviewed ZIP: no source code,
fonts, assets or instructions are redistributed. This local method is independently
authored. Accessibility source/update pointers:
[WCAG pause/stop/hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html),
[animation from interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html),
[three flashes](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
[captions](https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded.html).
The operative method above works offline; links supply attribution and updates.
