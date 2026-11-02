"""Turn titles into URL slugs."""
import re


def slugify(text):
    text = re.sub(r'[^a-z0-9]+', '-', text.lower())
    return text.strip('-')
