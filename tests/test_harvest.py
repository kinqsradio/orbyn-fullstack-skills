"""harvest.py: a case from a fix commit has no future history, a hidden key outside the fixture, cleaned task text,
and is refused inside the project clone."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/orbyn-skill-creator/scripts'
GIT_ENV = {'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@example.com', 'GIT_COMMITTER_NAME': 'T',
           'GIT_COMMITTER_EMAIL': 't@example.com', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_SYSTEM': os.devnull}


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


harvest = load('harvest')
evaluate = load('evaluate')
eval_run = load('eval_run')

MESSAGE = """Fix the off-by-one in add()

add() returned a + b - 1. See https://example.com/issues/12 for the report.
Reported by dev@example.com with api_key=sk-abcdef1234567890 and token: ghp_0123456789abcdefghij.
Regression of 1a2b3c4d5e6f.

Co-authored-by: Someone <someone@example.com>
"""


class HarvestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / 'project'
        self.repo.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.write('calc.py', 'def add(a, b):\n    return a + b - 1\n')
        self.write('tests/test_calc.py', 'import unittest\nfrom calc import add\n\n\nclass T(unittest.TestCase):\n'
                   '    def test_zero(self):\n        self.assertEqual(add(0, 0), -1)\n')
        self.commit('initial')
        self.parent = self.rev('HEAD')
        self.write('calc.py', 'def add(a, b):\n    return a + b\n')
        self.write('tests/test_calc.py', 'import unittest\nfrom calc import add\n\n\nclass T(unittest.TestCase):\n'
                   '    def test_zero(self):\n        self.assertEqual(add(0, 0), 0)\n')
        self.write('tests/test_more.py', 'import unittest\nfrom calc import add\n\n\nclass M(unittest.TestCase):\n'
                   '    def test_two(self):\n        self.assertEqual(add(1, 1), 2)\n')
        self.commit(MESSAGE)
        self.fix = self.rev('HEAD')
        self.write('later.py', 'FUTURE = True\n')
        self.commit('later work')
        self.check = f'"{sys.executable}" -m unittest discover -s tests'

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True, text=True, env={**os.environ, **GIT_ENV})
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

    def run_harvest(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = harvest.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class HarvestTests(HarvestCase):
    def test_builds_a_case_from_the_fix_commit(self):
        out = self.base / 'cases' / 'calc-fix'
        code, text, err = self.run_harvest('--repo', str(self.repo), '--commit', self.fix, '--out', str(out),
                                           '--check', self.check, '--id', 'calc-fix')
        self.assertEqual(code, 0, err)
        info = json.loads(text)
        self.assertEqual(info['base'], self.parent)
        fixture = out / 'fixture'
        self.assertEqual((fixture / 'calc.py').read_text(), 'def add(a, b):\n    return a + b - 1\n')
        self.assertFalse((fixture / 'later.py').exists(), 'no future files')
        self.assertFalse((fixture / '.git').exists(), 'no history of any kind')
        self.assertFalse((fixture / 'tests/test_more.py').exists())
        key = json.loads((out / 'key/key.json').read_text())
        self.assertEqual(key['protected'], ['tests/test_calc.py'])  # added tests do not exist at the base
        self.assertEqual(key['checks'], [self.check])
        hidden = out / 'key/hidden'
        self.assertIn('add(0, 0), 0', (hidden / 'tests/test_calc.py').read_text())
        self.assertTrue((hidden / 'tests/test_more.py').is_file())
        case = json.loads((out / 'case.json').read_text())
        for leak in ('https://', 'example.com', 'sk-abcdef', 'ghp_', '1a2b3c4d', 'Co-authored', 'dev@', self.fix[:8], 'test_more'):
            self.assertNotIn(leak, case['prompt'])
        self.assertIn('off-by-one', case['prompt'])
        self.assertNotIn(self.fix, json.dumps(case))
        self.assertTrue(case['id'] == 'calc-fix' and 'push' in case['forbidden_actions'])

    def test_harvested_case_is_runnable_and_graded_by_its_key(self):
        out = self.base / 'cases' / 'calc-fix'
        self.assertEqual(self.run_harvest('--repo', str(self.repo), '--commit', self.fix, '--out', str(out),
                                          '--check', self.check, '--id', 'calc-fix')[0], 0)
        loaded = evaluate.load_executable(out.parent)
        self.assertEqual([c['id'] for c in loaded], ['calc-fix'])
        case = loaded[0]
        work = self.base / 'work'
        grade_dir = self.base / 'grade'
        grade_dir.mkdir()
        base = eval_run.export_fixture(case, work)
        # unfixed tree fails the hidden tests
        final = eval_run.git(work, 'rev-parse', 'HEAD').stdout.strip()
        self.assertEqual(eval_run.grade_candidate(case, work, base, final, grade_dir)['result'], 'fail')
        (work / 'calc.py').write_text('def add(a, b):\n    return a + b\n')
        eval_run.git(work, 'add', '-A')
        eval_run.git(work, 'commit', '-q', '-m', 'fix')
        final = eval_run.git(work, 'rev-parse', 'HEAD').stdout.strip()
        grade_dir2 = self.base / 'grade2'
        grade_dir2.mkdir()
        self.assertEqual(eval_run.grade_candidate(case, work, base, final, grade_dir2)['result'], 'pass')
        # editing a protected test is a failure even when the code is right
        (work / 'tests/test_calc.py').write_text('import unittest\n')
        eval_run.git(work, 'add', '-A')
        eval_run.git(work, 'commit', '-q', '-m', 'tamper')
        final = eval_run.git(work, 'rev-parse', 'HEAD').stdout.strip()
        grade_dir3 = self.base / 'grade3'
        grade_dir3.mkdir()
        report = eval_run.grade_candidate(case, work, base, final, grade_dir3)
        self.assertEqual((report['result'], report['protected']['status']), ('fail', 'fail'))

    def test_output_inside_the_repository_is_refused(self):
        for target in (self.repo / 'evals' / 'case', self.repo / 'tests' / 'case', self.repo / 'newdir' / 'a' / 'b'):
            code, _, err = self.run_harvest('--repo', str(self.repo), '--commit', self.fix, '--out', str(target),
                                            '--check', self.check)
            self.assertEqual(code, 2)
            self.assertIn('inside the repository', err)
            self.assertFalse(target.exists())
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_default_output_is_the_workspace_evals_folder_outside_the_clone(self):
        default = harvest.default_out(self.repo, 'x-1')
        self.assertEqual(default.parts[-4:], ('repo', '.evals', 'project', 'x-1'))
        self.assertEqual(default.relative_to(harvest.ROOT).parts[0], 'repo')
        self.assertFalse(harvest.inside(default, self.repo))
        self.assertEqual(subprocess.run(['git', '-C', str(harvest.ROOT), 'check-ignore', '-q', 'repo/.evals/project/x-1']).returncode, 0)

    def test_refuses_without_tests_or_checks_or_merge_commits(self):
        code, _, err = self.run_harvest('--repo', str(self.repo), '--commit', self.fix, '--out', str(self.base / 'a'))
        self.assertEqual((code, 'check' in err), (2, True))
        later = self.rev('HEAD')
        code, _, err = self.run_harvest('--repo', str(self.repo), '--commit', later, '--out', str(self.base / 'b'), '--check', 'true')
        self.assertEqual((code, 'no test files' in err), (2, True))
        self.git('checkout', '-q', '-b', 'side', self.parent)
        self.write('side.py', 'S = 1\n')
        self.commit('side')
        self.git('checkout', '-q', 'main')
        self.git('merge', '-q', '--no-ff', '-m', 'merge side', 'side')
        code, _, err = self.run_harvest('--repo', str(self.repo), '--commit', self.rev('HEAD'), '--out', str(self.base / 'c'), '--check', 'true')
        self.assertEqual((code, 'one parent' in err), (2, True))

    def test_sanitize(self):
        text = harvest.sanitize('Use https://a.example/x?token=abc and password=hunter2 or Bearer abc123 now')
        for leak in ('https', 'hunter2', 'abc123'):
            self.assertNotIn(leak, text)


if __name__ == '__main__':
    unittest.main()
