import unittest

from price import cart_total_cents


class PriceTests(unittest.TestCase):
    def test_no_tax(self):
        self.assertEqual(cart_total_cents([100, 250], 0), 350)

    def test_half_cent_rounds_up(self):
        self.assertEqual(cart_total_cents([15], 10), 17)
