"""Synthetic plates for the lyric and logo legibility screen."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'skills/technical-illustration/scripts/legibility-check.py'


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Existing FFmpeg unavailable; no installation')
class LegibilityCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'plate.mkv'

    def plate(self, source, *filters):
        command = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', source]
        command += ['-vf', ','.join(filters)] if filters else []
        subprocess.run([*command, '-c:v', 'ffv1', str(self.path)], check=True, timeout=60)

    def run_check(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.path), *args],
                                capture_output=True, text=True, timeout=60)
        return result.returncode, json.loads(result.stdout) if result.stdout else result.stderr

    def test_white_text_on_a_dark_plate_passes(self):
        self.plate('color=c=#101018:s=320x180:r=10:d=2')
        code, report = self.run_check('--box', 'lyric:.1,.7,.8,.15')
        self.assertEqual((code, report['status']), (0, 'pass'))
        self.assertGreater(report['boxes'][0]['worst_contrast'], 15)

    def test_white_text_on_a_bright_plate_fails(self):
        self.plate('color=c=#f0f0f0:s=320x180:r=10:d=2')
        code, report = self.run_check('--box', 'lyric:.1,.7,.8,.15')
        self.assertEqual((code, report['status']), (1, 'fail'))
        self.assertFalse(report['boxes'][0]['contrast_pass'])

    def test_a_bright_moment_is_found_and_timed(self):
        self.plate('color=c=#101018:s=320x180:r=10:d=4', "drawbox=c=white:t=fill:enable='between(t,2,3)'")
        code, report = self.run_check('--box', 'lyric:.1,.7,.8,.15')
        self.assertEqual(code, 1)
        self.assertTrue(2 <= report['boxes'][0]['at_seconds'] < 3.1, report)

    def test_a_time_range_ignores_frames_outside_the_box(self):
        self.plate('color=c=#101018:s=320x180:r=10:d=4', "drawbox=c=white:t=fill:enable='between(t,2,3)'")
        code, report = self.run_check('--box', 'lyric:.1,.7,.8,.15@0-1.9')
        self.assertEqual(code, 0, report)

    def test_a_small_bright_speck_does_not_fail_the_box(self):
        self.plate('color=c=#101018:s=320x180:r=10:d=2', 'drawbox=x=40:y=130:w=8:h=8:c=white:t=fill')
        self.assertEqual(self.run_check('--box', 'lyric:.1,.7,.8,.15')[0], 0)

    def test_a_bright_band_over_much_of_the_box_fails(self):
        self.plate('color=c=#101018:s=320x180:r=10:d=2', 'drawbox=x=0:y=126:w=320:h=14:c=white:t=fill')
        self.assertEqual(self.run_check('--box', 'lyric:.1,.7,.8,.15')[0], 1)

    def test_a_box_at_the_edge_fails_the_safe_area(self):
        self.plate('color=c=#101018:s=320x180:r=10:d=2')
        code, report = self.run_check('--box', 'logo:.01,.01,.1,.1', '--min-contrast', '3')
        self.assertEqual(code, 1)
        self.assertEqual((report['boxes'][0]['contrast_pass'], report['boxes'][0]['safe_area_pass']), (True, False))

    def test_dark_logo_colour_uses_the_given_foreground(self):
        self.plate('color=c=#f0f0f0:s=320x180:r=10:d=2')
        self.assertEqual(self.run_check('--box', 'logo:.8,.8,.1,.1', '--color', '#101018', '--min-contrast', '3')[0], 0)

    def test_a_still_image_is_one_frame(self):
        self.path = Path(self.temp.name)/'plate.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=#101018:s=320x180:d=0.1',
                        '-frames:v', '1', str(self.path)], check=True, timeout=30)
        code, report = self.run_check('--box', 'title:.1,.4,.8,.2')
        self.assertEqual((code, report['boxes'][0]['frames_checked']), (0, 1))

    def test_bad_input_cannot_pass(self):
        self.plate('color=c=#101018:s=320x180:r=10:d=2')
        self.assertEqual(self.run_check('--box', 'lyric:.5,.5,.8,.2')[0], 2)
        self.assertEqual(self.run_check('--box', 'lyric:.1,.7,.8,.15', '--color', 'white')[0], 2)
        self.assertEqual(self.run_check('--box', 'a:.1,.1,.1,.1', '--box', 'a:.2,.2,.1,.1')[0], 2)
        self.assertEqual(self.run_check('--box', 'lyric:.1,.7,.8,.15@9-10')[0], 2)
        self.path = Path(self.temp.name)/'missing.mkv'
        self.assertEqual(self.run_check('--box', 'lyric:.1,.7,.8,.15')[0], 2)


if __name__ == '__main__':
    unittest.main()
