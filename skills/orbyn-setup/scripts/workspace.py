#!/usr/bin/env python3
"""Prepare/check a nested workspace without installing or modifying target files."""
import argparse
import json
import os
from pathlib import Path
import subprocess

INSTRUCTIONS = ('AGENTS.md', 'AGENT.md', 'CLAUDE.md', '.cursorrules', 'codex.md',
                'CONTRIBUTING.md', 'SECURITY.md')
HOSTS = ('.agents', '.claude', '.cursor')


def git(root, *args):
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(root), *args], capture_output=True, text=True,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Git inspection failed')
    return result.stdout.strip()


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


def prepare(library):
    root = library_root(library)
    (root/'repo').mkdir(exist_ok=True)
    library_root(root)  # Recheck before reporting success if a concurrent writer changed the boundary.
    return {'library': str(root), 'workspace': str(root/'repo'),
            'target_files_changed': False, 'host_discovery': 'not_observed'}


def check(library, target, in_place=False):
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
            'target_files_changed': False, 'host_discovery': 'not_observed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'check'])
    parser.add_argument('--library', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--target', type=Path)
    parser.add_argument('--in-place', action='store_true',
                        help='check a registered target that stays outside the library')
    args = parser.parse_args()
    try:
        if args.command == 'check' and args.target is None:
            parser.error('--target is required for check')
        result = prepare(args.library) if args.command == 'prepare' else check(args.library, args.target, args.in_place)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'Workspace stopped: {error}\n')


if __name__ == '__main__':
    main()
