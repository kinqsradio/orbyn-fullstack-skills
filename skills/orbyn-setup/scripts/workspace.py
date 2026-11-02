#!/usr/bin/env python3
"""Prepare/check a nested workspace without installing or modifying target files."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

INSTRUCTIONS = ('AGENTS.md', 'AGENT.md', 'CLAUDE.md', '.cursorrules', 'codex.md',
                'CONTRIBUTING.md', 'SECURITY.md')
HOSTS = ('.agents', '.claude', '.cursor')
MEMORY_CLI = Path(__file__).resolve().parents[2]/'reflect/scripts/memory.py'
MEMORY_OFF = ('off', '0', 'false', 'no')


def git(root, *args):
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(root), *args], capture_output=True, text=True,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Git inspection failed')
    return result.stdout.rstrip('\n')  # A leading space is porcelain's unstaged status column.


def real_path(path):
    path = Path(path).absolute()
    for parent in (*reversed(path.parents), path):
        if parent.is_symlink():
            raise ValueError(f'Symlinked workspace path is not supported: {parent}')
    return path.resolve(strict=True)


def library_root(path):
    root = real_path(path)
    if Path(git(root, 'rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('Select the actual library Git root')
    if not (root/'skills/catalog.json').is_file() or not (root/'AGENTS.md').is_file():
        raise ValueError('Expected a complete skills library checkout')
    workspace = root/'repo'
    if workspace.is_symlink() or (workspace.exists() and not workspace.is_dir()):
        raise ValueError('repo/ must be a real directory')
    if git(root, 'ls-files', '-z', '--', 'repo'):
        raise ValueError('Nested repositories must not be tracked or staged in the library')
    probe = subprocess.run(['git', '-C', str(root), 'check-ignore', '--no-index',
                            '--quiet', '--', 'repo/__workspace_probe__/file'])
    if probe.returncode:
        raise ValueError('repo/ must be ignored by the library')
    return root


def memory_cli(*args):
    result = subprocess.run([sys.executable, str(MEMORY_CLI), *map(str, args)], capture_output=True, text=True)
    if result.returncode:
        try:
            raise ValueError(json.loads(result.stderr)['error'])
        except (json.JSONDecodeError, KeyError, TypeError):
            raise ValueError(result.stderr.strip() or 'Memory helper failed')
    return json.loads(result.stdout)['result']


def memory_setup(no_memory=False, project=None):
    """Turn shared memory on in manual mode unless opted out; never re-initialize or touch records."""
    if no_memory or os.environ.get('ORBYN_MEMORY', '').strip().lower() in MEMORY_OFF:
        return {'state': 'off', 'reason': '--no-memory' if no_memory else 'ORBYN_MEMORY=off',
                'note': 'Memory is off; nothing was created or read.'}
    try:
        where = memory_cli('where')
        report = {'state': 'on', 'mode': 'manual', 'root': where['root'], 'root_source': where['source'],
                  'initialized_now': False, 'scopes': []}
        if not where['initialized']:
            memory_cli('init', '--mode', 'manual')
            report['initialized_now'] = True
        for name, selector in (('personal', ['--personal']), ('project', ['--project', project] if project else None)):
            if selector:
                memory_cli(*selector, 'register')
                report['scopes'].append(name)
        return report
    except ValueError as error:
        state = 'off' if str(error) == 'Memory is off' else 'blocked'
        return {'state': state, 'reason': str(error),
                'note': 'Memory is off for this store.' if state == 'off' else 'Memory was not set up; the rest of setup is unaffected.'}


def prepare(library, no_memory=False):
    root = library_root(library)
    (root/'repo').mkdir(exist_ok=True)
    library_root(root)  # Recheck before reporting success if a concurrent writer changed the boundary.
    return {'library': str(root), 'workspace': str(root/'repo'),
            'memory': memory_setup(no_memory),
            'target_files_changed': False, 'host_discovery': 'not_observed'}


def check(library, target, in_place=False, no_memory=False):
    root = library_root(library)
    target = real_path(target)
    workspace = root/'repo'
    if in_place:
        if target.is_relative_to(root) or root.is_relative_to(target):
            raise ValueError('An in-place target must sit outside the library and must not contain it')
    elif target == workspace or not target.is_relative_to(workspace):
        raise ValueError('Target must be nested under this library repo/; preserve external checkouts until migration is authorized')
    if Path(git(target, 'rev-parse', '--show-toplevel')).resolve() != target:
        raise ValueError('Select the target Git root, not a subdirectory or ancestor repository')
    if not in_place:
        common = Path(git(target, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve()
        if not common.is_relative_to(workspace):
            raise ValueError('Target Git metadata belongs outside repo/; an external linked worktree is not a migrated primary clone')
        relative = target.relative_to(root).as_posix()
        ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '--no-index', '--quiet', '--', relative])
        if ignored.returncode:
            raise ValueError('Target is exposed by library ignore rules')
    # Inspect metadata only; never execute project hooks, setup or source code.
    documents = [name for name in INSTRUCTIONS if (target/name).is_file()]
    skill_names = {entry['name'] for entry in json.loads((root/'skills/catalog.json').read_text())['skills']}
    collisions = []
    for host in HOSTS:
        base = target/host/'skills'
        if base.is_dir():
            collisions.extend(f'{host}/skills/{name}' for name in sorted(skill_names)
                              if (base/name).exists() or (base/name).is_symlink())
    return {'library': str(root), 'library_revision': git(root, 'rev-parse', 'HEAD'),
            'library_status': git(root, 'status', '--porcelain'),
            'target': str(target), 'target_revision': git(target, 'rev-parse', 'HEAD'),
            'target_status': git(target, 'status', '--porcelain'),
            'target_instructions': documents,
            'target_skill_directories': [f'{host}/skills' for host in HOSTS if (target/host/'skills').is_dir()],
            'same_name_target_skills': collisions,
            'layout': 'in_place' if in_place else 'nested',
            'memory': memory_setup(no_memory, target),
            'target_files_changed': False, 'host_discovery': 'not_observed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'check'])
    parser.add_argument('--library', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--target', type=Path)
    parser.add_argument('--in-place', action='store_true',
                        help='check a registered target that stays outside the library')
    parser.add_argument('--no-memory', action='store_true',
                        help='skip shared memory setup (also ORBYN_MEMORY=off)')
    args = parser.parse_args()
    try:
        if args.command == 'check' and args.target is None:
            parser.error('--target is required for check')
        result = prepare(args.library, args.no_memory) if args.command == 'prepare' \
            else check(args.library, args.target, args.in_place, args.no_memory)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'Workspace stopped: {error}\n')


if __name__ == '__main__':
    main()
