"""Adapter contracts plus explicitly opted-in Java/TLC semantic integration checks."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / 'skills/architect/scripts/check-statechart.py'
SAMPLE = ROOT / 'skills/architect/examples/leased-job'
spec = importlib.util.spec_from_file_location('statechart_adapter', ADAPTER)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
ENV = {name: os.environ.get('ORBYN_STATECHART_' + name.upper()) for name in ['node', 'java', 'tlc']}
READY = all(ENV.values())


class AdapterContracts(unittest.TestCase):
    def test_full_runtime_snapshot_is_checked_before_execution(self):
        receipt = adapter.compiler_identity()
        self.assertEqual(sum(k.endswith('.ts') for k in receipt['files']), 26)
        with tempfile.TemporaryDirectory() as temp:
            source = adapter.COMPILER.parent.parent
            copied = Path(temp) / 'snapshot'
            shutil.copytree(source, copied)
            changed = copied / 'compiler/passes/label.ts'
            changed.write_text(changed.read_text() + '\n// drift\n')
            with patch.object(adapter, 'COMPILER', copied / 'compiler/statechart.ts'):
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    adapter.compiler_identity()

    def test_windows_is_blocked_without_launch(self):
        with patch.object(adapter.sys, 'platform', 'win32'), patch.object(adapter.subprocess, 'run') as launch:
            with self.assertRaisesRegex(ValueError, 'Windows is unsupported'):
                adapter.doctor(SimpleNamespace())
            launch.assert_not_called()

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'output'
            out.mkdir(); sentinel = out / 'keep'; sentinel.write_text('prior evidence')
            with self.assertRaisesRegex(ValueError, 'must be new'):
                adapter.run(SimpleNamespace(out=str(out), timeout=1))
            self.assertEqual(sentinel.read_text(), 'prior evidence')
            self.assertFalse(out.with_name(out.name + '.run').exists())

    def test_missing_prerequisite_retains_error_and_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'output'
            args = SimpleNamespace(out=str(out), timeout=1, node='/missing/node', java='/missing/java', tlc='/missing/jar')
            self.assertEqual(adapter.run(args), 2)
            record = out.with_name(out.name + '.run')
            receipt = json.loads((record / 'receipt.json').read_text())
            self.assertEqual(receipt['model'], 'not checked')
            self.assertTrue((record / 'stdout.txt').exists())
            self.assertTrue((record / 'stderr.txt').read_text())
            self.assertFalse(out.exists())

    def test_unknown_tlc_identity_is_refused_without_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            jar = Path(temp) / 'wrong.jar'; jar.write_bytes(b'not pinned TLC')
            args = SimpleNamespace(node=sys.executable, java=sys.executable, tlc=str(jar))
            with patch.object(adapter.subprocess, 'run') as launch:
                with self.assertRaisesRegex(ValueError, 'Unsupported TLC jar identity'):
                    adapter.doctor(args)
                launch.assert_not_called()

    def test_exception_after_spawn_still_settles_owned_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'output'
            tools = {name: {'path': sys.executable} for name in ['node', 'java', 'tlc']}
            child = Mock(pid=1234567, returncode=None)
            child.poll.side_effect = lambda: child.returncode
            def settle(*args, **kwargs):
                child.returncode = -15
                return -15
            child.wait.side_effect = settle
            args = SimpleNamespace(out=str(out), timeout=.001, spec=str(SAMPLE/'LeasedJob.tla'), config=str(SAMPLE/'fixed.cfg'), view=None)
            with patch.object(adapter, 'doctor', return_value=tools), patch.object(adapter.subprocess, 'Popen', return_value=child), patch.object(adapter, 'descendants', side_effect=OSError('ps denied')):
                self.assertEqual(adapter.run(args), 2)
            child.terminate.assert_called_once()
            self.assertEqual(child.returncode, -15)
            receipt = json.loads((out.with_name(out.name+'.run')/'receipt.json').read_text())
            self.assertIn('ps denied', receipt['error'])
            self.assertIn('not independently established', receipt['exception_cleanup'])


@unittest.skipUnless(READY, 'Opt-in: set ORBYN_STATECHART_NODE/JAVA/TLC to explicit trusted local tools; no bootstrap')
class CompilerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.tool_args = [item for name, value in ENV.items() for item in ['--'+name, value]]

    def check(self, name, body, config='SPECIFICATION Spec\nINVARIANT Safe\n', view=None, timeout=40, files=None):
        case = self.base / name; case.mkdir()
        for filename, contents in (files or {}).items():
            (case/filename).write_text(contents)
        model = case/'Fixture.tla'; model.write_text('---- MODULE Fixture ----\nEXTENDS Naturals, TLC\n'+body+'\n====\n')
        cfg = case/'Fixture.cfg'; cfg.write_text(config)
        args = [sys.executable, str(ADAPTER), 'check', str(model), '--config', str(cfg), '--out', str(case/'result'), '--timeout', str(timeout), *self.tool_args]
        if view is not None:
            path = case/'view.mjs'; path.write_text(view); args += ['--view', str(path)]
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout+25)
        receipt = json.loads((case/'result.run/receipt.json').read_text())
        report = (case/'result/report.md').read_text() if (case/'result/report.md').exists() else ''
        return result, receipt, report, case

    BODY = '''VARIABLE x
vars == <<x>>
Init == x = 0
Up == x < 2 /\\ x' = x + 1
Down == x > 0 /\\ x' = x - 1
Next == Up \\/ Down
Spec == Init /\\ [][Next]_vars /\\ WF_vars(Next)
Safe == x <= 2
NoTwo == x < 2
Goal == <> (x = 3)'''

    def test_pass_fail_and_plain_tlc_agree(self):
        for name, invariant, broken in [('safe', 'Safe', False), ('broken', 'NoTwo', True)]:
            result, receipt, report, case = self.check(name, self.BODY, 'SPECIFICATION Spec\nINVARIANT '+invariant+'\n')
            self.assertEqual(result.returncode, 1 if broken else 0, result.stderr)
            plain = subprocess.run([ENV['java'], '-cp', ENV['tlc'], 'tlc2.TLC', '-workers', '1', '-fp', '0', '-lncheck', 'final', '-metadir', str(case/'plain-meta'), '-config', str(case/'Fixture.cfg'), str(case/'Fixture.tla')], capture_output=True, text=True, timeout=30)
            self.assertEqual('Invariant NoTwo is violated' in plain.stdout, broken)
            self.assertEqual('Model checking completed. No error has been found.' in plain.stdout, not broken)
            self.assertIn('Rules that hold' if not broken else 'NoTwo breaks', report)
            self.assertEqual(receipt['source_correspondence'], 'not established by compiler')

    def test_terminal_stutter_is_distinct_from_deadlock(self):
        body = self.BODY.replace('Next == Up \\/ Down', 'Next == Up').replace('x < 2', 'x < 1')
        result, _, report, _ = self.check('deadlock', body)
        self.assertEqual(result.returncode, 1); self.assertIn('NoDeadlock breaks', report)
        result, _, report, _ = self.check('terminal', body.replace('Next == Up', 'End == x = 1 /\\ UNCHANGED vars\nNext == Up \\/ End'))
        self.assertEqual(result.returncode, 0, result.stderr); self.assertIn('NoDeadlock', report)

    def test_temporal_lasso_is_not_an_invariant_pass(self):
        result, _, report, _ = self.check('temporal', self.BODY, 'SPECIFICATION Spec\nINVARIANT Safe\nPROPERTY Goal\n')
        self.assertEqual(result.returncode, 1); self.assertIn('Goal breaks', report)
        self.assertRegex(report, 'forever|loops'); self.assertIn('Safe', report)

    def test_constraints_view_symmetry_and_disabled_deadlock_are_disclosed(self):
        body = self.BODY + '\nLimit == x < 2\nDisplay == x\n'
        result, _, report, _ = self.check('constraint', body, 'SPECIFICATION Spec\nINVARIANT NoTwo\nCONSTRAINT Limit\nVIEW Display\n')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('NoTwo breaks', report); self.assertIn('VIEW', report)
        result, _, report, _ = self.check('disabled', self.BODY, 'SPECIFICATION Spec\nINVARIANT Safe\nCHECK_DEADLOCK FALSE\n')
        self.assertEqual(result.returncode, 0, result.stderr); self.assertNotIn('NoDeadlock', report)
        symmetric = """CONSTANTS A, B
