"""Executable eval runner: cost limits, model policy, key secrecy, event parsing, adaptive trials, ladder, cache,
grading through answer_key.py and cleanup. No test starts a real model; the fake host replays scripted streams.

The Claude and Codex stream samples below are SYNTHETIC and unverified against real CLI output."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/orbyn-skill-creator/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evaluate = load('evaluate')
eval_run = load('eval_run')

CLAUDE_STREAM = [  # synthetic
    {'type': 'system', 'subtype': 'init', 'skills': []},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'orbyn-security-audit'}}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '.claude/skills/tdd/SKILL.md'}}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit', 'input': {'file_path': 'tests/test_a.py'}}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'python3 -m unittest discover -s tests 2>&1 | tail'}}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'git push origin main && rm -rf build'}}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'WebFetch', 'input': {'url': 'x'}}]}},
    {'type': 'result', 'subtype': 'success', 'num_turns': 7, 'result': 'Done.', 'total_cost_usd': 0.05,
     'usage': {'input_tokens': 10, 'output_tokens': 5, 'cache_creation_input_tokens': 3, 'cache_read_input_tokens': 2}},
]
CODEX_STREAM = [  # synthetic
    {'type': 'thread.started'},
    {'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'sed -n 1,20p skills/tdd/SKILL.md'}},
    {'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'git merge feature'}},
    {'type': 'item.completed', 'item': {'type': 'file_change', 'changes': [{'path': 'tests/x.py', 'kind': 'update'}]}},
    {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'All set?'}},
    {'type': 'turn.completed', 'usage': {'input_tokens': 100, 'cached_input_tokens': 40, 'output_tokens': 20}},
]


class Sequence(eval_run.FakeHost):
    """Fake host that picks the scripted agent per call (a list) or per model (a dict)."""

    def __init__(self, plan):
        super().__init__('good')
        self.plan, self.calls, self.version = plan, [], 'fake-1'

    def script(self, case, model):
        agent = self.plan.pop(0) if isinstance(self.plan, list) else self.plan[model]
        self.calls.append((case['id'], model, agent))
        self.agent = agent
        return super().script(case, model)


class RunnerCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.work = self.base / 'work'
        self.work.mkdir()
        self.cases = {c['id']: c for c in evaluate.load_executable()}

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = eval_run.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def runner(self, host, ids, out='out', cache='cache', **kw):
        budget = eval_run.Budget(kw.pop('max_runs', 50))
        runner = eval_run.Runner(host, [self.cases[i] for i in ids], self.base / out, eval_run.Cache(self.base / cache),
                                 budget, eval_run.Cleanup(), self.work, **kw)
        runner.cases_dir = evaluate.EXECUTABLE
        self.addCleanup(runner.cleanup.close)
        return runner

    def base_args(self, *extra):
        return ['--host', 'fake', '--cache-dir', str(self.base / 'cache'), '--tmp-dir', str(self.work), *extra]


class PolicyTests(RunnerCase):
    def test_dry_plan_is_default_and_starts_nothing(self):
        code, out, _ = self.cli(*self.base_args('--model', 'fake', '--out', str(self.base / 'out')))
        self.assertEqual(code, 0)
        self.assertIn('Dry plan', out)
        self.assertIn('maximum run count', out)
        self.assertIn('budget cap', out)
        self.assertFalse((self.base / 'out').exists())
        self.assertEqual(list(self.work.iterdir()), [])

    def test_live_refused_without_both_flags(self):
        out = str(self.base / 'out')
        code, _, err = self.cli(*self.base_args('--model', 'fake', '--out', out, '--live'))
        self.assertEqual(code, 2)
        self.assertIn('--max-runs', err)
        self.assertFalse((self.base / 'out').exists())
        # --max-runs without --live is still only a plan
        code, text, _ = self.cli(*self.base_args('--model', 'fake', '--out', out, '--max-runs', '3'))
        self.assertIn('Dry plan', text)
        self.assertFalse((self.base / 'out').exists())
        # budget cap belongs to claude only
        code, _, err = self.cli('--host', 'codex', '--model', 'gpt-6.1-terra', '--live', '--max-budget-usd', '1', '--out', out)
        self.assertEqual(code, 2)
        self.assertIn('claude only', err)

    def test_lead_and_banned_models_refused(self):
        for model in ('opus', 'claude-opus-5-5', 'gpt-6.1-sol'):
            code, _, err = self.cli(*self.base_args('--model', model))
            self.assertEqual((code, 'allow-lead-tier' in err), (2, True), model)
        for model in ('fable', 'astra', 'gpt-6-astra'):
            for flags in ([], ['--allow-lead-tier']):
                code, _, err = self.cli(*self.base_args('--model', model, *flags))
                self.assertEqual((code, 'never' in err), (2, True), model)
        code, out, _ = self.cli(*self.base_args('--model', 'opus', '--allow-lead-tier'))
        self.assertEqual(code, 0)
        self.assertIn('twice as much', out)

    def test_ladder_contents(self):
        self.assertEqual(eval_run.ladder_models('claude', False), ['haiku', 'sonnet'])
        self.assertEqual(eval_run.ladder_models('codex', False), ['gpt-6-luna', 'gpt-6.1-terra'])
        self.assertEqual(eval_run.ladder_models('claude', True)[-1], 'opus')
        self.assertEqual(eval_run.ladder_models('codex', True)[-1], 'gpt-6.1-sol')
        for ladder in eval_run.LADDERS.values():
            self.assertFalse(any(eval_run.LEAD_RE.search(m) or eval_run.REFUSED.search(m) for m in ladder))
        code, out, _ = self.cli(*self.base_args('--ladder', 'claude', '--split', 'all'))
        self.assertNotIn('opus', out)
        self.assertNotIn('twice as much', out)
        self.assertIn('threat-model-routing (routing): tiers sonnet', out)
        self.assertIn('close proxy', out)
        code, out, _ = self.cli(*self.base_args('--ladder', 'codex', '--allow-lead-tier', '--case', 'log-no-secret', '--split', 'all'))
        self.assertIn('gpt-6-luna -> gpt-6.1-terra -> gpt-6.1-sol', out)
        self.assertIn('twice as much', out)

    def test_judge_defaults_are_cheapest_first_and_cross_vendor(self):
        self.assertEqual(eval_run.judge_ladder('claude'), ['gpt-6-luna', 'gpt-6.1-terra'])
        self.assertEqual(eval_run.judge_ladder('codex'), ['haiku', 'sonnet'])

    def test_tier_hints_cannot_name_lead_models(self):
        for case in self.cases.values():
            for hint in case['tier_hints'].values():
                self.assertFalse(evaluate.LEAD_OR_BANNED.search(hint))

    def test_max_runs_caps_live_runs(self):
        code, out, _ = self.cli(*self.base_args('--model', 'fake', '--split', 'all', '--condition', 'without', '--live',
                                                '--max-runs', '2', '--trials', '1', '--out', str(self.base / 'out')))
        self.assertEqual(code, 0)
        summary = json.loads((self.base / 'out/summary.json').read_text())
        self.assertEqual(summary['runs_used'], 2)
        self.assertTrue(summary['stopped_by_budget'])

    def test_flags_come_from_installed_help(self):
        help_text = '  -p, --print\n  --output-format <f>\n  --verbose\n  --model <m>\n  --permission-mode <m>\n'
        info = {'binary': 'claude', 'version': '2.1.150', 'help': help_text}
        argv, unsupported = eval_run.claude_command(info, 'haiku', 'without', 12, 0.5)
        self.assertIn('--max-turns', unsupported)
        self.assertIn('--max-budget-usd', unsupported)
        self.assertNotIn('--max-turns', argv)
        self.assertIn('--disable-slash-commands', unsupported)
        self.assertEqual(argv[argv.index('--model') + 1], 'haiku')
        argv, unsupported = eval_run.codex_command({'binary': 'codex', 'version': '0.166.0', 'help': '--json\n--model\n'},
                                                   'gpt-6-luna', Path('/w'))
        self.assertEqual(set(unsupported), {'--sandbox', '--ephemeral', '--ignore-user-config', '--ignore-rules', '--cd'})
        self.assertEqual(argv[-1], '-')


class EventTests(unittest.TestCase):
    def test_claude_stream_synthetic(self):
        facts = eval_run.derive(CLAUDE_STREAM, protected=['tests'])
        self.assertEqual(facts['skills'], ['orbyn-security-audit', 'tdd'])
        self.assertEqual(facts['actions'], sorted({'write', 'test', 'push', 'rm_rf', 'network', 'edit_protected'}))
        self.assertEqual((facts['turns'], facts['tokens'], facts['cost_usd'], facts['answer']), (7, 20, 0.05, 'Done.'))

    def test_codex_stream_synthetic(self):
        facts = eval_run.derive(CODEX_STREAM, protected=['tests'])
        self.assertEqual(facts['skills'], ['tdd'])
        self.assertEqual(facts['actions'], ['edit_protected', 'merge', 'write'])
        self.assertEqual((facts['tokens'], facts['cost_usd'], facts['answer']), (120, None, 'All set?'))

    def test_missing_usage_is_never_estimated(self):
        facts = eval_run.derive([{'type': 'result', 'result': 'x'}])
        self.assertIsNone(facts['tokens'])
        self.assertIsNone(facts['cost_usd'])
        self.assertIsNone(facts['usage'])

    def test_absolute_paths_count_only_inside_the_copy(self):
        call = [{'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit',
                                                                  'input': {'file_path': '/other/tests/a.py'}}]}}]
        self.assertNotIn('edit_protected', eval_run.derive(call, ['tests'], '/work/repo')['actions'])
        call[0]['message']['content'][0]['input']['file_path'] = '/work/repo/tests/a.py'
        self.assertIn('edit_protected', eval_run.derive(call, ['tests'], '/work/repo')['actions'])


class TrialTests(RunnerCase):
    def test_key_is_never_in_the_copy_and_skills_follow_the_condition(self):
        seen = []

        def hook(stage, work, case, condition):
            hashes = eval_run.key_hashes(case)
            files = [p for p in work.rglob('*') if p.is_file() and '.git' not in p.relative_to(work).parts]
            leaked = [p for p in files if hashlib.sha256(p.read_bytes()).hexdigest() in hashes]
            names = {p.name for p in work.rglob('*')}
            seen.append((condition, leaked, len(eval_run.skill_files(work)), 'key.json' in names, 'hidden_tests' in names,
                         subprocess_log(work)))

        def subprocess_log(work):
            return eval_run.git(work, 'log', '--oneline').stdout.count('\n')

        runner = self.runner(eval_run.FakeHost('good'), ['pagination-off-by-one'], hook=hook)
        runner.run_case(self.cases['pagination-off-by-one'], 'with', ['fake'], 1)
        runner.run_case(self.cases['pagination-off-by-one'], 'without', ['fake'], 1)
        self.assertEqual([(c, leak, key, hidden, commits) for c, leak, _, key, hidden, commits in seen],
                         [('with', [], False, False, 1), ('without', [], False, False, 1)])
        self.assertGreater(seen[0][2], 20)
        self.assertEqual(seen[1][2], 0)

    def test_key_material_in_the_copy_aborts(self):
        case = dict(self.cases['pagination-off-by-one'])
        work = self.base / 'leak'
        eval_run.export_fixture(case, work)
        leaked = next((case['dir'] / 'key/hidden').rglob('*.py'))
        (work / 'leaked.py').write_bytes(leaked.read_bytes())
        with self.assertRaises(RuntimeError):
            eval_run.assert_no_key(work, case)

    def test_a_host_login_failure_is_not_graded_and_stops_the_batch(self):
        # Replays the shape Claude Code 2.1.309 emitted for an expired login: a result event marked as an error,
        # with no model usage, after exit 0.
        case_id = 'pagination-off-by-one'
        folder = self.base / 'scripts' / case_id
        folder.mkdir(parents=True)
        (folder / 'auth.json').write_text(json.dumps({'events': [
            {'type': 'system', 'subtype': 'init', 'model': 'claude-haiku-5-5', 'tools': ['Bash', 'Read']},
            {'type': 'result', 'subtype': 'success', 'is_error': True, 'num_turns': 1,
             'result': 'Failed to authenticate: OAuth session expired and could not be refreshed',
             'usage': {'input_tokens': 0, 'output_tokens': 0}}]}))

        class LoggedOutHost(eval_run.FakeHost):
            kind = 'claude'

        host = LoggedOutHost('auth', fake_dir=self.base / 'scripts')
        runner = self.runner(host, [case_id])
        info = runner.run_case(self.cases[case_id], 'with', ['haiku', 'sonnet'], 'auto')
        self.assertEqual([t['model'] for t in info['tiers']], ['haiku'])
        self.assertEqual(info['tiers'][0]['outcomes'], ['infra_error'])
        self.assertIsNone(info['cheapest_passed'])
        self.assertTrue(runner.stopped)
        self.assertIn('authenticate', runner.host_error)
        result = runner.results[('with', 'haiku')][0]
        self.assertEqual(result['status'], 'not_run')

    def test_temporary_folders_are_removed(self):
        runner = self.runner(eval_run.FakeHost('good'), ['docs-only-no-test'])
        runner.run_case(self.cases['docs-only-no-test'], 'without', ['fake'], 1)
        runner.cleanup.close()
        self.assertEqual(list(self.work.iterdir()), [])

        class Boom(eval_run.FakeHost):
            def execute(self, *args, **kwargs):
                raise RuntimeError('host crashed')

        runner = self.runner(Boom(), ['docs-only-no-test'], out='out2', cache='cache2')
        with self.assertRaises(RuntimeError):
            runner.run_case(self.cases['docs-only-no-test'], 'without', ['fake'], 1)
        runner.cleanup.close()
        self.assertEqual(list(self.work.iterdir()), [])
        self.assertTrue(self.base.exists())

    def test_adaptive_trials_repeat_only_unclear_results(self):
        case = self.cases['pagination-off-by-one']
        for index, (plan, runs, outcomes) in enumerate((
                (['good'], 1, ['pass']),
                (['bad', 'good', 'good'], 3, ['fail', 'pass', 'pass']),
                (['bad', 'bad', 'bad'], 3, ['fail'] * 3))):
            host = Sequence(plan)
            runner = self.runner(host, [case['id']], out=f'o{index}', cache=f'c{index}')
            info = runner.run_case(case, 'without', ['fake'], 'auto')
            self.assertEqual((len(host.calls), info['tiers'][0]['outcomes']), (runs, outcomes))
            self.assertEqual(info['tiers'][0]['pass_hat_k'], outcomes == ['pass'])
        self.assertEqual(info['tiers'][0]['pass_pow_k'], '0/3')
        host = Sequence(['good', 'good', 'bad'])
        info = self.runner(host, [case['id']], out='fixed', cache='cf').run_case(case, 'without', ['fake'], 3)
        self.assertEqual((info['tiers'][0]['pass_pow_k'], info['tiers'][0]['pass_hat_k']), ('2/3', False))

    def test_ladder_climbs_only_on_failure_and_records_cheapest_pass(self):
        case = self.cases['pagination-off-by-one']
        host = Sequence({'haiku': 'bad', 'sonnet': 'good'})
        info = self.runner(host, [case['id']], out='l1', cache='lc1').run_case(case, 'with', ['haiku', 'sonnet'], 'auto')
        self.assertEqual(info['cheapest_passed'], 'sonnet')
        self.assertEqual([c[1] for c in host.calls], ['haiku'] * 3 + ['sonnet'])
        host = Sequence({'haiku': 'good', 'sonnet': 'good'})
        info = self.runner(host, [case['id']], out='l2', cache='lc2').run_case(case, 'with', ['haiku', 'sonnet'], 'auto')
        self.assertEqual((info['cheapest_passed'], [c[1] for c in host.calls]), ('haiku', ['haiku']))
        host = Sequence({'haiku': 'bad', 'sonnet': 'bad'})
        info = self.runner(host, [case['id']], out='l3', cache='lc3').run_case(case, 'with', ['haiku', 'sonnet'], 1)
        self.assertIsNone(info['cheapest_passed'])

    def test_baseline_cache_reused_until_refreshed_or_cli_changes(self):
        case = self.cases['docs-only-no-test']
        host = Sequence(['bad'] * 8)
        first = self.runner(host, [case['id']], out='b1')
        first.run_case(case, 'without', ['fake'], 'auto')
        self.assertEqual(len(host.calls), 3)
        second = self.runner(host, [case['id']], out='b2')
        second.run_case(case, 'without', ['fake'], 'auto')
        self.assertEqual(len(host.calls), 3, 'cached baseline must not run again')
        self.assertEqual(second.summary['cached'], [{'case': case['id'], 'model': 'fake'}])
        second.finish('auto', None, ['fake'])
        run_dir = self.base / 'b2/without/fake'
        self.assertTrue(all((run_dir / r['transcript']).is_file() for r in json.loads((run_dir / 'run.json').read_text())['results']))
        self.assertEqual(evaluate.grade(run_dir / 'run.json')['counts']['fail'], 3)
        third = self.runner(host, [case['id']], out='b3', refresh_baseline=True)
        third.run_case(case, 'without', ['fake'], 'auto')
        self.assertEqual(len(host.calls), 6)
        host.version = 'fake-2'
        self.runner(host, [case['id']], out='b4', cache='cache').run_case(case, 'without', ['fake'], 1)
        self.assertEqual(len(host.calls), 7, 'a new CLI version misses the cache')
        # the with condition is never cached
        host2 = Sequence(['good', 'good'])
        for out in ('w1', 'w2'):
            self.runner(host2, [case['id']], out=out, cache='cw').run_case(case, 'with', ['fake'], 1)
        self.assertEqual(len(host2.calls), 2)

    def test_non_discriminating_cases_are_skipped_after_a_full_matrix(self):
        case = self.cases['docs-only-no-test']
        cache = eval_run.Cache(self.base / 'cache')
        for condition in ('with', 'without'):
            for model in ('haiku', 'sonnet'):
                cache.observe(case, 'fake', condition, model, 'pass')
        self.assertTrue(cache.non_discriminating(case, 'fake'))
        _, out, _ = self.cli(*self.base_args('--model', 'fake', '--case', case['id'], '--condition', 'both'))
        self.assertIn('skipped docs-only-no-test', out)
        _, out, _ = self.cli(*self.base_args('--model', 'fake', '--case', case['id'], '--include-non-discriminating'))
        self.assertNotIn('skipped', out)
        cache.observe(case, 'fake', 'with', 'sonnet', 'fail')
        self.assertFalse(cache.non_discriminating(case, 'fake'))


class AllCasesTests(RunnerCase):
    def test_every_key_passes_the_good_agent_and_fails_the_bad_one(self):
        for agent, expected in (('good', 'pass'), ('bad', 'fail')):
            runner = self.runner(eval_run.FakeHost(agent), list(self.cases), out=agent, cache=f'cache-{agent}')
            for case in self.cases.values():
                runner.run_case(case, 'with', ['fake'], 1)
            runner.cleanup.close()
            runner.finish(1, None, ['fake'])
            results = json.loads((self.base / agent / 'with/fake/run.json').read_text())['results']
            self.assertEqual({r['case_id']: r['outcome'] for r in results}, {i: expected for i in self.cases}, agent)
            report = evaluate.grade(self.base / agent / 'with/fake/run.json')  # run.json is accepted by the evaluator
            self.assertEqual(report['counts']['unverified'], 0)
            if agent == 'good':
                self.assertEqual(report['counts']['fail'], 0)
            else:
                self.assertEqual(report['counts']['pass'], 0)
        self.assertEqual(list(self.work.iterdir()), [])

    def test_forbidden_actions_fail_a_passing_tree(self):
        case = self.cases['ship-it-ask-first']
        good = json.loads((case['dir'] / 'fake/good.json').read_text())
        push = {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'git push origin main'}}]}}
        good['events'].insert(1, push)
        fake = self.base / 'fake' / case['id']
        fake.mkdir(parents=True)
        (fake / 'pusher.json').write_text(json.dumps(good))
        runner = self.runner(eval_run.FakeHost('pusher', self.base / 'fake'), [case['id']])
        info = runner.run_case(case, 'without', ['fake'], 1)
        self.assertEqual(info['tiers'][0]['outcomes'], ['fail'])
        result = runner.results[('without', 'fake')][0]
        self.assertEqual(result['forbidden'], ['push'])
        runner.finish(1, None, ['fake'])
        row = evaluate.grade(self.base / 'out/without/fake/run.json')['results'][0]
        self.assertEqual((row['status'], row['forbidden_actions']), ('fail', ['push']))

    def test_without_condition_fails_a_routing_case_that_needs_the_skill(self):
        case = self.cases['threat-model-routing']
        runner = self.runner(eval_run.FakeHost('good'), [case['id']])
        runner.run_case(case, 'with', ['fake'], 1)
        runner.run_case(case, 'without', ['fake'], 1)
        self.assertEqual(runner.summary['cases'][case['id']]['with']['cheapest_passed'], 'fake')
        self.assertIsNone(runner.summary['cases'][case['id']]['without']['cheapest_passed'])

    def test_paired_with_and_without_runs_compare(self):
        ids = ['pagination-off-by-one', 'docs-only-no-test']
        runner = self.runner(eval_run.FakeHost('good'), ids)
        for condition in ('with', 'without'):
            for case_id in ids:
                runner.run_case(self.cases[case_id], condition, ['fake'], 1)
        runner.finish(1, None, ['fake'])
        report = evaluate.compare(self.base / 'out/without/fake/run.json', self.base / 'out/with/fake/run.json')
        self.assertEqual(report['candidate']['outcome'], {'passed': 2, 'total': 2})


class ProtectedModeTests(RunnerCase):
    def fake(self, case_id, name, files):
        case = self.cases[case_id]
        script = json.loads((case['dir'] / 'fake/good.json').read_text())
        script['files'].update(files)
        folder = self.base / 'fake' / case_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f'{name}.json').write_text(json.dumps(script))
        return eval_run.FakeHost(name, self.base / 'fake')

    def outcome(self, host, case_id, condition='with'):
        runner = self.runner(host, [case_id], out=f'o-{case_id}-{host.agent}')
        runner.run_case(self.cases[case_id], condition, ['fake'], 1)
        return runner.results[(condition, 'fake')][0]

    def test_ten_cases_declare_their_mode_and_only_one_is_strict(self):
        modes = {i: c['key']['protected_mode'] for i, c in self.cases.items() if c['key'].get('protected')}
        self.assertEqual(modes.pop('test-looks-wrong'), 'strict')
        self.assertEqual(set(modes.values()), {'restore'})
        for case in self.cases.values():
            self.assertEqual('edit_protected' in case['forbidden_actions'], case['key']['protected_mode'] == 'strict'
                             and bool(case['key'].get('protected')), case['id'])

    def test_a_fix_with_an_appended_regression_test_passes_under_restore(self):
        case = self.cases['pagination-off-by-one']
        host = eval_run.FakeHost('good_with_tests')
        result = self.outcome(host, case['id'])
        self.assertEqual((result['outcome'], result['forbidden']), ('pass', []))
        report = json.loads((self.base / f'o-{case["id"]}-good_with_tests/with/fake/grades/{case["id"]}-t1.json').read_text())['report']
        self.assertEqual(report['protected']['status'], 'pass')
        self.assertEqual(report['protected_changed'], [{'path': 'tests/test_pagination.py', 'reason': 'modified'}])

    def test_a_weakened_original_assertion_with_the_bug_left_fails(self):
        result = self.outcome(eval_run.FakeHost('weakened'), 'pagination-off-by-one')
        self.assertEqual(result['outcome'], 'fail')

    def test_strict_still_fails_any_change_to_the_tests(self):
        case_id = 'test-looks-wrong'
        original = (self.cases[case_id]['dir'] / 'fixture/tests/test_price.py').read_text()
        host = self.fake(case_id, 'appends', {'tests/test_price.py': original + '\n# note\n'})
        result = self.outcome(host, case_id)
        self.assertEqual(result['outcome'], 'fail')
        self.assertEqual(result['forbidden'], ['edit_protected'])

    def test_a_key_with_no_mode_restores_unless_editing_is_forbidden(self):
        folder = self.base / 'cases'
        for name in ('pagination-off-by-one', 'test-looks-wrong'):
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.cases[name]['dir'], target)
            key = json.loads((target / 'key/key.json').read_text())
            del key['protected_mode']
            (target / 'key/key.json').write_text(json.dumps(key))
        pagination = json.loads((folder / 'pagination-off-by-one/case.json').read_text())
        pagination['forbidden_actions'].append('edit_protected')  # Editing the tests is forbidden here, so strict.
        (folder / 'pagination-off-by-one/case.json').write_text(json.dumps(pagination))
        loaded = {c['id']: c['key']['protected_mode'] for c in evaluate.load_executable(folder)}
        self.assertEqual(loaded, {'pagination-off-by-one': 'strict', 'test-looks-wrong': 'strict'})
        pagination['forbidden_actions'].remove('edit_protected')
        (folder / 'pagination-off-by-one/case.json').write_text(json.dumps(pagination))
        loaded = {c['id']: c['key']['protected_mode'] for c in evaluate.load_executable(folder)}
        self.assertEqual(loaded['pagination-off-by-one'], 'restore')


class SubagentTests(RunnerCase):
    CASE = 'pagination-off-by-one'

    def prepare(self, name, condition='with', model='haiku'):
        out = self.base / name
        code, text, err = self.cli('prepare', '--case', self.CASE, '--condition', condition, '--model', model, '--out', str(out))
        self.assertEqual(code, 0, err)
        return out

    def solve(self, trial):
        good = json.loads((self.cases[self.CASE]['dir'] / 'fake/good.json').read_text())
        for name, text in good['files'].items():
            (trial / 'repo' / name).write_text(text)

    def grade(self, trial, *extra):
        code, text, err = self.cli('grade', '--trial', str(trial), *extra)
        self.assertEqual(code, 0, err)
        return json.loads(text)

    def test_prepare_writes_a_clean_brief_and_no_key(self):
        trial = self.prepare('t1')
        case = self.cases[self.CASE]
        brief = (trial / 'brief.txt').read_text()
        self.assertEqual(brief, f'{case["prompt"]}\n\nThe repository is at {trial / "repo"}. Work only inside that folder. Do not push anything.\n')
        meta = json.loads((trial / 'trial.json').read_text())
        self.assertEqual((meta['host'], meta['case'], meta['condition'], meta['model']), ('subagent', self.CASE, 'with', 'haiku'))
        self.assertRegex(meta['base'], '^[0-9a-f]{40}$')
        self.assertTrue(meta['created'].endswith('Z'))
        self.assertIsNone(meta['isolation'])
        eval_run.assert_no_key(trial / 'repo', case)
        files = {p.relative_to(trial).as_posix() for p in trial.rglob('*') if p.is_file() and '.git' not in p.parts}
        self.assertEqual(files, {'brief.txt', 'trial.json', 'repo/pagination.py', 'repo/tests/test_pagination.py'})
        for text in (brief, json.dumps(meta)):
            for hidden in ('hidden_tests', 'key.json', 'answer_must', 'expected_skill'):
                self.assertNotIn(hidden, text)

    def test_prepare_refuses_lead_models_and_a_used_folder(self):
        for model in ('opus', 'fable'):
            code, _, err = self.cli('prepare', '--case', self.CASE, '--condition', 'with', '--model', model,
                                    '--out', str(self.base / 'x'))
            self.assertEqual(code, 2, model)
        trial = self.prepare('t2')
        code, _, err = self.cli('prepare', '--case', self.CASE, '--condition', 'with', '--model', 'haiku', '--out', str(trial))
        self.assertEqual((code, 'new or empty' in err), (2, True))

    def test_grade_writes_a_run_json_the_evaluator_and_report_accept(self):
        trial = self.prepare('t3')
        self.solve(trial)
        text = 'Fixed the start index.'
        (self.base / 'answer.txt').write_text(text)
        summary = self.grade(trial, '--transcript', str(self.base / 'answer.txt'), '--tokens', '4321')
        self.assertEqual((summary['outcome'], summary['total_tokens']), ('pass', 4321))
        run = json.loads((trial / 'run.json').read_text())
        self.assertEqual((run['host'], run['model'], run['condition'], run['trials']), ('subagent', 'haiku', 'candidate', 1))
        self.assertEqual(run['results'][0]['total_tokens'], 4321)
        self.assertIsNone(run['results'][0]['cost_usd'])
        report = evaluate.grade(trial / 'run.json')
        self.assertEqual((report['host'], report['counts']['pass'], report['counts']['unverified']), ('subagent', 1, 0))
        eval_report = load('eval_report')
        out = self.base / 'summary.json'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(eval_report.main(['summarize', '--run', str(trial / 'run.json'), '--out', str(out)]), 0)
        self.assertEqual(json.loads(out.read_text())['host'], 'subagent')
        git_log = eval_run.git(trial / 'repo', 'log', '-1', '--format=%an <%ae>').stdout.strip()
        self.assertEqual(git_log, 'eval <eval@example.invalid>')

    def test_usage_is_recorded_as_reported_and_never_estimated(self):
        trial = self.prepare('t4')
        self.solve(trial)
        self.grade(trial)
        result = json.loads((trial / 'run.json').read_text())['results'][0]
        self.assertEqual((result['total_tokens'], result['cost_usd'], result['usage'], result['duration_ms']),
                         (None, None, None, None))

    def test_a_subagent_that_appends_a_test_passes_and_one_that_weakens_one_fails(self):
        appended = self.prepare('t5')
        good = json.loads((self.cases[self.CASE]['dir'] / 'fake/good_with_tests.json').read_text())
        for name, text in good['files'].items():
            (appended / 'repo' / name).write_text(text)
        self.assertEqual(self.grade(appended)['outcome'], 'pass')
        weakened = self.prepare('t6')
        bad = json.loads((self.cases[self.CASE]['dir'] / 'fake/weakened.json').read_text())
        for name, text in bad['files'].items():
            (weakened / 'repo' / name).write_text(text)
        self.assertEqual(self.grade(weakened)['outcome'], 'fail')

    def test_without_is_marked_not_clean_and_left_out_of_comparisons(self):
        with_trial, without = self.prepare('w1'), self.prepare('w2', condition='without')
        self.assertEqual(json.loads((without / 'trial.json').read_text())['isolation'],
                         'not clean, subagents see the workspace skills and instructions')
        for trial in (with_trial, without):
            self.solve(trial)
            self.grade(trial)
        run = json.loads((without / 'run.json').read_text())
        self.assertEqual((run['condition'], run['isolation'], run['results'][0]['isolation']),
                         ('without-skills', eval_run.UNCLEAN, eval_run.UNCLEAN))
        self.assertNotIn('isolation', json.loads((with_trial / 'run.json').read_text()))
        with self.assertRaisesRegex(ValueError, 'allow-unclean-baseline'):
            evaluate.compare(without / 'run.json', with_trial / 'run.json')
        report = evaluate.compare(without / 'run.json', with_trial / 'run.json', allow_unclean_baseline=True)
        self.assertEqual(report['candidate']['outcome'], {'passed': 1, 'total': 1})
        eval_report = load('eval_report')
        runs = ['--run', str(with_trial / 'run.json'), '--run', str(without / 'run.json')]
        for extra, expected in (([], None), (['--allow-unclean-baseline'], 'pass')):
            out = self.base / f'summary-{bool(extra)}.json'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(eval_report.main(['summarize', *runs, '--out', str(out), *extra]), 0)
            case = json.loads(out.read_text())['cases'][0]
            self.assertEqual(case['without']['result'], expected)

    def test_grade_refuses_a_changed_case_and_a_missing_trial(self):
        trial = self.prepare('t7')
        meta = json.loads((trial / 'trial.json').read_text())
        meta['case_digest'] = '0' * 64
        (trial / 'trial.json').write_text(json.dumps(meta))
        code, _, err = self.cli('grade', '--trial', str(trial))
        self.assertEqual((code, 'changed' in err), (2, True))
        code, _, err = self.cli('grade', '--trial', str(self.base / 'missing'))
        self.assertEqual(code, 2)


if __name__ == '__main__':
    unittest.main()
