#!/usr/bin/env python3
"""Library-only skill asset inventory. No target installation or synchronization."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

REPOSITORY = 'https://github.com/kinqsradio/orbyn-fullstack-skills'
MANIFEST = 'distribution/manifest.json'
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
EXTENSIONS = {'.md', '.json', '.py', '.sh', '.cjs', '.mjs', '.html', '.css', '.txt', '.yaml', '.yml', '.tla', '.cfg'}
PINNED_SUPPORT_EXTENSIONS = {'.ts', '.tsx', '.css', '.png'}



def pinned_support_asset(path, root):
    """Extra types must be declared in a canonical owner offline snapshot."""
    if path.suffix not in PINNED_SUPPORT_EXTENSIONS:
        return False
    parts = path.relative_to(root).parts
    if (len(parts) < 6 or parts[0] != 'skills'
            or not NAME.fullmatch(parts[1]) or parts[2:4] != ('references', 'upstream')
            or not NAME.fullmatch(parts[4])):
        return False
    catalog = load(root/'skills/catalog.json')
    if parts[1] not in {item['name'] for item in catalog['skills']}:
        return False
    snapshot = root.joinpath(*parts[:5])/'snapshot.json'
    return (snapshot.is_file()
            and '/'.join(parts[5:]) in load(snapshot).get('files', {}))


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def control_path(root, relative):
    if relative not in {MANIFEST}:
        raise ValueError('Unknown control file')
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f'Symlink in control path: {relative}')
    return root / relative


def safe_path(root, relative):
    """Reject escape paths and symlink parents before either reads or writes."""
    parts = PurePosixPath(relative).parts
    if (not isinstance(relative, str) or '\\' in relative or not parts
            or PurePosixPath(relative).is_absolute() or '..' in parts
            or any(part.startswith('.') for part in parts)):
        raise ValueError(f'Unsafe managed path: {relative}')
    if not (relative in {'skills/catalog.json', 'skills/README.md'}
            or (len(parts) >= 3 and parts[0] == 'skills' and NAME.fullmatch(parts[1]))):
        raise ValueError(f'Path outside skills allowlist: {relative}')
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f'Symlink in managed path: {relative}')
    return root / relative


def inventory(root):
    catalog = load(safe_path(root, 'skills/catalog.json'))
    names = [entry['name'] for entry in catalog['skills']]
    if len(names) != len(set(names)) or any(not NAME.fullmatch(name) for name in names):
        raise ValueError('Invalid or duplicate catalog name')
    actual = {p.parent.name for p in (root / 'skills').glob('*/SKILL.md')}
    if set(names) != actual:
        raise ValueError('Catalog and skill folders differ')
    paths = ['skills/catalog.json', 'skills/README.md']
    for name in sorted(names):
        base = safe_path(root, f'skills/{name}/SKILL.md').parent
        for path in sorted(base.rglob('*')):
            relative = path.relative_to(root).as_posix()
            if '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            safe_path(root, relative)
            if path.is_dir():
                continue
            if path.name != 'LICENSE' and path.suffix not in EXTENSIONS and not pinned_support_asset(path, root):
                raise ValueError(f'Unexpected skill asset type: {relative}')
            if path.stat().st_size > 1024 * 1024:
                raise ValueError(f'Skill asset exceeds 1 MiB: {relative}')
            paths.append(relative)
    return {p: hashlib.sha256(safe_path(root, p).read_bytes()).hexdigest() for p in sorted(paths)}


def validate_map(files):
    if not isinstance(files, dict) or not files:
        raise ValueError('Missing managed file hashes')
    for path, digest in files.items():
        safe_path(Path('/__skills_manifest__'), path)
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError(f'Invalid digest for {path}')


def manifest(root):
    data = load(control_path(root, MANIFEST))
    if data.get('schema_version') != 1 or data.get('repository') != REPOSITORY:
        raise ValueError('Unsupported manifest or repository')
    validate_map(data.get('files'))
    if data['files'] != inventory(root):
        raise ValueError('Manifest differs from files; regenerate and review it')
    return data['files']


def run(command, root, write=False):
    if command != 'manifest':
        raise ValueError('Only library manifest validation is supported; use nested workspaces')
    root = root.resolve()
    value = {'schema_version': 1, 'repository': REPOSITORY, 'files': inventory(root)}
    if write:
        save(control_path(root, MANIFEST), value)
    elif load(control_path(root, MANIFEST)) != value:
        raise ValueError('Manifest is stale')
    print(f'Library inventory matches {len(value["files"])} skill assets.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    try:
        run('manifest', args.root, args.write)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Library inventory stopped: {error}\n')


if __name__ == '__main__':
    main()
