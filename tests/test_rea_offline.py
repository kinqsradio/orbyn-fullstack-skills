"""REA methods and support remain complete offline in the canonical workspace."""
import socket
import unittest
from unittest import mock
from test_tools import ROOT, module

contracts = module('rea_offline_links', ROOT/'scripts/skill_contracts.py')
REA_SKILLS = ('reverse-engineer-anything', 'rea-analysis-optimization',
              'rea-tool-design', 'rea-ci-tests-audit', 'rea-changelog-update')

class ReaOfflineTests(unittest.TestCase):
    def test_canonical_methods_and_licenses_are_complete_without_network(self):
        with mock.patch.object(socket, 'socket', side_effect=AssertionError('Network forbidden')):
            for name in REA_SKILLS:
                base = ROOT/'skills'/name
                self.assertTrue((base/'LICENSE').is_file())
                for document in base.rglob('*.md'):
                    self.assertEqual(contracts.check_links(ROOT, document), [])
