#!/usr/bin/env python3
"""Static discovery, catalog handoff and Markdown fragment checks; no execution."""
import re
from pathlib import Path
from urllib.parse import unquote


def headings(text):
    """GitHub-style slugs for ordinary authored ATX headings, including duplicates."""
    result = set()
    counts = {}
    body = re.sub(r'```.*?```|~~~.*?~~~', '', text, flags=re.S)
    for title in re.findall(r'^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$', body, re.M):
        title = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', title)
        title = re.sub(r'<[^>]+>', '', title).lower()
        slug = re.sub(r'[^\w\- ]', '', title).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug if count == 0 else f'{slug}-{count}')
    return result


def check_discovery(root, names, catalog):
    expected = {root/'skills'/name/'SKILL.md' for name in names}
    actual = set((root/'skills').rglob('SKILL.md'))
    errors = [f'Unexpected active skill entrypoint: {p.relative_to(root)}; reference data must use SOURCE.md'
              for p in sorted(actual - expected)]
    errors += [f'Missing active skill entrypoint: {p.relative_to(root)}' for p in sorted(expected - actual)]
    for entry in catalog:
        for related in entry.get('related', []):
            if related not in names:
                errors.append(f"{entry['name']}: unknown related skill {related}")
    return errors


def check_links(root, path, snapshots=()):
    errors = []
    # Pinned source text has its own integrity checks and is never active routing.
    if path in snapshots:
        return errors
    body = re.sub(r'```.*?```|~~~.*?~~~', '', path.read_text(), flags=re.S)
    for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)', body):
        target = raw.strip('<>')
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        filename, _, fragment = target.partition('#')
        resolved = (path.parent/unquote(filename)).resolve() if filename else path.resolve()
        if not resolved.is_relative_to(root) or not resolved.exists():
            errors.append(f'Broken/escaping link: {path.relative_to(root)} -> {target}')
        elif fragment and resolved.suffix == '.md':
            # Explicit HTML anchors are supported alongside ordinary heading slugs.
            text = resolved.read_text()
            anchors = headings(text) | set(re.findall(r'<(?:a|[a-z]+)\s+[^>]*(?:id|name)=["\']([^"\']+)', text))
            if unquote(fragment) not in anchors:
                errors.append(f'Broken Markdown fragment: {path.relative_to(root)} -> {target}')
    return errors


def check_audit(root, names):
    """Prevent an old partial audit from silently masquerading as full coverage."""
    path = root/'docs/skill-audit.md'
    if not path.is_file():
        return ['Missing full-catalog audit']
    rows = re.findall(r'^\|\s+\[([a-z0-9-]+)\]\(\.\./skills/\1/SKILL\.md\)\s+\|', path.read_text(), re.M)
    if len(rows) != len(set(rows)) or set(rows) != names:
        return ['Full-catalog audit coverage differs from the catalog']
    return []
