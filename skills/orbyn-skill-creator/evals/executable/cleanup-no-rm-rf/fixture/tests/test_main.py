import unittest

from src.main import main


class MainTests(unittest.TestCase):
    def test_main(self):
        self.assertEqual(main(), 0)
