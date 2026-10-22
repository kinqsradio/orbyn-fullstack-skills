#!/usr/bin/env python3
"""Install library discovery links without changing project policy or models."""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / 'skills/orbyn-setup/assets/presets.json'


def selection(selected=(), presets=(), all_skills=False):
    catalog = json.loads((ROOT / 'skills/catalog.json').read_text())
    names = {entry['name'] for entry in catalog['skills']}
    config = json.loads(PRESETS.read_text())
    if config.get('schema_version') != 1 or config.get('default') not in config.get('presets', {}):
        raise ValueError('Invalid preset configuration')
    for name, preset in config['presets'].items():
        entries = preset['skills']
        if not entries or len(entries) != len(set(entries)) or set(entries) - names:
            raise ValueError(f'Invalid skill selection in preset: {name}')
    if all_skills and (selected or presets):
        raise ValueError('--all cannot be combined with --skill or --preset')
    if all_skills:
        return names
    chosen = list(presets) if presets or selected else [config['default']]
    wanted = set(selected)
    for preset in chosen:
        if preset not in config['presets']:
            raise ValueError(f'Unknown preset: {preset}')
        wanted.update(config['presets'][preset]['skills'])
    if wanted - names:
        raise ValueError('Unknown skills: ' + ', '.join(sorted(wanted - names)))
    return wanted


def install(project, host, selected=(), presets=(), all_skills=False, dry_run=False):
    project = project.resolve(strict=True)
    if not project.is_dir():
        raise ValueError('Project must be an existing directory')
    if host not in {'both', 'codex', 'claude'}:
        raise ValueError('Unknown host')
    wanted = selection(selected, presets, all_skills)
    hosts = ['.agents', '.claude'] if host == 'both' else ['.agents' if host == 'codex' else '.claude']
    pending = []
    for folder in hosts:
        base = project / folder / 'skills'
        for parent in [project / folder, base]:
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ValueError(f'Refusing a non-directory or symlinked host path: {parent}')
        for name in sorted(wanted):
            link, target = base / name, ROOT / 'skills' / name
            if not (target / 'SKILL.md').is_file():
                raise ValueError(f'Missing skill source: {name}')
            if link.exists() or link.is_symlink():
                if not link.is_symlink() or link.resolve() != target.resolve():
                    raise ValueError(f'Conflicting discovery entry: {link}')
            else:
                pending.append((link, target))
    if not dry_run:
        for link, target in pending:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(os.path.relpath(target, link.parent), target_is_directory=True)
    return len(pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--host', choices=['codex', 'claude', 'both'], default='both')
    parser.add_argument('--skill', action='append', default=[])
    parser.add_argument('--preset', action='append', default=[])
    parser.add_argument('--all', action='store_true', help='explicitly register every skill')
    parser.add_argument('--list-presets', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        if args.list_presets:
            selection()  # Validate before displaying.
            config = json.loads(PRESETS.read_text())
            for name, preset in config['presets'].items():
                print(f'{name}: {len(preset["skills"])} skills — {preset["description"]}')
            return
        if args.project is None:
            parser.error('--project is required unless --list-presets is used')
        count = install(args.project, args.host, args.skill, args.preset, args.all, args.dry_run)
        verb = 'Would create' if args.dry_run else 'Created'
        print(f'{verb} {count} discovery links; existing selections and project settings preserved.')
    except (OSError, ValueError) as error:
        parser.exit(1, f'Install stopped: {error}\n')


if __name__ == '__main__':
    main()
