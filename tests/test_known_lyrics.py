#!/usr/bin/env python3
"""Known-lyrics timing contracts on invented text and generated tones; no model runs."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
MOTION = ROOT / 'skills/orbyn-ui-design/examples/spatial-review/motion'
sys.path.insert(0, str(MOTION))
import known_lyrics

try:
    import numpy as np
except ImportError:
    np = None

SR = 16000
LYRICS = """[Hook]
Hold the line tonight

Paper boats and rain
Hold the line tonight
"""


def asr(text, start, step=.3, length=.25, probability=.9):
    return [{'word': ' ' + word, 'start': round(start + i * step, 3), 'end': round(start + i * step + length, 3),
             'probability': probability} for i, word in enumerate(text.split())]


class SuppliedText(unittest.TestCase):
    def test_section_markers_and_blank_lines_are_not_sung_text(self):
        lines = known_lyrics.parse_lyrics(LYRICS)
        self.assertEqual([l['text'] for l in lines], ['Hold the line tonight', 'Paper boats and rain', 'Hold the line tonight'])
        self.assertEqual(lines[0]['words'], ['Hold', 'the', 'line', 'tonight'])
        with self.assertRaisesRegex(ValueError, 'lyric'):
            known_lyrics.parse_lyrics('[Hook]\n\n')

    def test_prompt_drops_repeats_and_stops_on_a_whole_line(self):
        lines = known_lyrics.parse_lyrics(LYRICS + '\n'.join(f'Line number {i} of many' for i in range(200)))
        prompt = known_lyrics.lyric_prompt(lines, limit=120)
        self.assertEqual(prompt.count('Hold the line tonight'), 1)
        self.assertLessEqual(len(prompt), 120)
        self.assertTrue(prompt.endswith('many'))

    def test_invented_words_never_reach_displayed_text(self):
        lines = known_lyrics.parse_lyrics('Hold the line tonight')
        heard = asr('bass chop', 0) + asr('Hold the line tonight', 1) + asr('yeah yeah drop', 3)
        words, rejected = known_lyrics.align_supplied(lines, heard)
        self.assertEqual([w['text'] for w in words], ['Hold', 'the', 'line', 'tonight'])
        self.assertTrue(all(w['status'] == 'aligned' for w in words))
        self.assertEqual(words[0]['start'], 1)
        self.assertEqual([r['word'] for r in rejected], ['bass', 'chop', 'yeah', 'yeah', 'drop'])

    def test_supplied_spelling_survives_a_misheard_word_and_timing_is_marked_inferred(self):
        lines = known_lyrics.parse_lyrics('We gonna hold on, tonight')
        words, rejected = known_lyrics.align_supplied(lines, asr('we gunna hold on tonight', 0))
        self.assertEqual([w['text'] for w in words], ['We', 'gonna', 'hold', 'on,', 'tonight'])
        self.assertEqual(words[0]['status'], 'aligned')
        self.assertEqual(words[1]['status'], 'inferred')
        self.assertEqual(words[1]['start'], .3)
        self.assertEqual(words[1]['score'], None)
        self.assertEqual(rejected, [])

    def test_a_block_of_different_length_is_rejected_rather_than_paired_by_guess(self):
        lines = known_lyrics.parse_lyrics('Paper boats and rain')
        words, rejected = known_lyrics.align_supplied(lines, asr('paper wubwub wub wub rain', 0))
        self.assertEqual([w['status'] for w in words], ['aligned', 'missing', 'missing', 'aligned'])
        self.assertEqual([r['word'] for r in rejected], ['wubwub', 'wub', 'wub'])

    def test_unheard_supplied_words_stay_missing_with_null_times(self):
        lines = known_lyrics.parse_lyrics('Paper boats and rain')
        words, _ = known_lyrics.align_supplied(lines, asr('paper rain', 0))
        self.assertEqual([w['status'] for w in words], ['aligned', 'missing', 'missing', 'aligned'])
        self.assertIsNone(words[1]['start'])
        self.assertIsNone(words[1]['end'])

    def test_collapsed_runs_lose_their_times_but_a_short_real_word_keeps_them(self):
        lines = known_lyrics.parse_lyrics('Hold the line tonight a day')
        heard = [{'word': w, 'start': 5 + i * .01, 'end': 5 + i * .01 + .01, 'probability': .9}
                 for i, w in enumerate(['Hold', 'the', 'line', 'tonight'])]
        heard += [{'word': 'a', 'start': 6, 'end': 6.03, 'probability': .9}, {'word': 'day', 'start': 6.1, 'end': 6.5, 'probability': .9}]
        words, _ = known_lyrics.align_supplied(lines, heard)
        collapsed = known_lyrics.mark_collapsed(words)
        self.assertEqual([c['id'] for c in collapsed], ['word-0', 'word-1', 'word-2', 'word-3'])
        self.assertEqual(collapsed[0]['originalStart'], 5)
        self.assertEqual([w['status'] for w in words], ['missing'] * 4 + ['aligned', 'aligned'])
        self.assertIsNone(words[0]['start'])


class FakeWord:
    def __init__(self, word, start, end, probability):
        self.word, self.start, self.end, self.probability = word, start, end, probability


class FakeSegment:
    def __init__(self, words):
        self.words = words


class FakeModel:
    """Stands in for WhisperModel: this proves our call, not any model's output."""
    def __init__(self):
        self.calls = []

    def transcribe(self, audio, **options):
        self.calls.append((audio, options))
        def generate():
            yield FakeSegment([FakeWord(' Hold', 1.0, 1.2, .8), FakeWord(' on', 1.2, 1.4, .7)])
        return generate(), object()


