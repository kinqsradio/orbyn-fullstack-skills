"""Synthetic flashing and steady clips for the post-render WCAG screen."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/technical-illustration/scripts/flash-check.py'
WIDTH, HEIGHT, FPS = 126, 72, 30
BLACK, WHITE = (0, 0, 0), (255, 255, 255)


def clip(path, hertz, first, second, patch=None, seconds=2):
    """Alternate two colours at `hertz`, across the frame or inside `patch` (x, y, w, h)."""
    x, y, w, h = patch or (0, 0, WIDTH, HEIGHT)
    period = FPS / hertz if hertz else None
    encoder = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-video_size', f'{WIDTH}x{HEIGHT}', '-framerate', str(FPS), '-i', '-', '-c:v', 'ffv1', str(path)], stdin=subprocess.PIPE)
    for frame in range(seconds * FPS):
        color = second if period and int(frame / (period / 2)) % 2 else first
        rows = bytearray(bytes(first) * WIDTH * HEIGHT)
        for row in range(y, y + h):
            rows[(row * WIDTH + x) * 3:(row * WIDTH + x + w) * 3] = bytes(color) * w
        encoder.stdin.write(rows)
    encoder.stdin.close()
    if encoder.wait():
        raise RuntimeError('Fixture encode failed')


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Existing FFmpeg unavailable; no installation')
class FlashCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'clip.mkv'

    def run_check(self, *args, **options):
        clip(self.path, *args, **options)
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.path)], capture_output=True, text=True, timeout=60)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_full_frame_flashing_fails(self):
        code, report = self.run_check(5, BLACK, WHITE)
        self.assertEqual((code, report['status']), (1, 'exceeds-three-flashes'))
        self.assertGreater(report['general']['worstFlashesPerSecond'], 3)

    def test_steady_frame_passes(self):
        code, report = self.run_check(0, (40, 90, 140), WHITE)
        self.assertEqual(code, 0)
        self.assertEqual(report['general']['worstFlashesPerSecond'], 0)

    def test_three_flashes_a_second_is_the_limit(self):
        self.assertEqual(self.run_check(3, BLACK, WHITE)[0], 0)
        self.assertEqual(self.run_check(4, BLACK, WHITE)[0], 1)

    def test_swing_under_ten_percent_passes(self):
        self.assertEqual(self.run_check(5, (118, 118, 118), (128, 128, 128))[0], 0)

    def test_both_states_above_the_dark_limit_pass(self):
        self.assertEqual(self.run_check(5, (235, 235, 235), WHITE)[0], 0)

    def test_localized_flash_filling_a_ten_degree_field_fails(self):
        code, report = self.run_check(5, BLACK, WHITE, patch=(42, 24, 42, 24))
        self.assertEqual(code, 1)
        self.assertIsNotNone(report['general']['windowCell'])

    def test_small_patch_under_the_area_limit_passes(self):
        self.assertEqual(self.run_check(5, BLACK, WHITE, patch=(60, 34, 6, 4))[0], 0)

    def test_saturated_red_flash_fails_without_a_luminance_swing(self):
        code, report = self.run_check(5, (200, 0, 0), (97, 97, 97))
        self.assertEqual(code, 1)
        self.assertEqual(report['general']['worstFlashesPerSecond'], 0)
        self.assertGreater(report['red']['worstFlashesPerSecond'], 3)

    def test_unreadable_input_reports_a_tool_failure(self):
        self.path.write_text('not a video')
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('flash-check:', result.stderr)


if __name__ == '__main__':
    unittest.main()
