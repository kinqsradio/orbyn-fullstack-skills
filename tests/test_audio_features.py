#!/usr/bin/env python3
"""Feature-bake contracts on generated tones and click tracks; no model or real song."""
from fractions import Fraction
import importlib.util
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
try:
    import numpy as np
except ImportError:
    np = None

SR = 22050


def silence(seconds):
    return np.zeros(round(seconds * SR))


def tone(seconds, hz, amplitude=1.0):
    t = np.arange(round(seconds * SR)) / SR
    return amplitude * np.sin(2 * np.pi * hz * t)


def hit(y, at, hz, decay, amplitude=1.0, length=.12):
    t = np.arange(round(length * SR)) / SR
    start = round(at * SR)
    y[start:start + len(t)] += (amplitude * np.exp(-t * decay) * np.sin(2 * np.pi * hz * t))[:len(y) - start]


def click_track(seconds, beats, kicks=(), hats=()):
    """Kicks are 60 Hz thumps, hats are 6 kHz ticks, beats are 1 kHz clicks."""
    y = silence(seconds)
    for at in beats:
        hit(y, at, 1000, 110, .4, .05)
    for at in kicks:
        hit(y, at, 60, 22)
    for at in hats:
        hit(y, at, 6000, 220, .5, .03)
    return y


def write_wav(path, y):
    with wave.open(str(path), 'wb') as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(SR)
        target.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())


