# Author and export motion films

This capability lives in the canonical **technical-illustration** skill, under its
[motion method](../../../technical-illustration/references/motion-sequences.md).
It is original maintained source, not an installed Scenario skill. The entrypoint
routes code-driven motion films here; UI layout, social posters and ordinary
editing of existing footage retain their existing owners.

Prepare a **new** package under the consuming repo's design owner using `prepare.py`
as described in [the review README](README.md). Retain the existing review/version;
never overwrite it to update an exporter. The package contains the preview, exact
film model/DOM renderer, source hashes, a fixed-path server and this command:

```sh
node /ABS/PACKAGE/export-film.mjs --package /ABS/PACKAGE --output /ABS/REPO/docs/design/NEW_EXPORT --playwright /ABS/playwright/index.mjs --chrome /ABS/Chrome --python /ABS/python3 --ffmpeg /ABS/ffmpeg --ffprobe /ABS/ffprobe --width 1280 --height 720 --samples 2 --shutter 0.5 --grain 2 --bloom 0.05
```

Use existing tools only. No account, provider or download is required. The agent
resolves executable paths and runs the command; flags are not manual user homework.
`--output` must be a fresh directory under an existing real owner. Retain failures;
the exporter does not delete frames, overwrite a prior film or update an old review.
The output includes `film.mp4`, `poster.png`, `captions.vtt`, `captions-decoded.vtt`, `playback.html`, `film-spec.json`, source
frames, encode/probe/decode logs and a read-back `receipt.json` with source/model,
spec/media/output hashes and runtime identity. Keep these with the consuming repo's
artifact owner; raw qualification captures may follow its ignored-evidence policy.

## Make your film

Use `--spec /ABS/film.json` with the following strict versioned format. Shot times
are seconds; `time * bpm / 60` supplies the beat grid. Convert planned beats to
frame-aligned seconds when authoring; declaring BPM does not detect or synchronize
an arbitrary soundtrack. This is a complete two-shot example:

```json
{
  "version": 1,
  "title": "A product idea",
  "fps": 30,
  "bpm": 120,
  "duration": 6,
  "palette": {"paper":"#eedfc3","ink":"#152823","accent":"#b95937","deep":"#244b40"},
  "font": "system-ui",
  "shots": [
    {"id":"idea","from":0,"to":3,"composition":"title","title":"MAKE IT CLEAR","caption":"A concrete idea for the audience."},
    {"id":"action","from":3,"to":6,"composition":"end-card","title":"TRY THE NEXT STEP","caption":"A specific, readable action."}
  ]
}
```

