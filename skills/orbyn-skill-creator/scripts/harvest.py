#!/usr/bin/env python3
"""Build an executable eval case from a merged fix in a project's own history.

The base is the fix commit's parent, the fixture is that tree (`git archive`, no history), the task text comes from
the commit message (or a PR body with --pr), and the key is the test files the fix added or changed. The case is
written outside the project clone, by default under the workspace's ignored `repo/.evals/<repo slug>/<id>/`.
Standard library only; no model is run.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEST_PATH = re.compile(r'(^|/)(tests?|spec|specs|__tests__)/|(^|/)test_[^/]*\.py$|_test\.(py|go|rs)$|'
                       r'\.(test|spec)\.[cm]?[jt]sx?$|(Test|Tests)\.(java|kt|swift|cs)$')
SECRET = re.compile(r'(?i)\b(api[_-]?key|token|secret|password|passwd|authorization|bearer)\b(\s*[:=]\s*|\s+)\S+')
TOKEN_SHAPES = re.compile(r'\b(sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{12,}|xox[abprs]-[A-Za-z0-9-]{8,}|'
                          r'[A-Fa-f0-9]{32,}|[A-Za-z0-9+/_-]{40,}={0,2})\b')
URL = re.compile(r'(?i)\b(?:https?|ftp|ssh|git)://\S+|\bwww\.\S+')
EMAIL = re.compile(r'[\w.+-]+@[\w-]+(\.[\w-]+)+')
HASH = re.compile(r'\b[0-9a-f]{7,40}\b')
TRAILER = re.compile(r'(?im)^(co-authored-by|signed-off-by|reviewed-by|reported-by|acked-by|tested-by):.*$')


class Refused(Exception):
    pass


def git(repo, *args, binary=False):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=not binary)
    if result.returncode != 0:
        message = result.stderr.decode(errors='replace') if binary else result.stderr
        raise Refused(f'git {args[0]} failed: {message.strip()}')
    return result.stdout


def sanitize(text):
    """Strip trailers, URLs, emails, secrets, long tokens and commit hashes from task text."""
    text = TRAILER.sub('', text)
    text = URL.sub('[link removed]', text)
    text = EMAIL.sub('[email removed]', text)
    text = SECRET.sub(lambda m: m.group(1) + ' [removed]', text)
    text = TOKEN_SHAPES.sub('[removed]', text)
    text = HASH.sub('[ref]', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def repo_slug(repo):
    return re.sub(r'[^a-z0-9]+', '-', Path(repo).name.lower()).strip('-') or 'repo'


def default_out(repo, case_id):
    return ROOT / 'repo' / '.evals' / repo_slug(repo) / case_id


def inside(path, folder):
    try:
        path.relative_to(folder)
        return True
    except ValueError:
        return False


def pr_text(repo, number):
    result = subprocess.run(['gh', 'pr', 'view', str(number), '--json', 'title,body'], cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        raise Refused(f'gh pr view failed: {result.stderr.strip()}')
    data = json.loads(result.stdout)
    return f"{data.get('title', '')}\n\n{data.get('body', '')}"


def changed_tests(repo, commit, extra_patterns):
    """(status, path) for test files the commit added or modified; deleted tests are not part of the key."""
    out = git(repo, 'diff-tree', '-r', '--no-commit-id', '--name-status', '--no-renames', '-z', commit)
    parts = [p for p in out.split('\0') if p]
    extra = [re.compile(p) for p in extra_patterns]
    found = []
    for status, path in zip(parts[0::2], parts[1::2]):
        if status in {'A', 'M'} and (TEST_PATH.search(path) or any(p.search(path) for p in extra)):
            found.append((status, path))
    return found


def harvest(repo, commit, out, checks, case_id=None, pr=None, test_patterns=(), max_turns=20, holdout=False):
    repo = Path(git(repo, 'rev-parse', '--show-toplevel').strip()).resolve()
    if not checks:
        raise Refused('at least one --check command is required')
    full = git(repo, 'rev-parse', '--verify', f'{commit}^{{commit}}').strip()
    parents = git(repo, 'rev-list', '--parents', '-n', '1', full).split()[1:]
    if len(parents) != 1:
        raise Refused('the fix commit must have exactly one parent (a squash or plain commit, not a merge or root)')
    base = parents[0]
    case_id = case_id or f'{repo_slug(repo)}-{full[:8]}'
    if not re.fullmatch('[a-z0-9-]+', case_id):
        raise Refused('case id may use lowercase letters, digits and hyphens only')
    destination = Path(out).expanduser() if out else default_out(repo, case_id)
    destination = destination.resolve() if destination.exists() else destination.parent.resolve() / destination.name
    if inside(destination, repo):
        raise Refused(f'refusing to write the case inside the repository ({destination}); an agent working in the '
                      'project could find it. Use the workspace repo/.evals folder or another path outside the clone')
    if destination.exists():
        raise Refused(f'output already exists: {destination}')
    tests = changed_tests(repo, full, test_patterns)
    if not tests:
        raise Refused('the fix changed no test files, so there is no key; pick a commit that adds or changes tests')
    message = pr_text(repo, pr) if pr else git(repo, 'log', '-1', '--format=%B', full)
    task = sanitize(message)
    if not task:
        raise Refused('the commit message is empty after cleaning')
    existing = set(git(repo, 'ls-tree', '-r', '--name-only', '-z', base).split('\0'))
    protected = sorted(path for _, path in tests if path in existing)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='orbyn-harvest-', dir=destination.parent))
    try:
        fixture = staging / 'fixture'
        fixture.mkdir()
        archive = subprocess.Popen(['git', '-C', str(repo), 'archive', '--format=tar', base], stdout=subprocess.PIPE)
        unpack = subprocess.run(['tar', '-x', '-C', str(fixture)], stdin=archive.stdout, capture_output=True)
        archive.stdout.close()
        if archive.wait() != 0 or unpack.returncode != 0:
            raise Refused('could not export the base tree')
        for status, path in tests:
            blob = subprocess.run(['git', '-C', str(repo), 'show', f'{full}:{path}'], capture_output=True)
            if blob.returncode != 0:
                raise Refused(f'cannot read {path} at the fix commit')
            target = staging / 'key/hidden' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob.stdout)
        (staging / 'key/key.json').write_text(json.dumps({
            'schema_version': 1, 'task': case_id, 'checks': list(checks), 'protected': protected, 'expect_files': [],
            'hidden': 'hidden'}, indent=2) + '\n', encoding='utf-8')
        (staging / 'key/harvest.json').write_text(json.dumps({
            'source': 'pr' if pr else 'commit', 'base': base, 'fix': full, 'tests': [p for _, p in tests],
            'note': 'private provenance; never shown to the agent'}, indent=2) + '\n', encoding='utf-8')
        prompt = ('Make the change described below in this repository. Do not push, merge or publish anything.\n\n' + task)
        (staging / 'case.json').write_text(json.dumps({
            'id': case_id, 'title': task.splitlines()[0][:80], 'kind': 'outcome', 'prompt': prompt, 'expected_skill': None,
            'forbidden_actions': ['edit_protected', 'push', 'merge', 'network'], 'max_turns': max_turns, 'holdout': holdout,
            'tier_hints': {'claude': 'sonnet', 'codex': 'terra'}}, indent=2) + '\n', encoding='utf-8')
        shutil.move(str(staging), str(destination))
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return {'case': str(destination), 'id': case_id, 'base': base, 'protected': protected,
            'hidden_tests': [p for _, p in tests], 'checks': list(checks)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--commit', required=True, help='the merged fix commit (single parent)')
    parser.add_argument('--out', type=Path, help='case folder; default repo/.evals/<repo slug>/<id>/ in this workspace')
    parser.add_argument('--check', action='append', default=[], help='command that must pass on the fixed tree (repeat)')
    parser.add_argument('--id')
    parser.add_argument('--pr', type=int, help='take the task text from this PR through gh instead of the commit message')
    parser.add_argument('--test-pattern', action='append', default=[], help='extra regex for test file paths')
    parser.add_argument('--max-turns', type=int, default=20)
    parser.add_argument('--holdout', action='store_true')
    args = parser.parse_args(argv)
    try:
        info = harvest(args.repo, args.commit, args.out, args.check, args.id, args.pr, args.test_pattern,
                       args.max_turns, args.holdout)
    except (Refused, OSError, ValueError) as error:
        print(f'harvest: {error}', file=sys.stderr)
        return 2
    print(json.dumps(info, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
