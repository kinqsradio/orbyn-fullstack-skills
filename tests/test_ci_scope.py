"""CI scope and promotion must fail conservatively with real Git diff fixtures."""
import copy
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_tools import ROOT, module

scope = module('ci_scope', ROOT/'skills/orbyn-ci-design/scripts/ci_scope.py')
POLICY = dict(schema_version=1, docs_files=['README.md', 'LICENSE'], docs_prefixes=['docs/'],
              skills_files=['AGENTS.md', 'scripts/library_manifest.py'],
              skills_prefixes=['skills/', 'project-skills/', 'docs/agents/'],
              deployment_files=['package-lock.json'], deployment_prefixes=['backend/', 'packages/'],
              application_jobs=['api', 'web'])


class ScopeTests(unittest.TestCase):
    def decision(self, paths, complete=True):
        return scope.classify(paths, POLICY, complete)

    def test_docs_do_not_run_or_deploy_the_application(self):
        data = self.decision(['README.md', 'docs/setup.md', 'LICENSE'])
        self.assertEqual(data['scope'], 'docs')
        self.assertFalse(data['run_app'])
        self.assertFalse(data['deploy'])

    def test_skills_and_helpers_select_the_focused_lane(self):
        data = self.decision(['README.md', 'skills/example/script.py', 'scripts/library_manifest.py'])
        self.assertEqual(data['scope'], 'skills')
        self.assertFalse(data['run_app'])
        self.assertFalse(data['deploy'])
        self.assertEqual(self.decision(['docs/agents/coordination.md'])['scope'], 'skills')

    def test_runtime_shared_dependencies_and_mixed_paths_select_full_checks(self):
        for path in ['backend/auth.ts', 'packages/core/schema.ts', 'package-lock.json']:
            with self.subTest(path=path):
                data = self.decision(['docs/setup.md', path])
                self.assertTrue(data['run_app'])
                self.assertTrue(data['deploy'])

    def test_unknown_binary_and_ci_inputs_cannot_take_the_docs_lane(self):
        for path in ['unknown/new.tool', 'docs/template.html', 'docs/diagram.png',
                     '.github/workflows/ci.yml', 'skills/orbyn-ci-design/scripts/ci_scope.py']:
            with self.subTest(path=path):
                data = self.decision([path])
                self.assertTrue(data['run_app'])
                self.assertFalse(data['deploy'])

    def test_incomplete_evidence_and_unsafe_paths_never_skip_or_auto_deploy(self):
        for paths, complete in [(['backend/auth.ts'], False), (['../outside'], True),
                                (['docs/name\nextra.md'], True)]:
            data = self.decision(paths, complete)
            self.assertTrue(data['run_app'])
            self.assertFalse(data['deploy'])
            self.assertFalse(data['complete'])

    def test_invalid_policy_is_rejected(self):
        for key, value in [('docs_prefixes', ['../outside/']), ('skills_files', ['']),
                           ('application_jobs', []), ('schema_version', True),
                           ('docs_files', ['README.md', 'README.md'])]:
            policy = copy.deepcopy(POLICY)
            policy[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                scope.classify(['README.md'], policy)

    def test_required_gate_rejects_failure_cancellation_missing_and_unexpected_skip(self):
        good = {'changes': {'result': 'success', 'outputs': {'run_app': 'true'}},
                'api': {'result': 'success'}, 'web': {'result': 'success'}}
        scope.check_gate(good, POLICY)
        for outcome in ['failure', 'cancelled', 'skipped', None]:
            needs = copy.deepcopy(good)
            needs['web']['result'] = outcome
            with self.subTest(outcome=outcome), self.assertRaises(ValueError):
                scope.check_gate(needs, POLICY)
        for selection in [{'result': 'failure'}, {'result': 'skipped'},
                          {'result': 'success', 'outputs': {}}]:
            needs = dict(good, changes=selection)
            with self.assertRaises(ValueError):
                scope.check_gate(needs, POLICY)

    def test_lightweight_gate_allows_only_intentional_skips_or_success(self):
        needs = {'changes': {'result': 'success', 'outputs': {'run_app': 'false'}},
                 'api': {'result': 'skipped'}, 'web': {'result': 'skipped'}}
        scope.check_gate(needs, POLICY)
        for outcome in ['failure', 'cancelled', None]:
            needs['web']['result'] = outcome
            with self.assertRaises(ValueError):
                scope.check_gate(needs, POLICY)

    def test_deployment_requires_matching_trusted_runtime_decision(self):
        record = dict(self.decision(['backend/auth.ts']), schema_version=1,
                      event='push', head='a'*40, repository='acme/app')
        self.assertTrue(scope.deployment_allowed(record, 'a'*40, 'acme/app'))
        for field, value in [('event', 'pull_request'), ('head', 'b'*40),
                             ('repository', 'fork/app'), ('complete', False),
                             ('run_app', False), ('scope', 'docs'), ('deploy', 'true')]:
            changed = dict(record, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                scope.deployment_allowed(changed, 'a'*40, 'acme/app')
        record.update(self.decision(['README.md']))
        self.assertFalse(scope.deployment_allowed(record, 'a'*40, 'acme/app'))


class GitChangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q', '-b', 'main')
        self.write('docs/source.md', 'baseline')
        self.base = self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True,
                                       stderr=subprocess.STDOUT).strip()

    def write(self, path, text):
        target = self.root/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self):
        self.git('add', '--all')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'Fixture', '--no-verify')
        return self.git('rev-parse', 'HEAD')

    def test_whole_push_sees_runtime_change_before_final_docs_commit(self):
        self.write('backend/code.ts', 'runtime')
        self.commit()
        self.write('docs/source.md', 'final docs edit')
        head = self.commit()
        paths, complete = scope.changed_paths(self.root, self.base, head, 'push')
        self.assertTrue(complete)
        self.assertIn('backend/code.ts', paths)
        self.assertTrue(scope.classify(paths, POLICY, complete)['deploy'])

    def test_rename_checks_old_and_new_paths_and_deleted_files(self):
        (self.root/'backend').mkdir()
        (self.root/'docs/source.md').rename(self.root/'backend/source.md')
        head = self.commit()
        paths, complete = scope.changed_paths(self.root, self.base, head, 'pull_request')
        self.assertTrue(complete)
        self.assertEqual(set(paths), {'docs/source.md', 'backend/source.md'})
        self.assertTrue(scope.classify(paths, POLICY, complete)['run_app'])

    def test_pr_merge_base_excludes_unrelated_new_base_changes(self):
        self.git('checkout', '-qb', 'feature')
        self.write('docs/source.md', 'feature docs')
        head = self.commit()
        self.git('checkout', '-q', 'main')
        self.write('backend/code.ts', 'new base runtime')
        base = self.commit()
        paths, complete = scope.changed_paths(self.root, base, head, 'pull_request')
        self.assertTrue(complete)
        self.assertEqual(paths, ['docs/source.md'])

    def test_missing_revision_keeps_full_checks_and_disables_deployment(self):
        paths, complete = scope.changed_paths(self.root, '0'*40, self.base, 'push')
        data = scope.classify(paths, POLICY, complete)
        self.assertTrue(data['run_app'])
        self.assertFalse(data['deploy'])
