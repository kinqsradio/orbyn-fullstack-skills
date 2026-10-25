#!/usr/bin/env python3
"""Internal library discovery generation; not a target installer."""
import os
from pathlib import Path
import re

NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


def retirements(catalog):
    """Only explicit one-step retirements into a current canonical owner."""
    retired = catalog.get('retired_skills', {})
    names = {entry['name'] for entry in catalog['skills']}
    if not isinstance(retired, dict):
        raise ValueError('Invalid retired skill map')
    for old, replacement in retired.items():
        if (not isinstance(old, str) or not NAME.fullmatch(old)
                or not isinstance(replacement, str) or replacement not in names
                or old in names or len(old) >= 64):
            raise ValueError('Retired skills must map distinct old names to current owners')
    return retired


def plan_retired_links(project, source_root, retired, sources, hosts):
    """Remove only known links into this same source tree; never delete content."""
    pending = {}
    for host in hosts:
        base = project/host/'skills'
        for parent in [project/host, base]:
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ValueError(f'Refusing a non-directory or symlinked host path: {parent}')
        for old, replacement in retired.items():
            if replacement not in sources:
                continue  # A smaller unrelated selection never uninstalls old skills.
            link = base/old
            target = source_root/'skills'/old
            if link.is_symlink() and link.resolve() == target.resolve():
                if (target/'SKILL.md').exists() or (target/'SKILL.md').is_symlink():
                    raise ValueError(f'Retired skill still has an active source: {old}')
                pending[link] = target.resolve()
    return pending


def remove_retired_links(pending):
    for link, target in pending.items():
        if not link.is_symlink() or link.resolve() != target:
            raise ValueError(f'Retired discovery entry changed after preflight; preserved: {link}')
    for link in pending:
        link.unlink()  # Only preflighted symlinks; never their target directories.


def plan_links(project, sources, hosts, require_existing=False):
    """Preflight both hosts before returning any writes; preserve unrelated entries."""
    pending = []
    for host in hosts:
        base = project / host / 'skills'
        for parent in [project / host, base]:
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ValueError(f'Refusing a non-directory or symlinked host path: {parent}')
        for name, target in sorted(sources.items()):
            link = base / name
            if not (target / 'SKILL.md').is_file():
                raise ValueError(f'Missing skill source: {name}')
            if link.exists() or link.is_symlink():
                if not link.is_symlink() or link.resolve() != target.resolve():
                    raise ValueError(f'Conflicting discovery entry: {link}')
            elif require_existing:
                raise ValueError(f'Missing project discovery link: {link}')
            else:
                pending.append((link, target))
    return pending


def write_links(pending):
    """Undo this batch's links on ordinary errors; never remove a replacement writer."""
    created = []
    try:
        for link, target in pending:
            for parent in [link.parent.parent, link.parent]:
                if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                    raise ValueError(f'Host parent changed after preflight: {parent}')
            link.parent.mkdir(parents=True, exist_ok=True)
            relative = os.path.relpath(target, link.parent)
            link.symlink_to(relative, target_is_directory=True)
            identity = link.lstat()
            created.append((link, relative, identity.st_dev, identity.st_ino))
    except Exception as error:
        cleanup_errors = []
        preserved = []
        for link, relative, device, inode in reversed(created):
            try:
                identity = link.lstat()
                if (link.is_symlink() and (identity.st_dev, identity.st_ino) == (device, inode)
                        and os.readlink(link) == relative):
                    link.unlink()
                else:
                    preserved.append(str(link))
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                cleanup_errors.append(f'{link}: {cleanup_error}')
        if cleanup_errors:
            raise RuntimeError(f'Registration failed: {error}; rollback incomplete; inspect before retry: '
                               + '; '.join(cleanup_errors) + '; preserved changed entries: '
                               + ', '.join(preserved)) from error
        if preserved:
            raise RuntimeError(f'Registration failed: {error}; preserved changed entries: '
                               + ', '.join(preserved) + '; inspect before retry') from error
        raise
