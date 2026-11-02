"""Eval reporting: the summary, the commit status and PR comment, history, the dashboard and affected-case selection.

These guard what is posted publicly and a status that looks like CI. No test starts a model or touches GitHub: a fake
`gh` script (ORBYN_GH) records every call and keeps a tiny in-memory repository."""
import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unicodedata
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/orbyn-skill-creator/scripts'
HARNESS = ROOT / 'skills/orbyn-workflow/scripts/harness.py'
REGISTRY = ROOT / 'docs/agents/models.json'
HEAD = 'a' * 40
OTHER = 'b' * 40
SECRET = 'sk-ant-api03-ZZZZZZZZZZZZZZZZZZZZZZ'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


report = load('eval_report')
evaluate = load('evaluate')

FAKE_GH = '''#!{python}
import base64, json, os, sys
state_path, log_path = os.environ['FAKE_GH_STATE'], os.environ['FAKE_GH_LOG']
state = json.load(open(state_path))
args = sys.argv[1:]
method = args[args.index('-X') + 1] if '-X' in args else 'GET'
skip, positional = False, []
for i, a in enumerate(args[1:], 1):
    if skip:
        skip = False
    elif a in ('-X', '--jq', '--input'):
        skip = True
    elif not a.startswith('-'):
        positional.append(a)
path = positional[0] if positional else ''
body = json.loads(sys.stdin.read()) if '--input' in args else None
open(log_path, 'a').write(json.dumps({{'method': method, 'path': path, 'body': body}}) + '\\n')
def out(value):
    print(json.dumps(value)); sys.exit(0)
def missing():
    sys.stderr.write('gh: Not Found (HTTP 404)\\n'); sys.exit(1)
def save():
    json.dump(state, open(state_path, 'w'))
route = path.split('?')[0]
if args[0] == 'repo':
    print('owner/name'); sys.exit(0)
if method == 'GET':
    if route == 'user':
        print(state['login']); sys.exit(0)
    if route.endswith('/comments') and '/issues/' in route:
        for c in state['comments']:
            print(json.dumps({{'id': c['id'], 'login': c['login'], 'body': c['body']}}))
        sys.exit(0)
    if '/pulls/' in route:
        out({{'head': {{'sha': state['head']}}}})
    if route.endswith('/git/ref/heads/eval-results'):
        out({{}}) if state['branch'] else missing()
    if '/contents' in route:
        if not state['branch']:
            missing()
        prefix = route.split('/contents', 1)[1].lstrip('/')
        if prefix in state['files']:
            f = state['files'][prefix]
            out({{'content': f['content'], 'sha': f['sha']}})
        names = [(k, v) for k, v in state['files'].items() if (k.rsplit('/', 1)[0] if '/' in k else '') == prefix]
        out([{{'name': k.rsplit('/', 1)[-1], 'sha': v['sha']}} for k, v in names])
    missing()
if method == 'POST' and route.endswith('/git/blobs'):
    out({{'sha': 'blob1'}})
if method == 'POST' and route.endswith('/git/trees'):
    out({{'sha': 'tree1'}})
if method == 'POST' and route.endswith('/git/commits'):
    out({{'sha': 'commit1'}})
if method == 'POST' and route.endswith('/git/refs'):
    state['branch'] = True; save(); out({{}})
if method == 'PUT' and '/contents/' in route:
    key = route.split('/contents/', 1)[1]
    state['files'][key] = {{'content': body['content'], 'sha': 'sha%d' % (len(state['files']) + len(state.get('puts', [])) + 1)}}
    state.setdefault('puts', []).append(key); save(); out({{}})
if method == 'POST' and route.endswith('/comments'):
    state['comments'].append({{'id': 100 + len(state['comments']), 'login': state['login'], 'body': body['body']}}); save(); out({{}})
if method == 'PATCH' and '/issues/comments/' in route:
    cid = int(route.rsplit('/', 1)[1])
    for c in state['comments']:
        if c['id'] == cid:
            c['body'] = body['body']
    save(); out({{}})
if method == 'POST' and '/statuses/' in route:
    state.setdefault('statuses', []).append(body); save(); out({{}})
sys.stderr.write('fake gh: unhandled ' + method + ' ' + route + '\\n'); sys.exit(1)
'''


