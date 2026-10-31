"""Verify prepared local speech resources before importing or loading models."""
from pathlib import Path, PurePosixPath
import re
from audio_tools import digest, read_json


def verify_profile(path):
    path = Path(path).resolve(strict=True)
    profile = read_json(path)
    if set(profile) != {'version', 'language', 'models', 'nltk', 'limits'} or profile['version'] != 1 or not re.fullmatch('[a-z]{2,3}', profile['language']):
        raise ValueError('Invalid prepared speech profile')
    if set(profile['models']) != {'asr', 'alignment'}:
        raise ValueError('Both explicitly prepared model roles are required')
    roots = {}
    for name, record in [*profile['models'].items(), ('nltk', profile['nltk'])]:
        folder_name = record.get('path')
        if not isinstance(folder_name, str) or not re.fullmatch('[a-z][a-z0-9-]*', folder_name):
            raise ValueError('Model directory must be an owned relative folder')
        folder = path.parent / folder_name
        if folder.is_symlink() or folder.resolve() != folder or not folder.is_dir() or not re.fullmatch('[a-f0-9]{40}', record.get('revision', '')):
            raise ValueError('Invalid model location/revision')
        files = record.get('files')
        if not isinstance(files, dict) or not 1 <= len(files) <= 1000:
            raise ValueError('Model closure budget')
        for relative, expected in files.items():
            item = PurePosixPath(relative)
            if item.is_absolute() or '..' in item.parts or any(p.startswith('.') for p in item.parts) or item.suffix in {'.py', '.so', '.dylib', '.dll'} or not re.fullmatch('[a-f0-9]{64}', expected):
                raise ValueError('Unsafe model data file')
            target = folder / item
            if target.resolve() != target or not target.is_file() or digest(target) != expected:
                raise ValueError('Prepared model bytes changed: ' + relative)
        # from_pretrained can consume neighboring configuration/weights: reject extras.
        actual = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()}
        if actual != set(files):
            raise ValueError('Prepared model closure contains unrecorded files')
        roots[name] = folder
    return profile, roots
