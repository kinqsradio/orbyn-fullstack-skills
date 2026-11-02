import unittest

from todo import add_task, complete


class TodoTests(unittest.TestCase):
    def test_add_and_complete(self):
        tasks = complete(add_task([], 'a'), 'a')
        self.assertTrue(tasks[0]['done'])
