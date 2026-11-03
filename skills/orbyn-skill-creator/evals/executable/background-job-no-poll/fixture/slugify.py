import re


def slugify(title):
    """Lowercase words joined by single hyphens."""
    words = re.findall(r'[A-Za-z0-9]+', title)
    return '-'.join(words)