@unittest.skipIf(np is None, 'numpy is the optional audio-profile dependency')
class FrameBake(unittest.TestCase):
    def setUp(self):
        import audio_features
        self.tools = audio_features

    def test_frame_count_and_sample_addresses_follow_rational_fps(self):
        y = silence(10)
        fps = Fraction(30000, 1001)
        self.assertEqual(self.tools.frame_count(len(y), SR, fps), 299)
        self.assertEqual(self.tools.frame_sample(1, SR, fps), 736)  # 735.735 rounds up.
        self.assertEqual(self.tools.frame_sample(0, SR, fps), 0)

    def test_bands_separate_tones_per_frame_and_keep_a_recoverable_scale(self):
        y = np.concatenate([tone(1, 60), tone(1, 1000, .5), tone(1, 6000, .25)])
        baked = self.tools.bake_frames(y, SR, Fraction(30))
        self.assertEqual(baked['frames'], 90)
        bands = {b['name']: b for b in baked['bands']}
        energy = baked['bandEnergy']
        self.assertEqual(len(energy['bass']), 90)
        self.assertGreater(energy['sub'][15] + energy['bass'][15], .9)
        self.assertLess(energy['mid'][15], .02)
        self.assertGreater(energy['mid'][45], .9)
        self.assertLess(energy['bass'][45], .02)
        self.assertGreater(energy['high'][75], .9)
        self.assertLess(energy['mid'][75], .02)
        # Bands normalize independently, so each records its raw peak.
        self.assertLess(bands['high']['peak'], bands['mid']['peak'])
        self.assertGreater(bands['mid']['peak'], 0)

    def test_kick_envelope_tracks_low_hits_and_ignores_ticks_and_sustain(self):
        kicks = [1, 2, 3, 4]
        hats = [1.25, 1.5, 1.75, 2.25, 2.5, 2.75, 3.25, 3.5]
        y = click_track(5, [], kicks, hats)
        baked = self.tools.bake_frames(y, SR, Fraction(30))
        kick = baked['kick']
        for at in kicks:
            frame = round(at * 30)
            self.assertGreater(max(kick[frame - 1:frame + 2]), .7, at)
        for at in hats:
            frame = round(at * 30)
            self.assertLess(max(kick[frame - 1:frame + 2]), .1, at)
        steady = np.concatenate([silence(1), tone(3, 60)])
        sustained = self.tools.bake_frames(steady, SR, Fraction(30))['kick']
        self.assertGreater(max(sustained[28:34]), .7)
        self.assertLess(max(sustained[40:]), .05)

    def test_short_kick_survives_a_low_frame_rate(self):
        y = click_track(4, [], [1.01, 2.03, 3.05])
        kick = self.tools.bake_frames(y, SR, Fraction(12))['kick']
        self.assertEqual(sum(1 for value in kick if value > .5), 3)

    def test_log_bars_peak_at_the_tone_and_map_decibels_linearly(self):
        loud = self.tools.bake_frames(tone(1, 440), SR, Fraction(30), bar_count=32)
        edges = loud['barEdgesHz']
        self.assertEqual(len(edges), 33)
        ratios = [b / a for a, b in zip(edges, edges[1:])]
        self.assertAlmostEqual(min(ratios), max(ratios), places=3)
        row = loud['bars'][15]
        peak = row.index(max(row))
        self.assertLessEqual(edges[peak], 440)
        self.assertGreaterEqual(edges[peak + 1], 440)
        y = np.concatenate([tone(1, 440), tone(1, 440, .5)])
        both = self.tools.bake_frames(y, SR, Fraction(30), bar_count=32, floor_db=60)
        self.assertAlmostEqual(max(both['bars'][15]), 1, places=2)
        self.assertAlmostEqual(max(both['bars'][45]), 1 - 6.02 / 60, places=2)

    def test_narrow_low_bars_are_not_structural_gaps(self):
        rng = np.random.default_rng(7)
        noise = rng.standard_normal(SR) * .2
        rows = self.tools.bake_frames(noise, SR, Fraction(30), bar_count=64)['bars']
        means = [sum(row[i] for row in rows) / len(rows) for i in range(64)]
        self.assertGreater(min(means), .3)

    def test_silence_is_zero_not_a_division_error_and_bake_repeats_exactly(self):
        quiet = self.tools.bake_frames(silence(1), SR, Fraction(30))
        self.assertEqual(max(quiet['kick']), 0)
        self.assertEqual(max(max(row) for row in quiet['bars']), 0)
        self.assertEqual(quiet['status'], 'silent')
        y = click_track(2, [.5, 1], [.5, 1])
        self.assertEqual(self.tools.bake_frames(y, SR, Fraction(30)), self.tools.bake_frames(y, SR, Fraction(30)))

    def test_budgets_refuse_before_computing(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.tools.bake_frames(silence(1), SR, Fraction(30), bar_count=1000)
        with self.assertRaisesRegex(ValueError, 'fps'):
            self.tools.bake_frames(silence(1), SR, Fraction(0))
        with self.assertRaisesRegex(ValueError, 'band'):
            self.tools.bake_frames(silence(1), SR, Fraction(30), fft_size=256)


@unittest.skipIf(np is None, 'numpy is the optional audio-profile dependency')
class BeatGrid(unittest.TestCase):
    def setUp(self):
        import audio_features
        self.tools = audio_features

    def test_grid_phase_is_fitted_through_jitter_and_a_dropped_beat(self):
        offset, period = .137, .5
        rng = np.random.default_rng(3)
        beats = [offset + i * period for i in range(40) if i != 17]
        beats = [t + float(rng.uniform(-.005, .005)) for t in beats]
        grid = self.tools.fit_grid(beats)
        self.assertEqual(grid['status'], 'fitted')
        self.assertAlmostEqual(grid['bpm'], 120, delta=.1)
        self.assertAlmostEqual(grid['offsetSeconds'], offset, delta=.005)
        self.assertLess(grid['residualMs'], 5)

    def test_tempo_drift_and_too_few_beats_are_not_reported_as_a_grid(self):
        drifting = [sum(.5 + .004 * i for i in range(n)) for n in range(40)]
        self.assertEqual(self.tools.fit_grid(drifting)['status'], 'irregular')
        self.assertEqual(self.tools.fit_grid([.5, 1])['status'], 'unknown')

    def test_first_beat_is_never_assumed_to_be_the_downbeat(self):
        beats = [.5 + i * .5 for i in range(24)]
        y = click_track(13, beats)  # Every beat identical: no bar line in the signal.
        baked = self.tools.bake_frames(y, SR, Fraction(30))
        grid = self.tools.fit_grid(beats)
        downbeat = self.tools.estimate_downbeat(grid, baked['onsetCurve'], baked['onsetHopSeconds'])
        self.assertEqual(downbeat['status'], 'unknown')
        self.assertIsNone(downbeat['time'])
        self.assertAlmostEqual(grid['offsetSeconds'], .0, delta=.01)

    def test_accented_bar_line_differs_from_grid_phase(self):
        beats = [.5 + i * .5 for i in range(24)]
        kicks = [beats[i] for i in range(2, 24, 4)]  # Bars start on the third fitted beat.
        y = click_track(13, beats, kicks)
        baked = self.tools.bake_frames(y, SR, Fraction(30))
        grid = self.tools.fit_grid(beats)
        downbeat = self.tools.estimate_downbeat(grid, baked['onsetCurve'], baked['onsetHopSeconds'])
        self.assertEqual(downbeat['status'], 'estimated')
        self.assertAlmostEqual(downbeat['time'] % 2, kicks[0] % 2, delta=.02)
        self.assertNotAlmostEqual(downbeat['time'] % 2, beats[0] % 2, delta=.1)

    def test_kick_on_one_and_three_stays_ambiguous(self):
        beats = [.5 + i * .5 for i in range(24)]
        y = click_track(13, beats, beats[::2])
        baked = self.tools.bake_frames(y, SR, Fraction(30))
        grid = self.tools.fit_grid(beats)
        downbeat = self.tools.estimate_downbeat(grid, baked['onsetCurve'], baked['onsetHopSeconds'])
        self.assertEqual(downbeat['status'], 'unknown')
        self.assertIsNone(downbeat['time'])

    def test_manual_downbeat_supersedes_estimate_and_must_sit_on_the_grid(self):
        grid = self.tools.fit_grid([.5 + i * .5 for i in range(24)])
        curve = [0.0] * 2000
        self.assertEqual(self.tools.estimate_downbeat(grid, curve, .01, manual=2.0)['status'], 'manual')
        with self.assertRaisesRegex(ValueError, 'grid'):
            self.tools.estimate_downbeat(grid, curve, .01, manual=2.2)


@unittest.skipIf(np is None, 'numpy is the optional audio-profile dependency')
class SectionChecks(unittest.TestCase):
    def setUp(self):
        import audio_features
        self.tools = audio_features

    def test_rms_edges_find_level_steps_and_ignore_steady_clicks(self):
        y = np.concatenate([tone(8, 220, .05), tone(8, 220, .5)])
        edges = self.tools.rms_edges(y, SR)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]['direction'], 'up')
        self.assertAlmostEqual(edges[0]['time'], 8, delta=.06)
        self.assertAlmostEqual(edges[0]['deltaDb'], 20, delta=1.5)
        steady = click_track(16, [.5 + i * .5 for i in range(30)])
        self.assertEqual(self.tools.rms_edges(steady, SR), [])

    def test_boundary_checks_separate_beat_and_bar_agreement(self):
        grid = self.tools.fit_grid([i * .5 for i in range(1, 40)])
        downbeat = {'status': 'manual', 'time': 2.0, 'beatsPerBar': 4}
        checks = self.tools.check_boundaries(
            [{'time': 6.0, 'source': 'rms'}, {'time': 7.0, 'source': 'supplied', 'label': 'verse'},
             {'time': 7.2, 'source': 'rms'}], grid, downbeat)
        self.assertEqual([c['onBeat'] for c in checks], [True, True, False])
        self.assertEqual([c['onBar'] for c in checks], [True, False, False])
        self.assertEqual(checks[0]['barsFromDownbeat'], 2)
        self.assertEqual(checks[1]['beatsIntoBar'], 2)
        self.assertEqual(checks[1]['label'], 'verse')

    def test_unknown_downbeat_keeps_bar_agreement_unknown_but_shows_the_rotation(self):
        grid = self.tools.fit_grid([i * .5 for i in range(1, 40)])
        unknown = {'status': 'unknown', 'time': None, 'beatsPerBar': 4}
        boundaries = [{'time': t, 'source': 'rms'} for t in [2.5, 6.5, 10.5]]
        checks = self.tools.check_boundaries(boundaries, grid, unknown)
        self.assertEqual([c['onBar'] for c in checks], [None] * 3)
        self.assertEqual(checks[0]['gridBeatModBar'], 1)
        rotation = self.tools.boundary_rotation(checks, 4)
        self.assertEqual(rotation, {'counts': [0, 3, 0, 0], 'best': 1, 'boundaries': 3})

    def test_boundaries_conflicting_with_estimate_mark_the_downbeat(self):
        grid = self.tools.fit_grid([.5 + i * .5 for i in range(24)])
        estimated = {'status': 'estimated', 'time': 2.0, 'beatsPerBar': 4, 'barOffsetBeats': 3}
        boundaries = [{'time': t, 'source': 'rms'} for t in [2.5, 4.5, 6.5]]
        checks = self.tools.check_boundaries(boundaries, grid, estimated)
        result = self.tools.reconcile_downbeat(estimated, self.tools.boundary_rotation(checks, 4))
        self.assertEqual(result['status'], 'conflict')
        self.assertEqual(result['boundaryBarOffsetBeats'], 1)
        self.assertIsNone(result['time'])
        self.assertEqual(result['estimatedTime'], 2.0)

    def test_irregular_grid_reports_no_beat_agreement(self):
        grid = self.tools.fit_grid([.5, 1])
        check = self.tools.check_boundaries([{'time': 3.0, 'source': 'rms'}], grid,
                                            {'status': 'unknown', 'time': None, 'beatsPerBar': 4})[0]
        self.assertIsNone(check['onBeat'])
        self.assertIsNone(check['onBar'])


