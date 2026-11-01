"""audio-bake.py on generated tones and click tracks. Nothing here needs numpy or a model."""
from array import array
import ast
from fractions import Fraction
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'skills/technical-illustration/scripts/audio-bake.py'
spec = importlib.util.spec_from_file_location('audio_bake', SCRIPT)
bake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bake)
SR = bake.SAMPLE_RATE


def tone(seconds, hz, amplitude=.8):
    return array('f', (amplitude * math.sin(2 * math.pi * hz * i / SR) for i in range(round(seconds * SR))))


def clicks(seconds, times, length=.012):
    y = array('f', bytes(4 * round(seconds * SR)))
    for at in times:
        start = round(at * SR)
        for i in range(round(length * SR)):
            if start + i < len(y):
                y[start + i] = .9 * math.exp(-i / (length * SR / 4)) * math.sin(2 * math.pi * 1800 * i / SR)
    return y


def write_wave(path, samples):
    with wave.open(str(path), 'wb') as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(SR)
        target.writeframes(array('h', (round(max(-1, min(1, v)) * 32767) for v in samples)).tobytes())


class SpectrumTests(unittest.TestCase):
    def test_the_transform_finds_a_tone_in_its_bin(self):
        fft = bake.RealFFT(64)
        power = fft.power([math.sin(2 * math.pi * 5 * i / 64) for i in range(64)])
        self.assertEqual(max(range(len(power)), key=power.__getitem__), 5)
        self.assertAlmostEqual(power[5], (64 / 2) ** 2, places=6)
        self.assertLess(sum(power) - power[5], 1e-6)

    def test_the_transform_handles_both_ends(self):
        fft = bake.RealFFT(16)
        self.assertAlmostEqual(fft.power([1.] * 16)[0], 16 ** 2)
        self.assertAlmostEqual(fft.power([1., -1.] * 8)[8], 16 ** 2)

    def test_the_size_must_be_a_power_of_two(self):
        with self.assertRaises(ValueError):
            bake.RealFFT(100)


class FeatureTests(unittest.TestCase):
    def test_each_tone_lands_in_its_own_band(self):
        for hz, name in ((40, 'sub'), (120, 'bass'), (350, 'lowMid'), (1000, 'mid'), (3000, 'highMid'), (8000, 'high')):
            result = bake.analyze(tone(1, hz), SR, Fraction(30))
            peaks = {band['name']: band['peak'] for band in result['bands']}
            self.assertEqual(max(peaks, key=peaks.get), name, hz)
            self.assertGreater(peaks[name], .3, hz)

    def test_there_is_one_value_per_video_frame(self):
        for fps, frames in ((Fraction(30), 60), (Fraction(24), 48), (Fraction(60), 120), (Fraction(30000, 1001), 60)):
            result = bake.analyze(tone(2, 440), SR, fps)
            self.assertEqual(result['frames'], frames)
            for curve in (result['rms'], result['onsetEnvelope'], *result['bandEnergy'].values()):
                self.assertEqual(len(curve), frames)

    def test_rms_follows_the_signal(self):
        result = bake.analyze(array('f', bytes(4 * SR)) + tone(1, 440, .5), SR, Fraction(30))
        self.assertLess(max(result['rms'][:29]), .001)
        self.assertAlmostEqual(result['rms'][45], .5 / math.sqrt(2), places=2)

    def test_band_energy_rises_with_the_tone(self):
        result = bake.analyze(array('f', bytes(4 * SR)) + tone(1, 1000), SR, Fraction(30))
        curve = result['bandEnergy']['mid']
        self.assertEqual(max(curve), 1)
        self.assertEqual(curve[10], 0)
        self.assertGreater(curve[45], .9)

    def test_a_click_track_gives_every_onset_near_its_true_time(self):
        truth = [.5 + i * .5 for i in range(8)]
        result = bake.analyze(clicks(5, truth), SR, Fraction(30))
        times = [onset['time'] for onset in result['onsets']]
        self.assertEqual(len(times), len(truth), times)
        for found, expected in zip(times, truth):
            self.assertLess(abs(found - expected), .012, (found, expected))

    def test_uneven_clicks_are_found_without_a_grid(self):
        truth = [.31, .62, 1.13, 1.27, 2.09, 2.71]
        times = [onset['time'] for onset in bake.analyze(clicks(3.5, truth), SR, Fraction(60))['onsets']]
        self.assertEqual(len(times), len(truth), times)
        for found, expected in zip(times, truth):
            self.assertLess(abs(found - expected), .012)

    def test_the_envelope_peaks_on_the_frame_of_the_hit(self):
        for fps in (Fraction(30), Fraction(60), Fraction(30000, 1001)):
            result = bake.analyze(clicks(2, [1.]), SR, fps)
            envelope, expected = result['onsetEnvelope'], math.floor(fps)
            self.assertEqual(result['onsets'][0]['frame'], expected)
            self.assertEqual(max(range(len(envelope)), key=envelope.__getitem__), expected)
            self.assertEqual(max(envelope), 1)

    def test_onsets_can_drive_the_rig_accent_directly(self):
        onset = bake.analyze(clicks(2, [1.]), SR, Fraction(30))['onsets'][0]
        self.assertEqual(set(onset), {'time', 'gain', 'frame'})
        self.assertGreater(onset['gain'], .5)

    def test_a_held_tone_has_one_onset_at_its_start(self):
        result = bake.analyze(array('f', bytes(2 * SR)) + tone(2.5, 500), SR, Fraction(30))
        times = [onset['time'] for onset in result['onsets']]
        self.assertEqual(len(times), 1, times)
        self.assertLess(abs(times[0] - .5), .02)

    def test_silence_reads_as_silence(self):
        result = bake.analyze(array('f', bytes(4 * SR)), SR, Fraction(30))
        self.assertEqual((result['status'], result['onsets']), ('silent', []))
        self.assertEqual(sum(result['rms']) + sum(result['bandEnergy']['mid']), 0)

    def test_no_samples_fail(self):
        with self.assertRaises(ValueError):
            bake.analyze(array('f'), SR, Fraction(30))

    def test_a_frame_rate_must_be_sensible(self):
        self.assertEqual(bake.parse_fps('30000/1001'), Fraction(30000, 1001))
        for bad in ('0', 'fast', '1/0', '500', '-1'):
            with self.assertRaises(ValueError):
                bake.parse_fps(bad)


