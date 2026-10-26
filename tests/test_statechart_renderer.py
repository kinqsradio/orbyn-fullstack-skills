"""Check renderer handoff boundaries without installing a diagram dependency."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/architect/scripts/render-statechart.mjs'


@unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
class StatechartRendererTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'flow.mmd'
        self.source.write_text('stateDiagram-v2\n  Idle --> Busy: start\n')
        self.output = self.root / 'flow.svg'
        self.renderer = self.root / 'renderer.mjs'

    def run_adapter(self, renderer=None):
        return subprocess.run(['node', str(SCRIPT), '--input', str(self.source),
                               '--output', str(self.output), '--pele',
                               str(renderer or self.renderer)], capture_output=True, text=True)

    def test_missing_dependency_leaves_no_output(self):
        result = self.run_adapter()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_success_writes_renderer_output_and_unverified_receipt(self):
        self.renderer.write_text(
            'export const render = source => ({svg: "<svg><text>" + '
            'source.length + "</text></svg>"});\n')
        result = self.run_adapter()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(),
                         f'<svg><text>{len(self.source.read_text())}</text></svg>')
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['input'], str(self.source))
        self.assertEqual(receipt['output'], str(self.output))
        self.assertEqual(receipt['renderer'], str(self.renderer))
        self.assertIn('unverified', receipt['result'])

    def test_oversized_svg_result_leaves_no_output(self):
        self.renderer.write_text(
            'export const render = () => ({svg: "<svg>" + '
            '"x".repeat(8388608) + "</svg>"});\n')
        result = self.run_adapter()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('8 MiB', result.stderr)
        self.assertFalse(self.output.exists())

    def test_malformed_renderer_result_leaves_no_output(self):
        self.renderer.write_text('export const render = () => ({svg: "not an SVG"});\n')
        result = self.run_adapter()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_existing_capture_and_symlink_are_preserved(self):
        self.renderer.write_text('export const render = () => ({svg: "<svg></svg>"});\n')
        original = self.root / 'original.svg'
        original.write_text('previous receipt')
        self.output.symlink_to(original)
        result = self.run_adapter()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.output.is_symlink())
        self.assertEqual(original.read_text(), 'previous receipt')
        self.output.unlink()
        self.output.write_text('previous capture')
        self.assertNotEqual(self.run_adapter().returncode, 0)
        self.assertEqual(self.output.read_text(), 'previous capture')

    def test_oversized_input_rejected_before_loading_renderer(self):
        self.source.write_bytes(b'a' * 262145)
        result = self.run_adapter()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('256 KiB', result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
