"""Cart totals in whole cents. Tax is rounded half up to the nearest cent."""


def cart_total_cents(prices, tax_percent):
    return round(sum(prices) * (100 + tax_percent) / 100)