@unittest.skipIf(np is None, 'numpy is the optional audio-profile dependency')
class ModelCall(unittest.TestCase):
    def test_decoder_stays_out_of_the_model_call(self):
        import lyrics_worker
        with self.assertRaisesRegex(TypeError, 'numpy'):
            lyrics_worker.transcribe_words(object(), '/some/track.wav', 'prompt', 'en')

    def test_numpy_input_prompt_and_word_times_are_requested(self):
        import lyrics_worker
        model = FakeModel()
        audio = np.zeros(SR, dtype=np.float32)
        words, options = lyrics_worker.transcribe_words(model, audio, 'Hold on', 'en')
        passed, requested = model.calls[0]
        self.assertIs(passed, audio)
        self.assertEqual(requested['initial_prompt'], 'Hold on')
        self.assertEqual(requested['hotwords'], 'Hold on')
        self.assertTrue(requested['word_timestamps'])
        self.assertFalse(requested['condition_on_previous_text'])
        self.assertEqual(words[0], {'word': ' Hold', 'start': 1.0, 'end': 1.2, 'probability': .8})
        self.assertEqual(options['initial_prompt'], True)

    def test_wrong_sample_format_refuses_before_the_model_runs(self):
        import lyrics_worker
        model = FakeModel()
        with self.assertRaisesRegex(TypeError, 'float32'):
            lyrics_worker.transcribe_words(model, np.zeros((SR, 2), dtype=np.float32), 'p', 'en')
        self.assertEqual(model.calls, [])


def motif(seed, seconds=1.2):
    rng = np.random.default_rng(seed)
    t = np.arange(round(seconds * SR)) / SR
    tones = sum(np.sin(2 * np.pi * (f * t + .5 * s * t ** 2)) for f, s in zip(rng.uniform(150, 1800, 8), rng.uniform(-200, 200, 8)))
    return tones / 8


def place(y, at, source, amount=1.0):
    start = round(at * SR)
    y[start:start + len(source)] += source * amount


