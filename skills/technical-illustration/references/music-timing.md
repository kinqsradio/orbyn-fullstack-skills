# Time music-led motion from the audio

Read this when a shader or scene reacts to a track frame by frame, or when supplied
lyrics need timing. Start with `scripts/audio-bake.py`, which needs only Python's
standard library and FFmpeg, and place lyrics by hand on what it measures. That route
stays inside the [code-only rule](code-only.md). Keep the track and lyrics in ignored
task storage, and build fixtures from generated tones only.

## Bake features with no library

```sh
python3 scripts/audio-bake.py ./assets/track.wav --out ./output/bake.json --fps 30
```

Run it from the skill root. `--fps` also takes a ratio such as `30000/1001`. `--out` must
be a new file. A three-minute test track took about 11 seconds on one laptop.

| Field | Use | Scale |
| --- | --- | --- |
| `bandEnergy.<band>[frame]` | Drive one parameter from sub, bass, lowMid, mid, highMid or high | 0–1 of that band's track peak; `bands[].peak` restores amplitude |
| `rms[frame]` | Follow overall loudness | Linear, 1 is full scale |
| `onsetEnvelope[frame]` | Scale an accent by how hard the sound changed | 0–1 of the track's strongest change |
| `onsets[]` | Fire an accent at `{time, gain, frame}`; it feeds the rig's `accent()` as it is | Seconds, 0–1, whole frame |

Index by integer frame, so rational rates stay exact. Frame `n` covers the time from
`n / fps` up to the next frame. An onset's time comes from the sharpest rise in energy near
the spectral change, so a click lands within about 12 ms in the tests. A sound ending
gives no onset.

Onsets are candidates, not beats or bars. Listen, then keep the ones that matter. If
`status` is `silent`, the decoded audio has no signal, so check the file.

## Place lyrics by hand

1. Bake the track, and list the onsets near each sung word.
2. Write a word list, with one entry per sung word in order, using the bake's times or
   a tap pass:

   ```json
   {"producedBy": "hand placed on audio-bake onsets",
    "words": [{"word": "Hold", "start": 12.41, "end": 12.68, "probability": 1}]}
   ```

3. Run it through the same checks as any other source. The commands in this section and
   below run from the [motion example](../../orbyn-ui-design/examples/spatial-review/motion/audio-workflow.md)'s
   parent directory:

   ```sh
   python3 motion/align-lyrics.py --input ./assets/track.wav --lyrics ./design/lyrics.txt \
     --asr-words words.json --no-repeat-repair --out ./output/lyrics-1
   ```

`--no-repeat-repair` keeps this free of Python packages. It turns off the one numpy step,
so untimed lines stay listed under `repeats.unresolved`; place those by hand too. Then
use `correct-audio.mjs`, so that only corrected words become accepted captions.

## Opt-in routes

Everything below uses a third-party library or model, so use it only when the user
approves it for the job, and report it. All of it is local, and nothing here downloads a
model or calls a provider.

### Bake with librosa

`analyze-audio.py` needs librosa and numpy. It adds a beat grid, a kick envelope and
spectrum bars.

```sh
python motion/analyze-audio.py --input ./assets/track.wav --out ./output/bake-1 \
  --fps 30 --sections ./design/sections.json
```

`--sections` is optional: a JSON list such as `[{"label": "chorus", "start": 32.0}]`.
The bake writes `audio-features.json` beside `audio-analysis.json`:

| Field | Use | Scale |
| --- | --- | --- |
| `bandEnergy.<band>[frame]` | Drive one parameter from sub, bass, lowMid, mid, highMid or high | 0–1 of that band's track peak; `bands[].peak` restores amplitude |
| `kick[frame]` | Trigger on low-band attacks; ticks and held bass stay near 0 | 0–1, the strongest attack inside that frame |
| `bars[frame][bar]` | Upload as a frames × bars data texture | 0–1 over `barFloorDb`, on `barEdgesHz` log edges |

Address values by integer frame with `featureSampler`, not by time, so rational
rates stay exact. Band energies compare within a band only. Windows center on the
frame, so an attack can read up to half a window (46 ms at the defaults) early.

