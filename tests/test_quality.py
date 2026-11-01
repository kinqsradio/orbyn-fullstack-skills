"""Behavior boundaries for presets, consumer context and recorded-trial tooling.

All evaluation observations here are synthetic fixtures, never model results.
"""
import copy
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_tools import ROOT, module, selection

evaluator = module('skill_evaluator', ROOT/'skills/orbyn-skill-creator/scripts/evaluate.py')


class PresetTests(unittest.TestCase):
    def test_documented_presets_match_current_membership(self):
        config = json.loads((ROOT/'skills/orbyn-setup/assets/presets.json').read_text())
        text = (ROOT/'docs/installation.md').read_text()
        rows = re.findall(r'^\| `([a-z-]+)`\s*\|[^\n|]+\|\s*(\d+)\s*\|$', text, re.M)
        self.assertEqual(len(rows), len(config['presets']))
        self.assertEqual(dict(rows), {name:str(len(preset['skills'])) for name,preset in config['presets'].items()})

    def test_default_is_core_and_all_is_explicit(self):
        self.assertEqual(selection.selection(), selection.selection(presets=['core']))
        self.assertEqual(len(selection.selection()), 14)
        self.assertEqual(len(selection.selection(all_skills=True)), len(json.loads((ROOT/'skills/catalog.json').read_text())['skills']))
        self.assertIn('orbyn-security-audit', selection.selection(presets=['security']))
        self.assertEqual(selection.selection(['how']), {'how'})
        combined = selection.selection(['how'], ['core', 'creator', 'core'])
        self.assertEqual(combined, selection.selection(presets=['core']) | selection.selection(presets=['creator']))
        with self.assertRaises(ValueError):
            selection.selection(presets=['core'], all_skills=True)






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

    def test_prepare_subset_is_explicit_and_rejects_unknown_duplicate_or_wrong_split(self):
        chosen = ['trace-save']
        folder = self.root/'subset'
        run = evaluator.prepare(folder, 'a'*40, 'fixture', 'fixture', 'fixture', case_ids=chosen)
        self.assertEqual(run['case_ids'], chosen)
        self.assertEqual(evaluator.grade(folder/'run.json')['counts']['unverified'], 1)
        for cases in [['missing'], ['trace-save', 'trace-save'], ['worker-history']]:
            output = self.root/'invalid'
            with self.subTest(cases=cases), self.assertRaisesRegex(ValueError, 'requested split'):
                evaluator.prepare(output, 'a'*40, 'fixture', 'fixture', 'fixture', case_ids=cases)
            self.assertFalse(output.exists())

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

    def test_routing_case_rubric_failure_fails_the_row(self):
        result = self.complete('statechart-art-adjacent-text-only')
        self.assertEqual(evaluator.grade(self.path)['counts']['pass'], 1)
        result['rubric']['scope']['status'] = 'fail'
        self.save()
        report = evaluator.grade(self.path)
        self.assertEqual(report['counts']['fail'], 1)
        self.assertEqual(report['results'][0]['status'], 'fail')

    def test_evidence_symlink_loop_is_an_ordinary_refusal(self):
        result = self.complete('statechart-art-adjacent-text-only')
        loop = self.path.parent/'loop.txt'
        loop.symlink_to('loop.txt')
        result['transcript'] = 'loop.txt'
        self.save()
        with self.assertRaises((ValueError, OSError)):
            evaluator.grade(self.path)

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
