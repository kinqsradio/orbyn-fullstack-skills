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
FILES = ['index.html', 'style.css', 'engine.mjs', 'model.mjs', 'build.mjs', 'model.test.mjs', 'timeline.mjs', 'review-model.mjs', 'review.mjs', 'review.css', 'serve.py', 'reconcile.mjs', 'README.md', 'film.mjs', 'film.html', 'film-page.mjs', 'export-film.mjs', 'motion-films.md', 'film-primitives.mjs', 'demo-media.mjs', 'film-gallery.json', 'film-music-video.example.json']


def prepare(destination, node='node', assets=None):
    root = Path(destination).absolute()
    if root.exists() or root.is_symlink() or not root.parent.is_dir() or any(p.is_symlink() for p in root.parents): raise ValueError('Fresh owned directory and real existing parent required')
    spec = importlib.util.spec_from_file_location('figure_package', SKILLS / 'technical-illustration/scripts/package_figure.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if len(assets or {}) > 32: raise ValueError('At most 32 explicit raster inputs per package')
    imported = []
    for label, path in (assets or {}).items():
        import re
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,39}', label) or label in ('gallery', 'logo'): raise ValueError('Unsafe/reserved media label')
        path = Path(path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 10000000: raise ValueError('Explicit regular raster asset required')
        raw = path.read_bytes(); ext = path.suffix.lower()
        if not ((ext == '.png' and raw.startswith(b'\x89PNG\r\n\x1a\n')) or (ext in ('.jpg', '.jpeg') and raw.startswith(b'\xff\xd8\xff')) or (ext == '.webp' and raw.startswith(b'RIFF') and raw[8:12] == b'WEBP')): raise ValueError('PNG/JPEG/WebP signature required; SVG/HTML not accepted')
        imported.append((label + ext, path))
    root.mkdir()
    for name in FILES: shutil.copyfile(SOURCE / name, root / name)
    (root / 'film-gallery.mjs').write_text('export default ' + json.dumps(json.loads((root / 'film-gallery.json').read_text())) + ';\n')
    subprocess.run([node, str(root / 'demo-media.mjs'), str(root / 'media')], check=True, capture_output=True, text=True)
    for name, path in imported: shutil.copyfile(path, root / 'media' / name)
    module.package(root / 'renderer', mode='3d')
    shared = SOURCE.parent / 'review-workspace'
    shutil.copyfile(shared / 'serve.py', root / 'review-bridge.py')
    shutil.copyfile(shared / 'model.mjs', root / 'review-core.mjs')
    subprocess.run([node, str(root / 'build.mjs')], check=True, cwd=root, capture_output=True, text=True)
    (root / 'design.md').write_text('# V12 educational review\n\nPreserve these authored model limits. Ideal rigid links; no production simulation.\n')
    targets = [{'id': 'part/' + p['name'], 'kind': 'part'} for p in json.loads((root / 'engine-data.json').read_text())['parts']]
    targets += [{'id': 'control/' + n, 'kind': 'control'} for n in ['play', 'step', 'reset', 'crank', 'orbit', 'speed', 'guides', 'rods', 'story-time', 'story-scenario', 'story-play']]
    targets += [{'id': 'control/cylinder-' + bank + str(i), 'kind': 'control'} for bank in ['A', 'B'] for i in range(1, 7)]
    targets += [{'id': 'surface/' + n, 'kind': 'component'} for n in ['story-title', 'story-caption', 'story-data', 'story-card', 'film-stage', 'film-title', 'film-caption', 'film-primitive']]
    names = sorted(set(FILES + ['review-bridge.py', 'review-core.mjs', 'film-gallery.mjs', 'engine.svg', 'engine-data.json', 'turn.css', 'static-files.json', 'renderer/illustration-support.json'] + ['renderer/' + n for n in json.loads((root / 'renderer/illustration-support.json').read_text())['maintained_files']]))
    names += sorted('media/' + p.name for p in (root / 'media').iterdir()); names += ['manifest.json']; (root / 'static-files.json').write_text(json.dumps(names, indent=2) + '\n')
    assets = {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in names if n != 'manifest.json'}
    prototype = {'id': 'v12-scene', 'version': 1, 'candidate': 'spatial-v1'}
    payload = {'prototype': prototype, 'targets': targets, 'assets': assets}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (root / 'manifest.json').write_text(json.dumps({**payload, 'prototype': {**prototype, 'fingerprint': fingerprint}}, indent=2) + '\n')
    return {'package': str(root), 'sourceFingerprint': fingerprint, 'modelRevision': assets['engine-data.json'], 'sourceFiles': len(assets), 'reviewSaved': False, 'limits': 'Prepared source, not browser or physical qualification; existing package never overwritten.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--destination', required=True); p.add_argument('--node', default='node'); p.add_argument('--asset', action='append', default=[], metavar='ID=LOCAL_RASTER'); a = p.parse_args()
    assets = {}
    for value in a.asset:
        label, separator, path = value.partition('=')
        if not separator or label in assets: p.error('Unique ID=LOCAL_RASTER required')
        assets[label] = path
    print(json.dumps(prepare(a.destination, a.node, assets), indent=2))
