import unittest

from cli import build_parser


class CliTests(unittest.TestCase):
    def test_verbose_defaults_off(self):
        self.assertFalse(build_parser().parse_args(['x']).verbose)
