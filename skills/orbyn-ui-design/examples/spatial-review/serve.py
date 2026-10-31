"""Schema-2 spatial adapter for the shared fixed-path loopback writer."""
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('review_bridge', ROOT / 'review-bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def context(c, manifest, gallery=None):
    if manifest['prototype']['id'] == 'graphics-review-v1':
        return graphics_context(c, manifest)
    if manifest['prototype']['id'] == 'motion-composition-v1':
        return motion_context(c, manifest)
    bridge.fields(c, ['modelRevision', 'partId', 'camera', 'animation', 'layers', 'viewport'] + (['filmRevision'] if type(c) is dict and 'filmRevision' in c else []))
    if type(c['partId']) is not str or type(c['modelRevision']) is not str or c['modelRevision'] != manifest['assets']['engine-data.json'] or not any(t['id'] == 'part/' + str(c['partId']) for t in manifest['targets']):
        raise ValueError('Stale model/part')
    bridge.fields(c['camera'], ['yaw', 'elevation', 'scale'])
    number(c['camera']['yaw'], -180, 180)
    if type(c['camera']['elevation']) is not int or c['camera']['elevation'] != 27 or type(c['camera']['scale']) is not int or c['camera']['scale'] != 78:
        raise ValueError('Unsupported projection')
    a = c['animation']; bridge.fields(a, ['scenario', 'scene', 'time', 'cycleAngle', 'rate'])
    if 'filmRevision' in c and (a['scenario'] not in ('film','gallery') or type(c['filmRevision']) is not str or c['filmRevision'] != manifest['assets']['film-gallery.json' if a['scenario'] == 'gallery' else 'film.mjs']): raise ValueError('Stale film model')
    number(a['time'], 0, gallery['duration'] if a['scenario'] == 'gallery' and gallery else 12); number(a['cycleAngle'], 0, 720); number(a['rate'], .25, 1)
    scene = 'overview' if a['time'] < 3 else 'motion' if a['time'] < 7 else 'detail' if a['time'] < 10 else 'end'
    if a['scenario'] == 'gallery' and gallery:
        shot = next((s for s in gallery['shots'] if s['from'] <= a['time'] < s['to']), gallery['shots'][-1]); scene = shot['id']
    if a['scenario'] not in ('mechanism', 'interface', 'data', 'film', 'gallery') or a['scene'] != scene or a['rate'] not in (.25, .5, 1):
        raise ValueError('Invalid timeline')
    bridge.fields(c['layers'], ['guides', 'rods'])
    if any(type(v) is not bool for v in c['layers'].values()): raise ValueError('Invalid layers')
    bridge.fields(c['viewport'], ['width', 'height'])
    for v in c['viewport'].values(): bridge.integer(v, 160, 8192)


def motion_context(c, manifest):
    bridge.fields(c, ['profile', 'modelRevision', 'partId', 'camera', 'animation', 'layers', 'viewport', 'parameters'])
    motion = next((t['motion'] for t in manifest['targets'] if t['kind'] == 'profile'), None)
    if not motion or c['profile'] != 'motion-v1' or c['modelRevision'] != manifest['assets']['motion-project.json'] or not any(t['id'] == 'part/' + str(c['partId']) for t in manifest['targets']): raise ValueError('Stale motion profile/anchor')
    bridge.fields(c['camera'], ['x', 'y', 'zoom'])
    number(c['camera']['x'], -10000, 10000); number(c['camera']['y'], -10000, 10000); number(c['camera']['zoom'], .1, 10)
    a = c['animation']; bridge.fields(a, ['frame', 'time', 'scene', 'rate'])
    bridge.integer(a['frame'], 0, motion['durationFrames'] - 1); number(a['time'], 0, 100000); number(a['rate'], .25, 2)
    if a['rate'] not in (.25, .5, 1, 2) or abs(a['time'] - a['frame'] * motion['fps']['denominator'] / motion['fps']['numerator']) > 1e-8: raise ValueError('Invalid motion time')
    anchor = next((v for v in motion['anchors'] if v['id'] == a['scene']), None)
    part = next(t for t in manifest['targets'] if t['id'] == 'part/' + c['partId'])
    if not anchor or not anchor['start'] <= a['frame'] < anchor['end'] or c['partId'] not in anchor['parts'] or not part['motionRange']['start'] <= a['frame'] < part['motionRange']['end']: raise ValueError('Unmapped motion anchor')
    bindings = motion.get('bindings', [])
    bridge.fields(c['parameters'], [b['id'] for b in bindings])
    for b in bindings:
        v = c['parameters'][b['id']]
        if b['type'] == 'number':
            number(v, b['min'], b['max'])
            if abs((v - b['min']) / b['step'] - round((v - b['min']) / b['step'])) > 1e-6: raise ValueError('Numeric binding step')
        elif b['type'] == 'color':
            if type(v) is not str or not re.fullmatch(r'#[0-9a-fA-F]{6}', v): raise ValueError('Color binding')
        elif b['type'] == 'enum':
            if type(v) is not str or v not in b['options']: raise ValueError('Enum binding')
        else: raise ValueError('Unsupported binding type')
    bridge.fields(c['layers'], ['guides', 'reducedMotion'])
    if any(type(v) is not bool for v in c['layers'].values()): raise ValueError('Invalid motion layer')
    bridge.fields(c['viewport'], ['width', 'height'])
    for v in c['viewport'].values(): bridge.integer(v, 160, 8192)


def graphics_context(c, manifest):
    bridge.fields(c, ['profile', 'modelRevision', 'partId', 'camera', 'animation', 'parameters', 'viewport'])
    profile = next((t.get('graphics') for t in manifest['targets'] if t['id'] == 'profile/graphics-v1'), None)
    part = next((t for t in manifest['targets'] if t['id'] == 'part/' + str(c['partId'])), None)
    if not profile or not part or c['profile'] != 'graphics-v1' or c['modelRevision'] != manifest['assets']['motion/graphics-scene.json']: raise ValueError('Stale graphics source/part')
    camera = c['camera']
    bridge.fields(camera, ['type', 'position', 'target', 'near', 'far', 'span' if camera.get('type') == 'orthographic' else 'fov'])
    if camera['type'] not in ('perspective', 'orthographic') or camera['type'] != profile['cameraType']: raise ValueError('Graphics camera type')
    number(camera['near'], .001, 100); number(camera['far'], camera['near'] + .001, 1000000)
    number(camera['fov'], 1, 150) if camera['type'] == 'perspective' else number(camera['span'], .01, 10000)
    for vector in [camera['position'], camera['target']]:
        if type(vector) is not list or len(vector) != 3: raise ValueError('Invalid camera vector')
        for v in vector: number(v, -100000, 100000)
    import math
    if math.dist(c['camera']['position'], c['camera']['target']) < .001: raise ValueError('Degenerate camera')
    a = c['animation']; bridge.fields(a, ['time', 'tick', 'scene', 'mode'])
    number(a['time'], 0, profile['maxTicks'] / profile['tickRate']); bridge.integer(a['tick'], 0, profile['maxTicks'])
    if a['scene'] != profile['scene'] or a['mode'] not in ('raster', 'effects', 'pathtrace', 'webgpu') or a['tick'] != math.floor(a['time'] * profile['tickRate'] + 1e-8) or not any(r['start'] <= a['tick'] < r['end'] for r in part['tickRanges']): raise ValueError('Inactive graphics anchor/time')
    bindings = profile['bindings']; bridge.fields(c['parameters'], [b['id'] for b in bindings])
    for b in bindings:
        v = c['parameters'][b['id']]
        if b['type'] == 'number':
            number(v, b['min'], b['max'])
            if abs((v - b['min']) / b['step'] - round((v - b['min']) / b['step'])) > 1e-6: raise ValueError('Numeric graphics step')
        elif b['type'] == 'color':
            if type(v) is not str or not re.fullmatch(r'#[0-9a-fA-F]{6}', v): raise ValueError('Color graphics binding')
        else: raise ValueError('Unsupported graphics binding')
    bridge.fields(c['viewport'], ['width', 'height'])
    for v in c['viewport'].values(): bridge.integer(v, 160, 8192)


def number(v, low, high):
    import math
    if type(v) not in (int, float) or not low <= v <= high or not math.isfinite(v): raise ValueError('Invalid bound')


def validate(doc, manifest, gallery=None):
    bridge.fields(doc, ['schemaVersion', 'prototype', 'settings', 'state', 'pending', 'comments'])
    bridge.fields(doc['prototype'], ['id', 'version', 'candidate', 'fingerprint'])
    if type(doc['prototype']['version']) is not int or type(doc['schemaVersion']) is not int or doc['schemaVersion'] != 2 or doc['prototype'] != manifest['prototype']: raise ValueError('Stale source/schema')
    context(doc['settings'], manifest, gallery)
    if doc['state'] not in ('draft', 'submitted') or type(doc['comments']) is not list or len(doc['comments']) > 200: raise ValueError('Invalid review state')
    targets = {t['id'] for t in manifest['targets']}
    def anchor(c):
        if type(c['targetId']) is not str or c['targetId'] not in targets: raise ValueError('Removed target')
        context(c['context'], manifest, gallery)
        if c['targetId'].startswith('part/') and c['targetId'] != 'part/' + c['context']['partId']: raise ValueError('Wrong part anchor')
    ids = set()
    for c in doc['comments']:
        bridge.fields(c, ['id', 'targetId', 'context', 'text', 'disposition', 'decision']); anchor(c)
        if type(c['id']) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', c['id']) or c['id'] in ids: raise ValueError('Duplicate comment')
        ids.add(c['id']); bridge.text(c['text'], 3000); bridge.text(c['decision'], 1500, False)
        if c['disposition'] not in ('unresolved', 'accepted', 'rejected') or (c['disposition'] != 'unresolved' and not c['decision'].strip()) or (doc['state'] == 'draft' and c['disposition'] != 'unresolved'): raise ValueError('Invalid disposition')
    if doc['pending'] is not None:
        bridge.fields(doc['pending'], ['targetId', 'context', 'text']); anchor(doc['pending']); bridge.text(doc['pending']['text'], 3000, False)
        if doc['state'] != 'draft': raise ValueError('Submitted pending')
    return doc


def make_server(package=ROOT, port=0):
    root = Path(package).resolve(strict=True)
    # This allowlist is generated by the trusted local prepare helper, not a request.
    names = bridge.strict_json((root / 'static-files.json').read_text())
    if type(names) is not list or len(names) != len(set(names)) or len(names) > 100: raise ValueError('Invalid static file list')
    mimes = {'.html': 'text/html', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.md': 'text/plain', '.txt': 'text/plain', '.py': 'text/plain'}
    assets = {n: mimes.get(Path(n).suffix, 'text/plain') for n in names}
    manifest = bridge.strict_json((root / 'manifest.json').read_text()); bridge.fields(manifest, ['prototype', 'targets', 'assets'])
    if len({t['id'] for t in manifest['targets']}) != len(manifest['targets']): raise ValueError('Duplicate targets')
    gallery = bridge.strict_json((root/'film-gallery.json').read_text())
    return bridge.make_server(root, port, assets=assets, validator=lambda doc, m: validate(doc, m, gallery), allow_wasm=manifest['prototype']['id'] == 'graphics-review-v1')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--package', type=Path, default=ROOT); p.add_argument('--port', type=int, default=0); a = p.parse_args()
    server = make_server(a.package, a.port)
    print(f'http://127.0.0.1:{server.server_port}/', flush=True)
    try: server.serve_forever()
    finally: server.server_close()
