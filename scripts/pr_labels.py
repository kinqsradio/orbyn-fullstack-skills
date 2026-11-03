#!/usr/bin/env python3
"""Label a pull request by what it changes, who sent it and how it was built.

`decide` is a pure function from a PR record and its changed files to the labels to add
and remove. `apply` is what the workflow runs under pull_request_target: it reads the PR
through `gh api`, creates missing labels with fixed colours and sets them. It never
fetches or runs PR code, treats the body and file paths as untrusted data, and touches
only the labels in CATALOG. Standard library plus the GitHub CLI.
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMENT = re.compile(r'<!--.*?-->', re.S)
GENERATED = {'distribution/manifest.json', 'provenance.json'}
SIZES = ((100, 'size: s'), (500, 'size: m'), (2000, 'size: l'))
SIZE_XL = 'size: xl'
MAINTAINER_ROLES = {'OWNER', 'MEMBER', 'COLLABORATOR'}
FIRST_TIME = {'FIRST_TIME_CONTRIBUTOR', 'FIRST_TIMER'}

# The only labels this script may add or remove: name -> (colour, description).
CATALOG = {
    'skill: new': ('0e8a16', 'Adds a new skill'),
    'skill: update': ('1d76db', 'Changes an existing skill'),
    'area: harness': ('5319e7', 'Harness, model registry or agent definitions'),
    'area: evals': ('5319e7', 'Evaluation cases and runners'),
    'area: security': ('b60205', 'Security skills'),
    'area: ci': ('5319e7', 'Workflows and test tooling'),
    'area: hosts': ('5319e7', 'Host instruction files and discovery links'),
    'area: docs': ('0075ca', 'Documentation only'),
    'upstream adaptation': ('fbca04', 'Adapts or incorporates external material'),
    'community': ('c5def5', 'Author is outside the maintainer group'),
    'first contribution': ('bfdadc', "Author's first contribution to this repository"),
    'built with: claude code': ('ededed', 'Disclosed tool: Claude Code'),
    'built with: codex': ('ededed', 'Disclosed tool: Codex'),
    'built with: cursor': ('ededed', 'Disclosed tool: Cursor'),
    'built with: copilot': ('ededed', 'Disclosed tool: Copilot'),
    'built with: gemini': ('ededed', 'Disclosed tool: Gemini'),
    'built with: other': ('ededed', 'Disclosed tool outside the named list'),
    'human only': ('ededed', 'Disclosure says no agent was used'),
    'size: s': ('c2e0c6', 'Under 100 changed lines'),
    'size: m': ('fef2c0', 'Under 500 changed lines'),
    'size: l': ('f9d0c4', 'Under 2000 changed lines'),
    'size: xl': ('e99695', '2000 or more changed lines'),
    'eval run': ('d4c5f9', 'Touches what an executable eval case depends on'),
    'agent hand-off': ('d93f0b', 'Draft with open findings after three review rounds'),
}
# Fixed allowlist of tool names; free text in the description can never create a label.
TOOLS = (
    ('built with: claude code', re.compile(r'\bclaude(?:[- ]code)?\b', re.I)),
    ('built with: codex', re.compile(r'\bcodex\b', re.I)),
    ('built with: cursor', re.compile(r'\bcursor\b', re.I)),
    ('built with: copilot', re.compile(r'\bcopilot\b', re.I)),
    ('built with: gemini', re.compile(r'\bgemini\b', re.I)),
)
NO_AGENT = re.compile(r'\b(no (?:ai|agents?|tools?)|human[- ]only|without (?:an? )?(?:ai|agents?)|none|not used|n/a)\b', re.I)

HARNESS = re.compile(r'(^|/)(harness\.py|sync-agent-models\.py)$|^docs/agents/models\.json$|^\.(claude|codex)/agents/')
EVALS = re.compile(r'^skills/orbyn-skill-creator/evals/|(^|/)(eval_[^/]*\.py|evaluate\.py)$')
SECURITY = re.compile(r'^skills/orbyn-security-[^/]+/')
HOSTS = re.compile(r'^(AGENTS?\.md|CLAUDE\.md|GEMINI\.md|\.github/copilot-instructions\.md|\.aider\.conf\.yml|'
                   r'\.(agents|claude/skills|continue|junie|kiro|cursor|codex/skills)/|'
                   r'scripts/(host_instructions|discovery_links|sync-host-instructions|sync-agent-skills)\.py)')
CI = re.compile(r'^\.github/(?!copilot-instructions\.md)|^scripts/(run_tests|pr_gate|pr_labels)\.py$')
DOCS = re.compile(r'^(README\.md|CONTRIBUTING\.md|docs/)')
SKILL_FILE = re.compile(r'^skills/([^/]+)/SKILL\.md$')
SKILL_PATH = re.compile(r'^skills/([^/]+)/')
UPSTREAM = re.compile(r'(^|/)references/upstream/')


def section(body, title):
    match = re.search(rf'^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)', body, re.M | re.S)
    return match.group(1).strip() if match else None


def field(text, name):
    match = re.search(rf'^\s*[-*]\s*{re.escape(name)}\s*:[ \t]*(.*)$', text, re.M)
    return match.group(1).strip() if match else None


def tool_labels(body):
    """Allowlisted `built with` labels from the disclosure's Tools line, or `human only`."""
    text = COMMENT.sub('', (body or '').replace('\r\n', '\n'))
    disclosure = section(text, 'Agent disclosure')
    tools = field(disclosure, 'Tools') if disclosure else None
    if not tools or not tools.strip().strip('`*_ ').strip('?-'):
        return set()
    found = {label for label, pattern in TOOLS if pattern.search(tools)}
    if found:
        return found
    return {'human only'} if NO_AGENT.search(tools) else {'built with: other'}


