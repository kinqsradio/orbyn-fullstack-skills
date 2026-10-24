"""Continuation records reject stale candidates and unsupported completion claims."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_tools import ROOT, module

checker = module('handoff_checker', ROOT/'skills/orbyn-workflow/scripts/check_handoff.py')
EXAMPLE = ROOT/'skills/orbyn-workflow/examples/public-only-handoff.json'


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(EXAMPLE.read_text())

    def test_unfinished_and_blocked_records_keep_continuation_and_exclusions(self):
        checker.validate(self.record, self.record['checkout']['revision'])
        self.record.update(status='blocked', decisions=['Need target ownership decision'])
        checker.validate(self.record)
        self.assertIn('Consumer pin updates', self.record['excluded'])

    def test_stale_revision_and_dirty_snapshot_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'Stale handoff'):
            checker.validate(self.record, 'f'*40)
        self.record['checkout']['diff_sha256'] = 'a'*64
        checker.validate(self.record, diff_sha256='a'*64)
        with self.assertRaisesRegex(ValueError, 'dirty diff changed'):
            checker.validate(self.record, diff_sha256='b'*64)

    def test_complete_requires_finished_work_and_passed_required_checks(self):
        self.record.update(status='complete', next_action=None)
        with self.assertRaisesRegex(ValueError, 'passed required checks'):
            checker.validate(self.record)
        check = self.record['verification'][0]
        check.update(state='passed', evidence=['checks.log: exit 0'])
        checker.validate(self.record)  # Local delivery can complete a local-only task.
        for field, value in [('decisions', ['Unresolved scope']), ('next_action', 'Still working'), ('completed', [])]:
            record = copy.deepcopy(self.record)
            record[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                checker.validate(record)

    def test_evidence_and_delivery_cannot_be_silently_omitted(self):
        for change in ['passed', 'failed', 'merged', 'completed']:
            record = copy.deepcopy(self.record)
            if change in ['passed', 'failed']:
                record['verification'][0]['state'] = change
            elif change == 'merged':
                record['delivery']['state'] = change
            else:
                record['completed'][0]['evidence'] = []
            with self.subTest(change=change), self.assertRaises(ValueError):
                checker.validate(record)

    def test_bad_types_unknown_fields_and_missing_next_action_are_refused(self):
        for field, value in [('schema_version', True), ('extra', 'Unknown'),
                             ('allowed_actions', 'merge'), ('verification', None),
                             ('status', 'accepted'), ('next_action', None)]:
            record = copy.deepcopy(self.record)
            record[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                checker.validate(record)

    def test_cli_works_offline_and_refuses_stale_or_oversized_input(self):
        cli = [sys.executable, str(ROOT/'skills/orbyn-workflow/scripts/check_handoff.py')]
        self.assertEqual(subprocess.run(cli+[str(EXAMPLE)], capture_output=True).returncode, 0)
        stale = subprocess.run(cli+[str(EXAMPLE), '--revision', 'f'*40], capture_output=True, text=True)
        self.assertEqual(stale.returncode, 1)
        self.assertIn('Stale handoff', stale.stderr)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'huge.json'
            path.write_text(' '*65537)
            result = subprocess.run(cli+[str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('64 KiB', result.stderr)
