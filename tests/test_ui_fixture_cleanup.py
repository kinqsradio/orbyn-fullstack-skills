"""Failure controls for opt-in fixture setup; no Playwright/browser installation."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BrowserFixtureCleanupTests(unittest.TestCase):
    def run_failure(self, module_source, expected, *, close_failures=False):
        node = shutil.which('node')
        if not node:
            self.skipTest('Existing Node required; no installation')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            temporary = root / 'temporary'
            temporary.mkdir()
            module = root / 'fake-playwright.mjs'
            if module_source is not None:
                module.write_text(module_source, encoding='utf-8')
            preparer = shutil.which('true') if close_failures else str(root / 'unavailable-preparer')
            if close_failures and not preparer:
                self.skipTest('Existing no-op executable required for synthetic successful preparation')
            env = {**os.environ, 'REVIEW_BROWSER_TESTS': '1',
                   'REVIEW_PLAYWRIGHT': module.as_uri(),
                   'REVIEW_PYTHON': preparer, 'REVIEW_CLEANUP_RECEIPT': str(root / 'cleanup.txt'),
                   'TMPDIR': str(temporary), 'TMP': str(temporary), 'TEMP': str(temporary)}
            # Successful process exit (with a failing test status) is the leak
            # witness: an open HTTP listener would keep this child alive.
            result = subprocess.run([node, '--test', str(ROOT / 'tests/ui-fixtures.browser.mjs')],
                                    cwd=ROOT, env=env, capture_output=True, text=True, timeout=8)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(expected, result.stdout + result.stderr)
            self.assertEqual(list(temporary.iterdir()), [], 'Fixture failure leaked a temp directory')
            if close_failures:
                self.assertEqual((root / 'cleanup.txt').read_text(encoding='utf-8'), 'close\nclose\n')

    def test_missing_playwright_releases_listeners_and_failed_preparation_temp(self):
        self.run_failure(None, 'ERR_MODULE_NOT_FOUND')

    def test_browser_startup_failure_releases_listeners(self):
        self.run_failure("export const chromium = {launch: async () => {throw new Error('startup failed')}};", 'startup failed')

    def test_browser_close_failure_does_not_prevent_server_or_temp_cleanup(self):
        self.run_failure("""import {appendFileSync} from 'node:fs';
        export const chromium = {launch: async () => ({
            newPage: async () => {throw new Error('page failed')},
            close: async () => {appendFileSync(process.env.REVIEW_CLEANUP_RECEIPT, 'close\\n'); throw new Error('close failed')}
        })};""", 'page failed', close_failures=True)


if __name__ == '__main__':
    unittest.main()
