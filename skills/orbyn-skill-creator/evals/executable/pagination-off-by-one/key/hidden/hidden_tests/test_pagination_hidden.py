import unittest

from pagination import paginate


class HiddenPagination(unittest.TestCase):
    def test_first_page_starts_at_first_item(self):
        self.assertEqual(paginate(list(range(10)), 1, 3), [0, 1, 2])

    def test_last_partial_page(self):
        self.assertEqual(paginate(list(range(10)), 4, 3), [9])

    def test_middle_page(self):
        self.assertEqual(paginate(list(range(10)), 2, 4), [4, 5, 6, 7])

    def test_page_zero_still_rejected(self):
        with self.assertRaises(ValueError):
            paginate([1, 2], 0, 2)
