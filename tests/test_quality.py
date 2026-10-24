"""Behavior boundaries for presets, consumer context and recorded-trial tooling.

All evaluation observations here are synthetic fixtures, never model results.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_tools import ROOT, module, installer

context = module('project_context', ROOT/'skills/orbyn-setup/scripts/project_context.py')
evaluator = module('skill_evaluator', ROOT/'skills/orbyn-skill-creator/scripts/evaluate.py')


class PresetTests(unittest.TestCase):
    def test_default_is_core_and_all_is_explicit(self):
        self.assertEqual(installer.selection(), installer.selection(presets=['core']))
        self.assertEqual(len(installer.selection()), 15)
        self.assertEqual(len(installer.selection(all_skills=True)), len(json.loads((ROOT/'skills/catalog.json').read_text())['skills']))
        self.assertIn('orbyn-security-audit', installer.selection(presets=['security']))
        self.assertEqual(installer.selection(['how']), {'how'})
        combined = installer.selection(['how'], ['core', 'creator', 'core'])
        self.assertEqual(combined, installer.selection(presets=['core']) | installer.selection(presets=['creator']))
        with self.assertRaises(ValueError):
            installer.selection(presets=['core'], all_skills=True)

    def test_dry_run_and_bad_names_leave_project_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(installer.install(root, 'both', dry_run=True), 30)
            for kwargs in [{'presets': ['missing']}, {'selected': ['missing']}]:
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    installer.install(root, 'both', **kwargs)
            self.assertEqual(list(root.iterdir()), [])

    def test_selecting_a_smaller_preset_never_uninstalls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installer.install(root, 'both', presets=['creator'])
            self.assertEqual(installer.install(root, 'codex', ['how']), 1)
            self.assertTrue((root/'.agents/skills/social-preview/SKILL.md').is_file())
            self.assertTrue((root/'.claude/skills/social-preview/SKILL.md').is_file())
            self.assertFalse((root/'.claude/skills/how').exists())


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'project'
        self.root.mkdir()
        (self.root/'AGENTS.md').write_text('Existing authority; do not replace.')

    def test_init_discovers_pointers_and_preserves_customization(self):
        self.assertTrue(context.initialize(self.root))
        path = self.root/context.CONTEXT
        data = context.check(self.root)
        self.assertEqual(data['documents'], {'instructions': 'AGENTS.md'})
        self.assertNotIn('Existing authority', path.read_text())
        (self.root/'src').mkdir()
        data['owners']['domain'] = 'src'
        path.write_text(json.dumps(data))
        original = path.read_bytes()
        self.assertFalse(context.initialize(self.root, 'Another name'))
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual((self.root/'AGENTS.md').read_text(), 'Existing authority; do not replace.')

    def test_invalid_pointers_and_executable_fields_are_refused(self):
        context.initialize(self.root)
        path = self.root/context.CONTEXT
        original = context.check(self.root)
        for value in ['../outside', '/etc/hosts', 'missing.md', 'file://outside']:
            data = copy.deepcopy(original)
            data['documents']['stack'] = value
            path.write_text(json.dumps(data))
            with self.subTest(value=value), self.assertRaises((ValueError, OSError)):
                context.check(self.root)
        data = copy.deepcopy(original)
        data['commands'] = {'build': 'arbitrary-command'}
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Unknown context fields'):
            context.initialize(self.root)
        self.assertEqual(json.loads(path.read_text()), data)

    def test_symlink_escape_and_symlink_destination_are_refused(self):
        outside = self.root.parent/'outside'
        outside.mkdir()
        (outside/'guide.md').write_text('Outside guide')
        (self.root/'docs').symlink_to(outside, target_is_directory=True)
        context.initialize(self.root)
        path = self.root/context.CONTEXT
        data = context.check(self.root)
        data['documents']['stack'] = 'docs/guide.md'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'leaves the project'):
            context.check(self.root)
        path.unlink()
        path.parent.rmdir()
        path.parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            context.initialize(self.root)
        self.assertFalse((outside/'orbyn-context.json').exists())


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root/'trial/run.json'
        protocol = self.root/'protocol-input.json'
        protocol.write_text(json.dumps({'fixture': 'synthetic', 'tools': 'none'}))
        self.run = evaluator.prepare(self.path.parent, 'a'*40, 'fixture host',
                                     'fixture model', 'fixture', split='all', protocol=protocol)
        self.cases = {c['id']: c for c in evaluator.suite()[0]['cases']}

    def save(self):
        self.path.write_text(json.dumps(self.run))

    def focus(self, name, trials=1):
        self.run['case_ids'] = [name]
        self.run['trials'] = trials
        self.run['results'] = [r for r in self.run['results'] if r['case_id'] == name]
        self.save()
        return self.run['results'][0]

    def complete(self, name):
        result = self.focus(name)
        (self.path.parent/'transcript.txt').write_text('SYNTHETIC TOOLING FIXTURE. Captured explanation.')
        (self.path.parent/'answer.md').write_text('SYNTHETIC TOOLING FIXTURE. Artifact explanation.')
        result.update(status='completed', selected_skills=self.cases[name]['expected_skills'],
                      transcript='transcript.txt', artifacts=['answer.md'], reviewer='Fixture observer',
                      rubric={key: {'status': 'pass', 'evidence': 'Artifact explanation.'}
                              for key in self.cases[name].get('rubric', {})})
        self.save()
        return result

    def test_prepare_keeps_answers_out_and_results_unverified(self):
        tasks = json.loads((self.path.parent/'tasks.json').read_text())
        self.assertEqual(len(tasks), len(self.cases))
        self.assertEqual({task['case_id'] for task in tasks}, set(self.cases))
        self.assertEqual(set(tasks[0]), {'case_id', 'trial', 'prompt'})
        report = evaluator.grade(self.path)
        self.assertEqual(report['counts'], {'pass': 0, 'fail': 0, 'unverified': len(self.cases)})
        self.assertEqual(report['evidence_kind'], 'synthetic-fixture')
        before = self.path.read_bytes()
        with self.assertRaises(FileExistsError):
            evaluator.prepare(self.path.parent, 'a'*40, 'fixture', 'fixture', 'fixture')
        self.assertEqual(self.path.read_bytes(), before)

    def test_omitted_result_is_not_silently_dropped(self):
        self.focus('trace-save', trials=2)
        self.run['results'] = []
        self.save()
        self.assertEqual(evaluator.grade(self.path)['counts']['unverified'], 2)

    def test_wrong_route_and_forbidden_effect_fail(self):
        result = self.complete('settings-copy')
        result['selected_skills'] = ['orbyn-content-design', 'social-content']
        self.save()
        self.assertEqual(evaluator.grade(self.path)['counts']['fail'], 1)
        result['selected_skills'] = ['orbyn-content-design']
        result['actions'] = ['publish']
        self.save()
        report = evaluator.grade(self.path)
        self.assertEqual(report['results'][0]['routing'], 'pass')
        self.assertEqual(report['counts']['fail'], 1)
        self.assertEqual(report['results'][0]['forbidden_actions'], ['publish'])

    def test_product_write_also_violates_no_write_scope(self):
        result = self.complete('app-ci-not-rea')
        result['actions'] = ['write_product']
        self.save()
        self.assertEqual(evaluator.grade(self.path)['counts']['fail'], 1)

    def test_empty_artifact_does_not_qualify_an_outcome(self):
        self.complete('approval-contract')
        (self.path.parent/'answer.md').write_text('')
        with self.assertRaisesRegex(ValueError, 'contain output'):
            evaluator.grade(self.path)

    def test_no_skill_case_requires_no_skill(self):
        result = self.complete('simple-text-edit')
        self.assertEqual(evaluator.grade(self.path)['counts']['pass'], 1)
        result['selected_skills'] = ['how']
        self.save()
        self.assertEqual(evaluator.grade(self.path)['counts']['fail'], 1)

    def test_outcome_requires_artifact_and_all_rubric_evidence(self):
        result = self.complete('approval-contract')
        result['artifacts'] = []
        result['rubric'] = {}
        self.save()
        self.assertEqual(evaluator.grade(self.path)['counts']['unverified'], 1)
        result['artifacts'] = ['answer.md']
        result['rubric'] = {'authority': {'status': 'pass', 'evidence': 'invented quote'}}
        self.save()
        with self.assertRaisesRegex(ValueError, 'exact excerpt'):
            evaluator.grade(self.path)

    def test_outcome_and_route_are_distinct_and_metrics_not_invented(self):
        result = self.complete('approval-contract')
        result['selected_skills'] = []
        self.save()
        row = evaluator.grade(self.path)['results'][0]
        self.assertEqual(row['routing'], 'fail')
        self.assertEqual(row['outcome'], 'pass')
        self.assertIsNone(row['total_tokens'])
        self.assertEqual(set(row['evidence_sha256']), {'transcript.txt', 'answer.md'})
        self.assertTrue(all(len(v) == 64 for v in row['evidence_sha256'].values()))
        result['rubric']['authority']['status'] = 'fail'
        self.save()
        self.assertEqual(evaluator.grade(self.path)['counts']['fail'], 1)

    def test_suite_changes_and_duplicate_results_are_rejected(self):
        self.focus('trace-save')
        self.run['suite_sha256'] = '0'*64
        self.save()
        with self.assertRaisesRegex(ValueError, 'another suite'):
            evaluator.grade(self.path)
        self.run['suite_sha256'] = evaluator.suite()[1]
        self.run['results'] *= 2
        self.save()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            evaluator.grade(self.path)

    def test_evidence_escape_is_rejected_including_symlinks(self):
        result = self.complete('trace-save')
        outside = self.root/'outside.txt'
        outside.write_text('Outside evidence')
        (self.path.parent/'escape.txt').symlink_to(outside)
        for filename in ['../outside.txt', str(outside), 'escape.txt']:
            result['transcript'] = filename
            self.save()
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                evaluator.grade(self.path)

    def test_comparison_refuses_fixtures_incomplete_and_unmatched_runs(self):
        self.complete('trace-save')
        with self.assertRaisesRegex(ValueError, 'fixtures are not benchmarks'):
            evaluator.compare(self.path, self.path)
        baseline = self.path.parent/'baseline.json'
        self.run['condition'] = 'baseline'
        baseline.write_text(json.dumps(self.run))
        self.run['condition'] = 'candidate'
        self.run['results'][0]['status'] = 'not_run'
        self.save()
        with self.assertRaisesRegex(ValueError, 'Complete both runs'):
            evaluator.compare(baseline, self.path)
        self.run['results'][0]['status'] = 'completed'
        self.run['host'] = 'different host'
        self.save()
        with self.assertRaisesRegex(ValueError, 'share host'):
            evaluator.compare(baseline, self.path)
        self.run['host'] = 'fixture host'
        self.run['results'][0]['selected_skills'] = []
        self.save()
        # Synthetic boundary check of the compare function, not a benchmark.
        report = evaluator.compare(baseline, self.path)
        self.assertEqual(report['baseline']['routing'], {'passed': 1, 'total': 1})
        self.assertEqual(report['candidate']['routing'], {'passed': 0, 'total': 1})

    def test_protocol_copy_is_frozen_and_tampering_is_rejected(self):
        protocol = self.path.parent/'protocol.json'
        before = protocol.read_bytes()
        (self.root/'protocol-input.json').write_text('{"changed": true}')
        self.assertEqual(protocol.read_bytes(), before)
        protocol.write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, 'Protocol checksum differs'):
            evaluator.grade(self.path)

    def test_comparison_requires_same_pinned_protocol(self):
        import hashlib
        import shutil
        self.complete('trace-save')
        self.run['condition'] = 'baseline'
        self.save()
        other = self.root/'candidate'
        shutil.copytree(self.path.parent, other)
        candidate = json.loads((other/'run.json').read_text())
        candidate['condition'] = 'candidate'
        (other/'protocol.json').write_text('{"fixture": "different"}')
        candidate['protocol_sha256'] = hashlib.sha256((other/'protocol.json').read_bytes()).hexdigest()
        (other/'run.json').write_text(json.dumps(candidate))
        with self.assertRaisesRegex(ValueError, 'share protocol_sha256'):
            evaluator.compare(self.path, other/'run.json')
        candidate['protocol_sha256'] = None
        (other/'run.json').write_text(json.dumps(candidate))
        with self.assertRaisesRegex(ValueError, 'pinned protocol'):
            evaluator.compare(self.path, other/'run.json')

    def test_cli_returns_failure_for_unverified_and_invalid_records(self):
        command = [sys.executable, str(ROOT/'skills/orbyn-skill-creator/scripts/evaluate.py'), 'grade', str(self.path)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['counts']['unverified'], len(self.cases))
        self.run['suite_sha256'] = '0'*64
        self.save()
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('another suite', result.stderr)


if __name__ == '__main__':
    unittest.main()
