"""Plain-text summaries of orders."""


def paid_report(orders):
    lines = []
    total = 0
    for order in orders:
        if order['status'] == 'paid':
            name = order['name'].strip().title()
            amount = order['qty'] * order['price']
            lines.append('%-12s %3d x %7.2f = %9.2f' % (name, order['qty'], order['price'], amount))
            total += amount
    lines.append('TOTAL %.2f' % total)
    return '\n'.join(lines)


def unpaid_report(orders):
    lines = []
    total = 0
    for order in orders:
        if order['status'] != 'paid':
            name = order['name'].strip().title()
            amount = order['qty'] * order['price']
            lines.append('%-12s %3d x %7.2f = %9.2f' % (name, order['qty'], order['price'], amount))
            total += amount
    lines.append('TOTAL %.2f' % total)
    return '\n'.join(lines)


def all_report(orders):
    lines = []
    total = 0
    for order in orders:
        name = order['name'].strip().title()
        amount = order['qty'] * order['price']
        lines.append('%-12s %3d x %7.2f = %9.2f' % (name, order['qty'], order['price'], amount))
        total += amount
    lines.append('TOTAL %.2f' % total)
    return '\n'.join(lines)
