#!/usr/bin/env python3
"""Decide whether a pull request is complete enough to ask the maintainer for review.

`check` reads a PR description and reports what is missing; it needs no network.
`apply` is what the workflow runs: it labels the PR and requests review only when the
disclosure is complete and CI is green. It reads the PR through the GitHub CLI and never
runs code from the PR. Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

READY, NEEDS = 'ready-for-review', 'needs-disclosure'
REQUIRED_CHECKS = ('Validate (Python 3.11)', 'Validate (Python 3.13)')
DISCLOSURE_FIELDS = ('Tools', 'Models', 'Effort', 'Human role')
EVIDENCE_FIELDS = ('Static/helper checks', 'Recorded host trials')
EMPTY = {'', 'none', 'n/a', 'na', 'tbd', 'todo', 'unknown', '-', '?'}
COMMENT = re.compile(r'<!--.*?-->', re.S)
# We may copy what we can modify and redistribute with credit alone; these ask for more.
ALLOWED_LICENCE = re.compile(r'\b(MIT|Apache|BSD|ISC|Zlib|CC[- ]?BY|CC0|Unlicense)\b', re.I)
OTHER_LICENCE = re.compile(r'\b(A?GPL|LGPL|MPL|EUPL|SSPL|BSL|Elastic|CC[- ]?BY[- ](?:NC|ND|SA)\S*|proprietary|no licen[cs]e|source[- ]available)\b', re.I)
FULL_COMMIT = re.compile(r'\b[0-9a-f]{40}\b')
GITHUB_COMMIT_LINK = re.compile(r'https://\S+/(?:tree|blob|commit)/[0-9a-f]{7,40}\b')
# A family name alone says too little to reproduce the work: sonnet, or gpt.
SPECIFIC_MODEL = re.compile(r'\d')


def section(body, title):
    """The text under a level-two heading, or None when the heading is absent."""
    match = re.search(rf'^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)', body, re.M | re.S)
    return match.group(1).strip() if match else None


def field(text, name):
    match = re.search(rf'^\s*[-*]\s*{re.escape(name)}\s*:[ \t]*(.*)$', text, re.M)
    return match.group(1).strip() if match else None


def blank(value):
    return value is None or value.strip().strip('`*_').lower() in EMPTY


def source_problems(text):
    """Each listed source needs a link, a pinned commit and its licence; "none" is an answer."""
    if text is None or not text.strip():
        return ['Fill in "External sources" under Agent disclosure; write "none" if there are none.']
    if text.strip().strip('`*_').lower() == 'none':
        return []
    problems = []
    if 'https://' not in text:
        problems.append('Link every external source under "External sources".')
    if not FULL_COMMIT.search(text) and not GITHUB_COMMIT_LINK.search(text):
        problems.append('Pin every external source to an exact commit.')
    if not ALLOWED_LICENCE.search(text) and not OTHER_LICENCE.search(text):
        problems.append('State the licence of every external source.')
    match = OTHER_LICENCE.search(text)
    if match and re.search(r'\b(copied|adapted|bundled)\b', text, re.I):
        problems.append(f'Copy or adapt only what we may modify and redistribute with credit alone; found {match.group(1)}.')
    return problems


def check(body):
    """Every reason this description is not ready; an empty list means it is."""
    body = COMMENT.sub('', (body or '').replace('\r\n', '\n'))
    problems = []
    problem = section(body, 'Problem and resulting behavior')
    if problem is None or not problem:
        problems.append('Describe the problem and the resulting behaviour.')
    disclosure = section(body, 'Agent disclosure')
    if disclosure is None:
        problems.append('Add the Agent disclosure section from the template.')
    else:
        for name in DISCLOSURE_FIELDS:
            if blank(field(disclosure, name)):
                problems.append(f'Fill in "{name}" under Agent disclosure.')
        problems += source_problems(field(disclosure, 'External sources'))
        models = field(disclosure, 'Models')
        if not blank(models) and not SPECIFIC_MODEL.search(models):
            problems.append('Name exact models with their version under Agent disclosure, not a family.')
    evidence = section(body, 'Evidence')
    if evidence is None:
        problems.append('Add the Evidence section from the template.')
    else:
        for name in EVIDENCE_FIELDS:
            if blank(field(evidence, name)):
                problems.append(f'Fill in "{name}" under Evidence; write "not run" if you did not run it.')
    boundary = section(body, 'Attribution and publication boundary')
    if boundary is None:
        problems.append('Add the Attribution and publication boundary section from the template.')
    elif re.search(r'^\s*[-*]\s*\[ \]', boundary, re.M):
        problems.append('Confirm every item under Attribution and publication boundary.')
    return problems


def decide(pr):
    """Pure decision for one PR record: labels to set, and whether to request review."""
    author = pr.get('author', {}).get('login', '')
    bot = author.endswith('[bot]') or pr.get('author', {}).get('is_bot', False)
    if pr.get('isDraft'):
        return {'state': 'draft', 'problems': [], 'add': [], 'remove': [READY], 'request': False}
    problems = [] if bot else check(pr.get('body'))
    if problems:
        return {'state': 'incomplete', 'problems': problems, 'add': [NEEDS], 'remove': [READY], 'request': False}
    results = {c.get('name'): c.get('conclusion') for c in pr.get('statusCheckRollup', [])}
    failed = [name for name in REQUIRED_CHECKS if results.get(name) in {'FAILURE', 'CANCELLED', 'TIMED_OUT'}]
    if failed:
        return {'state': 'failing', 'problems': [f'{name} did not pass.' for name in failed],
                'add': [], 'remove': [NEEDS, READY], 'request': False}
    if not all(results.get(name) == 'SUCCESS' for name in REQUIRED_CHECKS):
        return {'state': 'waiting', 'problems': [], 'add': [], 'remove': [NEEDS, READY], 'request': False}
    return {'state': 'ready', 'problems': [], 'add': [READY], 'remove': [NEEDS], 'request': True}


def gh(*args):
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True, timeout=60).stdout


def find_number(sha):
    """A workflow_run from a fork names no PR, so look it up by the commit."""
    found = json.loads(gh('pr', 'list', '--repo', os.environ['GH_REPO'], '--state', 'open',
                          '--search', sha, '--json', 'number'))
    return str(found[0]['number']) if found else None


def apply(number, maintainer):
    repo = os.environ['GH_REPO']
    pr = json.loads(gh('pr', 'view', number, '--repo', repo, '--json',
                       'author,body,isDraft,statusCheckRollup,reviewRequests,reviews,labels'))
    result = decide(pr)
    labels = {label['name'] for label in pr.get('labels', [])}
    for name, colour in ((READY, '0e8a16'), (NEEDS, 'd93f0b')):
        gh('label', 'create', name, '--repo', repo, '--color', colour, '--force')
    for name in result['add']:
        gh('pr', 'edit', number, '--repo', repo, '--add-label', name)
    for name in result['remove']:
        if name in labels:
            gh('pr', 'edit', number, '--repo', repo, '--remove-label', name)
    requested = {r.get('login') for r in pr.get('reviewRequests', [])}
    reviewed = {r.get('author', {}).get('login') for r in pr.get('reviews', [])}
    if result['request'] and pr['author']['login'] != maintainer and maintainer not in requested | reviewed:
        gh('pr', 'edit', number, '--repo', repo, '--add-reviewer', maintainer)
    print(json.dumps(result, indent=2))
    return 1 if result['state'] == 'incomplete' else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)
    checking = commands.add_parser('check', help='Report what a PR description is missing')
    checking.add_argument('body_file')
    applying = commands.add_parser('apply', help='Label one PR and request review when it is ready')
    applying.add_argument('--pr', default='')
    applying.add_argument('--sha', default='')
    applying.add_argument('--maintainer', required=True)
    options = parser.parse_args()
    try:
        if options.command == 'check':
            with open(options.body_file, encoding='utf-8') as file:
                problems = check(file.read())
            print(json.dumps({'status': 'fail' if problems else 'pass', 'problems': problems}, indent=2))
            return 1 if problems else 0
        number = options.pr or find_number(options.sha)
        if not number:
            print('No open pull request for this commit.')
            return 0
        return apply(number, options.maintainer)
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        print(f'pr_gate: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
