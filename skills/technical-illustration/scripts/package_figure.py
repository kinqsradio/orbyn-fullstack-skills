#!/usr/bin/env python3
"""Copy explicitly selected drawing support into a fresh authorized artifact directory.

No shared skills, account data, packages or user model files are installed/copied.
The caller resolves target instructions, authority and artifact ownership first.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

SUPPORT = Path(__file__).resolve().parents[1] / 'references/upstream/anatomy'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(destination, mode='core', inputs=None):
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination already exists; preserve it and choose a fresh artifact directory')
    if not destination.parent.is_dir() or any(p.is_symlink() for p in [destination.parent, *destination.parents]):
        raise ValueError('Destination needs an existing real parent without symlink traversal')
    selection = json.loads((SUPPORT / 'source-manifest.json').read_text())
    snapshot = json.loads((SUPPORT / 'snapshot.json').read_text())
    names = selection['runtime_modes'][mode]
    files = {}
    for name in names:
        path = SUPPORT / name
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe selected support path')
        relative = Path(name)
        if any((SUPPORT / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError('Selected support must not traverse a symlink')
        if not path.is_file() or digest(path) != snapshot['files'][name]['sha256']:
            raise ValueError('Selected support differs from the maintained snapshot: ' + name)
        files[name] = digest(path)
    declared_inputs = {}
    for label, path in (inputs or {}).items():
        if not label or not all(c.isalnum() or c in '-_.' for c in label):
            raise ValueError('Input label must be a public logical name without paths')
        path = Path(path)
        if not path.is_file() or path.is_symlink():
            raise ValueError('Explicit model/style/asset input must be a regular file')
        declared_inputs[label] = digest(path)
    # No existing directory is ever replaced, including a destination created during preflight.
    destination.mkdir(exist_ok=False)
    record = {'status': 'preparing', 'mode': mode, 'source_revision': selection['revision'],
              'maintained_files': files, 'declared_model_style_asset_inputs': declared_inputs,
              'limits': 'Hashes cover selected bytes only; no renderer/platform/model behavior or unlisted inputs qualified.'}
    receipt = destination / 'illustration-support.json'
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    for name in names:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SUPPORT / name, target)
        if digest(target) != files[name]:
            raise ValueError('Copied byte verification failed; owned partial destination retained')
    record['status'] = 'complete selected-byte copy'
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--mode', choices=['core', 'react', 'print', 'webgl', '3d', 'full'], default='core')
    parser.add_argument('--input', action='append', default=[], metavar='PUBLIC_LABEL=PATH')
    args = parser.parse_args()
    inputs = {}
    for item in args.input:
        if '=' not in item:
            parser.error('--input requires PUBLIC_LABEL=PATH')
        label, path = item.split('=', 1)
        if label in inputs:
            parser.error('Duplicate input label')
        inputs[label] = path
    try:
        print(json.dumps(package(args.destination, args.mode, inputs)))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, str(error) + '\n')
