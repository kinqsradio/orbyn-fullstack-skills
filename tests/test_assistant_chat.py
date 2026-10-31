"""Exercise the original chat teaching model, without SDK/provider installation."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AssistantChatTests(unittest.TestCase):
    def test_composer_scope_attachment_and_projection_controls(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Existing Node required; no dependency installation')
        sample = ROOT / 'skills/orbyn-ui-design/examples/assistant-chat'
        result = subprocess.run([node, '--test', str(sample / 'chat.test.mjs')],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for module in ['chat.mjs', 'palettes.mjs', 'preview.mjs']:
            syntax = subprocess.run([node, '--check', str(sample / module)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(syntax.returncode, 0, syntax.stderr)


if __name__ == '__main__':
    unittest.main()