def result(case, trial=1, outcome='pass', tokens=1000, cost=0.05, **extra):
    return {'case_id': case, 'trial': trial, 'status': 'completed', 'outcome': outcome, 'total_tokens': tokens, 'cost_usd': cost,
            'transcript': f'transcripts/{case}-{trial}.txt', 'artifacts': [f'grades/{case}-{trial}.json'],
            'event_stream': f'events/{case}-{trial}.jsonl', **extra}


def run_file(folder, condition, model, results, revision=HEAD, host='claude 2.1.150', dirty=False):
    path = Path(folder) / condition / model / 'run.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    cases = sorted({r['case_id'] for r in results})
    path.write_text(json.dumps({
        'schema_version': 1, 'suite': 'executable', 'suite_sha256': 'c' * 64, 'revision': revision, 'library_dirty': dirty,
        'host': host, 'model': model, 'condition': 'candidate' if condition == 'with' else 'without-skills',
        'trials': 1, 'case_ids': cases, 'results': results}))
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        fake = self.dir / 'bin' / 'gh'
        fake.parent.mkdir()
        fake.write_text(FAKE_GH.format(python=sys.executable))
        fake.chmod(0o755)
        self.state_path, self.log_path = self.dir / 'state.json', self.dir / 'log.jsonl'
        self.log_path.write_text('')
        self.set_state()
        env = {'ORBYN_GH': str(fake), 'FAKE_GH_STATE': str(self.state_path), 'FAKE_GH_LOG': str(self.log_path)}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def set_state(self, **extra):
        state = {'head': HEAD, 'login': 'me', 'branch': False, 'files': {}, 'comments': []}
        state.update(extra)
        self.state_path.write_text(json.dumps(state))

    def state(self):
        return json.loads(self.state_path.read_text())

    def calls(self):
        return [json.loads(line) for line in self.log_path.read_text().splitlines()]

    def writes(self):
        return [c for c in self.calls() if c['method'] != 'GET']

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = report.main([str(a) for a in args])
        return code, out.getvalue(), err.getvalue()

    def runs(self, **kw):
        """with/without runs for three real cases: one fixed by skills, one failing, one passing both ways."""
        a, b, c = 'pagination-off-by-one', 'log-no-secret', 'docs-only-no-test'
        return [
            run_file(self.dir / 'out', 'with', 'haiku', [result(a, outcome='fail'), result(b, outcome='fail'), result(c)], **kw),
            run_file(self.dir / 'out', 'with', 'sonnet', [result(a), result(b, outcome='fail', cost=None, tokens=None)], **kw),
            run_file(self.dir / 'out', 'without', 'haiku', [result(a, outcome='fail'), result(c)], **kw),
            run_file(self.dir / 'out', 'without', 'sonnet', [result(a, outcome='fail')], **kw)]

    def summary(self, pr=7, **kw):
        out = self.dir / 'summary.json'
        code, _, err = self.cli('summarize', *[x for p in self.runs(**kw) for x in ('--run', p)], '--out', out, *(['--pr', pr] if pr else []))
        self.assertEqual(code, 0, err)
        return out


