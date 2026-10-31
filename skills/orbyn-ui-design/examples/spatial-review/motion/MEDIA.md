# Repo-owned media editing

The original [planner](media.mjs) and [local CLI](edit-media.mjs) turn an inert,
hash-bound edit decision list into an inspected MP4/M4A. They invoke an explicitly
selected existing FFmpeg/ffprobe build. They do not launch OBS or LosslessCut, copy
those applications' GPL code, upload assets, or require an external authoring app.
Keep the EDL, authored captions, source asset provenance and selected output
receipts with the consuming repo's design/prototype record. Generated media,
decoded PCM and diagnostic logs belong in its declared ignored output directory.

## Contract and supported envelope

`validateEDL(edl)` validates a version1 record; `planEDL(edl, probes)` resolves
observed global stream indices, decoded video timestamps and the rational project
clock into an explicit filter/concat plan. Neither executes source JSON. Each
asset has a stable ID, relative local path and SHA-256. Clips are ordered,
contiguous and cover `durationFrames` exactly. `sourceIn`/`sourceOut` are seconds
relative to the first selected video PTS, or first audio PTS for audio-only work.
`atFrame`/`durationFrames` define placement; `speed` maps source duration onto
that frame interval. No implicit speed, unknown padding or gap repair is inferred.

The video profile is even-sized H264/yuv420p MP4, optional stereo AAC and authored
mov_text captions. Audio-only output is stereo AAC/M4A. Dimensions, FPS, sample
rate (44100/48000), stream selection and `copy`/`reencode` are explicit. Bounds:
120 seconds/7200 project frames,32 assets/64 clips,512MiB per input,3840 maximum
axis/8.3M pixels,1–4 threads,1MiB EDL, bounded probe/log capture and a disk estimate
plus256MiB reserve. Local containers accepted: MP4/MOV,Matroska/WebM,WAV,AIFF,MP3,
FLAC,Ogg,AAC. Decoder availability still depends on the recorded local build.

Copy supports **one video-only CFR H264 clip**, no Bframes, matching dimensions
and rational FPS, and observed keyframe boundaries (or observed source end).
Between-keyframe cuts, joins, audio, retiming, VFR and uncertain cadence refuse
copy; the caller must explicitly choose reencode. No general copy-mode frame
accuracy is promised. Reencode intentionally resamples to project FPS; speed/VFR
may duplicate or discard frames. CFR frame order and join continuity have their
own decoded coded-frame test below.

Audio frame boundaries map to integer samples using differences of absolute
rational addresses, avoiding accumulated clip-rounding drift. `audioOffsetSamples`
delays positive values and advances negative values. Unity speed bypasses the
time-stretcher entirely; non-unity speed uses FFmpeg atempo/WSOLA, whose transient
placement is not sample-exact. Its declared output duration may require explicit
final padding. Inspect retimed beats/transients against the authored intent. Original same-source A/V
start offset is retained. An optional `audioAsset` uses its own source clock;
`audioSourceIn`/`audioSourceOut` select that asset and `audioFill:'silence'` explicitly
allows a shorter selection to pad. Silence is not inferred for a missing stream.
AAC container duration is checked within two samples; decoded final AAC tail
padding may be at most1024 samples and is reported separately. Codec pre-ringing
can move a threshold-based onset by a few samples; that is not presented as a
sample-exact decoded acoustic onset.

Captions use authored `startFrame`/`endFrame` and text. Embedded blank lines and
cue arrows refuse; ordinary multiline text and escaped punctuation round-trip.
Extracted muxed captions must match text and rational timing within1.1ms. Optional
`loudness:{integrated,truePeak,range}` performs a measured first pass and uses its
values in a second pass, then measures decoded AAC again (integrated tolerance
1LU, true peak no more than0.5dB above request). Silence/nonfinite measurements
refuse. `false`/`null` are not silently interpreted as omitted loudness policy.

## Run

Agents resolve actual selected paths and hashes. This example shape selects a
second source audio stream and delays it100ms; stream indices must come from
actual ffprobe output:

