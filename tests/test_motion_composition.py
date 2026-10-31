"""Core clocks/authoring and existing review-writer integration; no GPU/model calls."""
import copy
import http.client
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'skills/orbyn-ui-design/examples/spatial-review'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class MotionCompositionTests(unittest.TestCase):
    def test_core_semantics_and_negative_controls(self):
        node = shutil.which('node')
        if not node: self.skipTest('Existing Node required; no install')
        result = subprocess.run([node, '--test', str(SOURCE / 'motion/core.test.mjs')], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_prepared_motion_uses_existing_writer_and_preserves_legacy_review(self):
        node = shutil.which('node')
        if not node: self.skipTest('Existing Node required; no install')
        with tempfile.TemporaryDirectory() as temp:
            pkg = Path(temp).resolve() / 'motion'
            receipt = load('motion_prepare', SOURCE / 'prepare.py').prepare(pkg, node, motion_example=0)
            manifest = json.loads((pkg / 'manifest.json').read_text())
            self.assertEqual(manifest['prototype']['id'], 'motion-composition-v1')
            self.assertEqual(receipt['modelRevision'], manifest['assets']['motion-project.json'])
            self.assertIn('Code-driven motion review', (pkg / 'design.md').read_text())
            names = json.loads((pkg / 'static-files.json').read_text())
            self.assertLessEqual(len(names), 100)
            self.assertFalse(any('node_modules' in n or '/.' in n for n in names))
            adapter = load('motion_server', pkg / 'serve.py')
            c = {'profile': 'motion-v1', 'modelRevision': manifest['assets']['motion-project.json'], 'partId': 'heading', 'camera': {'x': 0, 'y': 0, 'zoom': 1}, 'animation': {'frame': 0, 'time': 0, 'scene': 'heading', 'rate': 1}, 'layers': {'guides': True, 'reducedMotion': False}, 'viewport': {'width': 1080, 'height': 608}, 'parameters': {'orb-radius': 28, 'title-size': 44, 'orbit-speed': 1, 'orb-color': '#f8b454'}}
            doc = {'schemaVersion': 2, 'prototype': manifest['prototype'], 'settings': c, 'state': 'draft', 'pending': None, 'comments': []}
            adapter.validate(doc, manifest)
            doc['settings']['parameters']['orb-radius'] = 44
            doc['settings']['parameters']['title-size'] = 40
            doc['settings']['parameters']['orbit-speed'] = .75
            doc['settings']['parameters']['orb-color'] = '#123456'
            adapter.validate(doc, manifest)
            for key, value in [('orb-radius', 500), ('orbit-speed', .71), ('orb-color', 'url(remote)'), ('foreign-key', 1)]:
                bad = copy.deepcopy(doc); bad['settings']['parameters'][key] = value
                with self.assertRaises(ValueError): adapter.validate(bad, manifest)
            stale = copy.deepcopy(doc); stale['settings']['partId'] = 'signal'
            with self.assertRaises(ValueError): adapter.validate(stale, manifest)
            stale = copy.deepcopy(doc); stale['settings']['modelRevision'] = 'old'
            with self.assertRaises(ValueError): adapter.validate(stale, manifest)
            server = adapter.make_server(pkg)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                host = f'127.0.0.1:{server.server_port}'
                def request(method, payload=None, revision=0, token=None):
                    conn = http.client.HTTPConnection(host, timeout=5)
                    headers = {'Origin': 'http://' + host, 'Content-Type': 'application/json'}
                    if token: headers.update({'X-Review-Token': token, 'X-Review-Revision': str(revision)})
                    conn.request(method, '/api/review', None if payload is None else json.dumps({'review': payload}), headers)
                    response = conn.getresponse(); self.assertNotIn("'wasm-unsafe-eval'", response.getheader('Content-Security-Policy')); body = json.loads(response.read()); conn.close()
                    return response.status, body
                code, state = request('GET'); self.assertEqual(code, 200)
                code, saved = request('POST', doc, token=state['token']); self.assertEqual(code, 200)
                code, opened = request('GET'); self.assertEqual(code, 200); self.assertEqual(opened['review'], doc)
                conflicting = copy.deepcopy(doc); conflicting['settings']['camera']['x'] = 10
                code, _ = request('POST', conflicting, token=state['token']); self.assertEqual(code, 409)
                # This is the same durable store and revision protocol, not localStorage or a second file.
                self.assertEqual(json.loads((pkg / 'review.json').read_text())['review'], doc)
                self.assertEqual(saved['revision'], 1)
            finally:
                server.shutdown(); server.server_close(); thread.join()


class MotionAssetBoundaryTests(unittest.TestCase):
    def test_only_original_bounded_glb_fixture_is_accepted(self):
        inventory = load('motion_inventory', ROOT / 'scripts/library_manifest.py')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rel = 'skills/orbyn-ui-design/examples/spatial-review/motion/graphics-demo-assets/marker.glb'
            fixture = root / rel; fixture.parent.mkdir(parents=True)
            fixture.write_bytes(b'glTF' + (2).to_bytes(4, 'little') + (12).to_bytes(4, 'little'))
            self.assertTrue(inventory.original_motion_asset(fixture, root))
            other = fixture.with_name('unreviewed.glb'); other.write_bytes(fixture.read_bytes())
            self.assertFalse(inventory.original_motion_asset(other, root))
            fixture.write_bytes(b'glTF' + (2).to_bytes(4, 'little') + (99).to_bytes(4, 'little'))
            self.assertFalse(inventory.original_motion_asset(fixture, root))

class MotionExportBoundaryTests(unittest.TestCase):
    def test_export_refuses_overwrite_and_changed_source_before_loading_tools(self):
        node = shutil.which('node')
        if not node: self.skipTest('Existing Node required; no install')
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve(); pkg = base / 'motion'
            load('export_boundary_prepare', SOURCE / 'prepare.py').prepare(pkg, node, motion_example=0)
            occupied = base / 'occupied'; occupied.mkdir(); (occupied / 'keep.txt').write_text('owned output')
            cli = [node, str(SOURCE / 'motion/export-composition.mjs'), '--package', str(pkg), '--playwright', '/nonexistent-do-not-load.mjs']
            result = subprocess.run(cli + ['--output', str(occupied)], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('EEXIST', result.stderr)
            self.assertEqual((occupied / 'keep.txt').read_text(), 'owned output')
            result = subprocess.run(cli + ['--output', str(base / 'bad-window'), '--from-frame', '599', '--frames', '2'], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0); self.assertIn('frame window/budget', result.stderr)
            self.assertFalse((base / 'bad-window').exists())
            (pkg / 'motion/components.mjs').write_text('// stale source\n')
            result = subprocess.run(cli + ['--output', str(base / 'fresh')], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0); self.assertIn('Stale source', result.stderr)
            self.assertFalse((base / 'fresh').exists())

class CustomMotionSourceTests(unittest.TestCase):
    def test_external_project_and_trusted_component_are_copied_and_static_closure_parsed(self):
        node = shutil.which('node')
        if not node: self.skipTest('Existing Node required; no install')
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve(); external=base/'authored'; external.mkdir()
            project=external/'coast.json'; component=external/'coast.mjs'
            shutil.copyfile(SOURCE/'motion/custom-domain.example.json',project)
            shutil.copyfile(SOURCE/'motion/custom-domain.example.mjs',component)
            pkg=base/'package'
            load('custom_motion_prepare',SOURCE/'prepare.py').prepare(pkg,node,motion_project=project,component_source=component)
            manifest=json.loads((pkg/'manifest.json').read_text())
            self.assertIn('motion/custom-components.mjs',manifest['assets'])
            self.assertEqual((pkg/'motion/custom-components.mjs').read_bytes(),component.read_bytes())
            self.assertEqual(json.loads((pkg/'motion-project.json').read_text())['clips'][0]['component'],'tidal-observatory')
            closure=json.loads((pkg/'motion/custom-module-closure.json').read_text())
            self.assertIn('motion/time.mjs',closure['staticModules'])
            self.assertFalse((pkg/'motion-input.json').exists())
            # Parsing is not executing or sandboxing the explicitly trusted source.
            component.write_text("import fs from 'node:fs'; export function registerCustomComponents(r){return r;}\n")
            with self.assertRaises(subprocess.CalledProcessError):
                load('custom_motion_bad',SOURCE/'prepare.py').prepare(base/'bad',node,motion_project=project,component_source=component)
            self.assertTrue((base/'bad').exists())  # Failed setup is retained, never erased.

class GraphicsReviewStoreTests(unittest.TestCase):
    def test_explicit_graphics_profile_uses_same_writer_and_exact_active_part_boundaries(self):
        import hashlib
        node=shutil.which('node')
        if not node: self.skipTest('Existing Node required; no install')
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve(); profile=base/'profile'; profile.mkdir()
            files={}
            for name in ['vendor-raster.mjs','vendor-webgpu.mjs','vendor-jolt.mjs','NOTICES.md','vendor-raster.mjs.LEGAL.txt','vendor-webgpu.mjs.LEGAL.txt']:
                raw=b'// synthetic protocol fixture, not a runtime backend\n'; (profile/name).write_bytes(raw)
                files[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            receipt={'version':1,'status':'built; runtime qualification separate','lockSha256':hashlib.sha256((SOURCE/'motion/graphics/package-lock.json').read_bytes()).hexdigest(),'files':files,'totalBytes':sum(v['bytes'] for v in files.values())}
            (profile/'profile.json').write_text(json.dumps(receipt))
            pkg=base/'prepared'; load('graphics_store_prepare',SOURCE/'prepare.py').prepare(pkg,node,graphics_profile=profile)
            manifest=json.loads((pkg/'manifest.json').read_text()); self.assertEqual(manifest['prototype']['id'],'graphics-review-v1')
            self.assertIn('motion/graphics-profile/NOTICES.md',manifest['assets'])
            adapter=load('graphics_store_server',pkg/'serve.py')
            c={'profile':'graphics-v1','modelRevision':manifest['assets']['motion/graphics-scene.json'],'partId':'second','camera':{'type':'perspective','position':[7,4.5,8],'target':[0,1,0],'fov':43,'near':.1,'far':1000},'animation':{'time':121/120,'tick':121,'scene':'graphics-study','mode':'raster'},'parameters':{'ball-color':'#123456','ball-roughness':.4,'ball-metalness':.2,'key-light':3.2},'viewport':{'width':960,'height':540}}
            doc={'schemaVersion':2,'prototype':manifest['prototype'],'settings':c,'state':'draft','pending':None,'comments':[]}
            adapter.validate(doc,manifest)
            for tick in [120,301,420]:
                bad=copy.deepcopy(doc);bad['settings']['animation'].update({'time':tick/120,'tick':tick})
                with self.assertRaises(ValueError):adapter.validate(bad,manifest)
            for tick in [121,300,421,720]:
                good=copy.deepcopy(doc);good['settings']['animation'].update({'time':tick/120,'tick':tick});adapter.validate(good,manifest)
            server=adapter.make_server(pkg); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                host=f'127.0.0.1:{server.server_port}'
                conn=http.client.HTTPConnection(host,timeout=5);conn.request('GET','/api/review');response=conn.getresponse();state=json.loads(response.read());self.assertEqual(response.status,200);self.assertIn("'wasm-unsafe-eval'",response.getheader('Content-Security-Policy'));self.assertNotIn("'unsafe-eval'",response.getheader('Content-Security-Policy'));conn.close()
                headers={'Origin':'http://'+host,'Content-Type':'application/json','X-Review-Token':state['token'],'X-Review-Revision':'0'}
                conn=http.client.HTTPConnection(host,timeout=5);conn.request('POST','/api/review',json.dumps({'review':doc}),headers);response=conn.getresponse();saved=json.loads(response.read());self.assertEqual(response.status,200,saved);conn.close()
                self.assertEqual(json.loads((pkg/'review.json').read_text())['review'],doc)
            finally:server.shutdown();server.server_close();thread.join()
            # Tampered actual bundle fails before making another destination.
            (profile/'vendor-raster.mjs').write_text('changed')
            with self.assertRaises(ValueError):load('graphics_bad_profile',SOURCE/'prepare.py').prepare(base/'bad',node,graphics_profile=profile)
            self.assertFalse((base/'bad').exists())


if __name__ == '__main__': unittest.main()
