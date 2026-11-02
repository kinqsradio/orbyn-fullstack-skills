#!/usr/bin/env python3
"""Fail when a skill changed without a new authoring record in provenance.json.

Compares HEAD with a base revision, so CI runs it on pull requests. Standard library only.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GENERATED = {'README.md', 'catalog.json'}


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], check=True, capture_output=True, text=True).stdout


def changed_skills(base):
    names = set()
    for path in git('diff', '--name-only', f'{base}...HEAD').split('\n'):
        parts = path.split('/')
        if len(parts) > 2 and parts[0] == 'skills':
            names.add(parts[1])
        elif len(parts) == 2 and parts[0] == 'skills' and parts[1] not in GENERATED:
            names.add(parts[1])
    return names


def authoring(text):
    return {name: record.get('authoring', []) for name, record in json.loads(text)['skills'].items()}


def missing(base):
    before = authoring(git('show', f'{base}:provenance.json'))
    after = authoring(git('show', 'HEAD:provenance.json'))
    return sorted(name for name in changed_skills(base)
                  if name in after and len(after[name]) <= len(before.get(name, [])))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--base', required=True)
    options = parser.parse_args()
    try:
        names = missing(options.base)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f'check-authoring: {error}', file=sys.stderr)
        return 2
    if names:
        print('These skills changed with no new "authoring" entry in provenance.json, naming the '
              'tool, model and effort used:', ', '.join(names), file=sys.stderr)
        return 1
    print('OK: every changed skill records how it was authored.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
