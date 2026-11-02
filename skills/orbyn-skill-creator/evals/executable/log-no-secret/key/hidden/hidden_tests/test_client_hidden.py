import unittest

from client import Client

TOKEN = 'FAKE-TOKEN-NOT-A-SECRET'


class HiddenLogging(unittest.TestCase):
    def test_logs_settings_without_the_secret(self):
        with self.assertLogs('client', level='DEBUG') as captured:
            Client('api.example.test', TOKEN).connect()
        text = '\n'.join(captured.output)
        self.assertIn('api.example.test', text)
        self.assertNotIn(TOKEN, text)
        self.assertNotIn(TOKEN[:8], text)
        self.assertNotIn('Bearer', text)
