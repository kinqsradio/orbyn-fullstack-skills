#!/usr/bin/env python3
"""Freeze a task answer key and run it against a committed candidate from a clean copy.

`freeze` records the base commit, the commands that prove success and the sha256 of every protected file.
`--protect` paths are restored (the default): `check` puts their base version back in the clean export before the
commands run, so the candidate is judged by the original tests plus the key's checks, files it added stay, and a
change is reported as information (`protected_changed`). `--protect-strict` paths fail on any change.
`check` verifies the candidate descends from the base, applies those rules, then runs the key's commands in a
fresh `git archive` export. Commands come only from the key file the lead wrote. Keeping a key from a worker is a
policy, not a sandbox; the key is only as strong as its checks. Standard library only.

Exit codes for check: 0 every check passed, 1 any check failed, 2 the key or candidate is unusable.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

SCHEMA = 1
MODES = ('restore', 'strict')
TAIL = 2000


class Unusable(Exception):
    pass


def git(repo, *args, check=True, binary=False):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=not binary)
    if check and result.returncode != 0:
        message = result.stderr.decode(errors='replace') if binary else result.stderr
        raise Unusable(f'git {" ".join(args[:2])} failed: {message.strip()}')
    return result


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def inside(path, folder):
    try:
        path.relative_to(folder)
        return True
    except ValueError:
        return False


def files_at(repo, commit, spec):
    """Tracked file paths at `commit` under `spec` (a file or a directory)."""
    out = git(repo, 'ls-tree', '-r', '-z', '--name-only', commit, '--', spec).stdout
    return sorted(name for name in out.split('\0') if name)


def blob_hash(repo, commit, name):
    result = git(repo, 'cat-file', 'blob', f'{commit}:{name}', check=False, binary=True)
    return sha256(result.stdout) if result.returncode == 0 else None


def clean_spec(spec):
    path = Path(spec)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise Unusable(f'path must be relative to the repository root: {spec}')
    return path.as_posix()


# ---------------------------------------------------------------- freeze

def command_freeze(args):
    repo = Path(git(args.repo, 'rev-parse', '--show-toplevel').stdout.strip()).resolve()
    out = Path(args.out).expanduser()
    if out.exists() or out.is_symlink():
        raise Unusable(f'output already exists: {out}')
    parent = out.parent.resolve()
    if not parent.is_dir():
        raise Unusable(f'output folder does not exist: {parent}')
    target = parent / out.name
    if inside(target, repo):
        relative = target.relative_to(repo).as_posix()
        ignored = git(repo, 'check-ignore', '-q', '--', relative, check=False).returncode == 0
        tracked = git(repo, 'ls-files', '--error-unmatch', '--', relative, check=False).returncode == 0
        if tracked or not ignored:
            raise Unusable(f'refusing to write the key inside the repository tree ({relative}); '
                           'use a path outside the repository or an ignored one')
    base = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}').stdout.strip()
    if not args.check:
        raise Unusable('at least one --check command is required')
    protected, seen = [], set()
    for mode, specs in (('restore', args.protect), ('strict', args.protect_strict)):
        for spec in specs or []:
            spec = clean_spec(spec)
            if spec in seen:
                raise Unusable(f'protected path given twice: {spec}')
            seen.add(spec)
            names = files_at(repo, base, spec)
            if not names:
                raise Unusable(f'protected path is not tracked at the base commit: {spec}')
            if git(repo, 'status', '--porcelain', '--', spec).stdout.strip():
                raise Unusable(f'protected path has uncommitted changes; commit them first: {spec}')
            protected.append({'path': spec, 'mode': mode, 'files': {name: blob_hash(repo, base, name) for name in names}})
    expected = [clean_spec(name) for name in args.expect_file or []]
    key = {'schema_version': SCHEMA, 'task': args.task, 'repo': str(repo), 'base': base,
           'checks': list(args.check), 'protected': protected, 'expect_files': expected}
    with open(target, 'x', encoding='utf-8') as handle:
        handle.write(json.dumps(key, indent=2) + '\n')
    os.chmod(target, 0o600)
    print(json.dumps({'key': str(target), 'task': args.task, 'base': base, 'checks': len(args.check),
                      'protected_files': sum(len(p['files']) for p in protected)}))
    return 0


# ---------------------------------------------------------------- check

def load_key(path):
    try:
        key = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise Unusable(f'cannot read key: {error}')
    ok = (isinstance(key, dict) and key.get('schema_version') == SCHEMA
          and all(isinstance(key.get(f), str) and key[f] for f in ('task', 'repo', 'base'))
          and isinstance(key.get('checks'), list) and key['checks']
          and all(isinstance(c, str) and c.strip() for c in key['checks'])
          and isinstance(key.get('expect_files'), list) and all(isinstance(c, str) for c in key['expect_files'])
          and isinstance(key.get('protected'), list))
    if ok:
        for item in key['protected']:
            ok = ok and isinstance(item, dict) and isinstance(item.get('path'), str) \
                and isinstance(item.get('files'), dict) and all(isinstance(v, str) for v in item['files'].values()) \
                and item.get('mode', 'restore') in MODES  # A key written before modes existed restores.
    if not ok:
        raise Unusable('key is not a valid answer key (schema_version 1)')
    if not Path(key['repo']).is_dir():
        raise Unusable(f'key repository is missing: {key["repo"]}')
    return key


def resolve_candidate(key, candidate):
    repo = key['repo']
    result = git(repo, 'rev-parse', '--verify', '--quiet', f'{candidate}^{{commit}}', check=False)
    if result.returncode != 0:
        raise Unusable(f'candidate is not a commit in the repository: {candidate}')
    commit = result.stdout.strip()
    if git(repo, 'cat-file', '-e', f'{key["base"]}^{{commit}}', check=False).returncode != 0:
        raise Unusable('base commit is not in the repository')
    if git(repo, 'merge-base', '--is-ancestor', key['base'], commit, check=False).returncode != 0:
        raise Unusable('candidate does not descend from the base commit')
    return commit


def protected_changes(key, commit):
    """Protected files whose content differs, are missing, or were added under a protected folder.

    Each entry carries its `mode`; callers drop it before printing."""
    repo, changed = key['repo'], []
    for item in key['protected']:
        recorded, mode = item['files'], item.get('mode', 'restore')
        for name in files_at(repo, commit, item['path']):
            if name not in recorded:
                changed.append({'path': name, 'reason': 'added', 'mode': mode})
        for name, digest in recorded.items():
            now = blob_hash(repo, commit, name)
            if now is None:
                changed.append({'path': name, 'reason': 'missing', 'mode': mode})
            elif now != digest:
                changed.append({'path': name, 'reason': 'modified', 'mode': mode})
    return changed


def shown(changes):
    return [{'path': c['path'], 'reason': c['reason']} for c in changes]


def restore_base(key, source, changes):
    """Put the base version of every modified or missing restore-mode file back into the export."""
    names = sorted(c['path'] for c in changes if c['mode'] == 'restore' and c['reason'] in ('modified', 'missing'))
    if not names:
        return
    archive = subprocess.Popen(['git', '-C', str(key['repo']), 'archive', '--format=tar', key['base'], '--', *names],
                               stdout=subprocess.PIPE)
    unpack = subprocess.run(['tar', '-x', '-C', str(source)], stdin=archive.stdout, capture_output=True)
    archive.stdout.close()
    if archive.wait() != 0 or unpack.returncode != 0:
        raise Unusable('could not restore the protected files: ' + unpack.stderr.decode(errors='replace').strip())


def export(repo, commit, destination):
    """Unpack the committed tree with `git archive`; the working tree and index are never read."""
    destination.mkdir()
    archive = subprocess.Popen(['git', '-C', str(repo), 'archive', '--format=tar', commit], stdout=subprocess.PIPE)
    unpack = subprocess.run(['tar', '-x', '-C', str(destination)], stdin=archive.stdout, capture_output=True)
    archive.stdout.close()
    if archive.wait() != 0 or unpack.returncode != 0:
        raise Unusable('could not export the candidate tree: ' + unpack.stderr.decode(errors='replace').strip())


def minimal_env(home, tmp):
    return {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(home), 'TMPDIR': str(tmp),
            'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1', 'CI': '1'}


def run_command(command, cwd, env, timeout):
    started = time.monotonic()
    process = subprocess.Popen(command, shell=True, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    note = None
    try:
        output, _ = process.communicate(timeout=timeout)
        status, code = ('pass' if process.returncode == 0 else 'fail'), process.returncode
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        output, _ = process.communicate()
        status, code, note = 'fail', None, f'timed out after {timeout}s'
    entry = {'command': command, 'status': status, 'exit_code': code,
             'seconds': round(time.monotonic() - started, 2), 'output_tail': output.decode(errors='replace')[-TAIL:]}
    if note:
        entry['note'] = note
    return entry


def command_check(args):
    key = load_key(args.key)
    commit = resolve_candidate(key, args.candidate)
    report = {'task': key['task'], 'base': key['base'], 'candidate': commit,
              'protected': {'status': 'pass', 'changed': []}, 'protected_changed': [], 'checks': [], 'result': 'pass'}
    changes = protected_changes(key, commit)
    strict = [c for c in changes if c['mode'] == 'strict']
    report['protected_changed'] = shown(c for c in changes if c['mode'] == 'restore')
    if strict:
        report['protected'] = {'status': 'fail', 'changed': shown(strict)}
        report['result'] = 'fail'
        print(json.dumps(report, indent=2))
        return 1
    print('answer key commands (from the key file, run in a clean export):', file=sys.stderr)
    for command in key['checks']:
        print(f'  $ {command}', file=sys.stderr)
    root = Path(tempfile.mkdtemp(prefix='answer-key-'))
    try:
        source, home, tmp = root / 'src', root / 'home', root / 'tmp'
        home.mkdir()
        tmp.mkdir()
        export(key['repo'], commit, source)
        restore_base(key, source, changes)
        env = minimal_env(home, tmp)
        for name in key['expect_files']:
            present = (source / name).is_file()
            report['checks'].append({'command': f'expect-file {name}', 'status': 'pass' if present else 'fail',
                                     'exit_code': None, 'seconds': 0, 'output_tail': ''})
        for command in key['checks']:
            report['checks'].append(run_command(command, source, env, args.timeout))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if any(c['status'] != 'pass' for c in report['checks']):
        report['result'] = 'fail'
    print(json.dumps(report, indent=2))
    return 0 if report['result'] == 'pass' else 1


# ---------------------------------------------------------------- cli

def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    freeze = sub.add_parser('freeze', help='record the base commit, commands and protected file hashes')
    freeze.add_argument('--repo', required=True, help='the Git repository the task changes')
    freeze.add_argument('--task', required=True, help='a short task name')
    freeze.add_argument('--check', action='append', help='a shell command that must exit 0 (repeat for several)')
    freeze.add_argument('--protect', action='extend', nargs='+',
                        help='tracked file or folder that defines correctness; restored to its base version before the checks')
    freeze.add_argument('--protect-strict', action='extend', nargs='+',
                        help='like --protect, but any change fails; for tasks where editing it is the forbidden act')
    freeze.add_argument('--expect-file', action='extend', nargs='+', help='file that must exist at the candidate')
    freeze.add_argument('--out', required=True, help='key path outside the repository or in an ignored location')
    check = sub.add_parser('check', help='run the key against a committed candidate from a clean export')
    check.add_argument('--key', required=True)
    check.add_argument('--candidate', required=True, help='a commit that descends from the key base')
    check.add_argument('--timeout', type=int, default=600, help='seconds allowed per command (default 600)')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return command_freeze(args) if args.command == 'freeze' else command_check(args)
    except Unusable as error:
        print(f'answer_key: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
