"""REA guidance survives the managed skills-only distribution without network."""
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, installer, module, sync

contracts = module('rea_offline_links', ROOT/'scripts/skill_contracts.py')
REA_SKILLS = ('reverse-engineer-anything', 'rea-analysis-optimization',
              'rea-tool-design', 'rea-ci-tests-audit', 'rea-changelog-update')


class ReaOfflineDistributionTests(unittest.TestCase):
    def test_managed_copy_installs_with_local_support_and_preserves_consumer(self):
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory).resolve()
            policy = consumer/'AGENTS.md'
            policy.write_text('Consumer policy remains authoritative.\n')
            settings = consumer/'.claude/settings.json'
            settings.parent.mkdir()
            settings.write_text('{"existing": true}\n')
            foreign = consumer/'.claude/skills/company-method/SKILL.md'
            foreign.parent.mkdir(parents=True)
            foreign.write_text('Existing consumer-owned guidance.\n')
            preserved = {p: p.read_bytes() for p in (policy, settings, foreign)}

            with mock.patch.object(socket, 'socket', side_effect=AssertionError('Network forbidden')):
                # Use the real managed-file copy boundary, not a full library clone.
                files = sync.manifest(ROOT)
                sync.copy_changes(ROOT, consumer, files)
                for excluded in ('docs', 'tools', 'provenance.json', '.codex'):
                    self.assertFalse((consumer/excluded).exists(), excluded)
                with mock.patch.object(installer, 'ROOT', consumer), mock.patch.object(
                        installer, 'PRESETS', consumer/'skills/orbyn-setup/assets/presets.json'):
                    self.assertEqual(installer.install(consumer, 'all', REA_SKILLS, dry_run=True), 15)
                    self.assertFalse((consumer/'.agents').exists())
                    self.assertEqual(installer.install(consumer, 'all', REA_SKILLS), 15)
                    self.assertEqual(installer.install(consumer, 'all', REA_SKILLS), 0)

                for host in ('.agents', '.claude', '.cursor'):
                    for name in REA_SKILLS:
                        installed = consumer/host/'skills'/name
                        self.assertEqual(installed.resolve(), consumer/'skills'/name)
                        self.assertEqual((installed/'LICENSE').read_bytes(),
                                         (ROOT/'skills'/name/'LICENSE').read_bytes())
                        for document in installed.resolve().rglob('*.md'):
                            with self.subTest(host=host, document=document.relative_to(consumer)):
                                self.assertEqual(contracts.check_links(consumer, document), [])
                self.assertEqual(sync.inventory(consumer), files)
                catalog = json.loads((consumer/'skills/catalog.json').read_text())
                self.assertTrue(set(REA_SKILLS).issubset({s['name'] for s in catalog['skills']}))

            for path, contents in preserved.items():
                self.assertEqual(path.read_bytes(), contents)
            self.assertFalse((consumer/'tools/rea').exists())


if __name__ == '__main__':
    unittest.main()
