"""Split a list of items into pages."""


def page_count(total, per_page):
    if per_page < 1:
        raise ValueError('per_page must be positive')
    return (total + per_page - 1) // per_page


def paginate(items, page, per_page):
    """Return the items on a 1-based page."""
    if per_page < 1 or page < 1:
        raise ValueError('page and per_page must be positive')
    start = page * per_page
    return items[start:start + per_page]