```json
{
  "version": 1,
  "title": "Reviewed authored edit",
  "sourceRevision": "repo-owned-source-revision",
  "kind": "video",
  "fps": {"numerator": 30000, "denominator": 1001},
  "durationFrames": 30,
  "width": 1280,
  "height": 720,
  "sampleRate": 48000,
  "assets": [{"id": "film", "path": "film.mp4", "sha256": "REPLACE_WITH_ACTUAL_SHA256"}],
  "clips": [{"id": "opening", "asset": "film", "sourceIn": 0,
    "sourceOut": 1.001, "atFrame": 0, "durationFrames": 30,
    "videoStream": 0, "audioStream": 2, "audioOffsetSamples": 4800,
    "mode": "reencode"}],
  "captions": [{"startFrame": 0, "endFrame": 30, "text": "Authored caption"}]
}
```

```sh
node /ABS/library/skills/orbyn-ui-design/examples/spatial-review/motion/edit-media.mjs \
  --edl /ABS/repo/design/edit.json --root /ABS/repo/media \
  --output /ABS/repo/ignored/NEW-export \
  --ffmpeg /ABS/existing/ffmpeg --ffprobe /ABS/existing/ffprobe \
  --threads 2 --timeout 120
```

Output must be new; source files are never overwritten. The CLI snapshots and
hash-checks the source closure, records exact tool binary hashes/version/build
configuration and the wrapper/planner/clock/strict-parser source hashes, verifies
that source closure again before completion, probes actual frames/streams, runs the selected plan, decodes the
whole output, checks frame/sample/caption contracts and re-reads source/EDL/media
hashes. `receipt.json` is complete only after these checks. `playback.html` allows
local inspection. Commands, stdout/stderr, probes, copied inputs and failed output
remain available after a refusal or failure. SIGINT/SIGTERM and deadlines stop
owned process groups, escalating after one second if necessary; receipts separate
cancelled, timed-out and failed states. This is an owned-child audit, not a claim
that every host process was inspected. No host-wide kill or output overwrite.

The programmatic `executeEDL(options)` accepts those paths and bounded numeric
`threads`/`timeout`, with defaults2/120. A completed receipt proves this specific
execution and readback; it does not prove playback on every target decoder.

## Reproducible local qualification

The [original fixture helper](media-fixtures.mjs) generates60 coded160×96 frames,
two distinct synthetic sine tones, CFR H264 with/without Bframes, lossless FFV1,
and VFR media. It requires an existing local FFmpeg and creates a new ignored
directory. No downloaded film, song, model or dataset is required.

```sh
node /ABS/library/skills/orbyn-ui-design/examples/spatial-review/motion/media-fixtures.mjs \
  --out /ABS/ignored/NEW-fixtures --ffmpeg /ABS/existing/ffmpeg
ORBYN_MEDIA_FIXTURES=/ABS/ignored/NEW-fixtures \
ORBYN_MEDIA_OUTPUT=/ABS/ignored/NEW-test-output \
ORBYN_FFMPEG=/ABS/existing/ffmpeg ORBYN_FFPROBE=/ABS/existing/ffprobe \
  node --test /ABS/library/skills/orbyn-ui-design/examples/spatial-review/motion/media.test.mjs
```

Without those variables, pure validation/caption tests run and actual FFmpeg cases
explicitly skip. Actual tests decode every coded frame at a two-clip join
(expected0..59), keyframe copy(expected15..44), Bframe reencode and speed/VFR
resampling; inspect selected880Hz audio, authored100ms delay, sparse unity-speed impulse
peaks with/without delay (within1ms after AAC decode), measured loudness,
caption text/time, audio-only decode and30000/1001→48048-sample mapping. Negative
cases cover non-key/Bframe/VFR copy refusal, hash mismatch, no overwrite,
deadline and SIGTERM, including a fake local CLI that ignores SIGTERM and must
receive SIGKILL. Synthetic tones qualify these mechanics, not music mastering or
subjective audiovisual quality. Windows process-tree qualification, arbitrary
codec/container profiles, very long edits and independently reviewed real media
remain separate checks.

FFmpeg is LGPL/GPL depending on its configuration and external codecs. Record the
actual build; a GPL-enabled libx264 binary is not relabeled MIT by this wrapper.
This source does not redistribute that binary. Codec patent, media/music/model
rights and any distribution obligations remain specific to the selected closure.