LIBROSA = importlib.util.find_spec('librosa') is not None and shutil.which('ffmpeg') and shutil.which('ffprobe')


@unittest.skipUnless(LIBROSA, 'End-to-end analyzer needs the optional librosa profile and FFmpeg')
class AnalyzerCli(unittest.TestCase):
    def test_click_track_writes_source_bound_features_and_keeps_analysis_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            beats = [.5 + i * .5 for i in range(30)]
            source, out = root / 'clicks.wav', root / 'attempt'
            write_wav(source, click_track(16, beats, beats[2::4]))
            sections = root / 'sections.json'
            sections.write_text(json.dumps([{'label': 'turn', 'start': 8.0}]))
            result = subprocess.run([sys.executable, str(MOTION / 'analyze-audio.py'), '--input', str(source),
                                     '--out', str(out), '--fps', '30', '--sections', str(sections)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            analysis = json.loads((out / 'audio-analysis.json').read_text())
            features = json.loads((out / 'audio-features.json').read_text())
            receipt = json.loads((out / 'receipt.json').read_text())
            self.assertNotIn('bands', analysis['analysis'])
            self.assertEqual(features['audioSha256'], analysis['audio']['sha256'])
            self.assertEqual(features['fps'], {'num': 30, 'den': 1})
            self.assertEqual(features['frames'], 480)
            self.assertEqual(len(features['bars']), 480)
            self.assertEqual(features['grid']['status'], 'fitted')
            self.assertAlmostEqual(features['grid']['bpm'], 120, delta=2)
            self.assertIn('audio_features.py', receipt['toolSources'])
            self.assertIn('audio-features.json', receipt['outputs'])
            supplied = [b for b in features['boundaries'] if b['source'] == 'supplied']
            self.assertEqual([b['label'] for b in supplied], ['turn'])
            self.assertTrue(supplied[0]['onBeat'])


if __name__ == '__main__':
    unittest.main()