@unittest.skipIf(np is None, 'numpy is the optional audio-profile dependency')
class Repeats(unittest.TestCase):
    def track(self):
        y = np.zeros(20 * SR)
        hook = motif(1)
        place(y, 2, hook)
        place(y, 5, motif(2))
        place(y, 8, hook)
        place(y, 14, hook)
        t = np.arange(4 * SR) / SR
        place(y, 12, .9 * (t / 4) * np.sin(2 * np.pi * (300 * t + 400 * t ** 2)))  # Riser over the last hook.
        return y

    def test_template_finds_each_exact_repeat_and_refuses_a_different_phrase(self):
        y = self.track()
        found = known_lyrics.find_repeats(y, SR, 2, 3.2, threshold=.5)
        self.assertEqual(len(found), 3)
        for match, expected in zip(found, [2, 8, 14]):
            self.assertAlmostEqual(match['time'], expected, delta=.002)
        self.assertGreater(found[0]['score'], .99)
        self.assertLess(found[2]['score'], found[0]['score'])

    def test_silent_or_short_template_refuses(self):
        with self.assertRaisesRegex(ValueError, 'Template'):
            known_lyrics.find_repeats(np.zeros(SR * 4), SR, 1, 2)
        with self.assertRaisesRegex(ValueError, 'Template'):
            known_lyrics.find_repeats(self.track(), SR, 2, 2.05)

    def lines_and_words(self):
        lines = known_lyrics.parse_lyrics('Hold the line tonight\nPaper boats and rain\nHold the line tonight\nHold the line tonight')
        heard = asr('Hold the line tonight', 2.1, step=.28) + asr('Paper boats and rain', 5.1) \
            + asr('Hold the line tonight', 8.1, step=.28)
        heard += [{'word': w, 'start': 14.5 + i * .01, 'end': 14.5 + i * .01 + .01, 'probability': .9}
                  for i, w in enumerate(['Hold', 'the', 'line', 'tonight'])]
        words, _ = known_lyrics.align_supplied(lines, heard)
        return lines, words

    def test_clean_repeat_offsets_replace_collapsed_times_and_record_their_source(self):
        lines, words = self.lines_and_words()
        known_lyrics.mark_collapsed(words)
        report = known_lyrics.repair_repeats(self.track(), SR, words, lines, threshold=.5)
        repaired = [w for w in words if w['line'] == 3]
        self.assertEqual([w['status'] for w in repaired], ['inferred'] * 4)
        self.assertAlmostEqual(repaired[0]['start'], 14.1, delta=.003)
        self.assertAlmostEqual(repaired[3]['start'], 14.1 + 3 * .28, delta=.003)
        record = report['repaired'][0]
        self.assertEqual(record['line'], 3)
        self.assertEqual(record['sourceLine'], 0)
        self.assertEqual(record['method'], 'repeat-offset')
        self.assertGreater(record['score'], .5)
        self.assertEqual(report['provenance']['word-12'], {'method': 'repeat-offset', 'sourceWord': 'word-0'})
        self.assertEqual([w['status'] for w in words if w['line'] == 2], ['aligned'] * 4)

    def test_without_a_matching_repeat_the_words_stay_missing(self):
        lines, words = self.lines_and_words()
        known_lyrics.mark_collapsed(words)
        report = known_lyrics.repair_repeats(self.track(), SR, words, lines, threshold=.995)
        self.assertEqual([w['status'] for w in words if w['line'] == 3], ['missing'] * 4)
        self.assertEqual(report['repaired'], [])
        self.assertEqual(report['unresolved'], [{'line': 3, 'reason': 'no repeat inside the gap'}])

    def test_a_line_without_a_clean_source_is_reported_not_guessed(self):
        lines = known_lyrics.parse_lyrics('Hold the line tonight\nHold the line tonight')
        words, _ = known_lyrics.align_supplied(lines, [])
        report = known_lyrics.repair_repeats(self.track(), SR, words, lines)
        self.assertEqual(report['unresolved'][0]['reason'], 'no clean repeat of this line')


CLI = np is not None and shutil.which('ffmpeg') and shutil.which('ffprobe')


