import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slugify import slugify


class SlugifyTests(unittest.TestCase):
    def test_lowercases_and_joins(self):
        self.assertEqual(slugify('Hello, World'), 'hello-world')

    def test_collapses_separators(self):
        self.assertEqual(slugify('  a -- b  '), 'a-b')


if __name__ == '__main__':
    unittest.main()