VARIABLE x
vars == <<x>>
Init == x \in {A, B}
Next == x' = IF x = A THEN B ELSE A
Spec == Init /\ [][Next]_vars
Safe == x \in {A, B}
Sym == Permutations({A, B})"""
        result, _, report, _ = self.check('symmetry', symmetric, 'CONSTANT A = a\nCONSTANT B = b\nSPECIFICATION Spec\nINVARIANT Safe\nSYMMETRY Sym\n')
        self.assertEqual(result.returncode, 0, result.stderr); self.assertIn('SYMMETRY', report)

    def test_qualified_temporal_actions_remain_in_trace(self):
        worker = """---- MODULE Worker ----
EXTENDS Naturals
VARIABLE item
Init == item = 0
Up == item = 0 /\ item' = 1
Back == item = 1 /\ item' = 0
====
"""
        body = """VARIABLE x
vars == <<x>>
C == INSTANCE Worker WITH item <- x
Init == C!Init
Next == C!Up \/ C!Back
Spec == Init /\ [][Next]_vars /\ WF_vars(Next)
Safe == x <= 1
Goal == <> (x = 2)"""
        result, _, report, case = self.check('qualified', body, 'SPECIFICATION Spec\nINVARIANT Safe\nPROPERTY Goal\n', files={'Worker.tla': worker})
        self.assertEqual(result.returncode, 1, result.stderr)
        trace = (case/'result/tlc-Goal.out').read_text()
        self.assertIn('C!Up', trace); self.assertIn('C!Back', trace)
        self.assertIn('Goal breaks', report)

    def test_hidden_path_parse_error_and_timeout_are_not_passes(self):
        result, _, _, _ = self.check('hidden', self.BODY, 'SPECIFICATION Spec\nINVARIANT NoTwo\n', 'export const state = v => String(v.x); export const step = () => null;')
        self.assertEqual(result.returncode, 2)
        result, receipt, _, _ = self.check('parse', 'this is not a valid specification')
        self.assertEqual(result.returncode, 2); self.assertEqual(receipt['status'], 'tool_error')
        result, receipt, _, case = self.check('timeout', self.BODY, view='await new Promise(() => setInterval(() => {}, 1000)); export const state = v => String(v.x);', timeout=.3)
        self.assertEqual(result.returncode, 2); self.assertEqual(receipt['status'], 'timeout')
        self.assertEqual(receipt['remaining_observed_processes'], [])
        self.assertFalse((case/'result').exists())

    def test_real_sigterm_retains_cancel_receipt(self):
        case = self.base/'cancel'; case.mkdir()
        model = case/'Fixture.tla'; model.write_text('---- MODULE Fixture ----\nEXTENDS Naturals\n'+self.BODY+'\n====\n')
        cfg = case/'Fixture.cfg'; cfg.write_text('SPECIFICATION Spec\nINVARIANT Safe\n')
        view = case/'view.mjs'; view.write_text("import fs from 'node:fs'; fs.writeFileSync(new URL('./entered', import.meta.url), 'ready'); await new Promise(() => setInterval(() => {}, 1000)); export const state = v => String(v.x);")
        command = [sys.executable, str(ADAPTER), 'check', str(model), '--view', str(view), '--out', str(case/'result'), *self.tool_args]
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            import time
            deadline = time.monotonic()+10
            while not (case/'entered').exists() and time.monotonic()<deadline and child.poll() is None:
                time.sleep(.05)
            self.assertTrue((case/'entered').exists())
            child.terminate(); child.communicate(timeout=15)
            self.assertEqual(child.returncode, 143)
            receipt = json.loads((case/'result.run/receipt.json').read_text())
            self.assertEqual(receipt['status'], 'cancelled'); self.assertEqual(receipt['remaining_observed_processes'], [])
        finally:
            if child.poll() is None:
                child.kill(); child.communicate(timeout=5)

    def test_cold_commonjs_ancestor_uses_local_esm_boundary(self):
        parent = self.base/'commonjs'; parent.mkdir()
        (parent/'package.json').write_text('{"type":"commonjs"}')
        copied = parent/'architect'
        shutil.copytree(ROOT/'skills/architect', copied, ignore=shutil.ignore_patterns('__pycache__'))
        model = copied/'examples/leased-job/LeasedJob.tla'
        result = subprocess.run([sys.executable, str(copied/'scripts/check-statechart.py'), 'check', str(model), '--config', str(copied/'examples/leased-job/fixed.cfg'), '--out', str(parent/'result'), *self.tool_args], capture_output=True, text=True, timeout=65)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('MODULE_TYPELESS_PACKAGE_JSON', (parent/'result.run/stderr.txt').read_text())

    def test_sample_guard_replay_and_fixed_bounded_pass(self):
        for variant in ['broken', 'fixed']:
            case = self.base/variant; case.mkdir()
            command = [sys.executable, str(ADAPTER), 'check', str(SAMPLE/'LeasedJob.tla'), '--config', str(SAMPLE/(variant+'.cfg')), '--view', str(SAMPLE/'view.mjs'), '--out', str(case/'result'), *self.tool_args]
            result = subprocess.run(command, capture_output=True, text=True, timeout=65)
            self.assertEqual(result.returncode, 1 if variant=='broken' else 0, result.stderr)
            report = (case/'result/report.md').read_text()
            if variant == 'broken':
                replay = subprocess.run([ENV['node'], str(SAMPLE/'replay.mjs'), str(case/'result/tlc.out')], capture_output=True, text=True, check=True)
                record = json.loads(replay.stdout)
                self.assertEqual(record['fixedRejectedStep'], 4)
                self.assertEqual(record['broken']['result']['generation'], 1)
                self.assertEqual(record['fixed']['published'][0]['generation'], 2)
            else:
                for rule in ['FreshResult', 'PublishedFresh', 'CancelledHasNoResult', 'EventuallyTerminal', 'NoDeadlock']:
                    self.assertIn(rule, report)
                self.assertNotIn('breaks', report)


if __name__ == '__main__':
    unittest.main()
