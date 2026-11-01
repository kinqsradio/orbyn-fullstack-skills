#!/usr/bin/env python3
"""Report which worktrees can retire, and retire one exact path without losing ignored files.

`inventory` reads Git, `gh` and `lsof` and changes nothing. `retire` rechecks one
path, moves its ignored files to an archive, sends named caches to the system
trash and calls `git worktree remove` without force. Standard library only.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HOST_MANAGED = ('.claude/worktrees/', '.codex/worktrees/')
SKIP_IGNORED = ('__pycache__', '.DS_Store')


class Refused(Exception):
    pass


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)


def git(path, *args):
    return run('git', '-C', str(path), *args)


def worktrees(repo):
    """Registered trees in Git's order; the first is the primary checkout."""
    result = git(repo, 'worktree', 'list', '--porcelain')
    if result.returncode:
        raise Refused(result.stderr.strip() or f'Not a Git repository: {repo}')
    trees, current = [], {}
    for line in result.stdout.split('\n'):
        if not line:
            if current:
                trees.append(current)
            current = {}
            continue
        key, _, value = line.partition(' ')
        current[key] = value
    return trees


def open_paths():
    """Every path a process holds, or None when lsof cannot answer."""
    if not shutil.which('lsof'):
        return None
    # lsof exits 1 for some unreadable processes, so judge it by its output.
    lines = run('lsof', '-Fn').stdout.split('\n')
    return {line[1:] for line in lines if line.startswith('n/')} or None


def size_kb(path):
    result = run('du', '-sk', str(path))
    return int(result.stdout.split()[0]) if result.returncode == 0 and result.stdout else 0


def ignored(path):
    lines = git(path, 'status', '--porcelain', '--ignored').stdout.split('\n')
    entries = (line[3:].strip('"').rstrip('/') for line in lines if line.startswith('!! '))
    return [e for e in entries if not any(part in SKIP_IGNORED for part in e.split('/'))]


def landed(path, head, branch, base):
    """Prove HEAD reached the base by ancestry or by an exact merged PR head."""
    if git(path, 'merge-base', '--is-ancestor', head, base).returncode == 0:
        return f'ancestor of {base}'
    if not branch or not shutil.which('gh'):
        return None
    result = run('gh', 'pr', 'list', '--head', branch, '--state', 'merged',
                 '--json', 'number,headRefOid', cwd=path)
    if result.returncode:
        return None
    # A squash leaves no ancestry, and a later local commit must not pass as landed.
    match = next((pr for pr in json.loads(result.stdout) if pr['headRefOid'] == head), None)
    return f"merged PR #{match['number']}" if match else None


def assess(tree, primary, base, held):
    path = tree['worktree']
    branch = tree.get('branch', '').removeprefix('refs/heads/')
    head = tree.get('HEAD', '')
    item = {'path': path, 'branch': branch or None, 'head': head}
    if path == primary:
        return {**item, 'disposition': 'keep', 'reason': 'primary checkout'}
    if not os.path.isdir(path):
        return {**item, 'disposition': 'hold', 'reason': 'registered path is missing; inspect before pruning'}
    item.update(size_kb=size_kb(path), ignored=ignored(path), ignored_kb=0)
    item['ignored_kb'] = sum(size_kb(Path(path)/entry) for entry in item['ignored'])
    prefix = path + os.sep
    reasons = []
    if any(mark in prefix for mark in HOST_MANAGED):
        reasons.append("host-managed; use the host's own cleanup")
    if 'locked' in tree:
        reasons.append('locked')
    if git(path, 'status', '--porcelain').stdout.strip():
        reasons.append('uncommitted or untracked changes')
    if held is None:
        reasons.append('cannot check open files')
    elif any(name == path or name.startswith(prefix) for name in held):
        reasons.append('a process has files open here')
    proof = landed(path, head, branch, base)
    if proof:
        item['landed'] = proof
    else:
        reasons.append('landing not proven')
    return {**item, 'disposition': 'hold' if reasons else 'ready', 'reason': '; '.join(reasons) or proof}


def inventory(repo, base):
    trees = worktrees(repo)
    held = open_paths()
    return [assess(tree, trees[0]['worktree'], base, held) for tree in trees]


def trash(paths):
    """Send caches to the system trash, so a wrong call can still be undone."""
    command = next(([tool, *args] for tool, args in (('trash', ()), ('gio', ('trash',)))
                    if shutil.which(tool)), None)
    if paths and not command:
        raise Refused('No system trash command; move these caches yourself or leave them in the archive')
    for path in paths:
        if run(*command, str(path)).returncode or path.exists():
            raise Refused(f'Could not trash {path}; the worktree is unchanged past this point')


def retire(repo, target, base, archive, drop=()):
    target = str(Path(target).resolve())
    trees = worktrees(repo)
    tree = next((t for t in trees if str(Path(t['worktree']).resolve()) == target), None)
    if tree is None:
        raise Refused(f'Not a registered worktree: {target}')
    item = assess(tree, str(Path(trees[0]['worktree']).resolve()), base, open_paths())
    if item['disposition'] != 'ready':
        raise Refused(f"{target}: {item['reason']}")
    root = Path(target)
    keep = (Path(archive).resolve()/root.name)
    if keep.is_relative_to(root):
        raise Refused('Archive must sit outside the worktree being retired')
    if keep.exists():
        raise Refused(f'Archive already exists: {keep}')
    drops = [(root/rel).resolve() for rel in drop]
    entries = [root/entry for entry in item['ignored']]
    for path in drops:
        # A drop must be ignored output; tracked source never goes to the trash.
        if not path.is_relative_to(root) or not path.exists() or not any(
                path == entry or path.is_relative_to(entry) for entry in entries):
            raise Refused(f'Drop must be an existing ignored path in the worktree: {path}')
    trash(drops)
    moved = []
    for entry in ignored(root):
        destination = keep/entry
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root/entry), str(destination))
        moved.append(entry)
    keep.mkdir(parents=True, exist_ok=True)
    record = {**{k: item.get(k) for k in ('path', 'branch', 'head', 'landed')}, 'archived': moved,
              'trashed': [str(path.relative_to(root)) for path in drops],
              'retired_on': datetime.date.today().isoformat()}
    (keep/'RETIRED.json').write_text(json.dumps(record, indent=2) + '\n')
    # Plain removal refuses anything that changed since the check above; never force it.
    removed = git(repo, 'worktree', 'remove', target)
    if removed.returncode:
        raise Refused(f'git worktree remove refused, tree retained: {removed.stderr.strip()}')
    return {**record, 'archive': str(keep)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--base', default='origin/main')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('inventory', help='Report each worktree; changes nothing')
    retiring = commands.add_parser('retire', help='Archive ignored files and remove one exact worktree')
    retiring.add_argument('path')
    retiring.add_argument('--archive', required=True, help='Directory outside the worktree for its ignored files')
    retiring.add_argument('--drop', action='append', default=[], help='Rebuildable ignored path to trash instead')
    args = parser.parse_args(argv)
    try:
        if args.command == 'inventory':
            result = inventory(args.repo, args.base)
        else:
            result = retire(args.repo, args.path, args.base, args.archive, args.drop)
    except (Refused, OSError, subprocess.SubprocessError) as error:
        print(f'Refused: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
