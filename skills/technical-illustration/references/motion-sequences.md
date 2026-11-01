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
Check movement-triggered discomfort, focus, readable dwell and pause/stop, and
[measure flashing](#check-flashing-on-the-rendered-file) on the rendered file.

For text, wait for actual font readiness, fit every intended aspect/viewport, reserve
safe areas for captions and keep reading order and contrast. Do not treat a measured
fraction of moving frames as accessibility or readability evidence. Captions must
follow the real spoken/audible content when audio exists; the V12 example's silent
explanatory text is not evidence of captioning an audio track. Provide transcript
and meaningful content without relying on motion or sound alone.

## Check flashing on the rendered file

Run the check on the encoded video, since grading, blur and encoding all change
what flashes. It needs existing FFmpeg and writes nothing:

```sh
python3 skills/technical-illustration/scripts/flash-check.py /ABS/film.mp4
```

It prints JSON and exits 0 at three flashes a second or fewer, 1 above that, and 2
when it cannot read the video. `startsAtSeconds` and `windowCell` locate the worst
second. It applies the WCAG 2.2 thresholds: a general flash is an opposing pair of
luminance swings of at least 10% with the darker state below 0.80; a red flash is
an opposing pair where one state is saturated red and chromaticity moves more than
0.2. Either kind counts only over more than 25% of a window one third of the frame
each way, which estimates a 10 degree field. A localized flash therefore fails even
when the frame average barely moves. A 5 Hz strobe on a third-by-third patch exits 1;
the same strobe on a small patch exits 0.

Treat a pass as a screen. It is not a Harding or PEAT certification, it averages
away detail finer than its grid, and it assumes the frame fills the screen. Fix a
failure in the source, then render and check again.

## Persist and qualify the actual delivery

Use [durable review](../../orbyn-ui-design/references/review-packages.md). Save source,
settings, model/media hashes, scene/time/part/camera/layers, comments, dispositions
and design decisions with the consuming repo's actual design owner. A screenshot
coordinate cannot identify a moving 3D part. The
[original spatial example](../../orbyn-ui-design/examples/spatial-review/README.md)
provides four small executable motion modes and source-bound 3D review/replay;
it includes the [MP4 exporter](../../orbyn-ui-design/examples/spatial-review/motion-films.md)
for the same film stage. This is not a general media editor or a copy of all source blocks.

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

Separate export evidence: full video/audio decode catches unreadable streams;
packet presentation/decode timestamps and spacing check cadence; container rate and
duration fields check mux metadata. Playback with sound and close-up cycle review
check perceptual smoothness, audible sync and visible artifacts. Frame differences,
a higher FPS or a successful hardware encode do not establish creative acceptance.
Preserve separately requested outputs, such as an unbranded poster, with their own
checks rather than inheriting the film's branding settings.

If timestamps already have the intended cadence but container headers disagree,
investigate a packet remux before re-encoding or retiming. Use a new output and
compare stream identities, ordered encoded-payload hashes and every packet's PTS,
DTS and duration in a common time base, then probe and fully decode the result.
Report any changed fields; a payload hash alone does not prove timestamp
preservation. This is a conditional diagnosis, not a generic timing-repair command
or qualification of every codec/container.

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


## Film capability and reviewed-source parity

The original [exporter](../../orbyn-ui-design/examples/spatial-review/motion-films.md)
provides authored JSON shots, frame-aligned cuts, FPS/BPM, palette/local font roles,
pure seek/replay, shared preview/render DOM, cut-bounded temporal averaging,
optional highlight bloom/seeded grain, local audio, timed subtitles, H.264 MP4,
poster, probe/decode/fast-start and source/output receipts, and
[streaming export](../../orbyn-ui-design/examples/spatial-review/motion-films.md#stream-a-full-length-film)
for full-length songs. No Scenario connection
is required. Keep unsupported cells visible; matching output format is not matching
every visual block, quality metric or provider service.

The reviewed blocks document actually lists **14** named blocks. Their names below
identify the comparison scope; none of their implementation is copied.

| Reviewed block | Original functional primitive | Deliberate boundary |
|---|---|---|
| Words | `words`: timed word sequencing and entrances | Different styling; no copied glyph/glitch catalog |
| Strike | `crossout`: drawn strike and replacement reveal | Original text sequence, not arbitrary mock-UI destruction |
| Graph | `chart`: values, bars and labels share a sampled reveal | No source-specific graph portal camera |
| Hero | `3d-title`: layered type with sampled CSS 3D orientation | CSS depth planes, not a font-mesh/GPU renderer |
| Prompt | `typing`: deterministic prefix/cursor | No external prompt execution |
| Stretch | `stretch`: sampled elastic type transform | CSS deformation, no bundled variable font |
| Fly | `flythrough`: camera-relative CSS 3D word planes | No source glyph-counter portal geometry |
| Notes | `annotations`: timed labels and drawn connectors | Parametric plane, not an arbitrary notes editor |
| Counters | `counter`: sampled numeric interpolation/precision | Caller supplies facts and claims |
| Progress | `progress`: time-aligned steps, fill and readout | Synthetic scene state, not measured product completion |
| Chain | `chain`: nodes and sequential connections | Illustrative dependency sequence |
| Rewind | `rewind`: reverse an earlier nonrecursive clip | No recursive/cyclic clip graph |
| Picture | `image`: approved raster with sampled framing | PNG/JPEG/WebP; no remote assets or SVG markup |
| Logo | `logo`: text or approved raster reveal | No arbitrary SVG/HTML injection |

The [14-shot gallery](../../orbyn-ui-design/examples/spatial-review/film-gallery.json)
is executable with the shared preview/render path; each primitive has deterministic
model and bad-input controls. New extensions remain under this owner and need those
controls plus actual MP4 checks. Do not install or relabel the reviewed ZIP. Sound kits, provider generation,
automatic beat detection/mixing/loudness, external fonts/remote images, multi-worker rendering and style-specific dynamism scoring are not implemented parity. The supported 4K profile requires its own recorded short export/decode; the full
gallery/film qualification is separately recorded at 720p. Neither establishes universal
parity or permission to generate assets, publish or deploy.


For music-led supplied art/track requests, use the [music-video intake and background
path](../../orbyn-ui-design/examples/spatial-review/motion-films.md#music-led-artwork-and-music-videos).
Choose source/rights, actual track/BPM or markers, aspect/duration, crop/focal motion
and verified text/captions. The original full-frame background path pans and zooms a
picture under foreground scenes and music, so use it only for an image with no character
in it. When the image holds a character, that character must really move: follow
[animate an image](animate-an-image.md), and treat pan, zoom and layers as support for
that motion. [Lyric performance](lyric-performance.md) describes bounded local 2D options
and their limits. Do not invoke a paid provider without task
authority.

For frame-accurate audio-reactive shaders, a checkable beat grid or timing supplied
lyrics, use [music timing](music-timing.md).