Supported compositions: title, split, poster and end-card. Change words, timings,
shot order, FPS/BPM, palette and local system-ui/serif/monospace family. Unknown
fields, invalid text, duplicate IDs, gaps/overlap, unaligned cuts or incomplete
coverage reject. Decimal frame boundaries such as 4.1 seconds at 30 FPS are valid.
No arbitrary JavaScript/CSS/URLs are evaluated from the JSON. Fonts are existing
local families; source-specific downloaded fonts and external media are not imported.
The browser waits for font readiness and checks text bounds in every captured
subframe. This detects overflow, not contrast, reading comprehension or all safe
areas; inspect meaningful frames in the intended format, and run the
[legibility check](../../../technical-illustration/references/video-scenarios.md#check-words-and-logos)
for contrast and safe areas.

`film.html` and the interactive preview share `film.mjs` and its DOM renderer.
`--reduced-motion` exports static entrances while preserving complete content.
Reverse/repeated seek does not inherit prior frame transforms. The film export
contains the film stage, not a recording of the V12 controls or review panel.

## Motion blur, effects and budgets

`--samples 1..4` and `--shutter 0..1` sample around each output frame, **clamped to
that frame's shot**. The HUD stays at the output-frame instant. FFmpeg averages
only each frame's own group, selects one result per group and resets timestamps;
a cut cannot blend the preceding shot into the new one. `--grain 0..20` uses a
recorded seed of 42; `--bloom 0..0.2` is an optional bounded highlight glow. Defaults
are one sample and no effects. These are original implementations, not assertions
of pixel-identical upstream effects. Avoid blur/effects that reduce legibility.

One browser/page renders sequentially; encoder threads are bounded 1–4. Current
bounded envelope: even dimensions up to 3840 per side and 8,294,400 pixels,
10–60 FPS, duration up to 120 seconds and no more than 3,600 output frames, or
the [long-form limits](#stream-a-full-length-film) with `--stream`. The
12-second 720p qualification is evidence for that tested workload, not a promise
that every permitted extreme passes. `--timeout` is 10–1,800 seconds (default 600),
with conservative raw-frame disk reservation checks, a remaining-space floor, retained failures and owned-process cancellation. No
parallel render farm is implied. A short 3840×2160 profile check is distinct from
full-film qualification at that resolution. Capture normalizes the long edge to
1,280 logical pixels and scales device pixels, then Lanczos-normalizes the encoded
frame to exact output dimensions; the same composition survives 720p/1080p/4K.
Portrait or custom aspect ratios still require their own readability review.

## Stream a full-length film

A 159-second song at 60 FPS has 9,549 frames, which is past the default limits and
far past what raw frames should take on disk. Add `"longForm": true` to the spec
and `--stream` to the command. The film may then run 900 seconds, 54,000 frames and
240 shots, and `--timeout` may reach 14,400 seconds. Without `--stream` a `longForm`
spec is rejected.

```sh
node /ABS/PACKAGE/export-film.mjs --package /ABS/PACKAGE --output /ABS/REPO/docs/design/NEW_EXPORT --spec /ABS/song.json --audio /ABS/owned-track.wav --stream --frame-source /ABS/canvas-film --width 1920 --height 1080 --timeout 3600 --playwright /ABS/playwright/index.mjs
```

The encoder starts first and frames go straight to its stdin, so a full pipe pauses
rendering and no frame reaches disk. Disk reservation covers the encoded film only.
Retained output matches the other path, minus `frames/`. To look at a source frame,
render it again; a failed film leaves its receipt and logs but no frames.

Two capture sources share that pipe:

| Source | Command | Pixels |
|---|---|---|
| Film stage (`film.html`) | `--stream` | PNG screenshots piped to FFmpeg, slower but with the same DOM renderer and layout checks |
| Canvas page | `--stream --frame-source /ABS/DIR` | Raw RGBA read in the page and POSTed to a tokened loopback server |

`--frame-source` names a directory with `index.html`. The exporter reads its web
files into memory once, serves them from loopback and hashes them into the receipt.
Links reject, other file types stay unserved and are listed as excluded, and
a Content-Security-Policy header blocks requests off that origin. The page defines `window.streamFrame`:

```js
window.streamFrame = {
  rowOrder: 'bottom-first',                  // or 'top-first'; there is no default
  boot({width, height, frames, fps, spec, reducedMotion}) {},
  calibrate({width, height, pixels}) {},     // draw this Y-down card through the real passes
  render({index, time, sample}) {},          // pure: draw from index/time only
  read() { return pixels; }                  // opaque RGBA, width*height*4 bytes
};
```

Before encoding, `calibrate` proves the picture is upright; read
[full-screen pass orientation](../../../technical-illustration/references/fullscreen-pass-orientation.md).
`read` runs in the same task as `render`, so the buffer needs no preservation.

On macOS the exporter launches Chromium with `--use-angle=metal`, because headless
Chromium otherwise falls back from the GPU. Other platforms get no extra flag.
Only canvas pages receive it, and `receipt.stream.renderer` records what ran. Treat
`softwareRenderer: true` as a separate qualification cell, and raise `--timeout`
to suit: SwiftShader is far slower than a GPU.

Streaming adds its own receipts. `stream-probe.log` repeats every check in
[Validate the actual output](#validate-the-actual-output) and also requires BT.709
tags, which this path writes so colour matches on HD players. `stream-decode.log`
fails on any decoder message or a decoded frame count that differs from the film.
`receipt.stream` records capture source, accepted frames and bytes, renderer,
orientation, probe and decode results. An out-of-order or wrong-sized frame, or an
encoder that exits early, fails the export at once and retains the receipt.

Recorded qualification: a synthetic two-pass WebGL2 page ran 9,549 frames at 1080p60
with a tone track on an Apple M1 Pro over Metal. It took 12 minutes, passed 79 GB
of pixels through the pipe and left 19 MB on disk, peaking at 466 MB in the Node
process. That is evidence for that workload only. Heavy shaders, a real song, the
film stage at full length and other platforms each need their own run.

## Optional audio and captions

`--audio /ABS/owned-track.wav` accepts an explicitly selected local supported audio
container. No generation, URL fetching or external soundtrack upload occurs. Audio
is copied and hashed, padded/trimmed to film duration and encoded as stereo AAC
48 kHz/192 kbps. It is not beat-detected or automatically mixed/normalized. Inspect
rights, narration alignment, sync, clipping and intended playback/loudness; a
synthetic tone qualification does not prove a real music/narration mix.

`--captions /ABS/cues.json` accepts an ordered JSON array such as
`[{"start":0,"end":3,"text":"[Quiet tone] A visual explanation."}]`. Cues must
be bounded, non-overlapping and nonempty; text is escaped. Otherwise scene
explanations supply the subtitle track. The result includes WebVTT plus selectable
MP4 `mov_text` subtitles. Explanatory text is not evidence of transcribing speech;
provide actual spoken-content captions and transcript when needed. Caption display
support depends on the player, so inspect the target platform or export a reviewed
burned-caption variant separately; this pipeline does not claim a burned-caption path.

## Validate the actual output

The command requires H.264/yuv420p, exact output dimensions/FPS/frame count/duration,
selectable text track and an audio stream when requested. It extracts the encoded
subtitle track and compares authored cue text/timing; hashes of cues, WebVTT and
referenced media are retained. It probes the encoded
file, decodes every video/audio frame, verifies `moov` precedes `mdat` for fast-start,
extracts a poster, checks source again and rereads the output hash before recording
`complete`. A failed probe/decode is a failed export, even if an MP4 file exists.
Byte hashes are receipts, not cross-machine visual determinism or meaningful-film
quality. Open/play/seek the real MP4 in the intended player, inspect cuts and text,
and record any remaining audio/caption/platform limits.

The focused Python/Node checks cover specs, bad controls, no overwrite, failure
settlement and the streaming sink, server and orientation classifier. `MOTION_EXPORT_TESTS=1` with the existing browser/tool variables described
in the README runs the real small MP4 blur/effects/caption probe/decode test and
the real streaming, flipped-pass and encoder-death controls. Full
12-second 360-frame 720p export is a separate recorded qualification, not a model
benchmark or blanket native/GPU/accessibility certification.


## Fourteen scene primitives

Each shot may add `"primitive"` and `"data"`; omitting both preserves the four
composition-only format. The following strict payloads produce actual sampled
geometry, text, values or camera planes rather than renamed static cards:

| Primitive | Data | What varies with time |
|---|---|---|
| `words` | `{"words":["MAKE","IT","CLEAR"]}` | Sequenced words and entrances |
| `crossout` | `{"text":"Noise","replacement":"Meaning"}` | Strike length and replacement opacity |
| `chart` | `{"labels":["A","B"],"values":[16,64]}` | Bar geometry and numeric labels |
| `3d-title` | `{"text":"DEPTH","depth":8}` | Layered CSS 3D orientation |
| `typing` | `{"text":"A concrete brief."}` | Prefix length and deterministic cursor |
| `stretch` | `{"text":"FLEXIBLE"}` | Elastic type transform |
| `flythrough` | `{"words":["IDEA","FRAME","RESULT"]}` | CSS camera-relative word-plane depth |
| `annotations` | `{"notes":[{"x":0.2,"y":0.3,"text":"Source"}]}` | Drawn connectors and note reveal |
| `counter` | `{"from":0,"to":100,"decimals":0,"suffix":"%"}` | Numeric value |
| `progress` | `{"steps":["Plan","Build","Review"]}` | Fill, active steps and readout |
| `chain` | `{"nodes":["Input","Model","Frame"]}` | Sequential node/link path |
| `rewind` | `{"source":"earlier-shot-id"}` | Reverse playback of that prior primitive |
| `image` | `{"asset":"media/cover.png","alt":"Owned study"}` | Raster framing |
| `logo` | `{"text":"MOTION","asset":"media/mark.png"}` | Text/raster reveal; asset optional |

The depth/flythrough paths are CSS 3D planes, not a GPU font-mesh claim. Rewind
references only earlier non-rewind primitives, samples below the source clip's
exclusive end and rejects cycles/forward references. Text and arrays have bounded
size; image/logo data accepts only sealed raster paths and no arbitrary URLs.

`film-gallery.json` supplies a complete original 28-second, 14-shot authoring
example. In the interactive review choose **Fourteen motion primitives**: scrub or
play, annotate the film surface, and save the gallery scene/time/spec revision
with the existing review. To export it, pass `--spec /ABS/PACKAGE/film-gallery.json`.
The generated example circle/diamond rasters are original, not downloaded artwork.

To include owned artwork when preparing a fresh package, add
`--asset cover=/ABS/owned-cover.png --asset mark=/ABS/owned-mark.png`. Inputs must be
regular PNG/JPEG/WebP files with matching signatures (≤10 MB each, ≤32 explicit inputs); reserved/duplicate
IDs, SVG/HTML and links reject. The helper copies them under `media/`, seals hashes
and serves correct MIME types. The browser awaits actual image decode before each
captured frame. Receipts list used media digests. Check rights and provenance in
the consuming repo; this command does not grant redistribution rights.

Open `playback.html` through an existing loopback static server to play/seek the
actual MP4 with a WebVTT caption track and text transcript, then inspect cuts and
assets. A source-render or format pass does not prove audio listening quality or
pixel-identical parity with the reviewed source's styling/provider ecosystem.


## Music-led artwork and music videos

Choose the kind of film first in [video scenarios](../../../technical-illustration/references/video-scenarios.md).

For a supplied art/background plus track request, establish the actual files, rights
and intended use; duration/aspect/platform; the art's focal area; the intended mood
and motion; and whether words are lyrics, narration, explanation or no text. Use
measured/verified BPM or explicit audio markers; otherwise label the beat grid a
proposal. Do not guess lyrics or present generated captions as verified transcription.
No provider/account action or paid music/video generation follows from this intake.

The executable `film-music-video.example.json` combines full-frame original scenery,
pan/zoom, foreground type and timed scenes. With `--audio` it produces a music-led
video using the same renderer/export path. Its generated circle scenery and test
tone are qualification fixtures, not imported anime artwork or a real song. To use
owned supplied art, package it with `--asset scenery=/ABS/art.png` and use this
optional spec field (alongside the ordinary film fields):

```json
"background": {
  "asset":"media/scenery.png", "alt":"Owned scenery description",
  "fit":"cover", "focal":{"x":0.5,"y":0.5},
  "pan":{"from":{"x":-0.05,"y":0},"to":{"x":0.05,"y":0}},
  "zoom":{"from":1.2,"to":1.4}, "dim":0.45
}
```

Focal values are normalized crop coordinates; pan uses bounded frame fractions,
zoom is 1–2 and dim is a 0–0.8 black overlay. Cover mode rejects pan that would
expose uncovered edges at either endpoint; contain deliberately retains the
background ground/letterbox. The image fills the film frame, separate from optional
foreground image primitives. Motion is sampled from absolute time and respects
reduced-motion export; source hash and decoded readiness are checked. Inspect focal
retention and foreground contrast; no automatic contrast/accessibility guarantee
follows from dimming.

A still image can supply camera motion, atmosphere and layered typography. It does
not create new poses, lip-sync, singing or character actions. Requests requiring
those need the project's actual animation/video-production tools and separately
qualified assets/providers. Report missing capability before committing to that
result; never silently substitute a moving still for requested character animation.
Audio mixing, automatic beat detection, word-level lyric alignment and song-rights
clearance remain explicit separate work. The exporter supports a selected local
track and authored caption timings; it does not claim to solve those tasks.
