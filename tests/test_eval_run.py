"""Executable eval runner: cost limits, model policy, key secrecy, event parsing, adaptive trials, ladder, cache,
grading through answer_key.py and cleanup. No test starts a real model; the fake host replays scripted streams.

The Claude and Codex stream samples below are SYNTHETIC and unverified against real CLI output."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
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


if __name__ == '__main__':
    unittest.main()