class StandardLibraryOnly(unittest.TestCase):
    def test_every_import_is_from_the_standard_library(self):
        tree = ast.parse(SCRIPT.read_text())
        names = {alias.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        names |= {node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertEqual(names - set(sys.stdlib_module_names), set())


@unittest.skipUnless(shutil.which('ffmpeg'), 'Existing FFmpeg unavailable; no installation')
class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.track = self.root/'track.wav'
        write_wave(self.track, clicks(2, [.5, 1.5]))

    def run_bake(self, *args, env=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60, env=env)

    def test_a_file_goes_in_and_a_bake_comes_out(self):
        out = self.root/'bake.json'
        result = self.run_bake(str(self.track), '--out', str(out), '--fps', '30000/1001')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(out.read_text())
        self.assertEqual((data['fps'], data['frames']), ('30000/1001', 60))
        self.assertEqual(len(data['onsets']), 2)
        self.assertEqual(len(data['sourceSha256']), 64)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['bake.json', 'track.wav'])

    def test_it_runs_where_numpy_cannot_be_imported(self):
        (self.root/'numpy.py').write_text("raise ImportError('blocked')\n")
        env = {'PYTHONPATH': str(self.root), 'PATH': shutil.os.environ['PATH']}
        result = self.run_bake(str(self.track), '--out', str(self.root/'bake.json'), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_failures_exit_2_and_write_nothing(self):
        existing = self.root/'kept.json'
        existing.write_text('keep')
        for args in (['missing.wav', '--out', str(self.root/'a.json')], [str(self.track), '--out', str(existing)],
                     [str(self.track), '--out', str(self.root/'none/a.json')], [str(self.track), '--out', str(self.root/'a.json'), '--fps', '0'],
                     [str(self.track), '--out', str(self.root/'a.json'), '--ffmpeg', 'no-such-ffmpeg']):
            self.assertEqual(self.run_bake(*args).returncode, 2, args)
        self.assertEqual(existing.read_text(), 'keep')
        self.assertFalse((self.root/'a.json').exists())

    def test_a_file_that_is_not_audio_fails(self):
        fake = self.root/'fake.wav'
        fake.write_text('not audio')
        self.assertEqual(self.run_bake(str(fake), '--out', str(self.root/'a.json')).returncode, 2)


if __name__ == '__main__':
    unittest.main()
