"""Execute the original provider-free fixture; no SDK/service or model calls."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StreamingInteractionTests(unittest.TestCase):
    def test_sample_reducer_queue_and_effect_fault_controls(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Existing Node required; no dependency installation')
        sample = ROOT / 'skills/orbyn-ai-application/examples/project-plan-stream'
        result = subprocess.run([node, '--test', str(sample / 'interaction.test.mjs')],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for module in ['interaction.mjs', 'fixtures.mjs', 'preview.mjs']:
            syntax = subprocess.run([node, '--check', str(sample / module)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(syntax.returncode, 0, syntax.stderr)


if __name__ == '__main__':
    unittest.main()
