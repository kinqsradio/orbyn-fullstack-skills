"""Host pointer generation and drift detection: they guard what every agent host loads."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_tools import ROOT, module

hosts = module('host_instructions', ROOT/'scripts/host_instructions.py')


class HostInstructionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_real_repository_matches_generated_text(self):
        self.assertEqual(hosts.problems(ROOT), [])

    def test_write_then_check_is_clean_and_pointers_defer(self):
        hosts.write(self.root)
        self.assertEqual(hosts.problems(self.root), [])
        self.assertTrue((self.root/'CLAUDE.md').read_text().startswith('@AGENTS.md\n'))
        self.assertIn('@./AGENTS.md', (self.root/'GEMINI.md').read_text())
        self.assertEqual((self.root/'.aider.conf.yml').read_text(), 'read: AGENTS.md\n')
        copilot = (self.root/'.github/copilot-instructions.md').read_text()
        self.assertLess(len(copilot.splitlines()), 15)
        self.assertIn('AGENTS.md', copilot)

    def test_missing_edited_and_shadowing_files_are_reported(self):
        hosts.write(self.root)
        (self.root/'GEMINI.md').write_text('hand edit\n')
        (self.root/'.aider.conf.yml').unlink()
        (self.root/'.rules').write_text('shadow\n')
        errors = hosts.problems(self.root)
        self.assertTrue(any('differs' in e and 'GEMINI.md' in e for e in errors), errors)
        self.assertTrue(any('Missing' in e and '.aider.conf.yml' in e for e in errors), errors)
        self.assertTrue(any('Forbidden' in e and '.rules' in e for e in errors), errors)

    def test_skill_links_cover_every_host_directory(self):
        for host in ('.agents', '.claude', '.kiro', '.junie'):
            self.assertTrue((ROOT/host/'skills'/'orbyn-workflow').is_symlink(), host)

    def test_cli_check_passes_on_repository(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/sync-host-instructions.py'), '--check'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
