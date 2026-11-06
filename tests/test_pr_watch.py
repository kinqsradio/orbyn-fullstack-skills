"""pr_watch.py: owner rule, merge authority, required checks, readiness, every event kind and the wait loop, on synthetic gh output."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pr_watch', ROOT / 'skills/orbyn-workflow/scripts/pr_watch.py')
pw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pw)

LOGIN = 'Maint'
HEAD = 'a' * 40
HEAD2 = 'b' * 40


def run(name, status='COMPLETED', conclusion='SUCCESS'):
    return {'__typename': 'CheckRun', 'name': name, 'status': status, 'conclusion': conclusion}


def node(number=1, author=LOGIN, head=HEAD, checks=(), issues=(), threads=(), reviews=(), mergeable='MERGEABLE',
         merge_state='BLOCKED', decision=None, base='main'):
    return {
        'number': number, 'title': f'PR {number}', 'url': f'https://x/pull/{number}', 'isDraft': False,
        'headRefOid': head, 'baseRefName': base, 'mergeable': mergeable, 'mergeStateStatus': merge_state,
        'reviewDecision': decision, 'author': {'login': author},
        'reviewThreads': {'nodes': [{'id': str(i), 'isResolved': r} for i, r in enumerate(threads)]},
        'latestReviews': {'nodes': [{'author': {'login': a}, 'state': s, 'submittedAt': t} for a, s, t in reviews]},
        'closingIssuesReferences': {'nodes': [{'number': n, 'assignees': {'nodes': [{'login': u} for u in users]}}
                                              for n, users in issues]},
        'commits': {'nodes': [{'commit': {'oid': head, 'statusCheckRollup': {'contexts': {'nodes': list(checks)}}
                                          if checks else None}}]}}


def ctx(role='admin', can_merge=True, required=None, now=1000.0, no_ci_after=600, login=LOGIN):
    return {'now': now, 'authority': {'can_merge': can_merge, 'role': role}, 'login': login,
            'no_ci_after': no_ci_after, 'required': {'main': set(required or ())}}


def step(previous, nodes, **kw):
    c = ctx(**kw)
    return pw.compare(previous, pw.owned_records(nodes, c['login']), c)


def kinds(events):
    return [e['kind'] for e in events]


class OwnerRuleTests(unittest.TestCase):
    def reasons(self, *nodes):
        return {r['number']: r['reason'] for r in pw.owned_records(list(nodes), LOGIN)}

    def test_author_matches_case_insensitively(self):
        self.assertEqual(self.reasons(node(1, author='MAINT')), {1: 'author'})

    def test_assigned_linked_issue_counts(self):
        self.assertEqual(self.reasons(node(2, author='other', issues=[(12, ['maint'])])), {2: 'assigned #12'})

    def test_other_authors_and_unassigned_issues_are_excluded(self):
        self.assertEqual(self.reasons(node(3, author='other', issues=[(5, ['someone'])]), node(4, author='other')), {})

    def test_review_requests_and_pr_assignees_do_not_count(self):
        n = node(5, author='other')
        n['reviewRequests'] = {'nodes': [{'requestedReviewer': {'login': LOGIN}}]}
        n['assignees'] = {'nodes': [{'login': LOGIN}]}
        self.assertEqual(self.reasons(n), {})


class AuthorityTests(unittest.TestCase):
    def authority(self, reply):
        def fake(args):
            if isinstance(reply, Exception):
                raise reply
            return json.dumps(reply)
        pw.run_gh, saved = fake, pw.run_gh
        self.addCleanup(setattr, pw, 'run_gh', saved)
        return pw.merge_authority('o/r', LOGIN)

    def test_roles_that_may_merge(self):
        for role in ('admin', 'maintain', 'write'):
            self.assertTrue(self.authority({'role_name': role, 'permission': 'read'})['can_merge'], role)

    def test_roles_that_may_not(self):
        for role in ('triage', 'read'):
            self.assertFalse(self.authority({'role_name': role})['can_merge'], role)

    def test_permission_field_is_the_fallback(self):
        self.assertTrue(self.authority({'permission': 'write'})['can_merge'])

    def test_a_refused_lookup_means_no_authority(self):
        result = self.authority(pw.GhError('gh api: HTTP 404'))
        self.assertFalse(result['can_merge'])
        self.assertIn('unknown', result['reason'])


class RulesTests(unittest.TestCase):
    def rules(self, routes):
        def fake(args):
            for key, reply in routes.items():
                if key in args[1]:
                    if isinstance(reply, Exception):
                        raise reply
                    return json.dumps(reply)
            raise pw.GhError('404')
        saved, pw.run_gh = pw.run_gh, fake
        self.addCleanup(setattr, pw, 'run_gh', saved)
        return pw.branch_rules('o/r', 'main')

    def test_required_names_are_the_union_of_ruleset_and_classic_protection(self):
        info = self.rules({
            '/rules/branches/': [{'type': 'pull_request'}, {'type': 'required_status_checks', 'parameters': {
                'required_status_checks': [{'context': 'test'}]}}],
            '/protection/required_status_checks': {'contexts': ['lint'], 'checks': [{'context': 'build'}]}})
        self.assertEqual(info['required'], ['build', 'lint', 'test'])
        self.assertEqual(info['types'], ['pull_request', 'required_status_checks'])

    def test_refused_lookups_mean_unknown(self):
        info = self.rules({})
        self.assertEqual((info['types'], info['required']), (None, []))


class FirstRunTests(unittest.TestCase):
    def test_first_run_is_a_silent_baseline(self):
        events, state = step(None, [node(1, checks=[run('t')])])
        self.assertEqual(events, [])
        again, _ = step(state, [node(1, checks=[run('t')])])
        self.assertEqual(again, [])


class EventTests(unittest.TestCase):
    def base(self, **kw):
        return step(None, [node(1, **kw)])[1]

    def test_new_pr_after_baseline(self):
        _, state = step(None, [])
        events, _ = step(state, [node(7)])
        self.assertEqual(kinds(events), ['new_pr'])

    def test_new_head(self):
        state = self.base()
        events, _ = step(state, [node(1, head=HEAD2)])
        self.assertEqual(kinds(events), ['new_head'])
        self.assertIn('aaaaaaa', events[0]['detail'])

    def test_review_threads_increase_only(self):
        state = self.base(threads=[True])
        events, state = step(state, [node(1, threads=[True, False, False])])
        self.assertEqual((kinds(events), events[0]['detail']), (['review_threads'], '2 unresolved (+2)'))
        events, _ = step(state, [node(1, threads=[True, True, False])])
        self.assertEqual(events, [])

    def test_new_pr_does_not_double_report_threads(self):
        _, state = step(None, [])
        events, _ = step(state, [node(1, threads=[False])])
        self.assertEqual(kinds(events), ['new_pr'])

    def test_conflict_once_per_head(self):
        state = self.base()
        events, state = step(state, [node(1, mergeable='CONFLICTING', merge_state='DIRTY')])
        self.assertEqual(kinds(events), ['conflict'])
        events, state = step(state, [node(1, mergeable='CONFLICTING', merge_state='DIRTY')])
        self.assertEqual(events, [])
        events, _ = step(state, [node(1, head=HEAD2, mergeable='CONFLICTING', merge_state='DIRTY')])
        self.assertEqual(kinds(events), ['conflict', 'new_head'])

    def test_changes_requested_by_a_new_review_once(self):
        state = self.base()
        review = [('rev', 'CHANGES_REQUESTED', '2026-01-01T00:00:00Z')]
        events, state = step(state, [node(1, reviews=review)])
        self.assertEqual((kinds(events), events[0]['detail']), (['changes_requested'], 'rev'))
        events, state = step(state, [node(1, reviews=review)])
        self.assertEqual(events, [])
        events, _ = step(state, [node(1, reviews=[('rev', 'CHANGES_REQUESTED', '2026-01-02T00:00:00Z')])])
        self.assertEqual(kinds(events), ['changes_requested'])

    def test_review_decision_newly_changes_requested(self):
        state = self.base(decision='REVIEW_REQUIRED')
        events, _ = step(state, [node(1, decision='CHANGES_REQUESTED', merge_state='BLOCKED')])
        self.assertEqual((kinds(events), events[0]['detail']), (['changes_requested'], 'review decision'))

    def test_closed_when_no_longer_open(self):
        state = self.base()
        events, state = step(state, [])
        self.assertEqual((kinds(events), events[0]['number']), (['closed'], 1))
        self.assertEqual(state['prs'], {})

    def test_events_are_ordered_by_number_then_kind(self):
        _, state = step(None, [])
        events, _ = step(state, [node(9), node(3)])
        self.assertEqual([e['number'] for e in events], [3, 9])

    def test_line_format(self):
        _, state = step(None, [])
        events, _ = step(state, [node(4, merge_state='BLOCKED')], can_merge=False, role='read')
        line = pw.format_event(events[0])
        self.assertTrue(line.startswith('new_pr #4 aaaaaaa '))
        self.assertTrue(line.endswith('authority=no ready=no state=BLOCKED'))


class CiTests(unittest.TestCase):
    def test_zero_checks_report_nothing_then_ci_missing_once_after_the_threshold(self):
        _, state = step(None, [node(1)], now=0)
        events, state = step(state, [node(1)], now=300)
        self.assertEqual(events, [])
        events, state = step(state, [node(1)], now=700)
        self.assertEqual(kinds(events), ['ci_missing'])
        events, _ = step(state, [node(1)], now=2000)
        self.assertEqual(events, [])

    def test_ci_reported_once_per_head_and_again_after_a_new_head(self):
        _, state = step(None, [node(1, checks=[run('t', 'IN_PROGRESS', None)])], now=0)
        events, state = step(state, [node(1, checks=[run('t')])], now=10)
        self.assertEqual(kinds(events), ['ci_passed'])
        events, state = step(state, [node(1, checks=[run('t')])], now=20)
        self.assertEqual(events, [])
        events, _ = step(state, [node(1, head=HEAD2, checks=[run('t')])], now=30)
        self.assertEqual(kinds(events), ['ci_passed', 'new_head'])

    def test_pending_check_blocks_the_ci_event(self):
        _, state = step(None, [node(1)], now=0)
        events, _ = step(state, [node(1, checks=[run('a'), run('b', 'QUEUED', None)])], now=10)
        self.assertEqual(events, [])

    def test_pending_status_context_blocks(self):
        status = {'__typename': 'StatusContext', 'context': 'ci/x', 'state': 'PENDING'}
        _, state = step(None, [node(1)], now=0)
        events, _ = step(state, [node(1, checks=[status])], now=10)
        self.assertEqual(events, [])

    def test_failing_checks_are_named_and_neutral_does_not_fail(self):
        _, state = step(None, [node(1)], now=0)
        checks = [run('lint', conclusion='FAILURE'), run('unit', conclusion='TIMED_OUT'), run('docs', conclusion='NEUTRAL'),
                  run('skip', conclusion='SKIPPED'), {'__typename': 'StatusContext', 'context': 'ci/y', 'state': 'ERROR'}]
        events, _ = step(state, [node(1, checks=checks)], now=10)
        self.assertEqual(kinds(events), ['ci_failed'])
        self.assertEqual(events[0]['detail'], 'lint,unit,ci/y')

    def test_a_flip_on_the_same_head_is_reported(self):
        _, state = step(None, [node(1, checks=[run('t', conclusion='FAILURE')])], now=0)
        events, _ = step(state, [node(1, checks=[run('t')])], now=10)
        self.assertEqual(kinds(events), ['ci_passed'])


class RequiredChecksTests(unittest.TestCase):
    def test_optional_failure_is_ignored_and_listed(self):
        checks = [run('test'), run('GitGuardian Security Checks', conclusion='FAILURE')]
        _, state = step(None, [node(1)], now=0, required=['test'])
        events, _ = step(state, [node(1, checks=checks)], now=10, required=['test'])
        self.assertEqual(kinds(events), ['ci_passed'])
        self.assertIn('optional failing: GitGuardian Security Checks', events[0]['detail'])

    def test_required_failure_is_ci_failed(self):
        _, state = step(None, [node(1)], now=0, required=['test'])
        events, _ = step(state, [node(1, checks=[run('test', conclusion='FAILURE'), run('other')])], now=10,
                         required=['test'])
        self.assertEqual((kinds(events), events[0]['detail']), (['ci_failed'], 'test'))

    def test_missing_required_check_counts_as_pending(self):
        _, state = step(None, [node(1)], now=0, required=['test', 'build'])
        events, _ = step(state, [node(1, checks=[run('test'), run('extra')])], now=10, required=['test', 'build'])
        self.assertEqual(events, [])

    def test_required_check_that_never_registers_is_ci_missing_once_after_the_threshold(self):
        req = ['test', 'build']
        _, state = step(None, [node(1)], now=0, required=req)
        events, state = step(state, [node(1, checks=[run('test'), run('b2', 'IN_PROGRESS', None)])], now=700,
                             required=['test', 'b2'] + ['build'])
        self.assertEqual(events, [], 'a required check still running is not missing')
        events, state = step(state, [node(1, checks=[run('test')])], now=700, required=req)
        self.assertEqual((kinds(events), events[0]['detail']), (['ci_missing'], 'required not reported: build'))
        events, _ = step(state, [node(1, checks=[run('test')])], now=900, required=req)
        self.assertEqual(events, [])

    def test_no_required_names_means_every_check_counts(self):
        _, state = step(None, [node(1)], now=0)
        events, _ = step(state, [node(1, checks=[run('x', conclusion='FAILURE')])], now=10)
        self.assertEqual(kinds(events), ['ci_failed'])

    def test_no_required_check_registered_follows_the_ci_missing_gap(self):
        _, state = step(None, [node(1)], now=0, required=['test'])
        events, _ = step(state, [node(1, checks=[run('extra')])], now=700, required=['test'])
        self.assertEqual(kinds(events), ['ci_missing'])


class ReadinessTests(unittest.TestCase):
    CHECKS = [run('test')]

    def ready(self, n, **kw):
        return pw.readiness(*self.parts(n, **kw))

    def parts(self, n, role='admin', can_merge=True, required=('test',)):
        c = ctx(role=role, can_merge=can_merge, required=required)
        record = pw.owned_records([n], LOGIN)[0]
        return record, pw.ci_status(record, c['required']['main']), c

    def owner_node(self, **kw):
        args = dict(merge_state='BLOCKED', decision='REVIEW_REQUIRED', checks=self.CHECKS)
        args.update(kw)
        return node(1, **args)

    def test_clean_with_authority_is_yes(self):
        self.assertEqual(self.ready(node(1, merge_state='CLEAN', checks=self.CHECKS)), 'yes')

    def test_clean_without_authority_is_no(self):
        self.assertEqual(self.ready(node(1, merge_state='CLEAN', checks=self.CHECKS), role='read', can_merge=False), 'no')

    def test_unstable_needs_every_required_check_passed(self):
        self.assertEqual(self.ready(node(1, merge_state='UNSTABLE', checks=self.CHECKS)), 'yes')
        self.assertEqual(self.ready(node(1, merge_state='UNSTABLE', checks=[run('test', conclusion='FAILURE')])), 'no')

    def test_owner_case_is_an_admin_blocked_only_by_their_own_approval(self):
        self.assertEqual(self.ready(self.owner_node()), 'owner')

    def test_non_admin_in_the_same_state_gets_no(self):
        self.assertEqual(self.ready(self.owner_node(), role='write'), 'no')

    def test_owner_case_needs_the_author_and_a_quiet_pr(self):
        self.assertEqual(pw.readiness(*self._as_other(self.owner_node(author='other', issues=[(1, [LOGIN])]))), 'no')
        self.assertEqual(self.ready(self.owner_node(threads=[False])), 'no')
        self.assertEqual(self.ready(self.owner_node(mergeable='CONFLICTING')), 'no')
        self.assertEqual(self.ready(self.owner_node(decision='CHANGES_REQUESTED')), 'no')
        self.assertEqual(self.ready(self.owner_node(checks=[run('test', conclusion='FAILURE')])), 'no')

    def _as_other(self, n):
        return self.parts(n)

    def test_ready_event_once_per_head_with_the_owner_detail(self):
        _, state = step(None, [self.owner_node()], now=0, required=['test'])
        events, state = step(state, [self.owner_node(head=HEAD2)], now=10, required=['test'])
        ready = [e for e in events if e['kind'] == 'ready']
        self.assertEqual(len(ready), 1)
        self.assertEqual((ready[0]['detail'], ready[0]['ready']), ('needs owner decision: approval required, own PR', 'owner'))
        events, _ = step(state, [self.owner_node(head=HEAD2)], now=20, required=['test'])
        self.assertEqual(events, [])

    def test_ready_yes_event(self):
        _, state = step(None, [node(1, merge_state='BLOCKED', checks=self.CHECKS)], now=0, required=['test'])
        events, _ = step(state, [node(1, merge_state='CLEAN', checks=self.CHECKS)], now=10, required=['test'])
        self.assertEqual(kinds(events), ['ready'])
        self.assertTrue(pw.format_event(events[0]).endswith('authority=yes ready=yes state=CLEAN'))


def fake_gh(nodes, role='admin', rules=None, calls=None):
    def fake(args):
        if calls is not None:
            calls.append(args)
        if args[:2] == ['api', 'graphql']:
            return json.dumps({'data': {'repository': {'pullRequests': {
                'pageInfo': {'hasNextPage': False, 'endCursor': None}, 'nodes': nodes}}}})
        if 'permission' in args[1]:
            return json.dumps({'role_name': role})
        if '/rules/branches/' in args[1]:
            return json.dumps(rules or [])
        raise pw.GhError('404')
    return fake


class WaitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = str(Path(self.temp.name) / 'state.json')
        self.saved = pw.run_gh
        self.addCleanup(setattr, pw, 'run_gh', self.saved)
        self.clock = [0.0]
        self.sleeps = []

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.clock[0] += seconds

    def wait(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        argv = ['--repo', 'o/r', '--login', LOGIN, 'wait', '--state', self.state, *extra]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = pw.main(argv, sleep=self.sleep, clock=lambda: self.clock[0], wall=lambda: self.clock[0])
        return code, out.getvalue(), err.getvalue()

    def test_quiet_run_exits_3_at_max_without_real_sleeping(self):
        pw.run_gh = fake_gh([node(1, checks=[run('t')])])
        code, out, _ = self.wait('--interval', '30', '--max', '100')
        self.assertEqual((code, out), (3, ''))
        self.assertEqual(self.sleeps, [30, 30, 30, 10])

    def test_event_exits_0_with_lines_after_the_baseline(self):
        pw.run_gh = fake_gh([node(1, checks=[run('t')])])
        self.assertEqual(self.wait('--max', '0')[0], 3)
        pw.run_gh = fake_gh([node(1, head=HEAD2, checks=[run('t')])])
        code, out, _ = self.wait('--max', '0')
        self.assertEqual(code, 0)
        self.assertIn('new_head #1 bbbbbbb', out)
        self.assertIn('ci_passed #1', out)

    def test_json_lines(self):
        pw.run_gh = fake_gh([node(1)])
        self.wait('--max', '0')
        pw.run_gh = fake_gh([node(1, head=HEAD2)])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            pw.main(['--repo', 'o/r', '--login', LOGIN, '--json', 'wait', '--state', self.state, '--max', '0'],
                    sleep=self.sleep, clock=lambda: 0.0, wall=lambda: 0.0)
        self.assertEqual(json.loads(out.getvalue().splitlines()[0])['kind'], 'new_head')

    def test_pr_flag_on_a_pr_not_owned_exits_2(self):
        pw.run_gh = fake_gh([node(1), node(2, author='other')])
        code, _, err = self.wait('--pr', '2', '--max', '0')
        self.assertEqual(code, 2)
        self.assertIn('#2', err)

    def test_required_checks_from_rules_are_used(self):
        rules = [{'type': 'required_status_checks', 'parameters': {'required_status_checks': [{'context': 't'}]}}]
        pw.run_gh = fake_gh([node(1)], rules=rules)
        self.wait('--max', '0')
        pw.run_gh = fake_gh([node(1, checks=[run('t'), run('GG', conclusion='FAILURE')])], rules=rules)
        code, out, _ = self.wait('--max', '0')
        self.assertEqual(code, 0)
        self.assertIn('ci_passed #1', out)
        self.assertIn('optional failing: GG', out)

    def test_gh_error_exits_2_with_one_line(self):
        def broken(args):
            raise pw.GhError('gh api: no network')
        pw.run_gh = broken
        code, _, err = self.wait('--max', '0')
        self.assertEqual((code, err.strip()), (2, 'pr_watch: gh api: no network'))

    def test_interval_below_the_minimum_is_refused(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            pw.build_parser().parse_args(['wait', '--interval', '5'])

    def test_scope_prints_owned_prs_and_unknown_required_checks(self):
        pw.run_gh = fake_gh([node(1), node(2, author='other')])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = pw.main(['--repo', 'o/r', '--login', LOGIN, 'scope'])
        self.assertEqual(code, 0)
        self.assertIn('#1 PR 1 [author]', out.getvalue())
        self.assertNotIn('#2', out.getvalue())
        self.assertIn('required: unknown', out.getvalue())
        self.assertIn('merge authority: yes', out.getvalue())

    def test_scope_json(self):
        pw.run_gh = fake_gh([node(1)])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            pw.main(['--repo', 'o/r', '--login', LOGIN, '--json', 'scope'])
        data = json.loads(out.getvalue())
        self.assertEqual((data['login'], data['prs'][0]['reason']), (LOGIN, 'author'))


if __name__ == '__main__':
    unittest.main()