def size_label(files):
    total = sum(int(f.get('additions') or 0) + int(f.get('deletions') or 0)
                for f in files if f.get('filename') not in GENERATED)
    for limit, label in SIZES:
        if total < limit:
            return label
    return SIZE_XL


def added_skills(files):
    return {m.group(1) for f in files if f.get('status') == 'added'
            for m in [SKILL_FILE.match(f.get('filename', ''))] if m}


def updated_skills(files):
    """Names of existing skills with changed files; a skill added by this PR does not count."""
    new = added_skills(files)
    return sorted({m.group(1) for f in files for m in [SKILL_PATH.match(f.get('filename', ''))]
                   if m and m.group(1) not in new})


def adds_incorporated_material(files):
    for f in files:
        name = f.get('filename', '')
        if name == 'provenance.json':
            if any(line.startswith('+') and 'incorporated_material' in line
                   for line in (f.get('patch') or '').splitlines()):
                return True
        elif UPSTREAM.search(name) and f.get('status') != 'removed':
            return True
    return False


def load_affected():
    """eval_report's pure affected_cases, loaded read-only from this checkout."""
    path = ROOT / 'skills/orbyn-skill-creator/scripts/eval_report.py'
    spec = importlib.util.spec_from_file_location('eval_report', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault('eval_report', module)
    spec.loader.exec_module(module)
    return module.affected_cases


def decide(pr, files, affected=None):
    """Labels to add and remove for one PR record and its changed files."""
    names = [f.get('filename', '') for f in files]
    substantive = [n for n in names if n not in GENERATED and n != 'distribution/manifest.json']
    want = set()
    if added_skills(files):
        want.add('skill: new')
    if updated_skills(files):
        want.add('skill: update')
    for label, pattern in (('area: harness', HARNESS), ('area: evals', EVALS), ('area: security', SECURITY),
                           ('area: ci', CI), ('area: hosts', HOSTS)):
        if any(pattern.search(n) for n in names):
            want.add(label)
    if substantive and all(DOCS.search(n) for n in substantive):
        want.add('area: docs')
    if adds_incorporated_material(files):
        want.add('upstream adaptation')
    association = pr.get('author_association') or ''
    if association not in MAINTAINER_ROLES:
        want.add('community')
    if association in FIRST_TIME:
        want.add('first contribution')
    want |= tool_labels(pr.get('body'))
    want.add(size_label(files))
    affected = affected or load_affected()
    if affected(names) or any(n.endswith('orbyn-workflow/scripts/harness.py') for n in names):
        want.add('eval run')
    body = COMMENT.sub('', (pr.get('body') or '').replace('\r\n', '\n'))
    if pr.get('draft') and re.search(r'^#{1,6}\s+Open findings\b', body, re.M | re.I):
        want.add('agent hand-off')
    have = {label['name'] if isinstance(label, dict) else label for label in pr.get('labels', [])}
    return {'desired': sorted(want), 'add': sorted(want - have),
            'remove': sorted((have & set(CATALOG)) - want)}


def gh(*args, stdin=None):
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True, timeout=60,
                          input=stdin).stdout


def fetch(number, repo):
    pr = json.loads(gh('api', f'repos/{repo}/pulls/{number}'))
    pages = json.loads(gh('api', '--paginate', '--slurp', f'repos/{repo}/pulls/{number}/files?per_page=100'))
    files = [f for page in pages for f in (page if isinstance(page, list) else [page])]
    return pr, files


def apply(number, repo, affected=None):
    pr, files = fetch(number, repo)
    result = decide(pr, files, affected)
    for name in result['add']:
        colour, description = CATALOG[name]
        gh('label', 'create', name, '--repo', repo, '--color', colour, '--description', description, '--force')
    if result['add']:
        gh('pr', 'edit', str(number), '--repo', repo, *[a for n in result['add'] for a in ('--add-label', n)])
    if result['remove']:
        gh('pr', 'edit', str(number), '--repo', repo, *[a for n in result['remove'] for a in ('--remove-label', n)])
    print(json.dumps(result, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)
    applying = commands.add_parser('apply', help='Label one PR')
    applying.add_argument('--pr', required=True)
    applying.add_argument('--repo', default=os.environ.get('GH_REPO', ''))
    options = parser.parse_args()
    try:
        if not options.repo or not options.pr.isdigit():
            raise ValueError('need --repo (or GH_REPO) and a numeric --pr')
        return apply(options.pr, options.repo)
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        print(f'pr_labels: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
