"""Selection rules of scripts/run_tests.py, on synthetic repositories and the real protected set."""
import tempfile
import unittest
from pathlib import Path

from test_tools import ROOT, module

runner = module('run_tests', ROOT/'scripts/run_tests.py')


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'tests').mkdir()
        self.modules = list(runner.PROTECTED) + ['test_alpha', 'test_beta', 'test_gamma']
        for name in runner.PROTECTED:
            (self.root/'tests'/f'{name}.py').write_text('import unittest\n')
        (self.root/'tests/test_alpha.py').write_text("P = 'skills/demo-skill/scripts/demo_tool.py'\n")
        (self.root/'tests/test_beta.py').write_text("P = 'docs/other.md'\n")
        (self.root/'tests/test_gamma.py').write_text("from helper_shared import value\n")
        (self.root/'tests/helper_shared.py').write_text('value = 1\n')
        (self.root/'skills/demo-skill/scripts').mkdir(parents=True)
        (self.root/'skills/demo-skill/scripts/demo_tool.py').write_text('x = 1\n')
        (self.root/'skills/demo-skill/SKILL.md').write_text('demo\n')

    def select(self, *changed):
        return runner.select(list(changed), self.modules, self.root)

    def test_protected_set_is_always_selected(self):
        for changed in ((), ('skills/demo-skill/SKILL.md',), ('docs/other.md',)):
            chosen, everything = self.select(*changed)
            self.assertIsNone(everything, changed)
            self.assertTrue(set(runner.PROTECTED) <= set(chosen), changed)
        self.assertEqual(len(runner.PROTECTED), 8)

    def test_the_real_protected_modules_exist(self):
        self.assertTrue(set(runner.PROTECTED) <= set(runner.discover()))

    def test_unknown_path_runs_everything(self):
        chosen, everything = self.select('mystery/file.bin')
        self.assertIn('mystery/file.bin', everything)

    def test_skill_change_picks_its_module_and_not_unrelated_ones(self):
        chosen, everything = self.select('skills/demo-skill/SKILL.md')
        self.assertIsNone(everything)
        self.assertIn('test_alpha', chosen)
        self.assertIn('demo-skill', chosen['test_alpha'])
        self.assertNotIn('test_beta', chosen)

    def test_script_change_picks_the_module_that_names_it(self):
        chosen, everything = self.select('skills/demo-skill/scripts/demo_tool.py')
        self.assertIsNone(everything)
        self.assertIn('test_alpha', chosen)

    def test_selection_logic_change_runs_everything(self):
        for path in ('scripts/run_tests.py', 'tests/test_run_tests.py'):
            self.assertIn('selection logic', self.select(path)[1])

    def test_shared_infrastructure_runs_everything(self):
        for path in ('scripts/check-library.py', '.github/workflows/validate.yml', 'distribution/plugin.json'):
            self.assertIsNotNone(self.select(path)[1], path)

    def test_test_helpers_run_everything_but_a_plain_test_module_selects_itself(self):
        self.assertIsNotNone(self.select('tests/helper_shared.py')[1])
        self.assertIsNotNone(self.select('tests/fixtures/data.json')[1])
        chosen, everything = self.select('tests/test_beta.py')
        self.assertIsNone(everything)
        self.assertIn('test_beta', chosen)

    def test_one_unmapped_path_among_mapped_ones_still_runs_everything(self):
        self.assertIsNotNone(self.select('skills/demo-skill/SKILL.md', 'mystery/file.bin')[1])

    def test_a_caller_of_a_changed_script_brings_in_the_tests_that_name_the_caller(self):
        caller = self.root/'skills/demo-skill/scripts/caller_tool.py'
        caller.write_text('import demo_tool_helper\n')
        helper = self.root/'skills/demo-skill/scripts/demo_tool_helper.py'
        helper.write_text('y = 1\n')
        (self.root/'tests/test_beta.py').write_text("P = 'skills/demo-skill/scripts/caller_tool.py'\n")
        chosen, everything = self.select('skills/demo-skill/scripts/demo_tool_helper.py')
        self.assertIsNone(everything)
        self.assertIn('test_beta', chosen)


class ShardTests(unittest.TestCase):
    def test_every_class_with_tests_is_listed_so_sharding_drops_nothing(self):
        for name in runner.discover():
            listed = runner.shards(name)
            if not listed:
                continue
            loaded = __import__(name)
            with_tests = {c for c in vars(loaded).values() if isinstance(c, type) and issubclass(c, unittest.TestCase)
                          and c.__module__ == name and unittest.defaultTestLoader.loadTestsFromTestCase(c).countTestCases()}
            self.assertEqual({c.__name__ for c in with_tests}, set(listed), name)


if __name__ == '__main__':
    unittest.main()
