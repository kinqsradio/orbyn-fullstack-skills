#!/usr/bin/env python3
"""Keep logos out of a repository: refuse a folder Git would commit, and fail closed on doubt."""
import os
from pathlib import Path
import subprocess

PROBES = ('manifest.json', 'icon.svg', 'icon_dark.svg', 'icon.png', 'icon.webp', 'diagram.html', 'diagram.png', 'diagram-dark.png')


class NotIgnored(ValueError):
    """Git would commit this folder, or it cannot be shown otherwise."""


def git_root(folder):
    for at in (folder, *folder.parents):
        if (at/'.git').exists():
            return at
    return None


def require_ignored(folder):
    """Pass outside any repository, or when Git confirms every output name is ignored."""
    folder = Path(folder).resolve()
    existing = next(at for at in (folder, *folder.parents) if at.exists())
    if git_root(existing) is None:
        return
    env = {key: value for key, value in os.environ.items() if key not in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE')}
    probes = [str(folder/name) for name in PROBES]
    try:
        result = subprocess.run(['git', '-C', str(existing), 'check-ignore', '--no-index', '--stdin', '-z'],
                                input='\0'.join(probes), capture_output=True, text=True, env=env, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        raise NotIgnored(f'cannot confirm {folder} is ignored by Git: {error}') from error
    if result.returncode not in (0, 1):
        raise NotIgnored(f'cannot confirm {folder} is ignored by Git: {result.stderr.strip()}')
    ignored = set(filter(None, result.stdout.split('\0')))
    exposed = [probe for probe in probes if probe not in ignored]
    if exposed:
        raise NotIgnored(f'{folder} would be committed ({Path(exposed[0]).name}). Choose a git-ignored working folder for logos.')
