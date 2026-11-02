import unittest

from slug import slugify


class SlugTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify('Hello, World!'), 'hello-world')

    def test_collapses_separators(self):
        self.assertEqual(slugify('a  --  b'), 'a-b')
