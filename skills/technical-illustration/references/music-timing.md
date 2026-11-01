# Time music-led motion from the audio

Read this when a shader or scene reacts to a track frame by frame, when sections
must land on bars, or when supplied lyrics need timing. Tools live in the
[motion example](../../orbyn-ui-design/examples/spatial-review/motion/audio-workflow.md),
and the commands below run from its parent directory. All are optional and local;
nothing here downloads a model or calls a provider. Keep the track and lyrics in
ignored task storage, and build fixtures from generated tones only.

## Bake features for each video frame

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

## Check the grid before trusting a bar

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

## Choose a lyric timing method

| Situation | Method | Why |
| --- | --- | --- |
| Lyrics supplied, vocals sit in a produced mix, no torch wanted | `align-lyrics.py --model-dir <small.en>` | Lighter than WhisperX; keeps only supplied text |
| Times already exist from another runtime or a hand-tap pass | `align-lyrics.py --asr-words words.json` | Same checks, and no model loads |
| Spoken narration or a clean vocal with unknown text | `align-audio.py` | ASR then forced alignment |
| Supplied text, clean vocal, tight word endpoints matter | `align-audio.py --segments` | Forced alignment; needs torch and prepared models |
| A chorus reuses the same recording | Repeat matching, on by default in `align-lyrics.py` | Reuses measured offsets |
| Final delivery | `correct-audio.mjs` | Only corrected words become accepted captions |

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
