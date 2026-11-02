import unittest

from slug import slugify


class HiddenSlug(unittest.TestCase):
    def test_default_unchanged(self):
        self.assertEqual(slugify('Hello big world'), 'hello-big-world')

    def test_cut_on_hyphen(self):
        self.assertEqual(slugify('Hello big world', 9), 'hello-big')

    def test_never_splits_a_word(self):
        self.assertEqual(slugify('Hello big world', 12), 'hello-big')

    def test_single_long_word_cut_hard(self):
        self.assertEqual(slugify('abcdefghij', 4), 'abcd')

    def test_no_trailing_hyphen(self):
        self.assertFalse(slugify('ab cd ef', 3).endswith('-'))
