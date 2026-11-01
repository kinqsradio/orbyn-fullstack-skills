# Local audio analysis and correction

Start with `audio-bake.py` from the [music timing](../../../../technical-illustration/references/music-timing.md)
method, which needs only Python and FFmpeg. The tools below are opt-in under the
[code-only rule](../../../../technical-illustration/references/code-only.md), so use them
only when the user approves them for the job.

These optional source tools use reviewed Python packages and existing FFmpeg/
FFprobe binaries. Ordinary UI preparation does not install them, download models
or call a hosted provider. Keep their environment, model profile and generated
output in an ignored, task-owned directory; keep deliberately authored source,
correction files and accepted caption data in the consuming repository.

Create an isolated Python 3.12 environment and install `audio-requirements.txt`
only for an authorized audio task. Record the resolved environment (`pip freeze`),
platform and binary versions alongside the output receipt. The top-level pins
are not a cross-platform lock of every transitive dependency. CUDA is conditional;
the qualified example uses CPU. No application-wide provider settings change.

```sh
python motion/analyze-audio.py --input ./assets/track.wav --out ./output/analysis-1
python motion/prepare-audio-models.py --download --out ./output/speech-models
python motion/align-audio.py --input ./assets/narration.wav \
  --models ./output/speech-models/models.json --out ./output/transcript-1
```

Run these from the spatial-review example directory, or use its actual absolute
path. The explicit model-preparation command acquires pinned ASR, English
alignment and English tokenizer data, records licenses and hashes, and refuses
reused output directories. Model weights are not bundled in this library.
Alignment verifies the complete prepared file closure before and after use and
loads local files only. There is no diarization or speaker identity qualification.
Other languages require an explicitly reviewed matching model/tokenizer profile.

The analysis contains variable beat/onset times, sampled RMS and waveform
envelopes, source SHA-256 and an explicit silent/estimated status. Beat detection
can be ambiguous; it is not a substitute for authoring musical intent. `audio.mjs`
samples these features without depending on playback history and exposes an
original component adapter. Generated speech times remain estimates, including
those with confidence scores. ASR segments are bounded to decoded sample length
before forced alignment; original times and adjustments remain in the output.
Unresolved words retain null timestamps. Silence is not a successful transcript.

Add `--fps 30` (or a rational rate such as `30000/1001`) to also write
`audio-features.json`: per-frame band energies, a kick onset envelope and log
spectrum bars, plus beat-grid phase, downbeat status and boundary checks. These
need numpy, already part of the profile above. `featureSampler` in `audio.mjs`
validates the file once and returns one frame's values. [Music timing](../../../../technical-illustration/references/music-timing.md)
says how to read them and which lyric method fits.

For supplied lyrics, `align-lyrics.py` is a lighter path that installs only
`lyrics-requirements.txt`, then runs a local model or reads a heard-word list:

```sh
python motion/align-lyrics.py --input ./assets/track.wav --lyrics ./design/lyrics.txt \
  --model-dir ./output/models/small.en --out ./output/lyrics-1
```

Its `transcript.json` feeds the correction flow below. With a hand-placed word list,
`--asr-words words.json --no-repeat-repair` needs no Python packages at all. Repeat
repair is the only step that needs numpy, and untimed lines then stay listed as
unresolved.

Author a correction JSON with the exact source hash and transcript revision:

```json
{
  "audioSha256": "<64 lowercase hexadecimal characters>",
  "revision": 1,
  "edits": [
    {"id": "word-0", "text": "Hello", "start": 0.12, "end": 0.48}
  ]
}
```

```sh
node motion/correct-audio.mjs --transcript ./output/transcript-1/transcript.json \
  --edits ./design/narration-edits.json --output ./output/corrected-1
```

This creates a new transcript with previous values and edit history, a caption
review containing unresolved IDs, and an input/edit/output hash receipt. It rejects
stale revisions and mismatched audio. It does not establish that a human actually
reviewed an edit: record that review separately in the consuming design/review
record. Unedited model words are excluded from accepted caption cues by default.
Draft estimates can be rendered explicitly through `wordsToCues` with
`includeModelEstimates`, retaining `reviewRequired: true`.

Beat corrections use `--analysis` instead of `--transcript`, with an edit object
containing only `audioSha256` and strictly increasing `beats` in seconds. Keep the
original analysis, the correction file and the resulting source-bound record.
Before delivering media, carry accepted cues into the EDL, verify extracted text
and actual A/V timing, and inspect playback. These tools do not establish media
rights, lip-sync, generated character poses or musical quality.

Run `node --test motion/audio.test.mjs`, `python motion/audio_tools_test.py` and
the library's `tests/test_audio_features.py` and `tests/test_known_lyrics.py` for
offline contracts. Actual model, codec,
platform and perceptual qualification is separate. Failed/cancelled attempts stay
in their own output directories; SIGINT/SIGTERM settles owned subprocesses and
retains the job receipt. No tool overwrites a prior attempt or purges a cache.
