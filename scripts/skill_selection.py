#!/usr/bin/env python3
"""Select reading groups in the library; never install into a target."""
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / 'skills/orbyn-setup/assets/presets.json'
DISCOVERY = runpy.run_path(str(ROOT / 'scripts/discovery_links.py'))


def selection(selected=(), presets=(), all_skills=False):
    catalog = json.loads((ROOT / 'skills/catalog.json').read_text())
    names = {entry['name'] for entry in catalog['skills']}
    retired = DISCOVERY['retirements'](catalog)
    selected = [retired.get(name, name) for name in selected]
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
