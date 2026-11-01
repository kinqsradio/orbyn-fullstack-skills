"""Run the image puppet's Node tests under CI, which discovers Python tests only."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUPPET = ROOT/'skills/technical-illustration/examples/image-puppet'


@unittest.skipUnless(shutil.which('node'), 'Existing Node unavailable; no installation')
class ImagePuppetTests(unittest.TestCase):
    def test_puppet_suite(self):
        result = subprocess.run(['node', '--test', str(PUPPET/'puppet.test.mjs'), str(PUPPET/'mask.test.mjs')],
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:])

    def test_the_page_draws_from_the_time_it_is_given(self):
        page = (PUPPET/'film.mjs').read_text()
        self.assertIn('render({time})', page)
        self.assertNotIn('/ fps', page)


if __name__ == '__main__':
    unittest.main()
