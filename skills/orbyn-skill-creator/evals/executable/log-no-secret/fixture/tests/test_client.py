import unittest

from client import Client


class ClientTests(unittest.TestCase):
    def test_connect(self):
        self.assertTrue(Client('example.test', 'tok').connect()['connected'])

    def test_headers(self):
        self.assertEqual(Client('h', 'tok').headers()['Authorization'], 'Bearer tok')
