import unittest

from todo import add_task, complete, summary


class HiddenSummary(unittest.TestCase):
    def test_counts_and_ratio(self):
        tasks = complete(add_task(add_task(add_task([], 'a'), 'b'), 'c'), 'a')
        self.assertEqual(summary(tasks), {'open': 2, 'done': 1, 'ratio': 0.33})

    def test_empty(self):
        self.assertEqual(summary([]), {'open': 0, 'done': 0, 'ratio': 0.0})
