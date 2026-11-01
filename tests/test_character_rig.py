"""Runs the code-only film's rig tests, and compares its two height functions in headless Chrome."""
import glob
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILM = ROOT / 'skills/technical-illustration/examples/code-only-film'
TESTS = FILM / 'rig.test.mjs'


def chrome():
    """Find an existing Chrome. CHROME_PATH wins; nothing is installed."""
    home = Path.home()
    found = [os.environ.get('CHROME_PATH'), *(shutil.which(name) for name in ('google-chrome', 'chromium', 'chromium-browser', 'chrome')),
             '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
             *glob.glob(str(home / 'Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/*')),
             *glob.glob(str(home / '.cache/ms-playwright/chromium-*/chrome-linux*/chrome'))]
    return next((path for path in found if path and Path(path).is_file()), None)


def parity(folder):
    """Load the page through file:// and return what it wrote."""
    with tempfile.TemporaryDirectory() as profile:
        result = subprocess.run([chrome(), '--headless=new', '--no-first-run', f'--user-data-dir={profile}', '--allow-file-access-from-files',
                                 '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--virtual-time-budget=20000',
                                 '--dump-dom', (folder / 'height-parity.html').as_uri()], capture_output=True, text=True, timeout=90)
    match = re.search(r'<pre id="result">([^<]*)', result.stdout)
    return json.loads(match.group(1).replace('&quot;', '"')) if match else {'status': 'error', 'reason': result.stderr[-400:]}


@unittest.skipUnless(shutil.which('node'), 'Existing Node unavailable; no installation')
class CharacterRigTests(unittest.TestCase):
    def test_rig_contract(self):
        result = subprocess.run(['node', '--test', str(TESTS)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_page_draws_from_the_time_it_is_given(self):
        page = (FILM / 'film.mjs').read_text()
        self.assertIn('render({ index, time })', page)
        self.assertIn('frameState(time,', page)
        self.assertNotIn('index / fps', page)


@unittest.skipUnless(chrome(), 'Existing Chrome unavailable; set CHROME_PATH to run the shader comparison')
class HeightParityTests(unittest.TestCase):
    def outcome(self, folder):
        report = parity(folder)
        if report['status'] == 'unavailable':
            self.skipTest('This Chrome cannot read float pixels: ' + report['reason'])
        return report

    def test_the_shader_and_the_rig_agree_on_the_ground(self):
        report = self.outcome(FILM)
        self.assertEqual(report['status'], 'match', report)
        self.assertGreater(report['spread'][1] - report['spread'][0], 20, 'the samples covered real terrain')

    def test_the_comparison_notices_a_changed_shader(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / 'film'
            shutil.copytree(FILM, copy)
            shaders = copy / 'shaders.mjs'
            text = shaders.read_text()
            self.assertIn('(ridged(p * .07 + vec2(3.1, 0.), 3) - .42)', text)
            shaders.write_text(text.replace('(ridged(p * .07 + vec2(3.1, 0.), 3) - .42)', '(ridged(p * .07 + vec2(3.1, 0.), 3) - .43)'))
            self.assertEqual(self.outcome(copy)['status'], 'differ')


if __name__ == '__main__':
    unittest.main()
