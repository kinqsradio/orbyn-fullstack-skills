"""bg.py and bg.sh: start returns at once, wait blocks until the job ends or --max, exit codes, on-done and a lost supervisor."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/orbyn-workflow/scripts'


class BackgroundJobTests:
    """The behavior every helper shares; each subclass sets `launcher`, the command prefix that runs one helper."""
    launcher = None

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'jobs'

    def bg(self, *args):
        result = subprocess.run([*self.launcher, '--root', str(self.root), *args],
                                capture_output=True, text=True, timeout=60)
        return result.returncode, json.loads(result.stdout) if result.stdout.strip().startswith('{') else result.stderr

    def stop(self, job):
        """End a test's long child so the temporary folder can go."""
        info = json.loads((self.root / job / 'supervisor.json').read_text())
        self.kill(info['child_pid'])
        self.bg('wait', job, '--max', '10')

    @staticmethod
    def kill(pid):
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True)
        else:
            os.kill(pid, 9)

    def start(self, code, *extra):
        rc, out = self.bg('start', *extra, '--', sys.executable, '-c', code)
        self.assertEqual(rc, 0, out)
        self.await_supervisor(out['id'])
        return out['id']

    def await_supervisor(self, job):
        """The supervisor starts detached, so give a slow machine time to record the running child."""
        path = self.root / job
        deadline = time.monotonic() + 20
        while not (path / 'supervisor.json').exists() and not (path / 'exit.json').exists() and time.monotonic() < deadline:
            time.sleep(0.05)

    def test_start_returns_before_the_job_and_wait_returns_its_output(self):
        began = time.monotonic()
        rc, out = self.bg('start', '--', sys.executable, '-c', 'import time; time.sleep(3); print("finished")')
        self.assertLess(time.monotonic() - began, 3)
        job = out['id']
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

    def test_a_killed_supervisor_is_reported_lost(self):
        job = self.start('import time; time.sleep(30)')
        path = self.root / job
        deadline = time.monotonic() + 20
        while not (path / 'supervisor.json').exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        info = json.loads((path / 'supervisor.json').read_text())
        self.kill(info['pid'])
        self.kill(info['child_pid'])
        rc, out = self.bg('wait', job, '--max', '10')
        self.assertEqual((rc, out['state']), (4, 'lost'))


class PythonHelperTests(BackgroundJobTests, unittest.TestCase):
    launcher = [sys.executable, str(SCRIPTS / 'bg.py')]


def _shell_class(shell):
    path = shutil.which(shell)
    return type(f'{shell.capitalize()}HelperTests', (BackgroundJobTests, unittest.TestCase),
                {'launcher': [path, str(SCRIPTS / 'bg.sh')]})


for _shell in ('sh', 'bash', 'dash', 'zsh'):
    if shutil.which(_shell) and os.name != 'nt':
        globals()[f'{_shell.capitalize()}HelperTests'] = _shell_class(_shell)


if __name__ == '__main__':
    unittest.main()
