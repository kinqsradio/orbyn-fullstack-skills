"""Calibrate the disposable execution fixture; no model or hosted-service calls."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, module, sync

lab = module('contribution_lab', ROOT/'skills/orbyn-skill-creator/scripts/contribution_lab.py')

# Independent calibration implementation. Subjects never receive this test file.
GOOD = '''class EventBus:
    def __init__(self):
        self._topics = {}

    def subscribe(self, topic, key, callback):
        group = self._topics.setdefault(topic, {})
        registration = (object(), callback)
        group[key] = registration
        def dispose():
            if group.get(key) is registration:
                del group[key]
        return dispose

    def emit(self, topic, value):
        for _, callback in tuple(self._topics.get(topic, {}).values()):
            callback(value)
'''

ORACLE = '''from src.event_bus import EventBus
bus = EventBus()
old, new = [], []
dispose_old = bus.subscribe('news', 'owner', old.append)
dispose_new = bus.subscribe('news', 'owner', new.append)
bus.emit('news', 1)
assert old == [] and new == [1], 'replacement must deliver once to latest'
dispose_old()
bus.emit('news', 2)
assert new == [1, 2], 'old disposer must not remove replacement'
dispose_new(); dispose_new()
bus.emit('news', 3)
assert new == [1, 2], 'disposal must be idempotent'
seen = []
callback = seen.append
bus.subscribe('news', 'a', callback)
bus.subscribe('news', 'b', callback)
bus.subscribe('other', 'a', callback)
bus.emit('news', 4); bus.emit('other', 5)
assert seen == [4, 4, 5], 'identities remain independent'
bus = EventBus(); seen = []
def first(value):
    seen.append('first')
    dispose_second()
bus.subscribe('news', 'a', first)
dispose_second = bus.subscribe('news', 'b', lambda value: seen.append('second'))
bus.emit('news', 1)
assert seen == ['first', 'second'], 'emit owns its starting snapshot'
# Review-phase composition
bus = EventBus(); seen = []
def replacing_first(value):
    seen.append(('first', value))
    if value == 1:
        bus.subscribe('news', 'b', lambda v: seen.append(('new', v)))
        dispose_old_b()
bus.subscribe('news', 'a', replacing_first)
dispose_old_b = bus.subscribe('news', 'b', lambda v: seen.append(('old', v)))
bus.emit('news', 1); bus.emit('news', 2)
assert seen == [('first', 1), ('old', 1), ('first', 2), ('new', 2)], 'nested replacement must preserve snapshot and new ownership'
'''


class ContributionLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()/'trial'
        self.created = lab.create(self.root)
        self.checkout = Path(self.created['checkout'])

    def forge(self, *args, code=0):
        result = subprocess.run([sys.executable, 'tools/forge.py', *args],
                                cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout+result.stderr)
        return json.loads(result.stdout if code != 2 else result.stderr)

    def commit_push(self, text):
        (self.checkout/'src/event_bus.py').write_text(text)
        lab.git(self.checkout, 'add', 'src/event_bus.py')
        lab.git(self.checkout, 'commit', '-q', '-m', 'Owned fixture change')
        lab.git(self.checkout, 'push', '-q', 'origin', 'HEAD')

    def test_real_worktree_and_no_overwrite_preserve_local_sentinels(self):
        self.assertEqual(lab.git(self.checkout, 'branch', '--show-current'), 'fix/duplicate-delivery')
        self.assertEqual(lab.git(self.checkout, 'rev-parse', 'HEAD'), self.created['base'])
        self.assertTrue((self.checkout/'.git').is_file())
        self.assertTrue((self.checkout/'.agents/skills/widget-contracts/SKILL.md').is_file())
        for relative, digest in self.created['preserved_sha256'].items():
            self.assertEqual(hashlib.sha256((self.checkout/relative).read_bytes()).hexdigest(), digest)
        before = (self.checkout/'docs/notes.md').read_bytes()
        with self.assertRaisesRegex(ValueError, 'must not exist'):
            lab.create(self.root)
        self.assertEqual((self.checkout/'docs/notes.md').read_bytes(), before)
        self.assertIsNone(self.forge('status')['head'])

    def test_oracle_rejects_seed_and_accepts_actual_behavioral_correction(self):
        result = subprocess.run([sys.executable, '-c', ORACLE], cwd=self.checkout,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('replacement must deliver once', result.stderr)
        partial = GOOD.replace('if group.get(key) is registration:', 'if key in group:')
        (self.checkout/'src/event_bus.py').write_text(partial)
        result = subprocess.run([sys.executable, '-c', ORACLE], cwd=self.checkout,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('old disposer must not remove replacement', result.stderr)
        (self.checkout/'src/event_bus.py').write_text(GOOD)
        result = subprocess.run([sys.executable, '-c', ORACLE], cwd=self.checkout,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ci_is_bound_to_pushed_clean_source_and_exposes_zero_selection(self):
        result = subprocess.run([sys.executable, 'tools/check.py', '--filter', 'does-not-exist'],
                                cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['selected'], 0)
        self.commit_push(GOOD)
        self.forge('open')
        check = self.forge('ci')['check']
        self.assertEqual(check['conclusion'], 'success')
        self.assertGreater(check['report']['selected'], 0)
        self.assertTrue(self.forge('status')['required_current'])
        self.commit_push(GOOD+'\n# Another owned revision\n')
        self.assertFalse(self.forge('status')['required_current'])
        (self.checkout/'src/event_bus.py').write_text(GOOD+'\n# Dirty source\n')
        self.assertIn('Commit owned', self.forge('ci', code=2)['error'])

    def test_review_pages_and_local_responses_do_not_mutate_dirty_work(self):
        self.commit_push(GOOD)
        self.forge('open')
        self.forge('ci')
        lab.inject_reviews(self.root)
        first = self.forge('reviews', '--cursor', '0')
        self.assertTrue(first['hasNextPage'])
        second = self.forge('reviews', '--cursor', str(first['endCursor']))
        self.assertFalse(second['hasNextPage'])
        self.assertEqual({r['id'] for r in first['threads']+second['threads']}, {'R1', 'R2', 'R3'})
        self.forge('respond', '--thread', 'R2', '--disposition', 'declined',
                   '--evidence', 'Distinct keys are independent under the target contract.')
        status = self.forge('status')
        self.assertEqual(status['responses']['R2']['disposition'], 'declined')
        self.assertEqual(status['pr']['state'], 'OPEN')
        for relative, digest in self.created['preserved_sha256'].items():
            self.assertEqual(hashlib.sha256((self.checkout/relative).read_bytes()).hexdigest(), digest)
        with self.assertRaisesRegex(ValueError, 'single-use'):
            lab.inject_reviews(self.root)

    def test_managed_distribution_can_create_lab_without_library_root_docs(self):
        package = self.root.parent/'package'
        sync.copy_changes(ROOT, package, sync.manifest(ROOT))
        self.assertFalse((package/'docs').exists())
        self.assertFalse((package/'tools').exists())
        packaged = module('packaged_contribution_lab',
                          package/'skills/orbyn-skill-creator/scripts/contribution_lab.py')
        created = packaged.create(self.root.parent/'packaged-trial')
        target = Path(created['checkout'])
        self.assertTrue((target/'tools/forge.py').is_file())
        self.assertTrue((target/'.claude/skills/widget-contracts/SKILL.md').is_file())

    def test_incomplete_or_symlinked_assets_fail_before_destination_writes(self):
        assets = self.root.parent/'assets'
        shutil.copytree(lab.ASSETS, assets)
        missing = assets/'src/event_bus.py'
        content = missing.read_bytes()
        missing.unlink()
        target = self.root.parent/'refused-trial'
        with mock.patch.object(lab, 'ASSETS', assets):
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                lab.create(target)
            self.assertFalse(target.exists())
            outside = self.root.parent/'outside.py'
            outside.write_bytes(content)
            missing.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'symlinks'):
                lab.create(target)
            self.assertFalse(target.exists())

    def test_primary_layout_and_transient_commit_failure_use_real_git(self):
        created = lab.create(self.root.parent/'primary-trial', layout='primary',
                             transient_commit_failure=True)
        checkout = Path(created['checkout'])
        self.assertTrue((checkout/'.git').is_dir())
        self.assertEqual(lab.git(checkout, 'branch', '--show-current'), 'fix/duplicate-delivery')
        (checkout/'src/event_bus.py').write_text(GOOD)
        lab.git(checkout, 'add', 'src/event_bus.py')
        first = subprocess.run(['git', '-C', str(checkout), 'commit', '-m', 'Owned fix'],
                               capture_output=True, text=True)
        self.assertNotEqual(first.returncode, 0)
        self.assertIn('no commit was written', first.stderr)
        self.assertEqual(lab.git(checkout, 'rev-parse', 'HEAD'), created['base'])
        self.assertEqual(lab.git(checkout, 'ls-remote', 'origin', 'refs/heads/fix/duplicate-delivery'), '')
        lab.git(checkout, 'commit', '-q', '-m', 'Owned fix')
        lab.git(checkout, 'push', '-q', 'origin', 'HEAD')
        head = lab.git(checkout, 'rev-parse', 'HEAD')
        self.assertTrue(lab.git(checkout, 'ls-remote', 'origin', 'refs/heads/fix/duplicate-delivery').startswith(head))
        self.assertNotEqual(head, created['base'])


if __name__ == '__main__':
    unittest.main()