### Check the grid before trusting a bar

Grid phase and the downbeat are separate facts. `grid.offsetSeconds` places the
beats. It says nothing about which beat starts a bar.

Worked failure: a fitted 120 BPM grid has offset 0.000 s, and a scene change is
authored on grid beats 0, 4, 8. The bar actually starts on grid beats 2, 6, 10, so
every cut lands two beats off. The bake reports `downbeat.barOffsetBeats: 2`
from accents, or `unknown` when the signal cannot decide. Then:

1. Require `grid.status: fitted`. `irregular` means tempo drift, so use manual
   beats instead of a grid.
2. Read `downbeat.status`. Use `downbeat.time` only for `estimated` or `manual`.
   `unknown` covers even patterns and a kick on both 1 and 3, which leave two
   candidates. `conflict` means RMS edges and sections disagree with the accents.
3. Read `boundaries`, which lists RMS level steps and your sections. Each has
   `onBeat`, `beatErrorMs`, `onBar` and `barsFromDownbeat`. `onBar` is null while
   the bar line is unknown.
4. Read `boundaryRotation.counts`. If most boundaries share one grid position, that
   position is your likely bar line even when accents could not say.
5. Listen, then pass the verified time back with `--downbeat 12.137`. It must sit
   on the grid, and it records status `manual`.

RMS edges need 1.5 s of audio each side, and they miss changes in texture that hold
the same level. A half-time or double-time grid passes these checks, so confirm
tempo by ear.

### Time lyrics with a model

| Situation | Method | Why |
| --- | --- | --- |
| Lyrics supplied, vocals sit in a produced mix, no torch wanted | `align-lyrics.py --model-dir <small.en>` | Lighter than WhisperX; keeps only supplied text |
| Times already exist from another runtime | `align-lyrics.py --asr-words words.json` | Same checks, and no model loads |
| Spoken narration or a clean vocal with unknown text | `align-audio.py` | ASR then forced alignment |
| Supplied text, clean vocal, tight word endpoints matter | `align-audio.py --segments` | Forced alignment; needs torch and prepared models |
| A chorus reuses the same recording | Repeat matching, on by default in `align-lyrics.py` | Reuses measured offsets |

A word list is `{"producedBy": "...", "words": [{"word", "start", "end", "probability"}]}`.
Supply a converted CTranslate2 model directory yourself, such as one converted
from `small.en`; the tool loads local files only and hashes them into its record.

Avoid these failures, all handled by `align-lyrics.py`:

- **Decoder crash.** faster-whisper 1.2.1's `decode_audio` raises `TypeError` under
  PyAV 19.0.2. Decode with FFmpeg and pass a numpy float32 array, which skips it.
- **Invented words.** Whisper writes words over bass and vocal chops. Show only
  supplied lyrics. Heard words with no match go to `asrRejected` for review.
- **Collapsed times.** Under a riser, several words can share one instant. Adjacent runs of
  words at 40 ms or less lose their times rather than flash past.
- **Fading prompt.** With `condition_on_previous_text=False`, faster-whisper 1.2.1
  applies `initial_prompt` to the first window only and keeps its last 223 tokens.
  So the prompt holds each unique line once, within 600 characters, and `hotwords`
  carries the same text to later windows.

Collapsed lines are repaired from a clean instance of the same line: correlate its
waveform across the track, then add its measured word offsets to the match found
between the neighbouring timed words. Repaired words are `inferred`. A line with
no clean source, no match or several matches stays `missing` and is listed under
`repeats.unresolved`. Correlation finds the same recording, so a re-sung chorus
will not match; lower `--repeat-threshold` only after inspecting scores.

`lyric-timing.json` records the runtime behind every word (`timingRuntime`,
`runtimes`), and the receipt's `modelRun` says whether a model ran at all.

## Report what actually ran

Generated tones prove the arithmetic, not musical judgement or model output. The
library's tests use a stand-in for the model object, so no real faster-whisper
transcription or `small.en` result is qualified here. Report that path as
unverified until you run it, and name the model hash and versions from the record.
