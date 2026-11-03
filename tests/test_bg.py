"""bg.py: start returns at once, wait blocks until the job ends or --max, exit codes, on-done and a lost supervisor."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'skills/orbyn-workflow/scripts/bg.py'


class BackgroundJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'jobs'

    def bg(self, *args):
        result = subprocess.run([sys.executable, str(TOOL), '--root', str(self.root), *args],
                                capture_output=True, text=True, timeout=60)
        return result.returncode, json.loads(result.stdout) if result.stdout.strip().startswith('{') else result.stderr

    def stop(self, job):
        """End a test's long child so the temporary folder can go."""
        info = json.loads((self.root / job / 'supervisor.json').read_text())
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(info['child_pid'])], capture_output=True)
        else:
            os.kill(info['child_pid'], 9)
        self.bg('wait', job, '--max', '10')

    def start(self, code, *extra):
        rc, out = self.bg('start', *extra, '--', sys.executable, '-c', code)
        self.assertEqual(rc, 0, out)
        return out['id']

    def test_start_returns_before_the_job_and_wait_returns_its_output(self):
        began = time.monotonic()
        job = self.start('import time; time.sleep(1.5); print("finished")')
        self.assertLess(time.monotonic() - began, 1.5)
        rc, out = self.bg('wait', job, '--max', '30')
        self.assertEqual((rc, out['state'], out['exit_code']), (0, 'done', 0))
        self.assertIn('finished', out['tail'])

    def test_wait_stops_at_max_and_reports_running(self):
        job = self.start('import time; time.sleep(20)')
        began = time.monotonic()
        rc, out = self.bg('wait', job, '--max', '1')
        self.assertLess(time.monotonic() - began, 10)
        self.assertEqual((rc, out['state']), (3, 'running'))
        self.stop(job)

    def test_a_failing_job_returns_its_exit_code(self):
        job = self.start('import sys; print("boom"); sys.exit(7)')
        rc, out = self.bg('wait', job, '--max', '30')
        self.assertEqual((rc, out['exit_code']), (7, 7))
        self.assertIn('boom', out['tail'])

    def test_a_missing_program_is_recorded_not_hung(self):
        rc, out = self.bg('start', '--', str(Path(self.temp.name) / 'no-such-program'))
        rc, out = self.bg('wait', out['id'], '--max', '30')
        self.assertEqual((rc, out['state'], out['exit_code']), (127, 'done', 127))

    def test_on_done_runs_after_the_job_with_its_exit_code(self):
        marker = Path(self.temp.name) / 'done.txt'
        hook = f'"{sys.executable}" -c "import os,pathlib; pathlib.Path(r\'{marker}\').write_text(os.environ[\'BG_EXIT_CODE\'])"'
        job = self.start('import sys; sys.exit(2)', '--on-done', hook)
        rc, _ = self.bg('wait', job, '--max', '30')
        self.assertEqual(rc, 2)
        deadline = time.monotonic() + 20
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertEqual(marker.read_text(), '2')

    def test_status_does_not_wait_and_unknown_jobs_are_refused(self):
        job = self.start('import time; time.sleep(20)')
        began = time.monotonic()
        rc, out = self.bg('status', job)
        self.assertLess(time.monotonic() - began, 10)
        self.assertEqual(rc, 3)
        self.assertIn(out['state'], ('running', 'starting'))
        for bad in ('nope', '../x', '.hidden'):
            rc, err = self.bg('status', bad)
            self.assertNotEqual(rc, 0)
            self.assertIn('no job', err)
        self.stop(job)

    @unittest.skipIf(os.name == 'nt', 'POSIX signal')
    def test_a_killed_supervisor_is_reported_lost(self):
        job = self.start('import time; time.sleep(30)')
        path = self.root / job
        deadline = time.monotonic() + 20
        while not (path / 'supervisor.json').exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        info = json.loads((path / 'supervisor.json').read_text())
        os.kill(info['pid'], 9)
        os.kill(info['child_pid'], 9)
        rc, out = self.bg('wait', job, '--max', '10')
        self.assertEqual((rc, out['state']), (4, 'lost'))


if __name__ == '__main__':
    unittest.main()
