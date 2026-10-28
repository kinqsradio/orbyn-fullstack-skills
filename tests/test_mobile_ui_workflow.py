"""Coverage integrity and executable synthetic contracts; no cloud/model calls."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/mobile-ui-workflow'

class MobileWorkflowTests(unittest.TestCase):
    def test_source_dispositions_close_to_real_local_owners(self):
        data = json.loads((ROOT / 'docs/work/mobile-ui-workflow-coverage.json').read_text())
        self.assertEqual(set(data['upstream_entrypoints']), {'expo', 'emil'})
        self.assertEqual(len(data['upstream_entrypoints']['expo']), 24)
        self.assertEqual(len(data['upstream_entrypoints']['emil']), 15)
        identities = set()
        for row in data['sources']:
            identity = row['source'], row['path']
            self.assertNotIn(identity, identities)
            identities.add(identity)
            self.assertRegex(row['sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(row['reason'])
            for destination in row['destinations']:
                path = (ROOT / destination).resolve()
                self.assertTrue(path.is_relative_to(ROOT))
                self.assertTrue(path.is_file(), destination)
            if row['disposition'] == 'selected-method-adaptation':
                self.assertTrue(row['destinations'])
        for source, entries in data['upstream_entrypoints'].items():
            selected = {row['family'] for row in data['sources']
                        if row['source'] == source and row['path'].endswith('/SKILL.md')}
            self.assertTrue(set(entries).issubset(selected))

    def test_acceptance_groups_have_cases_and_honest_surface(self):
        coverage = json.loads((ROOT / 'docs/work/mobile-ui-workflow-coverage.json').read_text())
        cases = {case['id']: case for case in json.loads((ROOT / 'skills/orbyn-skill-creator/evals/cases.json').read_text())['cases']}
        expected = {f'M{i:02}' for i in range(1, 18)} | {f'U{i:02}' for i in range(1, 9)} | {f'W{i:02}' for i in range(1, 5)} | {'E01','E02'}
        self.assertEqual({group['id'] for group in coverage['acceptance_groups']}, expected)
        for group in coverage['acceptance_groups']:
            case = cases[group['development_case_id']]
            self.assertEqual(case['split'], 'development')
            self.assertIn(group['owner'], case['expected_skills'])
            self.assertTrue(group['current_evidence'])
            self.assertTrue(group['failure_control'])
        pilot = json.loads((FIXTURE / 'pilot-protocol.json').read_text())
        self.assertEqual(len(pilot['tasks']) * pilot['trials_per_condition'] * len(pilot['conditions']), 48)
        self.assertEqual(pilot['completed_executions'], 0)  # prospective protocol, not a result

    @unittest.skipUnless(shutil.which('node'), 'Node required for executable fixture')
    def test_shared_screen_and_reconciliation_contracts(self):
        result = subprocess.run(['node', '--test', str(FIXTURE / 'contracts.test.mjs')], capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('# tests 14', result.stdout)
        self.assertIn('# fail 0', result.stdout)

    @unittest.skipUnless(shutil.which('node'), 'Node required for executable fixture')
    def test_actual_stale_owner_negative_control_is_detected(self):
        """Mutate the shared boundary in a disposable copy, never a mirrored stand-in."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copytree(FIXTURE / 'src', target / 'src')
            shutil.copy2(FIXTURE / 'contracts.test.mjs', target / 'contracts.test.mjs')
            source = target / 'src/contracts.mjs'
            text = source.read_text()
            old = 'if (!active || current !== generation) return;'
            self.assertEqual(text.count(old), 2)
            source.write_text(text.replace(old, 'if (!active) return;'))
            result = subprocess.run(['node', '--test', str(target / 'contracts.test.mjs')], capture_output=True, text=True, timeout=45)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('not ok 1 - screen boundary rejects late account completion', result.stdout)

    @unittest.skipUnless(shutil.which('ruby'), 'Ruby required for disposable native-target path guard')
    def test_native_target_guard_accepts_only_selected_root_without_opening_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source_dir = root / 'tests/fixtures/mobile-ui-workflow'
            source_dir.mkdir(parents=True)
            script = source_dir / 'configure-ui-tests.rb'
            shutil.copy2(FIXTURE / script.name, script)
            source = source_dir / 'native-ui-tests.swift'
            source.write_text('// owned source\n')
            project = root / 'output/mobile-ui-workflow/runtime/ios/OrbynWorkflowFixture.xcodeproj'
            project.mkdir(parents=True)
            sentinel = project / 'project.pbxproj'
            sentinel.write_text('Not a valid Xcode project: a --check must never open this.\n')
            result = subprocess.run(['ruby', str(script), str(project), str(source), '--check'], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('no project opened or written', result.stdout)
            self.assertTrue(sentinel.read_text().startswith('Not a valid Xcode'))

    @unittest.skipUnless(shutil.which('ruby'), 'Ruby required for disposable native-target path guard')
    def test_native_target_guard_rejects_foreign_fixture_shaped_project_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            owner = root / 'owner'
            source_dir = owner / 'tests/fixtures/mobile-ui-workflow'
            source_dir.mkdir(parents=True)
            script = source_dir / 'configure-ui-tests.rb'
            shutil.copy2(FIXTURE / script.name, script)
            source = source_dir / 'native-ui-tests.swift'
            source.write_text('// owned\n')
            own_project = owner / 'output/mobile-ui-workflow/runtime/ios/OrbynWorkflowFixture.xcodeproj'
            own_project.mkdir(parents=True)
            foreign = root / 'foreign/output/mobile-ui-workflow/runtime/ios/OrbynWorkflowFixture.xcodeproj'
            foreign.mkdir(parents=True)
            foreign_source = root / 'foreign/native-ui-tests.swift'
            foreign_source.write_text('// foreign\n')
            for project, selected_source in [(foreign, source), (own_project, foreign_source)]:
                result = subprocess.run(['ruby', str(script), str(project), str(selected_source), '--check'], capture_output=True, text=True, timeout=15)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Expected exact owned fixture', result.stderr)
            self.assertEqual(foreign_source.read_text(), '// foreign\n')

if __name__ == '__main__':
    unittest.main()
