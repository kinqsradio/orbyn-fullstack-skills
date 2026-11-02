#!/usr/bin/env python3
"""Generate CREDITS.md from provenance.json, so every external source is listed in one place."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'CREDITS.md'
HEADER = """# Credits

This library is built on other people's work. Everything copied or adapted here allows us to
modify and redistribute it with credit, and its notices stay in the skill. Reviewed sources shaped our thinking; none of their text is
bundled, and they may carry other licences. Generated from `provenance.json` by
`scripts/credits.py`, so edit the records, not this file. Full notices are in
[THIRD_PARTY_NOTICES.md](tools/THIRD_PARTY_NOTICES.md).
"""
SELF = 'kinqsradio/orbyn-fullstack-skills'


def project(url):
    match = re.match(r'https://github\.com/([^/]+/[^/#?]+)', url or '')
    return match.group(1).removesuffix('.git') if match else (url or '').split('#')[0]


def collect(skills):
    adapted, reviewed = defaultdict(lambda: {'skills': set(), 'credit': '', 'license': ''}), defaultdict(lambda: {'skills': set(), 'credit': '', 'license': ''})
    def add(table, item, name):
        url = item.get('source')
        if not url or SELF in url:
            return
        entry = table[project(url)]
        entry['skills'].add(name)
        entry['credit'] = entry['credit'] or item.get('credit') or item.get('copyright', '').replace('Copyright (c) ', '')
        entry['license'] = entry['license'] or item.get('license', '')
    for name, record in sorted(skills.items()):
        if record.get('relationship') == 'adapted':
            add(adapted, {**record, 'credit': record.get('copyright', '').replace('Copyright (c) ', '')}, name)
        for item in record.get('incorporated_material') or []:
            add(adapted, item, name)
        for path in sorted((ROOT/'skills'/name).glob('references/upstream/*/snapshot.json')):
            snapshot = json.loads(path.read_text())
            add(adapted, {'source': snapshot.get('repository'), 'license': snapshot.get('license'),
                          'credit': project(snapshot.get('repository')).split('/')[0]}, name)
        for key in ('reviewed_sources', 'reviewed_inspiration', 'reviewed_guidance'):
            for item in record.get(key) or []:
                if isinstance(item, dict):
                    add(reviewed, item, name)
    return adapted, {key: value for key, value in reviewed.items() if key not in adapted}


def table(rows, license_default):
    lines = ['| Source | Credit | Licence | Used in |', '| --- | --- | --- | --- |']
    for key in sorted(rows, key=str.lower):
        entry = rows[key]
        link = f'[{key}](https://github.com/{key})' if '/' in key and '://' not in key else key
        credit = entry['credit'].replace('|', '/').strip() or 'Listed in provenance'
        lines.append(f"| {link} | {credit} | {entry['license'] or license_default} | {', '.join(sorted(entry['skills']))} |")
    return '\n'.join(lines)


def render(skills):
    adapted, reviewed = collect(skills)
    return (HEADER + '\n## Copied or adapted\n\n' + table(adapted, 'MIT') + '\n\n## Reviewed for ideas, no text bundled\n\n'
            + table(reviewed, 'See source') + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args()
    text = render(json.loads((ROOT/'provenance.json').read_text())['skills'])
    if options.write:
        OUT.write_text(text)
        return 0
    if not OUT.is_file() or OUT.read_text() != text:
        print('CREDITS.md is stale: run python3 scripts/credits.py --write', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