@unittest.skipUnless(CLI, 'CLI path needs numpy and FFmpeg')
class AlignCli(unittest.TestCase):
    def run_cli(self, root, *extra):
        return subprocess.run([sys.executable, str(MOTION / 'align-lyrics.py'), *extra],
                              capture_output=True, text=True, cwd=root)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.source = self.root / 'tone.wav'
        y = Repeats().track()
        with wave.open(str(self.source), 'wb') as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(SR)
            target.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())
        self.lyrics = self.root / 'lyrics.txt'
        self.lyrics.write_text('Hold the line tonight\nPaper boats and rain\nHold the line tonight\nHold the line tonight\n')
        lines, _ = Repeats().lines_and_words()
        heard = asr('bass', 1) + asr('Hold the line tonight', 2.1, step=.28) + asr('Paper boats and rain', 5.1) \
            + asr('Hold the line tonight', 8.1, step=.28) \
            + [{'word': w, 'start': 14.5 + i * .01, 'end': 14.5 + i * .01 + .01, 'probability': .9}
               for i, w in enumerate(['Hold', 'the', 'line', 'tonight'])]
        self.words = self.root / 'heard.json'
        self.words.write_text(json.dumps({'producedBy': 'synthetic test list', 'words': heard}))

    def test_supplied_timing_writes_a_transcript_and_records_each_runtime(self):
        out = self.root / 'attempt'
        result = self.run_cli(self.root, '--input', str(self.source), '--lyrics', str(self.lyrics), '--asr-words',
                              str(self.words), '--out', str(out), '--repeat-threshold', '.5')
        self.assertEqual(result.returncode, 0, result.stderr)
        transcript = json.loads((out / 'transcript.json').read_text())
        timing = json.loads((out / 'lyric-timing.json').read_text())
        receipt = json.loads((out / 'receipt.json').read_text())
        self.assertEqual({tuple(sorted(w)) for w in transcript['words']}, {('end', 'id', 'score', 'start', 'status', 'text')})
        self.assertEqual(' '.join(w['text'] for w in transcript['words'][:4]), 'Hold the line tonight')
        self.assertNotIn('bass', [w['text'] for w in transcript['words']])
        self.assertEqual(timing['asrRejected'][0]['word'], 'bass')
        self.assertEqual(timing['runtimes']['asr']['kind'], 'supplied-asr-words')
        self.assertFalse(timing['runtimes']['asr']['modelRun'])
        self.assertEqual(timing['runtimes']['asr']['sha256'], hashlib.sha256(self.words.read_bytes()).hexdigest())
        self.assertEqual(timing['runtimes']['repeats']['kind'], 'numpy-waveform-correlation')
        self.assertEqual(timing['words'][12]['timingRuntime'], 'repeats')
        self.assertEqual(timing['words'][0]['timingRuntime'], 'asr')
        self.assertTrue(receipt['reviewRequired'])
        self.assertEqual(receipt['status'], 'completed')
        self.assertFalse(receipt['modelRun'])
        self.assertIn('known_lyrics.py', receipt['toolSources'])
        node = shutil.which('node')
        if node:
            check = "import {validateTranscript} from %s; import {readFileSync} from 'node:fs'; validateTranscript(JSON.parse(readFileSync(%s,'utf8')))"
            script = check % (json.dumps((MOTION / 'audio.mjs').as_uri()), json.dumps(str(out / 'transcript.json')))
            ran = subprocess.run([node, '--input-type=module', '-e', script], capture_output=True, text=True)
            self.assertEqual(ran.returncode, 0, ran.stderr)

    def test_timing_source_is_exactly_one_of_a_model_or_a_word_list(self):
        for extra in [[], ['--asr-words', str(self.words), '--model-dir', str(self.root)]]:
            result = self.run_cli(self.root, '--input', str(self.source), '--lyrics', str(self.lyrics),
                                  '--out', str(self.root / 'no'), *extra)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.root / 'no').exists())

    def test_invalid_word_list_fails_and_keeps_the_attempt(self):
        self.words.write_text(json.dumps({'producedBy': 'x', 'words': [{'word': 'a', 'start': 2, 'end': 1, 'probability': 1}]}))
        out = self.root / 'bad'
        result = self.run_cli(self.root, '--input', str(self.source), '--lyrics', str(self.lyrics),
                              '--asr-words', str(self.words), '--out', str(out))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads((out / 'receipt.json').read_text())['status'], 'failed')

    def test_model_directory_with_code_is_refused_before_loading(self):
        import lyrics_worker
        model = self.root / 'model'
        model.mkdir()
        (model / 'model.bin').write_bytes(b'weights')
        self.assertEqual(lyrics_worker.model_closure(model)['model.bin'], hashlib.sha256(b'weights').hexdigest())
        (model / 'run.py').write_text('print(1)')
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            lyrics_worker.model_closure(model)


if __name__ == '__main__':
    unittest.main()
