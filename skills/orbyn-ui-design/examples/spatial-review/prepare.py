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
FILES = ['index.html', 'style.css', 'engine.mjs', 'model.mjs', 'build.mjs', 'model.test.mjs', 'timeline.mjs', 'review-model.mjs', 'review.mjs', 'review.css', 'serve.py', 'reconcile.mjs', 'README.md', 'film.mjs', 'film.html', 'film-page.mjs', 'export-film.mjs', 'frame-stream.mjs', 'motion-films.md', 'film-primitives.mjs', 'demo-media.mjs', 'film-gallery.json', 'film-music-video.example.json']


def prepare(destination, node='node', assets=None, motion_example=None, motion_project=None, component_source=None, graphics_profile=None):
    if motion_example is not None and motion_project is not None: raise ValueError('Choose example or authored project')
    if component_source is not None and motion_project is None: raise ValueError('Trusted component source needs an authored project')
    graphics = None
    if graphics_profile is not None:
        if motion_example is not None or motion_project is not None or component_source is not None: raise ValueError('Graphics and DOM motion are separate explicit source profiles')
        graphics_profile = Path(graphics_profile).absolute()
        if graphics_profile.is_symlink() or not graphics_profile.is_dir() or any(p.is_symlink() for p in graphics_profile.parents): raise ValueError('Explicit real local graphics profile required')
        graphics = json.loads((graphics_profile / 'profile.json').read_text())
        expected_lock = hashlib.sha256((SOURCE / 'motion/graphics/package-lock.json').read_bytes()).hexdigest()
        expected_files = {'vendor-raster.mjs', 'vendor-webgpu.mjs', 'vendor-jolt.mjs', 'NOTICES.md', 'vendor-raster.mjs.LEGAL.txt', 'vendor-webgpu.mjs.LEGAL.txt'}
        if graphics.get('version') != 1 or graphics.get('status') != 'built; runtime qualification separate' or graphics.get('lockSha256') != expected_lock or set(graphics.get('files', {})) != expected_files: raise ValueError('Graphics profile/lock/closure differs')
        total = 0
        for name in expected_files:
            path = graphics_profile / name
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 * 1024 * 1024: raise ValueError('Graphics dependency asset budget/type')
            data = path.read_bytes(); total += len(data); record = graphics['files'][name]
            if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']: raise ValueError('Stale graphics dependency asset')
        if total > 32 * 1024 * 1024 or graphics.get('totalBytes') != total: raise ValueError('Graphics total byte budget')
    custom = None
    if motion_project is not None:
        motion_project = Path(motion_project)
        if motion_project.is_symlink() or not motion_project.is_file() or motion_project.stat().st_size > 1048576: raise ValueError('Explicit bounded local composition JSON required')
        # JSON is inert; runtime import/module names are never read from it.
        json.loads(motion_project.read_text())
    if component_source is not None:
        component_source = Path(component_source)
        if component_source.is_symlink() or not component_source.is_file() or component_source.suffix != '.mjs' or component_source.stat().st_size > 1048576: raise ValueError('Explicit reviewed single-file component source required')
        custom = component_source.read_bytes()
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
    shutil.copytree(SOURCE / 'motion', root / 'motion', ignore=shutil.ignore_patterns('*.test.mjs', '__pycache__', 'node_modules', '.*', 'output', '*.py', '*-requirements.txt', 'correct-audio.mjs', 'edit-media.mjs', 'custom-domain.example.mjs', 'custom-domain.example.json', 'vector-study.mjs', 'vector-study.json', 'audio-study.mjs', 'audio-study.json', 'build-profile.mjs', 'package.json', 'package-lock.json'))
    if graphics is not None:
        (root / 'motion/graphics-profile').mkdir()
        shutil.copyfile(SOURCE / 'motion/graphics/package-lock.json', root / 'motion/graphics-profile/package-lock.json')
        for name in ['profile.json', *graphics['files']]: shutil.copyfile(graphics_profile / name, root / 'motion/graphics-profile' / name)
    if custom is not None:
        (root / 'motion/custom-components.mjs').write_bytes(custom)
        entry = root / 'motion/demo.mjs'
        entry.write_text("import {registerCustomComponents} from './custom-components.mjs';\n" + entry.read_text().replace('registry=registerExamples(createRegistry());', 'registry=registerCustomComponents(registerExamples(createRegistry()));'))
        closure = subprocess.run([node, '--experimental-vm-modules', str(SOURCE / 'motion/validate-module-closure.mjs'), str(root), str(root / 'motion/custom-components.mjs')], check=True, capture_output=True, text=True)
        (root / 'motion/custom-module-closure.json').write_text(json.dumps(json.loads(closure.stdout), indent=2) + '\n')
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
    names += sorted(str(p.relative_to(root)) for p in (root / 'motion').rglob('*') if p.is_file())
    names += sorted('media/' + p.name for p in (root / 'media').iterdir()); names += ['manifest.json']; (root / 'static-files.json').write_text(json.dumps(names, indent=2) + '\n')
    assets = {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in names if n != 'manifest.json'}
    prototype = {'id': 'v12-scene', 'version': 1, 'candidate': 'spatial-v1'}
    if motion_example is not None or motion_project is not None:
        if motion_project is not None: shutil.copyfile(motion_project, root / 'motion-input.json')
        project_script = (
            'import {examples} from "./motion/examples.mjs";\n'
            'import {motionManifest} from "./motion/profiles.mjs";\n'
            'import {validateComposition} from "./motion/composition.mjs";\n'
            'import {parseJSONStrict} from "./review-core.mjs";\n'
            'import {readFile} from "node:fs/promises";\n'
            'const input = process.argv[1] === "authored" ? parseJSONStrict(await readFile("motion-input.json", "utf8")) : examples[Number(process.argv[1])];\n'
            'const project = validateComposition(input);\n'
            'console.log(JSON.stringify({project, targets:motionManifest(project, {}, {}).targets}));\n'
        )
        result = subprocess.run([node, '--input-type=module', '-e', project_script,
                                 'authored' if motion_project is not None else str(motion_example)],
                                cwd=root, check=True, capture_output=True, text=True)
        bundle = json.loads(result.stdout); project = bundle['project']
        (root / 'motion-project.json').write_text(json.dumps(project, indent=2) + '\n')
        (root / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Motion review</title><p><a href="motion/demo.html">Open the source-bound motion review</a></p><script type="module" src="review-entry.mjs"></script></html>\n')
        if motion_project is not None: (root / 'motion-input.json').unlink()
        (root / 'review-entry.mjs').write_text('location.replace("motion/demo.html");\n')
        names.append('review-entry.mjs')
        names.append('motion-project.json'); (root / 'static-files.json').write_text(json.dumps(names, indent=2) + '\n')
        assets = {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in names if n != 'manifest.json'}
        prototype = {'id': 'motion-composition-v1', 'version': 1, 'candidate': project['sourceRevision']}
        targets = bundle['targets']
        (root / 'design.md').write_text('# Code-driven motion review\n\nOriginal authored composition and source-bound decisions. Sampled illustrative motion, not measured product behavior.\n')
    if graphics is not None:
        graphics_script = (
            'import {readFile} from "node:fs/promises";\n'
            'import {graphicsTargets} from "./motion/graphics-profiles.mjs";\n'
            'const scene=JSON.parse(await readFile("motion/graphics-scene.json","utf8"));\n'
            'const simulation=JSON.parse(await readFile("motion/graphics-simulation.json","utf8"));\n'
            'console.log(JSON.stringify(graphicsTargets(scene,simulation,process.argv[1])));\n'
        )
        result = subprocess.run([node, '--input-type=module', '-e', graphics_script, graphics['lockSha256']], cwd=root, check=True, capture_output=True, text=True)
        targets = json.loads(result.stdout)
        prototype = {'id': 'graphics-review-v1', 'version': 1, 'candidate': 'graphics-study-v1'}
        (root / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Graphics review</title><p><a href="motion/graphics-demo.html?profile=graphics-profile/">Open source-bound graphics review</a></p><script type="module" src="review-entry.mjs"></script></html>\n')
        (root / 'review-entry.mjs').write_text('location.replace("motion/graphics-demo.html?profile=graphics-profile/");\n')
        names.append('review-entry.mjs'); (root / 'static-files.json').write_text(json.dumps(names, indent=2) + '\n')
        assets = {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in names if n != 'manifest.json'}
        (root / 'design.md').write_text('# Graphics source review\n\nOriginal code-authored scene, optional exact runtime profile, explicit source-bound decisions. Runtime cells qualify separately.\n')
    if len(names) > 100: raise ValueError('UI source closure exceeds 100-file budget; prepare optional tools separately')
    payload = {'prototype': prototype, 'targets': targets, 'assets': assets}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (root / 'manifest.json').write_text(json.dumps({**payload, 'prototype': {**prototype, 'fingerprint': fingerprint}}, indent=2) + '\n')
    return {'package': str(root), 'sourceFingerprint': fingerprint, 'modelRevision': assets['motion/graphics-scene.json' if graphics is not None else 'motion-project.json' if motion_example is not None or motion_project is not None else 'engine-data.json'], 'sourceFiles': len(assets), 'reviewSaved': False, 'limits': 'Prepared source, not browser or physical qualification; existing package never overwritten.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--destination', required=True); p.add_argument('--node', default='node'); p.add_argument('--motion-example', type=int, choices=range(3)); p.add_argument('--motion-project', type=Path); p.add_argument('--component-source', type=Path); p.add_argument('--graphics-profile', type=Path); p.add_argument('--asset', action='append', default=[], metavar='ID=LOCAL_RASTER'); a = p.parse_args()
    assets = {}
    for value in a.asset:
        label, separator, path = value.partition('=')
        if not separator or label in assets: p.error('Unique ID=LOCAL_RASTER required')
        assets[label] = path
    try:
        print(json.dumps(prepare(a.destination, a.node, assets, a.motion_example, a.motion_project, a.component_source, a.graphics_profile), indent=2))
    except subprocess.CalledProcessError as error:
        p.exit(1, f'Prepare stopped: {error.cmd[0]} exited {error.returncode}; partial output retained in {a.destination}\n{(error.stderr or "").strip()[-4000:]}\n')
