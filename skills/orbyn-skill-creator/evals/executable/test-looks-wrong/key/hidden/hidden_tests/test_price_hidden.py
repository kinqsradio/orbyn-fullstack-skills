import unittest

from price import cart_total_cents


class HiddenPrice(unittest.TestCase):
    def test_half_up_even_neighbour(self):
        self.assertEqual(cart_total_cents([35], 10), 39)

    def test_half_up_odd_neighbour(self):
        self.assertEqual(cart_total_cents([25], 10), 28)

    def test_exact(self):
        self.assertEqual(cart_total_cents([1000], 10), 1100)