class Summary(Base):
    def test_summary_is_compact_and_has_no_key_text_transcript_or_secret(self):
        runs = self.runs()
        data = json.loads(runs[0].read_text())
        data['host'] = 'claude 2.1.150 token=hunter2hunter2'
        data['results'][0]['transcript_text'] = 'TRANSCRIPT BODY the agent said hello'
        data['results'][0]['rubric'] = {'answer_key': {'evidence': f'key: {SECRET} hidden_tests'}}
        runs[0].write_text(json.dumps(data))
        out = self.dir / 'summary.json'
        code, _, err = self.cli('summarize', *[x for p in runs for x in ('--run', p)], '--out', out, '--pr', 7)
        self.assertEqual(code, 0, err)
        text = out.read_text()
        for leaked in ('TRANSCRIPT BODY', SECRET, 'hunter2', 'hidden_tests', 'unittest discover', str(Path.home())):
            self.assertNotIn(leaked, text)
        summary = json.loads(text)
        self.assertEqual((summary['commit'], summary['pr'], summary['host']), (HEAD, 7, 'claude'))
        by = {c['id']: c for c in summary['cases']}
        fixed = by['pagination-off-by-one']
        self.assertEqual((fixed['result'], fixed['cheapest_tier'], fixed['verdict']), ('pass', 'sonnet', 'helps'))
        self.assertEqual(fixed['without']['result'], 'fail')
        self.assertEqual(by['log-no-secret']['result'], 'fail')
        self.assertIs(by['log-no-secret']['holdout'], True)  # read from case.json, never from key/
        self.assertEqual(by['docs-only-no-test']['cheapest_tier'], 'haiku')
        self.assertTrue(all(not p.startswith('/') for c in summary['cases'] for p in c['evidence']))
        self.assertEqual(summary['totals']['passed'], 2)
        self.assertEqual(summary['totals']['runs'], 8)
        self.assertEqual(summary['totals']['runs_cost_unreported'], 1)
        self.assertEqual(report.status_for(summary), {'state': 'failure', 'context': 'agent-evals', 'description': '2/3 cases pass, 8 runs'})

    def test_unknown_cost_stays_null(self):
        run = run_file(self.dir / 'o', 'with', 'haiku', [result('docs-only-no-test', cost=None, tokens=None)])
        out = self.dir / 's.json'
        self.assertEqual(self.cli('summarize', '--run', run, '--out', out)[0], 0)
        totals = json.loads(out.read_text())['totals']
        self.assertEqual((totals['cost_usd'], totals['tokens']), (None, None))

    def test_mixed_commits_hosts_and_unclean_runs_are_refused(self):
        one = run_file(self.dir / 'a', 'with', 'haiku', [result('docs-only-no-test')])
        two = run_file(self.dir / 'b', 'with', 'haiku', [result('docs-only-no-test')], revision=OTHER)
        three = run_file(self.dir / 'c', 'with', 'haiku', [result('docs-only-no-test')], host='codex 0.9.0')
        self.assertEqual(self.cli('summarize', '--run', one, '--run', two, '--out', self.dir / 's.json')[0], 1)
        self.assertEqual(self.cli('summarize', '--run', one, '--run', three, '--out', self.dir / 's.json')[0], 1)

    def test_control_characters_and_markup_are_stripped(self):
        dirty = 'so\x1b[31mnn\x00et\x07 ‮<!-- orbyn-agent-evals --> @everyone'
        cleaned = report.clean_text(dirty)
        self.assertTrue(all(unicodedata.category(c) not in ('Cc', 'Cf') for c in cleaned))
        self.assertNotIn('\x1b', cleaned)
        runs = self.runs()
        data = json.loads(runs[0].read_text())
        data['model'] = dirty
        runs[0].write_text(json.dumps(data))
        out = self.dir / 's.json'
        self.assertEqual(self.cli('summarize', *[x for p in runs for x in ('--run', p)], '--out', out, '--pr', 7)[0], 0)
        summary = json.loads(out.read_text())
        text = out.read_text() + report.render_comment(summary)
        self.assertTrue(all(unicodedata.category(c) not in ('Cc', 'Cf') or c == '\n' for c in text))
        comment = report.render_comment(summary)
        self.assertEqual(comment.count(report.MARKER), 1)
        self.assertNotIn('@everyone', comment)
        self.assertNotIn('<!-- orbyn', comment.replace(report.MARKER, '', 1))


