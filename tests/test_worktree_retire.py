"""Worktree retirement keeps ignored files and refuses unproven trees, using synthetic repositories."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, module

tool = module('worktree_retire', ROOT/'skills/orbyn-worktree/scripts/worktree_retire.py')


class WorktreeRetireTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base/'repo'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        (self.repo/'.gitignore').write_text('output/\n')
        (self.repo/'a.txt').write_text('a\n')
        self.git('add', '.')
        self.commit('base')
        self.archive = self.base/'archive'
        patcher = mock.patch.object(tool, 'open_paths', return_value=set())
        patcher.start()
        self.addCleanup(patcher.stop)

    def git(self, *args, cwd=None):
        return subprocess.run(['git', '-C', str(cwd or self.repo), *args], check=True,
                              capture_output=True, text=True).stdout

    def commit(self, message, cwd=None):
        self.git('-c', 'user.name=Test', '-c', 'user.email=t@example.test', 'commit', '-qm', message, cwd=cwd)

    def tree(self, name='task'):
        path = self.base/'wt'/name
        self.git('worktree', 'add', '-q', '-b', f'feat/{name}', str(path), 'main')
        return path

    def state(self, path):
        real = str(path.resolve())
        return next(i for i in tool.inventory(self.repo, 'main') if i['path'] == real)

    def retire(self, path, **options):
        return tool.retire(self.repo, path, 'main', self.archive, **options)

    def test_inventory_marks_landed_ready_and_keeps_primary(self):
        path = self.tree()
        report = tool.inventory(self.repo, 'main')
        self.assertEqual(report[0]['disposition'], 'keep')
        self.assertEqual(self.state(path)['disposition'], 'ready')

    def test_dirty_unlanded_and_held_trees_stay(self):
        dirty = self.tree('dirty')
        (dirty/'new.txt').write_text('work\n')
        self.assertIn('uncommitted', self.state(dirty)['reason'])
        ahead = self.tree('ahead')
        (ahead/'b.txt').write_text('b\n')
        self.git('add', '.', cwd=ahead)
        self.commit('local only', cwd=ahead)
        self.assertIn('landing not proven', self.state(ahead)['reason'])
        with self.assertRaisesRegex(tool.Refused, 'landing not proven'):
            self.retire(ahead)
        self.assertTrue(ahead.is_dir())
        held = self.tree('held')
        tool.open_paths.return_value = {str(held.resolve()/'a.txt')}
        self.assertIn('open', self.state(held)['reason'])
        tool.open_paths.return_value = None
        self.assertIn('cannot check', self.state(held)['reason'])

    def test_squash_requires_the_exact_merged_head(self):
        path = self.tree()
        (path/'b.txt').write_text('b\n')
        self.git('add', '.', cwd=path)
        self.commit('task', cwd=path)
        head = self.git('rev-parse', 'HEAD', cwd=path).strip()
        merged = mock.Mock(returncode=0, stdout=json.dumps([{'number': 7, 'headRefOid': head}]))
        answer = lambda *args, cwd=None: mock.Mock(returncode=1) if args[0] == 'git' else merged
        with mock.patch.object(tool.shutil, 'which', return_value='/bin/tool'), \
                mock.patch.object(tool, 'run', side_effect=answer):
            self.assertEqual(tool.landed(path, head, 'feat/task', 'main'), 'merged PR #7')
            self.assertIsNone(tool.landed(path, 'f' * 40, 'feat/task', 'main'))

    def test_retire_moves_ignored_evidence_before_removal(self):
        path = self.tree()
        (path/'output/run').mkdir(parents=True)
        (path/'output/run/receipt.json').write_text('{}')
        result = self.retire(path)
        self.assertFalse(path.exists())
        kept = self.archive/'task'
        self.assertEqual((kept/'output/run/receipt.json').read_text(), '{}')
        self.assertEqual(json.loads((kept/'RETIRED.json').read_text())['archived'], ['output'])
        self.assertEqual(result['archived'], ['output'])
        self.assertIn('feat/task', self.git('branch', '--list', 'feat/task'))

    def test_drop_trashes_only_named_ignored_paths(self):
        path = self.tree()
        (path/'output/cache').mkdir(parents=True)
        (path/'output/cache/blob').write_text('x')
        (path/'output/receipt.json').write_text('{}')
        def fake(*args, cwd=None):
            if args[0] == 'trash':
                (path/'output/cache/blob').unlink()
                (path/'output/cache').rmdir()
                return mock.Mock(returncode=0)
            return subprocess.run(args, cwd=cwd, capture_output=True, text=True)
        with mock.patch.object(tool, 'run', side_effect=fake), \
                mock.patch.object(tool.shutil, 'which', side_effect=lambda name: name == 'trash' and '/bin/trash'):
            self.retire(path, drop=['output/cache'])
        self.assertTrue((self.archive/'task/output/receipt.json').is_file())
        self.assertFalse((self.archive/'task/output/cache').exists())

    def test_drop_cannot_reach_tracked_or_outside_files(self):
        path = self.tree()
        (path/'output').mkdir()
        (path/'output/receipt.json').write_text('{}')
        for drop in ('a.txt', '../../repo/a.txt'):
            with self.assertRaisesRegex(tool.Refused, 'ignored path'):
                self.retire(path, drop=[drop])
        self.assertTrue((path/'output/receipt.json').is_file())
        self.assertFalse(self.archive.exists())

    def test_primary_foreign_collision_and_inner_archive_are_refused(self):
        with self.assertRaisesRegex(tool.Refused, 'primary'):
            self.retire(self.repo)
        with self.assertRaisesRegex(tool.Refused, 'Not a registered'):
            self.retire(self.base)
        path = self.tree()
        with self.assertRaisesRegex(tool.Refused, 'outside'):
            tool.retire(self.repo, path, 'main', path)
        (self.archive/'task').mkdir(parents=True)
        with self.assertRaisesRegex(tool.Refused, 'already exists'):
            self.retire(path)
        self.assertTrue(path.is_dir())

    def test_cli_inventory_changes_nothing(self):
        self.tree()
        before = self.git('worktree', 'list')
        with mock.patch('builtins.print') as printed:
            self.assertEqual(tool.main(['--repo', str(self.repo), '--base', 'main', 'inventory']), 0)
        self.assertEqual(len(json.loads(printed.call_args.args[0])), 2)
        self.assertEqual(self.git('worktree', 'list'), before)
        self.assertEqual(tool.main(['--repo', os.devnull, 'inventory']), 1)


if __name__ == '__main__':
    unittest.main()
