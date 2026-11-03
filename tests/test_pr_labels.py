"""Automatic PR labels: what is applied publicly, and nothing else. A fake gh records every call."""
import json
import unittest
from unittest import mock

from test_tools import ROOT, module

labels = module('pr_labels', ROOT/'scripts/pr_labels.py')
insights = module('pr_insights', ROOT/'scripts/pr_insights.py')

BODY = """## Agent disclosure

- Tools: {tools}
- Models: claude-opus-5-5
"""


def pr(tools='Claude Code', association='OWNER', **extra):
    return {'author_association': association, 'draft': False, 'body': BODY.format(tools=tools), 'labels': [], **extra}


def file(name, status='modified', additions=1, deletions=0, patch=''):
    return {'filename': name, 'status': status, 'additions': additions, 'deletions': deletions, 'patch': patch}


def none(_):
    return []


def decide(record, files, affected=none):
    return labels.decide(record, files, affected)


def desired(record, files, affected=none):
    return set(decide(record, files, affected)['desired'])


class AreaTests(unittest.TestCase):
    def test_new_skill_versus_update(self):
        new = desired(pr(), [file('skills/fresh/SKILL.md', 'added'), file('skills/fresh/references/a.md', 'added')])
        self.assertIn('skill: new', new)
        self.assertNotIn('skill: update', new)
        update = desired(pr(), [file('skills/tdd/references/a.md')])
        self.assertIn('skill: update', update)
        self.assertNotIn('skill: new', update)

    def test_each_area_from_paths(self):
        cases = {
            'area: harness': ['skills/orbyn-workflow/scripts/harness.py', 'docs/agents/models.json',
                              '.claude/agents/orbyn-lead.md', 'scripts/sync-agent-models.py'],
            'area: evals': ['skills/orbyn-skill-creator/evals/cases.json', 'skills/x/scripts/eval_run.py', 'a/evaluate.py'],
            'area: security': ['skills/orbyn-security-audit/SKILL.md'],
            'area: ci': ['.github/workflows/x.yml', 'scripts/run_tests.py', 'scripts/pr_gate.py', 'scripts/pr_labels.py'],
            'area: hosts': ['AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '.agents/skills/x', '.claude/skills/x'],
        }
        for label, paths in cases.items():
            for path in paths:
                self.assertIn(label, desired(pr(), [file(path)]), (label, path))

    def test_docs_only_means_nothing_else_changed(self):
        self.assertIn('area: docs', desired(pr(), [file('README.md'), file('docs/a.md'), file('CONTRIBUTING.md')]))
        self.assertNotIn('area: docs', desired(pr(), [file('README.md'), file('scripts/x.py')]))
        self.assertIn('area: docs', desired(pr(), [file('docs/a.md'), file('distribution/manifest.json')]))

    def test_upstream_adaptation(self):
        patch = '@@ -1 +1,2 @@\n+  "incorporated_material": [\n'
        self.assertIn('upstream adaptation', desired(pr(), [file('provenance.json', patch=patch)]))
        self.assertIn('upstream adaptation', desired(pr(), [file('skills/x/references/upstream/a.md', 'added')]))
        self.assertNotIn('upstream adaptation', desired(pr(), [file('provenance.json', patch=' "incorporated_material": [\n')]))


class ContributorTests(unittest.TestCase):
    def test_community_and_first_contribution_come_from_association_only(self):
        expect = {'OWNER': set(), 'MEMBER': set(), 'COLLABORATOR': set(),
                  'CONTRIBUTOR': {'community'}, 'NONE': {'community'},
                  'FIRST_TIME_CONTRIBUTOR': {'community', 'first contribution'},
                  'FIRST_TIMER': {'community', 'first contribution'}}
        for association, wanted in expect.items():
            got = desired(pr(association=association), [file('docs/a.md')]) & {'community', 'first contribution'}
            self.assertEqual(got, wanted, association)

    def test_identity_in_the_description_or_user_changes_nothing(self):
        record = pr(association='OWNER', user={'login': 'x', 'email': 'a@acme.com', 'company': 'Acme'})
        record['body'] += '\nI work at Acme Corp, first time here, a@acme.com'
        got = desired(record, [file('docs/a.md')])
        self.assertFalse(got & {'community', 'first contribution'})
        self.assertEqual({l for l in got if not l.startswith(('built with', 'size', 'area'))}, set())


class ToolTests(unittest.TestCase):
    def test_allowlisted_tools(self):
        for text, label in (('Claude Code 2.1', 'built with: claude code'), ('Codex CLI', 'built with: codex'),
                            ('Cursor', 'built with: cursor'), ('GitHub Copilot', 'built with: copilot'),
                            ('Gemini CLI', 'built with: gemini')):
            self.assertIn(label, labels.tool_labels(BODY.format(tools=text)))
        both = labels.tool_labels(BODY.format(tools='Claude Code and Codex'))
        self.assertEqual(both, {'built with: claude code', 'built with: codex'})

    def test_unknown_tool_is_other_and_free_text_never_becomes_a_label(self):
        got = labels.tool_labels(BODY.format(tools='area: security, size: s, my-private-agent'))
        self.assertEqual(got, {'built with: other'})
        self.assertTrue(desired(pr(tools='skill: new; evil'), [file('docs/a.md')]) <= set(labels.CATALOG))

    def test_human_only_and_missing(self):
        self.assertEqual(labels.tool_labels(BODY.format(tools='No agent was used')), {'human only'})
        self.assertEqual(labels.tool_labels(BODY.format(tools='')), set())
        self.assertEqual(labels.tool_labels('no disclosure here'), set())
        self.assertEqual(labels.tool_labels(None), set())


class SizeAndNeedsTests(unittest.TestCase):
    def test_size_buckets_exclude_generated_files(self):
        def size(n, extra=()):
            return labels.size_label([file('a.md', additions=n), *extra])
        self.assertEqual((size(99), size(100), size(499), size(500), size(1999), size(2000)),
                         ('size: s', 'size: m', 'size: m', 'size: l', 'size: l', 'size: xl'))
        generated = [file('distribution/manifest.json', additions=5000), file('provenance.json', additions=5000)]
        self.assertEqual(size(10, generated), 'size: s')

    def test_eval_run_trigger(self):
        self.assertIn('eval run', desired(pr(), [file('skills/x/a.md')], lambda changed: ['case']))
        self.assertNotIn('eval run', desired(pr(), [file('docs/a.md')], none))
        self.assertIn('eval run', desired(pr(), [file('skills/orbyn-workflow/scripts/harness.py')], none))

    def test_eval_run_uses_the_real_affected_cases_rule(self):
        got = labels.load_affected()(['docs/agents/models.json'])
        self.assertTrue(got)
        self.assertEqual(labels.load_affected()(['README.md']), [])

    def test_hand_off_needs_draft_and_open_findings(self):
        body = BODY.format(tools='Codex') + '\n## Open findings\n\n- one\n'
        self.assertIn('agent hand-off', desired(pr(draft=True, body=body), [file('docs/a.md')]))
        self.assertNotIn('agent hand-off', desired(pr(draft=False, body=body), [file('docs/a.md')]))
        self.assertNotIn('agent hand-off', desired(pr(draft=True), [file('docs/a.md')]))
        commented = BODY.format(tools='Codex') + '\n<!-- ## Open findings -->\n'
        self.assertNotIn('agent hand-off', desired(pr(draft=True, body=commented), [file('docs/a.md')]))


class FakeGh:
    """Stands in for the gh CLI: serves a PR, records every call, and applies label edits."""
    def __init__(self, record, files, current=()):
        self.record, self.files = dict(record), files
        self.record['labels'] = [{'name': n} for n in current]
        self.calls = []

    def __call__(self, *args, stdin=None):
        self.calls.append(args)
        if args[0] == 'api' and args[-1].endswith('/files?per_page=100'):
            return json.dumps([self.files])
        if args[0] == 'api':
            return json.dumps(self.record)
        if args[:2] == ('pr', 'edit'):
            names = {l['name'] for l in self.record['labels']}
            for flag, name in zip(args[3::2], args[4::2]):
                (names.add if flag == '--add-label' else names.discard)(name)
            self.record['labels'] = [{'name': n} for n in sorted(names)]
        return ''

    def writes(self):
        return [c for c in self.calls if c[0] != 'api']


class ApplyTests(unittest.TestCase):
    def run_apply(self, fake):
        with mock.patch.object(labels, 'gh', fake), mock.patch('builtins.print'):
            labels.apply(7, 'o/r', none)

    def test_removes_stale_owned_labels_and_leaves_others(self):
        fake = FakeGh(pr(), [file('docs/a.md')], current=['size: xl', 'community', 'bug', 'needs-disclosure', 'ready-for-review', 'skill: new'])
        self.run_apply(fake)
        names = {l['name'] for l in fake.record['labels']}
        self.assertTrue({'bug', 'needs-disclosure', 'ready-for-review'} <= names)
        self.assertFalse(names & {'size: xl', 'community', 'skill: new'})
        self.assertTrue({'size: s', 'area: docs', 'built with: claude code'} <= names)
        touched = {c[i + 1] for c in fake.writes() if c[:2] == ('pr', 'edit') for i, a in enumerate(c) if a in ('--add-label', '--remove-label')}
        self.assertFalse(touched & {'bug', 'needs-disclosure', 'ready-for-review'})

    def test_creates_labels_with_fixed_colour_and_only_what_it_adds(self):
        fake = FakeGh(pr(), [file('docs/a.md')])
        self.run_apply(fake)
        created = [c for c in fake.writes() if c[:2] == ('label', 'create')]
        self.assertTrue(created)
        for call in created:
            self.assertIn(call[2], labels.CATALOG)
            self.assertEqual(call[call.index('--color') + 1], labels.CATALOG[call[2]][0])
        self.assertTrue(all(c[0] in ('label', 'pr') for c in fake.writes()))

    def test_second_run_writes_nothing(self):
        fake = FakeGh(pr(association='NONE'), [file('skills/tdd/a.md')])
        self.run_apply(fake)
        fake.calls.clear()
        self.run_apply(fake)
        self.assertEqual(fake.writes(), [])


class InsightsTests(unittest.TestCase):
    def test_summarises_a_fake_history(self):
        history = [
            {'labels': ['skill: update', 'community', 'built with: codex', 'size: s'], 'skills': ['tdd']},
            {'labels': ['skill: update', 'built with: claude code', 'size: m', 'eval run'], 'skills': ['tdd', 'how']},
            {'labels': ['skill: new', 'first contribution', 'community', 'human only', 'size: xl', 'agent hand-off'], 'skills': []},
            {'labels': ['area: docs', 'size: s', 'built with: claude code'], 'skills': []},
        ]
        got = insights.summarise(history)
        self.assertEqual(got['merged_prs'], 4)
        self.assertEqual(got['contributors'], {'community': 2, 'maintainer': 2, 'first contribution': 1})
        self.assertEqual(got['built_with'], {'claude code': 2, 'codex': 1, 'human only': 1})
        self.assertEqual(got['sizes'], {'m': 1, 's': 2, 'xl': 1})
        self.assertEqual(got['needs'], {'eval run': 1, 'agent hand-off': 1})
        self.assertEqual(got['areas'], {'docs': 1, 'skill: new': 1, 'skill: update': 2})
        self.assertEqual(got['skill_update_share'], {'tdd': {'prs': 2, 'share': 1.0}, 'how': {'prs': 1, 'share': 0.5}})
        self.assertIn('tdd: 2 (100%)', insights.markdown(got))

    def test_reads_merged_prs_only_and_never_writes(self):
        rows = [{'number': 1, 'merged_at': '2026-11-01', 'labels': [{'name': 'size: s'}]},
                {'number': 2, 'merged_at': None, 'labels': []}]
        calls = []

        def fake(*args):
            calls.append(args)
            return json.dumps(rows if '&page=1' in args[1] else [])
        with mock.patch.object(insights, 'gh', fake):
            got = insights.history('o/r', 10)
        self.assertEqual([p['number'] for p in got], [1])
        self.assertTrue(all(c[0] == 'api' and '-X' not in c for c in calls))


if __name__ == '__main__':
    unittest.main()