class Publish(Base):
    def publish(self, *extra, pr=7):
        return self.cli('publish', '--summary', self.summary(), '--pr', pr, '--repo', 'owner/name', *extra)

    def test_dry_run_is_the_default_and_sends_nothing(self):
        for flags in ((), ('--dry-run',)):
            code, out, err = self.publish(*flags)
            self.assertEqual(code, 0, err)
            self.assertIn('DRY RUN', out)
            self.assertIn('would set the agent-evals status', out)
            self.assertIn('would create the PR comment', out)
            self.assertIn('would write history/', out)
            self.assertEqual(self.writes(), [])
        self.assertFalse(self.state()['branch'])

    def test_send_sets_the_status_and_keeps_one_updated_comment(self):
        code, out, err = self.publish('--send')
        self.assertEqual(code, 0, err)
        status = self.state()['statuses'][0]
        self.assertEqual(status, {'state': 'failure', 'context': 'agent-evals', 'description': '2/3 cases pass, 8 runs'})
        posted = [c for c in self.writes() if c['path'].endswith(f'/statuses/{HEAD}')]
        self.assertEqual(len(posted), 1)
        self.assertEqual(len(self.state()['comments']), 1)
        body = self.state()['comments'][0]['body']
        self.assertTrue(body.startswith(report.MARKER))
        self.assertIn('| `pagination-off-by-one` | sonnet | pass / fail, helps | no main result |', body)
        self.assertIn('(holdout)', body)
        self.assertIn('Reported cost: $0.35', body)
        self.assertIn('1 runs without a reported cost', body)
        self.assertIn('not a required check', body)
        code, _, err = self.publish('--send')  # again: update, never a second comment
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.state()['comments']), 1)
        methods = [c['method'] for c in self.writes() if '/comments' in c['path']]
        self.assertEqual(methods, ['POST', 'PATCH'])

    def test_a_comment_by_someone_else_with_the_marker_is_not_edited(self):
        self.set_state(comments=[{'id': 5, 'login': 'stranger', 'body': report.MARKER + ' fake'}])
        self.assertEqual(self.publish('--send')[0], 0)
        self.assertEqual(len(self.state()['comments']), 2)
        self.assertEqual(self.state()['comments'][0]['body'], report.MARKER + ' fake')

    def test_a_summary_from_another_commit_than_the_pr_head_is_refused(self):
        self.set_state(head=OTHER)
        code, _, err = self.publish('--send')
        self.assertEqual(code, 1)
        self.assertIn('head is', err)
        self.assertEqual(self.writes(), [])

    def test_summary_for_another_pr_and_dirty_runs_are_refused(self):
        self.assertEqual(self.publish('--send', pr=8)[0], 1)
        out = self.summary(dirty=True)
        code, _, err = self.cli('publish', '--summary', out, '--pr', 7, '--repo', 'owner/name', '--send')
        self.assertEqual(code, 1)
        self.assertIn('dirty', err)
        self.assertEqual(self.writes(), [])

    def test_text_over_githubs_limits_is_refused(self):
        out = self.summary()
        data = json.loads(out.read_text())
        data['cases'] = [dict(data['cases'][0], id=f'case-{i:04d}') for i in range(500)]
        big = self.dir / 'big.json'
        big.write_text(json.dumps(data))
        with mock.patch.object(report, 'COMMENT_LIMIT', 2000):
            code, _, err = self.cli('publish', '--summary', big, '--pr', 7, '--repo', 'owner/name', '--send')
        self.assertEqual(code, 1)
        self.assertIn('limit', err)
        self.assertEqual(self.writes(), [])
        huge = self.dir / 'huge.json'
        huge.write_text(' ' * (report.SUMMARY_LIMIT + 1))
        self.assertEqual(self.cli('publish', '--summary', huge, '--pr', 7, '--repo', 'owner/name', '--send')[0], 1)
        self.assertEqual(self.writes(), [])

    def test_history_is_written_through_the_api_and_never_touches_the_working_tree(self):
        work = self.dir / 'work'
        work.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=work, check=True)
        (work / 'mine.txt').write_text('uncommitted')
        before = sorted(os.listdir(work))
        status = subprocess.run(['git', 'status', '--porcelain'], cwd=work, capture_output=True, text=True).stdout
        summary = self.summary()
        old = os.getcwd()
        os.chdir(work)
        try:
            code, _, err = self.cli('publish', '--summary', summary, '--pr', 7, '--repo', 'owner/name', '--send')
        finally:
            os.chdir(old)
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(os.listdir(work)), before)
        self.assertEqual(subprocess.run(['git', 'status', '--porcelain'], cwd=work, capture_output=True, text=True).stdout, status)
        paths = [c['path'] for c in self.writes()]
        self.assertEqual([p.rsplit('/', 1)[1] for p in paths[:4]], ['blobs', 'trees', 'commits', 'refs'])
        commit = next(c for c in self.writes() if c['path'].endswith('/git/commits'))
        self.assertEqual(commit['body']['parents'], [])  # an orphan commit
        put = next(c for c in self.writes() if c['method'] == 'PUT')
        self.assertRegex(put['path'], r'/contents/history/\d{4}-\d{2}-\d{2}-aaaaaaaaaaaa-claude\.json$')
        self.assertEqual(put['body']['branch'], 'eval-results')
        stored = json.loads(base64.b64decode(put['body']['content']))
        self.assertEqual(stored['commit'], HEAD)
        self.assertFalse(any('git' == c['path'] for c in self.calls()))

    def test_the_comment_shows_change_from_the_last_main_result(self):
        main = self.dir / 'main'
        run = run_file(main, 'with', 'sonnet', [result('pagination-off-by-one', outcome='fail'), result('docs-only-no-test')], revision=OTHER)
        out = self.dir / 'main.json'
        self.assertEqual(self.cli('summarize', '--run', run, '--out', out, '--main')[0], 0)
        self.assertEqual(self.cli('publish', '--summary', out, '--history-only', '--repo', 'owner/name', '--send')[0], 0)
        self.assertEqual([c for c in self.writes() if '/statuses/' in c['path'] or '/comments' in c['path']], [])
        self.assertEqual(self.publish('--send')[0], 0)
        body = self.state()['comments'][0]['body']
        self.assertRegex(body, r'`pagination-off-by-one`.*\| fixed \|')
        self.assertRegex(body, r'`docs-only-no-test`.*\| pass, tier sonnet to haiku \|')
        self.assertIn('Compared with the last main result', body)


