import unittest

from report import all_report, paid_report

ORDERS = [{'name': 'widget', 'qty': 2, 'price': 1.5, 'status': 'paid'}]


class ReportTests(unittest.TestCase):
    def test_paid(self):
        self.assertIn('TOTAL 3.00', paid_report(ORDERS))

    def test_all_matches_paid_when_all_paid(self):
        self.assertEqual(all_report(ORDERS), paid_report(ORDERS))
