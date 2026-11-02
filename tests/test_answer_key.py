"""Answer-key freeze and check: protected files, ancestry, failing commands, key location and cleanup."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'skills/orbyn-workflow/scripts/answer_key.py'
GIT_ENV = {'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@example.com', 'GIT_COMMITTER_NAME': 'T',
           'GIT_COMMITTER_EMAIL': 't@example.com', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_SYSTEM': os.devnull}
PYTHON = f'"{sys.executable}"'


class AnswerKeyCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.scratch = self.base / 'scratch'
        self.scratch.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.write('.gitignore', 'keys/\n')
        self.write('tests/test_app.py', "import pathlib, sys\nsys.exit(0 if pathlib.Path('app.txt').read_text() == 'done\\n' else 1)\n")
        self.write('app.txt', 'todo\n')
        self.commit('base')
        self.base_commit = self.rev('HEAD')
        self.check_cmd = f'{PYTHON} tests/test_app.py'

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True, text=True,
                                env={**os.environ, **GIT_ENV})
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def rev(self, ref):
        return self.git('rev-parse', ref)

    def write(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)
        return self.rev('HEAD')

    def run_tool(self, *args, expect):
        env = {**os.environ, 'TMPDIR': str(self.scratch)}
        result = subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def freeze(self, *extra, out=None, expect=0):
        out = out or self.base / 'key.json'
        args = ['freeze', '--repo', str(self.repo), '--task', 'demo', '--check', self.check_cmd,
                '--protect', 'tests', *extra, '--out', str(out)]
        self.run_tool(*args, expect=expect)
        return out

    def check(self, key, candidate, expect):
        result = self.run_tool('check', '--key', str(key), '--candidate', candidate, expect=expect)
        return result, (json.loads(result.stdout) if result.stdout.strip() else None)

    def solve(self):
        self.write('app.txt', 'done\n')
        return self.commit('solve')


class FreezeAndCheck(AnswerKeyCase):
    def test_a_correct_candidate_passes_and_commands_are_printed_first(self):
        key = self.freeze('--expect-file', 'app.txt')
        recorded = json.loads(key.read_text())
        self.assertEqual(recorded['base'], self.base_commit)
        self.assertEqual(list(recorded['protected'][0]['files']), ['tests/test_app.py'])
        result, report = self.check(key, self.solve(), 0)
        self.assertEqual(report['result'], 'pass')
        self.assertEqual([c['status'] for c in report['checks']], ['pass', 'pass'])
        self.assertIn(self.check_cmd, result.stderr)

    def test_a_changed_protected_file_fails(self):
        key = self.freeze()
        self.write('tests/test_app.py', 'import sys\nsys.exit(0)\n')
        self.write('app.txt', 'wrong\n')
        candidate = self.commit('weaken the test')
        _, report = self.check(key, candidate, 1)
        self.assertEqual(report['result'], 'fail')
        self.assertEqual(report['protected']['changed'], [{'path': 'tests/test_app.py', 'reason': 'modified'}])
        self.assertEqual(report['checks'], [])

    def test_a_deleted_or_added_protected_file_fails(self):
        key = self.freeze()
        (self.repo / 'tests' / 'test_app.py').unlink()
        self.write('tests/extra.py', 'pass\n')
        _, report = self.check(key, self.commit('swap tests'), 1)
        self.assertEqual({(c['path'], c['reason']) for c in report['protected']['changed']},
                         {('tests/test_app.py', 'missing'), ('tests/extra.py', 'added')})

    def test_a_candidate_not_descended_from_the_base_is_unusable(self):
        key = self.freeze()
        self.git('checkout', '-q', '--orphan', 'other')
        self.write('app.txt', 'done\n')
        other = self.commit('unrelated root')
        result, report = self.check(key, other, 2)
        self.assertIsNone(report)
        self.assertIn('does not descend', result.stderr)

    def test_an_unknown_candidate_or_broken_key_is_unusable(self):
        key = self.freeze()
        self.check(key, 'no-such-commit', 2)
        broken = self.base / 'broken.json'
        broken.write_text('{"schema_version": 1}')
        self.check(broken, self.base_commit, 2)
        broken.write_text('not json')
        self.check(broken, self.base_commit, 2)

    def test_a_failing_command_fails_the_check(self):
        key = self.freeze()
        _, report = self.check(key, self.base_commit, 1)
        self.assertEqual(report['result'], 'fail')
        self.assertEqual(report['checks'][0]['status'], 'fail')
        self.assertEqual(report['checks'][0]['exit_code'], 1)

    def test_a_missing_expected_file_fails(self):
        key = self.freeze('--expect-file', 'report.md')
        _, report = self.check(key, self.solve(), 1)
        self.assertEqual([(c['command'], c['status']) for c in report['checks']],
                         [('expect-file report.md', 'fail'), (self.check_cmd, 'pass')])

    def test_a_timeout_fails(self):
        key = self.base / 'slow.json'
        self.run_tool('freeze', '--repo', str(self.repo), '--task', 'slow', '--check', f'{PYTHON} -c "import time; time.sleep(30)"',
                      '--out', str(key), expect=0)
        result = self.run_tool('check', '--key', str(key), '--candidate', self.base_commit, '--timeout', '1', expect=1)
        self.assertIn('timed out', json.loads(result.stdout)['checks'][0]['note'])


class KeyLocation(AnswerKeyCase):
    def test_a_key_inside_the_tracked_tree_is_refused(self):
        out = self.repo / 'tests' / 'key.json'
        self.freeze(out=out, expect=2)
        self.assertFalse(out.exists())
        self.freeze(out=self.repo / 'key.json', expect=2)

    def test_an_ignored_folder_in_the_repo_is_allowed(self):
        (self.repo / 'keys').mkdir()
        out = self.freeze(out=self.repo / 'keys' / 'key.json')
        self.assertTrue(out.is_file())

    def test_an_existing_output_is_not_overwritten(self):
        out = self.freeze()
        before = out.read_text()
        self.freeze(out=out, expect=2)
        self.assertEqual(out.read_text(), before)

    def test_uncommitted_protected_changes_stop_freezing(self):
        self.write('tests/test_app.py', 'import sys\nsys.exit(0)\n')
        self.freeze(expect=2)


class CleanCopy(AnswerKeyCase):
    def test_an_uncommitted_solution_is_not_counted(self):
        key = self.freeze('--expect-file', 'notes.txt')
        self.write('app.txt', 'done\n')
        self.write('notes.txt', 'uncommitted\n')
        _, report = self.check(key, self.base_commit, 1)
        self.assertEqual({c['command']: c['status'] for c in report['checks']},
                         {'expect-file notes.txt': 'fail', self.check_cmd: 'fail'})

    def test_an_uncommitted_edit_to_a_protected_file_is_not_counted(self):
        key = self.freeze()
        candidate = self.solve()
        self.write('tests/test_app.py', 'import sys\nsys.exit(1)\n')
        _, report = self.check(key, candidate, 0)
        self.assertEqual(report['protected']['status'], 'pass')

    def test_temporary_files_are_removed_and_the_repository_is_untouched(self):
        key = self.freeze()
        for candidate, expect in ((self.solve(), 0), (self.base_commit, 1)):
            self.check(key, candidate, expect)
            self.assertEqual(list(self.scratch.iterdir()), [])
        self.assertEqual(self.git('worktree', 'list').count('\n'), 0)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_a_command_runs_with_a_minimal_environment(self):
        key = self.base / 'env.json'
        script = "import os, sys; sys.exit(0 if 'ORBYN_SECRET' not in os.environ else 1)"
        self.run_tool('freeze', '--repo', str(self.repo), '--task', 'env', '--check', f'{PYTHON} -c "{script}"',
                      '--out', str(key), expect=0)
        env = {**os.environ, 'TMPDIR': str(self.scratch), 'ORBYN_SECRET': 'x'}
        result = subprocess.run([sys.executable, str(TOOL), 'check', '--key', str(key), '--candidate', self.base_commit],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