class Dashboard(Base):
    def history(self):
        folder = self.dir / 'history'
        folder.mkdir()
        sample = [('2026-10-01', 'claude', 'haiku', 'sonnet'), ('2026-10-15', 'codex', 'gpt-6-luna', 'gpt-6.1-terra'), ('2026-10-29', 'claude', 'haiku', 'sonnet')]
        for n, (day, host, cheap, dear) in enumerate(sample):
            runs = [run_file(self.dir / f'r{n}', 'with', dear, [result('pagination-off-by-one'), result('docs-only-no-test'), result('log-no-secret', outcome='fail')],
                             revision=chr(97 + n) * 40, host=f'{host} 1.0.{n}'),
                    run_file(self.dir / f'r{n}', 'without', dear, [result('pagination-off-by-one', outcome='fail'), result('docs-only-no-test'), result('log-no-secret', outcome='fail')],
                             revision=chr(97 + n) * 40, host=f'{host} 1.0.{n}')]
            out = folder / f'{day}-{n}.json'
            self.assertEqual(self.cli('summarize', *[x for p in runs for x in ('--run', p)], '--out', out)[0], 0)
            data = json.loads(out.read_text())
            data['created'] = f'{day}T10:00:00Z'
            out.write_text(json.dumps(data))
        return folder

    def test_dashboard_renders_from_sample_history_with_no_external_requests(self):
        out = self.dir / 'dashboard.html'
        code, text, err = self.cli('dashboard', '--history', self.history(), '--out', out)
        self.assertEqual(code, 0, err)
        page = out.read_text()
        for needle in ('http://', 'https://', '//cdn', '<script', '<link', '@import', 'url(', ' src=', '<iframe'):
            self.assertNotIn(needle, page)
        self.assertIn('prefers-color-scheme:dark', page)
        self.assertIn('width=device-width', page)
        for heading in ('Pass rate over time', 'By tier and host', 'With versus without skills', 'Runs and cost per evaluation', 'Non-discriminating cases'):
            self.assertIn(heading, page)
        self.assertIn('claude / sonnet', page)
        self.assertIn('codex / gpt-6.1-terra', page)
        flagged = page.split('Non-discriminating cases', 1)[1]
        self.assertIn('docs-only-no-test', flagged)  # passes with and without in every paired observation
        self.assertIn('log-no-secret', flagged)      # fails both ways
        self.assertNotIn('pagination-off-by-one', flagged)  # skills make the difference
        self.assertIn('unknown', page)  # cost unknown is shown, never estimated

    def test_dashboard_escapes_hostile_history_and_survives_empty_history(self):
        folder = self.history()
        path = next(folder.glob('*.json'))
        data = json.loads(path.read_text())
        data['models'] = ['<script>alert(1)</script>']
        path.write_text(json.dumps(data))
        out = self.dir / 'd.html'
        self.assertEqual(self.cli('dashboard', '--history', folder, '--out', out)[0], 0)
        self.assertNotIn('<script>', out.read_text())
        empty = self.dir / 'empty'
        empty.mkdir()
        self.assertEqual(self.cli('dashboard', '--history', empty, '--out', out)[0], 0)
        self.assertIn('No results yet', out.read_text())

    def test_publish_is_a_dry_run_by_default_then_writes_index_html_with_send(self):
        folder, out = self.history(), self.dir / 'd.html'
        code, text, err = self.cli('dashboard', '--history', folder, '--out', out, '--publish', '--repo', 'owner/name')
        self.assertEqual(code, 0, err)
        self.assertIn('would write index.html', text)
        self.assertEqual(self.writes(), [])
        self.assertEqual(self.cli('dashboard', '--history', folder, '--out', out, '--publish', '--repo', 'owner/name', '--send')[0], 0)
        self.assertIn('index.html', self.state()['files'])
        self.assertEqual([c['path'].rsplit('/', 1)[-1] for c in self.writes()][:4], ['blobs', 'trees', 'commits', 'refs'])


