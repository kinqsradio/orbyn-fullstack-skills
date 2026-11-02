"""The PR gate asks for review only when disclosure is complete and CI is green."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, module

gate = module('pr_gate', ROOT/'scripts/pr_gate.py')
authoring = module('check_authoring', ROOT/'scripts/check-authoring.py')

GOOD = """## Problem and resulting behavior

Agents had no owner for this.

## Agent disclosure

- Tools: Claude Code
- Models: claude-opus-5-5 (lead), claude-sonnet-5-5 (worker)
- Effort: medium
- Human role: Reviewed the result and decided scope
- External sources: none

## Evidence

- Static/helper checks: check-library OK
- Recorded host trials: not run

## Attribution and publication boundary

- [x] I can contribute this material under MIT.
"""
GREEN = [{'name': name, 'conclusion': 'SUCCESS'} for name in gate.REQUIRED_CHECKS]


def pr(body=GOOD, checks=GREEN, **extra):
    return {'author': {'login': 'someone'}, 'body': body, 'isDraft': False, 'statusCheckRollup': checks, **extra}


class CheckTests(unittest.TestCase):
    def test_a_complete_description_passes(self):
        self.assertEqual(gate.check(GOOD), [])

    def test_the_shipped_template_cannot_pass_unfilled(self):
        template = (ROOT/'.github/pull_request_template.md').read_text()
        problems = ' '.join(gate.check(template))
        for name in ('Tools', 'Models', 'Effort', 'Human role', 'Confirm every item'):
            self.assertIn(name, problems)

    def test_the_shipped_template_has_every_section_the_gate_reads(self):
        template = (ROOT/'.github/pull_request_template.md').read_text()
        for title in ('Problem and resulting behavior', 'Agent disclosure', 'Evidence',
                      'Attribution and publication boundary'):
            self.assertIsNotNone(gate.section(template, title), title)

    def test_each_disclosure_field_is_required(self):
        for name in gate.DISCLOSURE_FIELDS:
            for value in ('', 'none', 'N/A', 'TBD', '`unknown`'):
                body = GOOD.replace(gate.field(GOOD, name), value)
                self.assertTrue(any(name in p for p in gate.check(body)), (name, value))

    def test_a_family_name_is_not_a_model(self):
        self.assertTrue(gate.check(GOOD.replace('claude-opus-5-5 (lead), claude-sonnet-5-5 (worker)', 'sonnet')))
        self.assertEqual(gate.check(GOOD.replace('claude-opus-5-5 (lead), claude-sonnet-5-5 (worker)', 'gpt-6.1-terra')), [])

    def test_a_missing_section_or_unticked_box_fails(self):
        self.assertTrue(gate.check(GOOD.replace('## Agent disclosure', '## Something else')))
        self.assertTrue(gate.check(GOOD.replace('- [x]', '- [ ]')))
        self.assertTrue(gate.check(''))
        self.assertTrue(gate.check(None))

    def test_text_hidden_in_a_comment_does_not_count(self):
        body = GOOD.replace('- Tools: Claude Code', '<!-- - Tools: Claude Code -->\n- Tools:')
        self.assertTrue(any('Tools' in p for p in gate.check(body)))

    def test_windows_line_endings_are_read(self):
        self.assertEqual(gate.check(GOOD.replace('\n', '\r\n')), [])


class SourceTests(unittest.TestCase):
    SOURCE = 'https://github.com/acme/skill/tree/802057409787133703c56001080169e347305572 MIT, adapted'

    def body(self, value):
        return GOOD.replace('- External sources: none', f'- External sources: {value}')

    def test_none_is_a_valid_answer_but_blank_is_not(self):
        self.assertEqual(gate.check(GOOD), [])
        self.assertTrue(gate.check(self.body('')))
        self.assertTrue(gate.check(GOOD.replace('- External sources: none\n', '')))

    def test_a_pinned_mit_source_passes(self):
        self.assertEqual(gate.check(self.body(self.SOURCE)), [])

    def test_a_source_needs_a_link_a_commit_and_a_licence(self):
        self.assertTrue(any('Link' in p for p in gate.check(self.body('acme skill 802057409787133703c56001080169e347305572 MIT'))))
        self.assertTrue(any('commit' in p for p in gate.check(self.body('https://github.com/acme/skill MIT'))))
        self.assertTrue(any('licence' in p for p in gate.check(self.body('https://github.com/acme/skill/tree/8020574'))))

    def test_copying_disallowed_material_fails(self):
        value = 'https://github.com/acme/a/tree/8020574 MIT; https://github.com/acme/b/tree/8020575 GPL, adapted'
        self.assertTrue(any('credit alone' in p for p in gate.check(self.body(value))))
        for name in ('AGPL-3.0', 'LGPL-3.0', 'MPL-2.0', 'CC-BY-NC-4.0', 'no licence', 'proprietary'):
            value = f'https://github.com/acme/b/tree/8020575 {name}, copied'
            self.assertTrue(any('credit alone' in p for p in gate.check(self.body(value))), name)

    def test_copying_credit_only_licences_passes(self):
        for name in ('Apache-2.0', 'BSD-3-Clause', 'ISC', 'CC0-1.0', 'CC-BY-4.0', 'Unlicense'):
            value = f'https://github.com/acme/a/tree/8020574 {name}, adapted'
            self.assertEqual(gate.check(self.body(value)), [], name)

    def test_a_reviewed_only_source_may_have_another_licence(self):
        value = 'https://github.com/acme/a/tree/8020574 MIT reviewed; https://github.com/acme/b/tree/8020575 GPL reviewed'
        self.assertEqual(gate.check(self.body(value)), [])


class DecideTests(unittest.TestCase):
    def test_review_is_requested_only_when_complete_and_green(self):
        result = gate.decide(pr())
        self.assertEqual((result['state'], result['request'], result['add']), ('ready', True, [gate.READY]))

    def test_an_incomplete_pr_is_never_requested(self):
        result = gate.decide(pr(body='Fixes things'))
        self.assertEqual((result['state'], result['request'], result['add']), ('incomplete', False, [gate.NEEDS]))
        self.assertIn(gate.READY, result['remove'])

    def test_pending_or_failing_ci_does_not_request(self):
        one = [{'name': gate.REQUIRED_CHECKS[0], 'conclusion': 'SUCCESS'}]
        self.assertEqual(gate.decide(pr(checks=one))['state'], 'waiting')
        self.assertFalse(gate.decide(pr(checks=one))['request'])
        failing = [{'name': gate.REQUIRED_CHECKS[0], 'conclusion': 'FAILURE'}, GREEN[1]]
        self.assertEqual(gate.decide(pr(checks=failing))['state'], 'failing')
        self.assertFalse(gate.decide(pr(checks=failing))['request'])

    def test_a_draft_stays_quiet(self):
        self.assertFalse(gate.decide(pr(isDraft=True))['request'])

    def test_a_dependency_bot_needs_no_disclosure_but_still_needs_ci(self):
        bot = pr(body='Bump', author={'login': 'dependabot[bot]'})
        self.assertEqual(gate.decide(bot)['state'], 'ready')
        self.assertEqual(gate.decide({**bot, 'statusCheckRollup': []})['state'], 'waiting')


class ApplyTests(unittest.TestCase):
    def run_apply(self, record, maintainer='kinqsradio'):
        calls = []
        def fake(*args):
            calls.append(args)
            return json.dumps(record) if args[:2] == ('pr', 'view') else ''
        with mock.patch.object(gate, 'gh', side_effect=fake), mock.patch.dict('os.environ', {'GH_REPO': 'o/r'}), \
                mock.patch('builtins.print'):
            code = gate.apply('7', maintainer)
        return code, [c for c in calls if '--add-reviewer' in c]

    def test_a_ready_pr_requests_the_maintainer_once(self):
        self.assertEqual(self.run_apply(pr())[1][0][-1], 'kinqsradio')
        record = pr(reviewRequests=[{'login': 'kinqsradio'}])
        self.assertEqual(self.run_apply(record)[1], [])

    def test_the_maintainers_own_pr_is_not_self_requested(self):
        self.assertEqual(self.run_apply(pr(author={'login': 'kinqsradio'}))[1], [])

    def test_an_incomplete_pr_exits_one_and_requests_nobody(self):
        code, requests = self.run_apply(pr(body='nope'))
        self.assertEqual((code, requests), (1, []))


class WorkflowTests(unittest.TestCase):
    def test_the_gate_never_touches_pr_code(self):
        text = (ROOT/'.github/workflows/pr-gate.yml').read_text()
        self.assertIn('default_branch', text)
        self.assertNotIn('head.sha', text)
        self.assertNotIn('head.ref', text)
        self.assertNotIn('${{ github.event.pull_request.body', text)
        self.assertNotIn('${{ github.event.pull_request.title', text)

    def test_nobody_is_tagged_before_the_gate(self):
        owners = (ROOT/'.github/CODEOWNERS').read_text()
        self.assertFalse([l for l in owners.split('\n') if l.strip() and not l.startswith('#')])

    def test_issue_forms_require_the_tool_and_model(self):
        for name in ('bug_report.yml', 'skill_proposal.yml'):
            text = (ROOT/'.github/ISSUE_TEMPLATE'/name).read_text()
            self.assertIn('id: agent', text)


class AuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = mock.patch.object(authoring, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.git('init', '-q', '-b', 'main')
        (self.root/'skills/a').mkdir(parents=True)
        (self.root/'skills/a/SKILL.md').write_text('x')
        self.record([])
        self.commit('base')
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True, text=True).stdout

    def commit(self, message):
        self.git('add', '.')
        self.git('-c', 'user.name=T', '-c', 'user.email=t@example.test', 'commit', '-qm', message)

    def record(self, entries):
        (self.root/'provenance.json').write_text(json.dumps({'skills': {'a': {'authoring': entries}}}))

    def test_a_changed_skill_needs_a_new_entry(self):
        (self.root/'skills/a/SKILL.md').write_text('y')
        self.commit('edit')
        self.assertEqual(authoring.missing(self.base), ['a'])

    def test_a_new_entry_satisfies_it(self):
        (self.root/'skills/a/SKILL.md').write_text('y')
        self.record([{'tool': 'Claude Code', 'model': 'claude-sonnet-5-5'}])
        self.commit('edit')
        self.assertEqual(authoring.missing(self.base), [])

    def test_generated_index_changes_do_not_count(self):
        (self.root/'skills/README.md').write_text('index')
        self.commit('index')
        self.assertEqual(authoring.missing(self.base), [])


class LicenceTests(unittest.TestCase):
    contracts = module('gate_contracts', ROOT/'scripts/skill_contracts.py')

    def test_only_allowed_licences_may_be_bundled(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root/'skills/a/references/upstream/x'
            source.mkdir(parents=True)
            (source/'snapshot.json').write_text('{"license": "MIT"}')
            self.assertEqual(self.contracts.check_licences(root, 'a', {'license': 'MIT'}), [])
            (source/'snapshot.json').write_text('{"license": "Apache-2.0"}')
            self.assertEqual(self.contracts.check_licences(root, 'a', {'license': 'MIT'}), [])
            (source/'snapshot.json').write_text('{"license": "BSD-3-Clause"}')
            self.assertEqual(self.contracts.check_licences(root, 'a', {'license': 'MIT'}), [])
            (source/'snapshot.json').write_text('{"license": "GPL-3.0"}')
            self.assertIn('GPL', self.contracts.check_licences(root, 'a', {'license': 'MIT'})[0])
            self.assertTrue(self.contracts.check_licences(root, 'b', {'license': 'GPL-3.0'}))
            record = {'license': 'MIT', 'incorporated_material': [{'license': 'GPL-3.0', 'source': 'x'}]}
            self.assertTrue(self.contracts.check_licences(root, 'b', record))

    def test_the_library_bundles_only_allowed_licences(self):
        records = json.loads((ROOT/'provenance.json').read_text())['skills']
        for name, record in records.items():
            self.assertEqual(self.contracts.check_licences(ROOT, name, record), [], name)


class RegistryTests(unittest.TestCase):
    def test_every_skill_records_how_it_was_authored(self):
        records = json.loads((ROOT/'provenance.json').read_text())['skills']
        for name, record in records.items():
            self.assertTrue(record.get('authoring'), name)
            for entry in record['authoring']:
                self.assertTrue(entry['tool'] and entry['model'] and entry['date'], name)


if __name__ == '__main__':
    unittest.main()
