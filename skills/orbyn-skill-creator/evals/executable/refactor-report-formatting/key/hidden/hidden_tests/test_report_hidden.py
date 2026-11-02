import unittest

from report import all_report, paid_report, unpaid_report

ORDERS = [
    {'name': ' widget ', 'qty': 3, 'price': 2.5, 'status': 'paid'},
    {'name': 'gadget', 'qty': 1, 'price': 19.99, 'status': 'open'},
    {'name': 'thing one', 'qty': 12, 'price': 0.1, 'status': 'paid'},
]


class Characterisation(unittest.TestCase):
    def test_paid(self):
        self.assertEqual(paid_report(ORDERS), 'Widget         3 x    2.50 =      7.50\nThing One     12 x    0.10 =      1.20\nTOTAL 8.70')

    def test_unpaid(self):
        self.assertEqual(unpaid_report(ORDERS), 'Gadget         1 x   19.99 =     19.99\nTOTAL 19.99')

    def test_all(self):
        self.assertEqual(all_report(ORDERS).splitlines()[-1], 'TOTAL 28.69')

    def test_empty(self):
        self.assertEqual(paid_report([]), 'TOTAL 0.00')
