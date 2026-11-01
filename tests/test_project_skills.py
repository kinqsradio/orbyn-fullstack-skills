"""Offline source integrity and ignored research boundaries."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, module




class ProjectContextTests(unittest.TestCase):
    def test_context_symlink_loop_is_an_ordinary_refusal(self):
        context = module('project_context', ROOT/'skills/orbyn-setup/scripts/project_context.py')
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory).resolve()
            (project/'.agents').mkdir()
            (project/'loop.md').symlink_to('loop.md')
            (project/context.CONTEXT).write_text(json.dumps({'schema_version': 1, 'project_name': 'Fixture',
                                                             'documents': {'guide': 'loop.md'}, 'owners': {}}))
            with self.assertRaises((ValueError, OSError)):
                context.check(project)


class OfflineSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.checker = module('offline_sources', ROOT/'skills/orbyn-skill-creator/scripts/check_sources.py')
        source = ROOT/'skills/social-content/references/upstream/marketingskills-social'
        self.base = self.root/'skills/social-content/references/upstream/marketingskills-social'
        shutil.copytree(source, self.base)


    def test_research_must_be_ignored_and_never_staged(self):
        subprocess.run(['git', '-C', str(self.root), 'init', '-q'], check=True)
        for name in ['openSrc', 'orbyn-references']:
            with self.subTest(root=name):
                source = self.root/name/'vendor/source.py'
                source.parent.mkdir(parents=True)
                source.write_text('Unexecuted research source')
                ignore = self.root/'.gitignore'
                ignore.write_text('')
                with self.assertRaisesRegex(ValueError, 'Exclude'):
                    self.checker.check(self.root)
                ignore.write_text('/openSrc/\n/orbyn-references/\n')
                self.checker.check(self.root)
                subprocess.run(['git', '-C', str(self.root), 'add', '-f', '--', str(source)], check=True)
                with self.assertRaisesRegex(ValueError, 'tracked or staged'):
                    self.checker.check(self.root)
                self.assertEqual(source.read_text(), 'Unexecuted research source')
                subprocess.run(['git', '-C', str(self.root), 'rm', '--cached', '-q', '--', str(source)], check=True)

    def test_reference_root_cannot_follow_a_symlink(self):
        subprocess.run(['git', '-C', str(self.root), 'init', '-q'], check=True)
        (self.root/'.gitignore').write_text('/orbyn-references/\n')
        (self.root/'orbyn-references').symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'real directory'):
            self.checker.check(self.root)

    def test_ignore_exception_cannot_expose_a_reference_file(self):
        subprocess.run(['git', '-C', str(self.root), 'init', '-q'], check=True)
        source = self.root/'orbyn-references/source.py'
        source.parent.mkdir()
        source.write_text('Unexecuted research source')
        (self.root/'.gitignore').write_text('/orbyn-references/*\n!/orbyn-references/source.py\n')
        with self.assertRaisesRegex(ValueError, 'Unignored files'):
            self.checker.check(self.root)

    def test_tampered_source_missing_license_and_extra_file_are_rejected(self):
        source = self.base/'SOURCE.md'
        before = source.read_bytes()
        source.write_bytes(before+b'changed')
        with self.assertRaisesRegex(ValueError, 'Changed/missing'):
            self.checker.check(self.root)
        source.write_bytes(before)
        license_file = self.base/'LICENSE'
        original = license_file.read_bytes()
        license_file.unlink()
        with self.assertRaisesRegex(ValueError, 'Changed/missing'):
            self.checker.check(self.root)
        license_file.write_bytes(original)
        (self.base/'extra.md').write_text('Undeclared material')
        with self.assertRaisesRegex(ValueError, 'Undeclared'):
            self.checker.check(self.root)

    def test_snapshot_manifest_cannot_escape_or_omit_license(self):
        path = self.base/'snapshot.json'
        original = json.loads(path.read_text())
        data = dict(original)
        data['files'] = dict(original['files'], **{'../../outside.md': {'sha256':'0'*64}})
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.checker.check(self.root)
        data = dict(original)
        data['license_files'] = []
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'license'):
            self.checker.check(self.root)
