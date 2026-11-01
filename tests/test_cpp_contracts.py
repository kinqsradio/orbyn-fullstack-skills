"""Compile focused C++ semantics when a configured/local compiler is available."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CppContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = os.environ.get('CXX') or shutil.which('clang++') or shutil.which('g++')
        if not compiler:
            raise unittest.SkipTest('Existing C++17 compiler required; no installation')
        folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(folder.cleanup)
        cls.binary = str(Path(folder.name) / 'contracts')
        result = subprocess.run([compiler, '-std=c++17', '-pthread',
                                 str(ROOT / 'tests/fixtures/language-contracts/cpp-move-and-capture.cpp'),
                                 '-o', cls.binary], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def run_control(self, mode):
        return subprocess.run([self.binary, mode], capture_output=True, text=True, timeout=5)

    def test_conditional_and_defaulted_moves_preserve_catchable_member_exception(self):
        for mode in ('conditional', 'inferred'):
            with self.subTest(mode=mode):
                result = self.run_control(mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, 'caught 7\n')
        self.assertEqual(self.run_control('unconditional').returncode, 42)

    def test_joined_reference_capture_preserves_output_that_value_capture_loses(self):
        reference = self.run_control('reference')
        copied = self.run_control('value')
        self.assertEqual(reference.returncode, 0, reference.stderr)
        self.assertEqual(copied.returncode, 0, copied.stderr)
        self.assertEqual(reference.stdout, '42\n')
        self.assertEqual(copied.stdout, '0\n')


if __name__ == '__main__':
    unittest.main()
