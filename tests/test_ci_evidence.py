"""Exercise complete evidence, adverse inputs and actual disposable pipeline behavior."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from test_tools import ROOT, module, sync

ci = module('ci_evidence', ROOT/'skills/orbyn-ci-design/scripts/ci_evidence.py')
junit = module('junit_evidence', ROOT/'skills/orbyn-ci-design/scripts/junit_evidence.py')
lab = module('pipeline_lab', ROOT/'skills/orbyn-skill-creator/scripts/pipeline_lab.py')


class CIEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()/'lab'
        lab.stress(self.root, 3)
        self.plan = json.loads((self.root/'plan.json').read_text())
        self.serial = 0

    def run_plan(self, plan=None):
        self.serial += 1
        p = self.root/f'plan-{self.serial}.json'
        p.write_text(json.dumps(plan or self.plan))
        return ci.analyze(p, self.root/f'analysis-{self.serial}'), self.root/f'analysis-{self.serial}'

    def report(self, cohort, rows, attempt=1, status=None):
        name = f'{cohort}-{attempt}.jsonl'
        path = self.root/name
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        template = copy.deepcopy(next(r for r in self.plan['runs'] if r['cohort'] == cohort))
        template.update(attempt=attempt, run_id=f'{cohort}-{attempt}', path=name,
                        sha256=ci.file_hash(path), status=status or ('success' if all(r['status']=='passed' for r in rows) else 'failure'))
        self.plan['runs'] = [r for r in self.plan['runs'] if not (r['cohort']==cohort and r['attempt']==attempt)]+[template]

    @staticmethod
    def row(name, state='passed', message='shared outage'):
        result = dict(test_id=name, status=state)
        if state in {'failed','error'}:
            result.update(failure_type='AssertionError' if state=='failed' else 'ConnectionError', message=message)
        return result

    def test_report_symlink_loop_is_a_blocker_not_a_crash(self):
        (self.root/'loop.jsonl').symlink_to('loop.jsonl')
        self.plan['runs'][1]['path'] = 'loop.jsonl'
        result, _ = self.run_plan()
        self.assertFalse(result['ci_evidence_ready'])
        self.assertTrue(any('Invalid report' in row['reason'] for row in result['blockers']))

    def test_streamed_scale_and_non_destructive_output(self):
        scale = self.root/'larger'
        lab.stress(scale, 10000)
        result = ci.analyze(scale/'plan.json', scale/'analysis')
        self.assertTrue(result['ci_evidence_ready'])
        self.assertEqual(result['counts'], {'passed':10000})
        with sqlite3.connect(scale/'analysis/evidence.sqlite') as db:
            self.assertEqual(db.execute('SELECT count(*) FROM results').fetchone()[0],20000)
        with self.assertRaisesRegex(ValueError,'must not exist'):
            ci.analyze(scale/'plan.json', scale/'analysis')

    def test_full_failure_inventory_and_comparison_not_just_top_clusters(self):
        self.report('baseline', [self.row('a','failed'),self.row('b'),self.row('c','failed','old'),self.row('resolved','failed')])
        self.report('candidate', [self.row('a','failed'),self.row('b','failed'),self.row('c','failed','new'),self.row('d','error'),self.row('resolved')])
        result, output = self.run_plan()
        self.assertEqual(result['failure_comparison'],dict(existing_failure=1,new_failure=1,changed_failure=1,unknown_baseline=1))
        self.assertEqual(result['resolved_failures'],1)
        self.assertFalse(result['ci_evidence_ready'])
        with sqlite3.connect(output/'evidence.sqlite') as db:
            db.row_factory=sqlite3.Row
            failures=[dict(r) for r in db.execute(ci.COMPARISON)]
        self.assertEqual(len(failures),4)
        self.assertTrue(all(r['environment']=='test' and r['report_sha256'] for r in failures))
        self.report('baseline',[self.row(str(i)) for i in range(1200)])
        self.report('candidate',[self.row(str(i),'failed') for i in range(1200)])
        result, output=self.run_plan()
        self.assertEqual(result['counts']['failed'],1200)
        self.assertEqual(result['top_clusters'][0]['affected_tests'],1200)
        self.assertIn('unconfirmed',result['top_clusters'][0]['interpretation'])

    def test_retry_success_keeps_failure_and_blocks_undispositioned_instability(self):
        names=['test-0000000','test-0000001','test-0000002']
        self.report('candidate',[self.row(n,'failed') for n in names])
        self.report('candidate',[self.row(n) for n in names],attempt=2)
        result, output=self.run_plan()
        self.assertEqual(result['counts'],{'passed':3})
        self.assertEqual(result['failed_then_passed'],3)
        self.assertFalse(result['ci_evidence_ready'])
        with sqlite3.connect(output/'evidence.sqlite') as db:
            self.assertEqual(db.execute("SELECT count(*) FROM results WHERE status='failed'").fetchone()[0],3)
        self.plan['runs'][-1]['attempt']=3
        result,_=self.run_plan()
        self.assertTrue(any('attempt history' in b['reason'] for b in result['blockers']))

    def test_missing_slots_reports_and_complete_inventory_fail_closed(self):
        for mutate in [lambda p:p['runs'].pop(),
                       lambda p:p.update(inventory_complete=False),
                       lambda p:p['runs'][1].update(path='missing.jsonl'),
                       lambda p:p['runs'][1].update(status='pending'),
                       lambda p:p['runs'][1].update(status='cancelled'),
                       lambda p:p['runs'][1].update(status='failure')]:
            plan=copy.deepcopy(self.plan);mutate(plan)
            result,_=self.run_plan(plan)
            self.assertFalse(result['ci_evidence_ready'])

    def test_no_partial_import_on_malformed_duplicate_or_mismatched_report(self):
        candidate=self.plan['runs'][1]
        for content in ['{"test_id":"x","status":"passed"}\nnot-json\n',
                        '{"test_id":"x","status":"failed","status":"passed"}\n',
                        '{"test_id":"x","status":"passed"}\n'*3,
                        '{"test_id":"x","status":"passed","padding":"'+'x'*65536+'"}\n']:
            path=self.root/'invalid.jsonl';path.write_text(content)
            candidate.update(path=path.name,sha256=ci.file_hash(path))
            result,output=self.run_plan()
            self.assertFalse(result['ci_evidence_ready'])
            with sqlite3.connect(output/'evidence.sqlite') as db:
                self.assertEqual(db.execute("SELECT count(*) FROM results WHERE cohort='candidate'").fetchone()[0],0)
        for key,value in [('sha256','0'*64),('revision','d'*40),('artifact_sha256','e'*64),('config_sha256','f'*64)]:
            plan=json.loads((self.root/'plan.json').read_text());plan['runs'][1][key]=value
            result,_=self.run_plan(plan);self.assertFalse(result['ci_evidence_ready'])

    def test_removed_zero_and_skipped_tests_do_not_turn_green(self):
        self.plan['slots'][0]['min_tests']=1
        for rows in [[],[self.row('x','skipped')],[self.row('test-0000000')]]:
            self.report('candidate',rows)
            result,_=self.run_plan();self.assertFalse(result['ci_evidence_ready'])

    def test_identity_dimensions_and_values_are_not_silently_collapsed(self):
        self.report('candidate',[self.row('x','failed','expected 1 actual 2'),self.row('y','failed','expected 2 actual 1'),self.row('z')])
        result,_=self.run_plan()
        self.assertEqual(len(result['top_clusters']),2)
        plan=copy.deepcopy(self.plan);plan['slots'].append(copy.deepcopy(plan['slots'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate slot'):
            self.run_plan(plan)
        plan=copy.deepcopy(self.plan);plan['runs'].append(copy.deepcopy(plan['runs'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate run'):
            self.run_plan(plan)

    def test_report_path_cannot_escape_fixture(self):
        outside=self.root.parent/'outside.jsonl';outside.write_text('{}\n')
        (self.root/'escape.jsonl').symlink_to(outside)
        for path in ['../outside.jsonl','escape.jsonl',str(outside)]:
            plan=copy.deepcopy(self.plan);plan['runs'][1]['path']=path
            result,_=self.run_plan(plan);self.assertFalse(result['ci_evidence_ready'])

    def test_thousand_slot_matrix_preserves_instance_identity_and_detects_missing_shard(self):
        slot=self.plan['slots'][0];runs=copy.deepcopy(self.plan['runs'])
        self.plan['slots']=[];self.plan['runs']=[]
        for i in range(1000):
            current=dict(slot,id=f'slot-{i}',instance=f'instance-{i}')
            self.plan['slots'].append(current)
            for run in runs:
                self.plan['runs'].append(dict(run,slot=current['id'],run_id=f"{run['cohort']}-{i}"))
        result,_=self.run_plan()
        self.assertTrue(result['ci_evidence_ready'])
        self.assertEqual(result['selected_current_candidate'],3000)
        self.plan['runs'].pop()
        result,_=self.run_plan()
        self.assertFalse(result['ci_evidence_ready'])
        self.assertTrue(any('Missing matrix slot' in b['reason'] for b in result['blockers']))

    def test_real_multisuite_pipeline_reproduces_corrects_and_verifies_release(self):
        target=self.root/'pipeline';created=lab.create(target,5)
        self.assertEqual(created['actual_test_executions'],270)
        broken=ci.analyze(target/'broken-plan.json',target/'broken-analysis')
        self.assertEqual(broken['counts'],dict(error=30,failed=24,passed=36))
        self.assertEqual(broken['failure_comparison'],dict(existing_failure=12,new_failure=36,changed_failure=6))
        self.assertFalse(broken['ci_evidence_ready'])
        fixed=ci.analyze(target/'fixed-plan.json',target/'fixed-analysis',release=(target/'fixed-policy.json',target/'fixed-stages.json',target/'fixed-artifact.bin'))
        self.assertTrue(fixed['ci_evidence_ready'])
        self.assertTrue(fixed['release_evidence_ready'])
        self.assertEqual(fixed['counts'],{'passed':90})
        self.assertEqual(fixed['resolved_failures'],18)
        for name,digest in created['preserved'].items():
            self.assertEqual(ci.file_hash(target/'project'/name),digest)
        self.assertIn(' M notes.md',subprocess.check_output(['git','status','--porcelain'],cwd=target/'project',text=True))

    def test_release_rejects_stale_wrong_missing_or_forged_context(self):
        target=self.root/'release';lab.create(target,5)
        plan=ci.load(target/'fixed-plan.json');policy=ci.load(target/'fixed-policy.json')
        evidence=ci.load(target/'fixed-stages.json');now=datetime.now(timezone.utc)
        def gate(p=policy,e=evidence,a=target/'fixed-artifact.bin'):
            return ci.release_checks(plan,ci.file_hash(target/'fixed-plan.json'),p,e,a,now)
        self.assertEqual(gate(),[])
        mutations=[lambda e:e.pop(),lambda e:e.append(copy.deepcopy(e[0])),
                   lambda e:e[0].update(revision='0'*40),lambda e:e[0].update(artifact_sha256='0'*64),
                   lambda e:e[0].update(run_id='old-green-run'),lambda e:e[0].update(config_sha256='0'*64),
                   lambda e:e[0].update(analysis_plan_sha256='0'*64),lambda e:e[0].update(conclusion='cancelled'),
                   lambda e:e[0].update(completed_at=(now-timedelta(days=2)).isoformat()),
                   lambda e:e[0].update(completed_at=(now+timedelta(days=2)).isoformat())]
        for mutate in mutations:
            changed=copy.deepcopy(evidence);mutate(changed);self.assertTrue(gate(e=changed))
        wrong=target/'different.bin';wrong.write_bytes(b'unverified build')
        self.assertTrue(gate(a=wrong))
        changed=copy.deepcopy(policy);changed['required_stages'][0]['environment']='imaginary'
        with self.assertRaisesRegex(ValueError,'not covered'):
            gate(p=changed)

    def test_junit_adapter_preserves_identity_and_rejects_unsafe_or_ambiguous_input(self):
        source=self.root/'junit.xml'
        source.write_text('<testsuites><testsuite name="one"><testcase classname="C" name="same"/><testcase name="f"><failure type="A" message="bad 42"/></testcase></testsuite><testsuite name="two"><testcase classname="C" name="same"/></testsuite></testsuites>')
        output=self.root/'normalized.jsonl';receipt=junit.convert(source,output)
        rows=[json.loads(line) for line in output.read_text().splitlines()]
        self.assertEqual(len({r['test_id'] for r in rows}),3)
        self.assertEqual(receipt['counts'],{'passed':2,'failed':1})
        self.assertEqual(receipt['normalized_sha256'],ci.file_hash(output))
        with self.assertRaisesRegex(ValueError,'must not exist'):
            junit.convert(source,output)
        for index,xml in enumerate(['<!DOCTYPE x [<!ENTITY a "boom">]><testsuite/>','<testsuite/>','<testsuite><testcase name="x"><failure/><error/></testcase></testsuite>','<testsuite><testcase name="x"/>',
                                    '<testsuite><testcase name="x"><flakyFailure/></testcase></testsuite>',
                                    '<testsuite><testcase name="x" status="notrun"/></testsuite>',
                                    '<testsuite tests="1" errors="1"><testcase name="x"/></testsuite>',
                                    '<testsuite><error/><testcase name="x"/></testsuite>']):
            source.write_text(xml);destination=self.root/f'bad-{index}.jsonl'
            with self.assertRaises((ValueError,junit.ET.ParseError)):
                junit.convert(source,destination)
            self.assertFalse(destination.exists())

    def test_packaged_skills_only_lab_and_analyzer_have_no_root_dependency(self):
        package=self.root/'package';sync.copy_changes(ROOT,package,sync.manifest(ROOT))
        self.assertFalse((package/'docs').exists())
        packaged_lab=module('packaged_pipeline',package/'skills/orbyn-skill-creator/scripts/pipeline_lab.py')
        packaged_ci=module('packaged_ci',package/'skills/orbyn-ci-design/scripts/ci_evidence.py')
        packaged_lab.stress(self.root/'portable',10)
        result=packaged_ci.analyze(self.root/'portable/plan.json',self.root/'portable/analysis')
        self.assertTrue(result['ci_evidence_ready'])


if __name__=='__main__':
    unittest.main()
