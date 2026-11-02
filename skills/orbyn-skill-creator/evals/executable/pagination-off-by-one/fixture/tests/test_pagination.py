import unittest

from pagination import page_count, paginate


class PaginationTests(unittest.TestCase):
    def test_page_count_rounds_up(self):
        self.assertEqual(page_count(10, 3), 4)

    def test_rejects_bad_sizes(self):
        with self.assertRaises(ValueError):
            paginate([1], 1, 0)

    def test_past_the_end_is_empty(self):
        self.assertEqual(paginate([1, 2, 3], 5, 2), [])
