"""Bounded export contract checks; real browser/codec path explicitly opt-in."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import signal
import time
import subprocess
import tempfile
import unittest
from test_spatial_review import ROOT, SOURCE, module


class MotionExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which('node')
        if not cls.node: raise unittest.SkipTest('Existing Node unavailable; no installation')
        cls.temp = tempfile.TemporaryDirectory(); cls.base = Path(cls.temp.name).resolve()
        cls.pkg = cls.base/'package'
        module('film_prepare', SOURCE/'prepare.py').prepare(cls.pkg, cls.node)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(); self.addCleanup(self.case.cleanup)
        self.owner = Path(self.case.name).resolve(); self.out = self.owner/'export'

    def run_export(self, *args):
        return subprocess.run([self.node, str(self.pkg/'export-film.mjs'), '--package', str(self.pkg), '--output', str(self.out), *args], capture_output=True, text=True, timeout=90)

    def test_specification_and_cut_controls(self):
        r = subprocess.run([self.node, str(ROOT/'tests/motion-film.test.mjs'), str(self.pkg)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_invalid_arguments_spec_and_source_do_not_create_export(self):
        for args in [('--width', '641'), ('--samples', '5'), ('--duration', '1'), ('--grain', 'nan')]:
            self.assertNotEqual(self.run_export(*args).returncode, 0); self.assertFalse(self.out.exists())
        spec = self.owner/'bad.json'; spec.write_text('{"version":1,"version":1}')
        self.assertNotEqual(self.run_export('--spec', str(spec)).returncode, 0); self.assertFalse(self.out.exists())
        captions=self.owner/'empty-captions.json'; captions.write_text('[]'); self.assertNotEqual(self.run_export('--captions',str(captions)).returncode,0); self.assertFalse(self.out.exists())
        # New owned copy proves changed source rejection without mutating the shared fixture.
        pkg = self.owner/'changed'; shutil.copytree(self.pkg, pkg); (pkg/'film.mjs').write_text('// changed')
        r = subprocess.run([self.node, str(self.pkg/'export-film.mjs'), '--package', str(pkg), '--output', str(self.out)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0); self.assertFalse(self.out.exists())

    def test_existing_export_is_never_overwritten(self):
        self.out.mkdir(); sentinel = self.out/'receipt.json'; sentinel.write_text('preserve me')
        self.assertNotEqual(self.run_export().returncode, 0); self.assertEqual(sentinel.read_text(), 'preserve me')

    def write_long_spec(self):
        spec = self.owner/'long.json'; spec.write_text(json.dumps({'version': 1, 'longForm': True, 'title': 'Synthetic long film', 'fps': 60, 'bpm': 120, 'duration': 9549/60, 'shots': [{'id': 'whole', 'from': 0, 'to': 9549/60, 'composition': 'title', 'title': 'LONG', 'caption': 'Synthetic full-length film.'}]}))
        return spec

    def test_long_form_film_requires_the_streaming_path(self):
        spec = self.write_long_spec()
        result = self.run_export('--spec', str(spec))
        self.assertNotEqual(result.returncode, 0); self.assertIn('needs --stream', result.stderr); self.assertFalse(self.out.exists())

    def test_frame_source_alone_and_stream_timeout_are_bounded(self):
        self.assertIn('needs --stream', self.run_export('--frame-source', str(self.owner)).stderr); self.assertFalse(self.out.exists())
        self.assertNotEqual(self.run_export('--stream', '--timeout', '20000').returncode, 0); self.assertFalse(self.out.exists())
        self.assertNotEqual(self.run_export('--timeout', '2000').returncode, 0); self.assertFalse(self.out.exists())

    def test_owned_raster_inputs_are_sealed_and_markup_rejects(self):
        imported = self.owner/'imported'
        module('film_import_prepare', SOURCE/'prepare.py').prepare(imported, self.node, {'cover': self.pkg/'media/gallery.png'})
        manifest = json.loads((imported/'manifest.json').read_text())
        self.assertEqual(manifest['assets']['media/cover.png'], hashlib.sha256((self.pkg/'media/gallery.png').read_bytes()).hexdigest())
        bad = self.owner/'bad.png'; bad.write_text('<svg onload="alert(1)"></svg>')
        with self.assertRaises(ValueError): module('bad_import_prepare', SOURCE/'prepare.py').prepare(self.owner/'bad-package', self.node, {'bad': bad})
        self.assertFalse((self.owner/'bad-package').exists())

    def test_missing_runtime_retains_failure_and_settles(self):
        result = self.run_export('--ffmpeg', str(self.owner/'missing'))
        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads((self.out/'receipt.json').read_text()); self.assertEqual(receipt['status'], 'failed'); self.assertIn('ENOENT', receipt['error'])
        self.assertFalse((self.out/'film.mp4').exists())

    def test_probe_stdout_is_read_to_end_of_stream(self):
        # A descendant keeps the pipe open past the tool's exit, so an exit-only reader loses its tail.
        pad = 'x' * 200000
        probe = self.owner/'ffprobe'
        probe.write_text(f'''#!/bin/sh
case "$1" in
  -version) echo ffprobe stub; exit 0;;
esac
(sleep 0.3; printf '%s' '"}}}}') &
printf '%s' '{{"streams":[{{"codec_type":"audio"}}],"format":{{"format_name":"wav","pad":"{pad}'
exit 0
''')
        probe.chmod(0o700)
        server = self.owner/'python'
        server.write_text('#!/bin/sh\ncase "$1" in --version) echo Python stub; exit 0;; esac\nexit 7\n'); server.chmod(0o700)
        audio = self.owner/'tone.wav'; audio.write_bytes(b'RIFF')
        result = self.run_export('--audio', str(audio), '--ffmpeg', shutil.which('true'), '--ffprobe', str(probe), '--python', str(server))
        self.assertNotEqual(result.returncode, 0)
        error = json.loads((self.out/'receipt.json').read_text())['error']
        self.assertIn('Source server exited', error)  # Past the audio probe, not a truncated-JSON failure.

    def test_descendant_holding_stdout_cannot_outlast_the_drain(self):
        # Cancellation cannot reach a tool that already exited, so the wait itself must be bounded.
        tool = self.owner/'ffmpeg'
        tool.write_text('#!/bin/sh\n(sleep 15) &\nexit 0\n'); tool.chmod(0o700)
        server = self.owner/'python'
        server.write_text('#!/bin/sh\nexit 7\n'); server.chmod(0o700)
        started = time.monotonic()
        result = self.run_export('--ffmpeg', str(tool), '--ffprobe', shutil.which('true'), '--python', str(server))
        self.assertLess(time.monotonic() - started, 12)
        self.assertNotEqual(result.returncode, 0)

    @unittest.skipUnless(os.environ.get('MOTION_EXPORT_TESTS') == '1', 'Optional actual existing browser/FFmpeg export; set MOTION_EXPORT_TESTS=1')
    def test_actual_mp4_blur_effects_captions_probe_decode(self):
        spec = self.owner/'film.json'; spec.write_text(json.dumps({'version': 1, 'title': 'Synthetic export check', 'fps': 10, 'bpm': 120, 'duration': 1, 'shots': [{'id': 'intro', 'from': 0, 'to': .5, 'composition': 'title', 'title': 'MOTION', 'caption': 'Original frames.'}, {'id': 'end', 'from': .5, 'to': 1, 'composition': 'end-card', 'title': 'REVIEW', 'caption': 'Readable ending.'}]}))
        r = self.run_export('--spec', str(spec), '--width', '640', '--height', '360', '--samples', '2', '--grain', '2', '--bloom', '.05', '--ffmpeg', shutil.which('ffmpeg') or '/missing', '--ffprobe', shutil.which('ffprobe') or '/missing')
        self.assertEqual(r.returncode, 0, r.stderr)
        receipt = json.loads((self.out/'receipt.json').read_text()); self.assertEqual(receipt['status'], 'complete'); self.assertEqual(receipt['frames'], 10); self.assertTrue(receipt['faststart']); self.assertTrue(receipt['decodePassed']); self.assertTrue(receipt['captionsVerified']); self.assertTrue((self.out/'poster.png').is_file()); self.assertEqual(len(list((self.out/'frames').glob('*.png'))), 20)

        four_k = self.owner/'4k'
        high = subprocess.run([self.node, str(self.pkg/'export-film.mjs'), '--package', str(self.pkg), '--output', str(four_k), '--spec', str(spec), '--width', '3840', '--height', '2160', '--ffmpeg', shutil.which('ffmpeg') or '/missing', '--ffprobe', shutil.which('ffprobe') or '/missing'], capture_output=True, text=True, timeout=90)
        self.assertEqual(high.returncode, 0, high.stderr)
        profile = json.loads((four_k/'receipt.json').read_text()); video = next(s for s in profile['probe']['streams'] if s['codec_type']=='video')
        self.assertEqual((video['width'],video['height'],video['level']),(3840,2160,52)); self.assertTrue(profile['decodePassed'])
        # Interrupt a separate fresh render and verify receipt/owned process settlement.
        cancelled = self.owner/'cancelled'
        process = subprocess.Popen([self.node, str(self.pkg/'export-film.mjs'), '--package', str(self.pkg), '--output', str(cancelled), '--width', '640', '--height', '360', '--samples', '4'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                path = cancelled/'receipt.json'
                try: state = json.loads(path.read_text())['status']
                except (FileNotFoundError, json.JSONDecodeError): state = None
                if state == 'rendering': break
                if process.poll() is not None: self.fail('Cancellation control exited before rendering')
                time.sleep(.05)
            else: self.fail('Cancellation control did not reach rendering')
            process.send_signal(signal.SIGTERM); stdout, stderr = process.communicate(timeout=15)
            self.assertNotEqual(process.returncode, 0, stdout+stderr)
            interrupted = json.loads((cancelled/'receipt.json').read_text()); self.assertEqual(interrupted['status'], 'cancelled')
            self.assertTrue(interrupted['cleanup']['browserCloseCompleted']); self.assertTrue(all(c['exitCode'] is not None or c['signal'] is not None for c in interrupted['cleanup']['directChildren']))
        finally:
            if process.poll() is None: process.kill(); process.communicate()

    def streamed(self, source, tool=None, timeout='60'):
        spec = self.owner/'stream.json'; spec.write_text(json.dumps({'version': 1, 'title': 'Synthetic stream', 'fps': 30, 'bpm': 120, 'duration': 2, 'shots': [{'id': 'whole', 'from': 0, 'to': 2, 'composition': 'title', 'title': 'STREAM', 'caption': 'Synthetic pixels.'}]}))
        return self.run_export('--spec', str(spec), '--stream', '--frame-source', str(source), '--width', '320', '--height', '240', '--timeout', timeout, '--ffmpeg', tool or shutil.which('ffmpeg') or '/missing', '--ffprobe', shutil.which('ffprobe') or '/missing')

    def rgb_at(self, video, x, y):
        raw = subprocess.run([shutil.which('ffmpeg'), '-v', 'error', '-i', str(video), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
        return tuple(raw[(y*320+x)*3:(y*320+x)*3+3])

    @unittest.skipUnless(os.environ.get('MOTION_EXPORT_TESTS') == '1', 'Optional actual existing browser/FFmpeg export; set MOTION_EXPORT_TESTS=1')
    def test_actual_stream_keeps_frames_off_disk_and_writes_receipts(self):
        result = self.streamed(ROOT/'tests/fixtures/stream-film')
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((self.out/'receipt.json').read_text()); stream = receipt['stream']
        self.assertEqual(receipt['status'], 'complete'); self.assertFalse((self.out/'frames').exists())
        self.assertEqual((stream['capture'], stream['rowOrder'], stream['orientation'], stream['frames'], stream['bytes']), ('canvas-rgba', 'bottom-first', 'upright', 60, 60*320*240*4))
        self.assertEqual((stream['probe']['frames'], stream['probe']['colorSpace'], stream['decode']['frames'], stream['decode']['decoderMessages']), (60, 'bt709', 60, 0))
        self.assertTrue((self.out/'stream-probe.log').is_file()); self.assertTrue((self.out/'stream-decode.log').is_file())
        self.assertIn('/film.js', receipt['frameSource']['files'])
        top, bottom = self.rgb_at(self.out/'film.mp4', 200, 40), self.rgb_at(self.out/'film.mp4', 200, 200)
        self.assertGreater(top[0], 200); self.assertLess(top[1], 40); self.assertLess(top[2], 40)
        self.assertGreater(bottom[2], 200); self.assertLess(bottom[0], 40); self.assertLess(bottom[1], 40)

    @unittest.skipUnless(os.environ.get('MOTION_EXPORT_TESTS') == '1', 'Optional actual existing browser/FFmpeg export; set MOTION_EXPORT_TESTS=1')
    def test_actual_upside_down_passes_stop_before_encoding(self):
        broken = self.owner/'broken'; shutil.copytree(ROOT/'tests/fixtures/stream-film', broken)
        film = broken/'film.js'; text = film.read_text(); film.write_text(text.replace("const ART_V = '1. - uv.y'", "const ART_V = 'uv.y'"))
        result = self.streamed(broken)
        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads((self.out/'receipt.json').read_text())
        self.assertEqual(receipt['stream']['orientation'], 'flipped-vertical'); self.assertIn('orientation', receipt['error']); self.assertFalse((self.out/'film.mp4').exists())

    @unittest.skipUnless(os.environ.get('MOTION_EXPORT_TESTS') == '1', 'Optional actual existing browser/FFmpeg export; set MOTION_EXPORT_TESTS=1')
    def test_actual_encoder_death_fails_the_export_quickly(self):
        tool = self.owner/'ffmpeg'
        tool.write_text(f'#!/bin/sh\ncase "$1" in -version) exec {shutil.which("ffmpeg")} -version;; esac\nhead -c 100000 >/dev/null\nexit 9\n'); tool.chmod(0o700)
        started = time.monotonic(); result = self.streamed(ROOT/'tests/fixtures/stream-film', tool=str(tool))
        self.assertNotEqual(result.returncode, 0); self.assertLess(time.monotonic() - started, 30)
        receipt = json.loads((self.out/'receipt.json').read_text()); self.assertEqual(receipt['status'], 'failed'); self.assertIn('Encoder', receipt['error'])

    @unittest.skipUnless(os.environ.get('MOTION_EXPORT_TESTS') == '1', 'Optional actual existing browser/FFmpeg export; set MOTION_EXPORT_TESTS=1')
    def test_actual_stalled_encoder_hits_the_time_budget(self):
        tool = self.owner/'ffmpeg'
        tool.write_text(f'#!/bin/sh\ncase "$1" in -version) exec {shutil.which("ffmpeg")} -version;; esac\ntrap "" TERM\nsleep 60\n'); tool.chmod(0o700)
        started = time.monotonic(); result = self.streamed(ROOT/'tests/fixtures/stream-film', tool=str(tool), timeout='10')
        self.assertNotEqual(result.returncode, 0); self.assertLess(time.monotonic() - started, 25)
        receipt = json.loads((self.out/'receipt.json').read_text()); self.assertEqual(receipt['status'], 'cancelled'); self.assertTrue(receipt['cleanup']['browserCloseCompleted'])

    @unittest.skipUnless(os.environ.get('MOTION_EXPORT_TESTS') == '1', 'Optional actual existing browser/FFmpeg export; set MOTION_EXPORT_TESTS=1')
    def test_actual_dom_stage_streams_without_frames(self):
        spec = self.owner/'dom.json'; spec.write_text(json.dumps({'version': 1, 'title': 'Synthetic DOM stream', 'fps': 10, 'bpm': 120, 'duration': 1, 'shots': [{'id': 'whole', 'from': 0, 'to': 1, 'composition': 'title', 'title': 'STREAM', 'caption': 'Synthetic stage.'}]}))
        result = self.run_export('--spec', str(spec), '--stream', '--width', '640', '--height', '360', '--samples', '2', '--ffmpeg', shutil.which('ffmpeg') or '/missing', '--ffprobe', shutil.which('ffprobe') or '/missing')
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((self.out/'receipt.json').read_text())
        self.assertEqual((receipt['stream']['capture'], receipt['stream']['frames'], receipt['stream']['decode']['frames']), ('dom-png', 20, 10)); self.assertFalse((self.out/'frames').exists())
