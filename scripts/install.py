#!/usr/bin/env python3
"""Install library discovery links without changing project policy or models."""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def install(project, host, selected):
    project = project.resolve(strict=True)
    if not project.is_dir():
        raise ValueError('Project must be an existing directory')
    catalog = json.loads((ROOT / 'skills/catalog.json').read_text())
    names = {entry['name'] for entry in catalog['skills']}
    wanted = set(selected) if selected else names
    if wanted - names:
        raise ValueError('Unknown skills: ' + ', '.join(sorted(wanted - names)))
    hosts = ['.agents', '.claude'] if host == 'both' else ['.agents' if host == 'codex' else '.claude']
    pending = []
    for folder in hosts:
        base = project / folder / 'skills'
        for parent in [project / folder, base]:
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ValueError(f'Refusing a non-directory or symlinked host path: {parent}')
        for name in sorted(wanted):
            link, target = base / name, ROOT / 'skills' / name
            if link.exists() or link.is_symlink():
                if not link.is_symlink() or link.resolve() != target.resolve():
                    raise ValueError(f'Conflicting discovery entry: {link}')
            else:
                pending.append((link, target))
    for link, target in pending:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(os.path.relpath(target, link.parent), target_is_directory=True)
    return len(pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--host', choices=['codex', 'claude', 'both'], default='both')
    parser.add_argument('--skill', action='append', default=[])
    args = parser.parse_args()
    try:
        print(f'Created {install(args.project, args.host, args.skill)} discovery links; no model/policy settings changed.')
    except (OSError, ValueError) as error:
        parser.exit(1, f'Install stopped: {error}\n')


if __name__ == '__main__':
    main()
