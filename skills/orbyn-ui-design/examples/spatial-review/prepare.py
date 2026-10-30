"""Prepare a durable spatial review in a fresh consuming repo directory, no installs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
SOURCE = Path(__file__).resolve().parent
SKILLS = SOURCE.parents[2]
FILES = ['index.html', 'style.css', 'engine.mjs', 'model.mjs', 'build.mjs', 'model.test.mjs', 'timeline.mjs', 'review-model.mjs', 'review.mjs', 'review.css', 'serve.py', 'reconcile.mjs', 'README.md']


def prepare(destination, node='node'):
    root = Path(destination).absolute()
    if root.exists() or root.is_symlink() or not root.parent.is_dir() or any(p.is_symlink() for p in root.parents): raise ValueError('Fresh owned directory and real existing parent required')
    spec = importlib.util.spec_from_file_location('figure_package', SKILLS / 'technical-illustration/scripts/package_figure.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    root.mkdir()
    for name in FILES: shutil.copyfile(SOURCE / name, root / name)
    module.package(root / 'renderer', mode='3d')
    shared = SOURCE.parent / 'review-workspace'
    shutil.copyfile(shared / 'serve.py', root / 'review-bridge.py')
    shutil.copyfile(shared / 'model.mjs', root / 'review-core.mjs')
    subprocess.run([node, str(root / 'build.mjs')], check=True, cwd=root, capture_output=True, text=True)
    (root / 'design.md').write_text('# V12 educational review\n\nPreserve these authored model limits. Ideal rigid links; no production simulation.\n')
    targets = [{'id': 'part/' + p['name'], 'kind': 'part'} for p in json.loads((root / 'engine-data.json').read_text())['parts']]
    targets += [{'id': 'control/' + n, 'kind': 'control'} for n in ['play', 'step', 'reset', 'crank', 'orbit', 'speed', 'guides', 'rods', 'story-time', 'story-scenario', 'story-play']]
    targets += [{'id': 'control/cylinder-' + bank + str(i), 'kind': 'control'} for bank in ['A', 'B'] for i in range(1, 7)]
    targets += [{'id': 'surface/' + n, 'kind': 'component'} for n in ['story-title', 'story-caption', 'story-data', 'story-card', 'film-stage', 'film-title', 'film-caption']]
    names = sorted(set(FILES + ['review-bridge.py', 'review-core.mjs', 'engine.svg', 'engine-data.json', 'turn.css', 'static-files.json', 'renderer/illustration-support.json'] + ['renderer/' + n for n in json.loads((root / 'renderer/illustration-support.json').read_text())['maintained_files']]))
    names += ['manifest.json']; (root / 'static-files.json').write_text(json.dumps(names, indent=2) + '\n')
    assets = {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in names if n != 'manifest.json'}
    prototype = {'id': 'v12-scene', 'version': 1, 'candidate': 'spatial-v1'}
    payload = {'prototype': prototype, 'targets': targets, 'assets': assets}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (root / 'manifest.json').write_text(json.dumps({**payload, 'prototype': {**prototype, 'fingerprint': fingerprint}}, indent=2) + '\n')
    return {'package': str(root), 'sourceFingerprint': fingerprint, 'modelRevision': assets['engine-data.json'], 'sourceFiles': len(assets), 'reviewSaved': False, 'limits': 'Prepared source, not browser or physical qualification; existing package never overwritten.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--destination', required=True); p.add_argument('--node', default='node'); a = p.parse_args()
    print(json.dumps(prepare(a.destination, a.node), indent=2))