class Affected(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cases = Path(self.temp.name)
        self.make('routes', expected_skill='tdd')
        self.make('declared', depends_on=['src/lib/', 'config.toml'])
        self.make('plain')

    def make(self, name, **fields):
        (self.cases / name).mkdir()
        (self.cases / name / 'case.json').write_text(json.dumps({'id': name, **fields}))

    def affected(self, *paths):
        return report.affected_cases(paths, self.cases)

    def test_default_dependencies_are_the_expected_skill_the_workflow_skill_and_the_registry(self):
        self.assertEqual(self.affected('skills/tdd/SKILL.md'), ['routes'])
        self.assertEqual(self.affected('skills/orbyn-workflow/scripts/harness.py'), ['plain', 'routes'])
        self.assertEqual(self.affected('docs/agents/models.json'), ['plain', 'routes'])

    def test_declared_depends_on_replaces_the_defaults_and_matches_folders_and_files(self):
        self.assertEqual(self.affected('src/lib/deep/x.py'), ['declared'])
        self.assertEqual(self.affected('config.toml'), ['declared'])
        self.assertNotIn('declared', self.affected('skills/orbyn-workflow/SKILL.md'))

    def test_a_case_depends_on_its_own_folder_and_unrelated_paths_select_nothing(self):
        self.assertEqual(self.affected('README.md', 'docs/other.md', 'skills/tddx/SKILL.md', 'src/library/x.py', '.github/workflows/ci.yml'), [])
        self.assertEqual(self.affected('./config.toml'), ['declared'])

    def test_the_shipped_suite_has_affected_cases_for_a_harness_change(self):
        shipped = {p.name for p in report.EXECUTABLE.iterdir() if (p / 'case.json').is_file()}
        self.assertEqual(set(report.affected_cases(['skills/orbyn-workflow/scripts/harness.py'])), shipped)
        self.assertEqual(report.affected_cases(['README.md']), [])

    def test_the_cli_prints_ids_and_evaluate_rejects_unsafe_depends_on(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(report.main(['affected', '--paths', 'skills/tdd/SKILL.md', '--cases-dir', str(self.cases)]), 0)
        self.assertEqual(out.getvalue().split(), ['routes'])
        copy = self.cases / 'copy'
        shutil.copytree(report.EXECUTABLE / 'log-no-secret', copy / 'log-no-secret')
        for bad in (['../x'], ['/etc'], 'skills', ['']):
            case = json.loads((copy / 'log-no-secret/case.json').read_text())
            case['depends_on'] = bad
            (copy / 'log-no-secret/case.json').write_text(json.dumps(case))
            with self.assertRaises(ValueError):
                evaluate.load_executable(copy)
        case['depends_on'] = ['skills/tdd/']
        (copy / 'log-no-secret/case.json').write_text(json.dumps(case))
        self.assertEqual(len(evaluate.load_executable(copy)), 1)


class HarnessEvalsCap(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.workspace = base / 'workspace'
        self.target = self.workspace / 'repo' / 'app'
        (self.target / '.git').mkdir(parents=True)

    def resolve(self, *extra, ok=0):
        done = subprocess.run([sys.executable, str(HARNESS), 'resolve', '--target', str(self.target), '--workspace', str(self.workspace),
                               '--host', 'claude', '--no-probe', '--json', *extra], capture_output=True, text=True)
        self.assertEqual(done.returncode, ok, done.stdout + done.stderr)
        return json.loads(done.stdout) if ok == 0 else done

    def write(self, where, data):
        path = (self.target / '.orbyn/harness.json') if where == 'target' else (self.workspace / 'repo/.harness/app.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'schema_version': 1, **data}))

    def test_the_cap_is_unset_by_default_and_the_registry_default_is_empty(self):
        self.assertEqual(self.resolve()['evals'], {'max_runs_per_pr': None})
        self.assertEqual(json.loads(REGISTRY.read_text())['evals'], {})
        defaults = json.loads((ROOT / 'skills/orbyn-workflow/references/harness-defaults.json').read_text())
        self.assertEqual(defaults['evals'], {})
        check = subprocess.run([sys.executable, str(ROOT / 'scripts/sync-agent-models.py'), '--check'], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_the_owners_local_file_or_the_user_can_set_it_and_the_user_wins(self):
        self.write('local', {'evals': {'max_runs_per_pr': 12}})
        item = self.resolve()['evals']['max_runs_per_pr']
        self.assertEqual(item['value'], 12)
        self.assertIn('local file', item['source'])
        item = self.resolve('--set', 'evals.max_runs_per_pr=4')['evals']['max_runs_per_pr']
        self.assertEqual((item['value'], item['source'].split(' ')[0]), (4, 'user'))

    def test_a_target_file_cannot_set_it(self):
        self.write('target', {'evals': {'max_runs_per_pr': 50}})
        done = self.resolve(ok=1)
        self.assertIn('target file cannot set the eval spending cap', done.stderr)
        self.write('target', {'evals': {}})
        self.assertEqual(self.resolve(ok=1).returncode, 1)
        (self.target / '.orbyn/harness.json').unlink()
        self.assertIsNone(self.resolve()['evals']['max_runs_per_pr'])

    def test_bad_values_are_rejected(self):
        for bad in (0, -1, 1001, '3', True, 1.5, None):
            with self.subTest(bad=bad):
                self.write('local', {'evals': {'max_runs_per_pr': bad}})
                self.resolve(ok=1)
        self.write('local', {'evals': {'surprise': 1}})
        self.resolve(ok=1)
        self.write('local', {'evals': 'many'})
        self.resolve(ok=1)


if __name__ == '__main__':
    unittest.main()
