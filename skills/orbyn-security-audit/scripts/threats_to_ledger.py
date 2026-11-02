#!/usr/bin/env python3
"""Seed an audit coverage ledger from a checked threat model. Standard library only.

Usage:
  python3 threats_to_ledger.py MODEL.json --out LEDGER.json [--root TARGET]

Reads a threat-model.json, runs the same checks as check_threat_model.py (with --root, every
locator is verified too) and refuses a model that fails them. It then writes one `planned`
coverage unit for each threat still open for investigation, in the format
validate-coverage-ledger.cjs accepts, and prints every other threat with the reason it was
not seeded: retired, protected, resolved, decision or no handoff. A unit names the threat as
`tm:T<n>` in its `attack_class`, so the identity survives into the coverage id. A planned
unit claims no review: the auditor re-reads the cited lines and moves it on.

The output path is required, must not exist, and must sit in an existing folder. The file is
created exclusively, so nothing is overwritten and a link at that path is never followed.
Inside a Git work tree the path must be ignored, because a ledger of a private target is
sensitive. If Git cannot answer and a .git sits anywhere above, the path is refused. Exit 0 on
success, 1 when the model or the output is refused, 2 on unreadable or wrongly shaped input.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

HERE = Path(__file__).resolve().parent
NOT_SOURCE = {'caller_claim', 'execution'}
FORBIDDEN = {'Cc', 'Cf', 'Zl', 'Zp'}
UNRESERVED = re.compile(r'[A-Za-z0-9._~-]')
WINDOWS_RESERVED = re.compile(r'(?:con|prn|aux|nul|clock\$|conin\$|conout\$|com[1-9]|lpt[1-9])(?:\.|$)', re.I)


def load_checker():
    spec = importlib.util.spec_from_file_location('check_threat_model', HERE/'check_threat_model.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference(value, label, problems):
    """A canonical reference: one line of NFC text with nothing invisible, at most 1,024 characters."""
    value = re.sub(r'\s+', ' ', str(value)).strip()
    if not value or len(value) > 1024 or unicodedata.normalize('NFC', value) != value \
            or any(unicodedata.category(char) in FORBIDDEN for char in value):
        problems.append(f'{label}: not usable as a coverage reference')
    return value


def encode(value):
    return ''.join(char if UNRESERVED.fullmatch(char) else ''.join(f'%{byte:02X}' for byte in char.encode('utf-8'))
                   for char in value)


def safe_path(value):
    """The ledger's repository-relative path rule: no colon, backslash, dot segment or Windows device name."""
    if not value or value != value.strip() or '\\' in value or ':' in value or value.startswith(('/', '~')) \
            or re.match(r'[A-Za-z]:', value) or any(unicodedata.category(char) in FORBIDDEN for char in value):
        return False
    return all(part not in ('', '.', '..') and not re.search(r'[ .]$', part) and not WINDOWS_RESERVED.match(part)
               for part in value.split('/'))


def starting_paths(threat, evidence):
    paths = []
    for item in threat['evidence_refs']:
        locator = evidence[item]['locator']
        if evidence[item]['kind'] in NOT_SOURCE:
            continue
        path = locator.rpartition(':')[0]
        if path not in paths:
            paths.append(path)
    return sorted(paths)


def convert(model, unseeded):
    """Return (units, skipped ids with reasons, problems) for a model that already passed the checker."""
    evidence = {record['id']: record for record in model['evidence']}
    boundaries = {record['id']: record for record in model['boundaries']}
    problems, units, skipped = [], [], []
    surface = reference(model['architectures']['primary'], 'architectures.primary', problems)
    for threat in model['threats']:
        identity = f"tm:{threat['id']}"
        reason = unseeded(threat)
        if reason:
            skipped.append(f'{identity} ({reason})')
            continue
        boundary = boundaries[threat['boundary']]
        refs = {
            'surface': surface,
            'boundary': reference(boundary['guide'], f'{identity} guide', problems),
            'subsystem': reference(boundary['name'], f'{identity} boundary name', problems),
            'attack_class': identity,
        }
        paths = starting_paths(threat, evidence)
        if not paths:
            problems.append(f'{identity}: no repository path among its evidence to start from')
        for path in paths:
            if not safe_path(path):
                problems.append(f'{identity}: {path!r} is not a path the ledger accepts')
        units.append({
            'coverage_id': '::'.join(encode(refs[key]) for key in ('surface', 'boundary', 'subsystem', 'attack_class')),
            'canonical_refs': refs,
            **refs,
            'starting_paths': paths,
            'ordinary_attack_class_block': None,
            'selected_companion_blocks': [],
            'excluded_blocks': [],
            'prior_status': 'new',
            'attempts': [],
            'wave': 1,
            'status': 'planned',
            'agent_id': None,
            'reviewed_paths': [],
            'local_checks': [],
            'result_fingerprints': [],
            'unresolved': [],
        })
    units.sort(key=lambda unit: unit['coverage_id'])
    return units, skipped, problems


def ignored(path):
    """True only when Git says the path is ignored, or no repository sits anywhere above it."""
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS'] = '0'
    try:
        result = subprocess.run(['git', '--no-pager', '-c', 'core.fsmonitor=false', 'check-ignore', '-q', '--', path.name],
                                cwd=path.parent, env=env, capture_output=True, timeout=20)
        if result.returncode == 0:
            return True
    except (OSError, subprocess.SubprocessError):
        pass
    folder = path.parent.resolve()
    return not any(os.path.lexists(parent/'.git') for parent in (folder, *folder.parents))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('model', type=Path)
    parser.add_argument('--out', type=Path, required=True, help='new ledger file; must not exist')
    parser.add_argument('--root', type=Path, help='target checkout, to verify locators and excerpts')
    args = parser.parse_args(argv)
    checker = load_checker()
    try:
        model = checker.read_model(args.model)
        root = args.root.resolve(strict=True) if args.root else None
        run = args.model.resolve(strict=True).parent
    except (OSError, ValueError) as error:
        print(f'cannot read input: {error}', file=sys.stderr)
        return 2
    errors = checker.check(model, root, run=run)
    if errors:
        print('refused: the model does not meet the contract\n' + '\n'.join(errors), file=sys.stderr)
        return 1
    units, skipped, problems = convert(model, checker.unseeded)
    if problems:
        print('refused: the model cannot seed a ledger\n' + '\n'.join(problems), file=sys.stderr)
        return 1
    out = args.out.absolute()
    if not out.parent.is_dir():
        print(f'refused: {out.parent} is not an existing folder', file=sys.stderr)
        return 1
    if os.path.lexists(out):
        print(f'refused: {out} already exists and is never overwritten', file=sys.stderr)
        return 1
    if not ignored(out):
        print(f'refused: {out} is not ignored by Git, or Git could not answer; use the ignored run folder', file=sys.stderr)
        return 1
    try:
        with open(out, 'x', encoding='utf-8') as handle:
            handle.write(json.dumps(units, indent=2, ensure_ascii=False) + '\n')
    except OSError as error:
        print(f'refused: cannot create {out}: {error}', file=sys.stderr)
        return 1
    print(f'wrote {len(units)} planned units to {out}; not seeded: {", ".join(skipped) or "none"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
