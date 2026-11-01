"""Owned-package/restart/protocol/model checks; no model calls or native claims."""
import copy
import http.client
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'skills/orbyn-ui-design/examples/spatial-review'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


class PrepareDiagnosticsTests(unittest.TestCase):
    def test_failed_node_step_reports_its_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            node = base / 'fake-node'
            node.write_text('#!/bin/sh\necho "composition rejected: scene 3" >&2\nexit 3\n')
            node.chmod(0o755)
            result = subprocess.run([sys.executable, '-B', str(SOURCE / 'prepare.py'), '--destination', str(base / 'package'),
                                     '--node', str(node)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('composition rejected: scene 3', result.stderr)
            self.assertNotIn('Traceback', result.stderr)


class SpatialReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which('node')
        if not cls.node: raise unittest.SkipTest('Existing Node required; no install attempted')
        cls.temp = tempfile.TemporaryDirectory(); cls.base = Path(cls.temp.name).resolve()
        cls.pkg = cls.base / 'prepared'
        cls.preparer = module('spatial_prepare', SOURCE / 'prepare.py')
        cls.receipt = cls.preparer.prepare(cls.pkg, cls.node)
        cls.adapter = module('spatial_adapter', cls.pkg / 'serve.py')
        cls.manifest = json.loads((cls.pkg / 'manifest.json').read_text())

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.temp_case = tempfile.TemporaryDirectory(); self.addCleanup(self.temp_case.cleanup)
        self.root = Path(self.temp_case.name) / 'package'; shutil.copytree(self.pkg, self.root)
        self.server = None

    def start(self):
        self.server = self.adapter.make_server(self.root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        status, data = self.request('GET'); self.assertEqual(status, 200)
        self.token = data['token']; return data

    def stop(self):
        if self.server: self.server.shutdown(); self.server.server_close(); self.thread.join(); self.server = None

    def tearDown(self): self.stop()

    def request(self, method, doc=None, revision=0, path='/api/review'):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        host = f'127.0.0.1:{self.server.server_port}'
        headers = {'Origin': 'http://' + host, 'Content-Type': 'application/json'}
        if method == 'POST': headers.update({'X-Review-Token': self.token, 'X-Review-Revision': str(revision)})
        conn.request(method, path, None if doc is None else json.dumps({'review': doc}), headers)
        r = conn.getresponse(); raw = r.read(); conn.close()
        try: data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeError): data = raw
        return r.status, data

    def review(self):
        c = {'modelRevision': self.manifest['assets']['engine-data.json'], 'partId': 'piston-B3', 'camera': {'yaw': 45, 'elevation': 27, 'scale': 78}, 'animation': {'scenario': 'film', 'scene': 'detail', 'time': 8.25, 'cycleAngle': 495, 'rate': .5}, 'layers': {'guides': False, 'rods': True}, 'viewport': {'width': 1280, 'height': 900}}
        return {'schemaVersion': 2, 'prototype': copy.deepcopy(self.manifest['prototype']), 'settings': c, 'state': 'draft', 'pending': None, 'comments': []}

    def test_preparer_preserves_notices_original_newlines_and_existing_destination(self):
        self.assertIn('\n\nPreserve', (self.pkg / 'design.md').read_text())
        for name in ['renderer/LICENSE', 'renderer/LICENSE-Orbyn.txt']:
            self.assertIn(name, self.manifest['assets']); self.assertTrue((self.pkg/name).is_file())
        self.assertIn('control/cylinder-B3', {t['id'] for t in self.manifest['targets']})
        self.assertIn('surface/story-data', {t['id'] for t in self.manifest['targets']})
        with self.assertRaises(ValueError): self.preparer.prepare(self.pkg, self.node)

    def test_settings_zero_comments_save_restart_and_source_readback(self):
        self.start(); doc = self.review(); code, result = self.request('POST', doc); self.assertEqual(code, 200); self.assertTrue(result['readback'])
        self.stop(); reopened = self.start(); self.assertEqual(reopened['review'], doc); self.assertEqual(reopened['revision'], 1)
        code, raw = self.request('GET', path='/engine.svg'); self.assertEqual(code, 200); self.assertEqual(raw, (self.root/'engine.svg').read_bytes())
        code, _ = self.request('GET', path='/design.md'); self.assertEqual(code, 404)

    def test_comments_submitted_immutable_stale_write_and_original_words(self):
        self.start(); doc = self.review(); words = '<img src=x onerror=alert(1)> retain my words'
        doc['comments'] = [{'id': 'note1', 'targetId': 'part/piston-B3', 'context': copy.deepcopy(doc['settings']), 'text': words, 'disposition': 'unresolved', 'decision': ''}]
        self.assertEqual(self.request('POST', doc)[0], 200)
        newer = copy.deepcopy(doc); newer['settings']['camera']['yaw'] = 0
        self.assertEqual(self.request('POST', newer)[0], 409)
        doc['state'] = 'submitted'; self.assertEqual(self.request('POST', doc, 1)[0], 200)
        changed = copy.deepcopy(doc); changed['comments'][0]['text'] = 'changed'
        self.assertEqual(self.request('POST', changed, 2)[0], 409)
        self.stop(); self.assertEqual(self.start()['review']['comments'][0]['text'], words)

    def test_invalid_types_context_source_scene_and_unknown_fields_reject(self):
        self.start()
        mutations = [lambda d: d['prototype'].update(version=True), lambda d: d['settings'].update(partId=[]), lambda d: d['settings'].update(modelRevision='0'*64), lambda d: d['settings']['animation'].update(scene='overview'), lambda d: d['settings']['animation'].update(time=True), lambda d: d['settings']['camera'].update(yaw=float('inf')), lambda d: d['settings']['layers'].update(rods=1), lambda d: d.update(extra=True), lambda d: d['settings']['viewport'].update(width=True)]
        for mutate in mutations:
            doc = self.review(); mutate(doc); self.assertEqual(self.request('POST', doc)[0], 400)
        self.assertFalse((self.root/'review.json').exists())

    def test_source_change_missing_asset_and_parent_symlink_reject(self):
        self.start(); p = self.root/'renderer/kit/turn.mjs'; p.write_text(p.read_text()+'\n// changed')
        self.assertEqual(self.request('POST', self.review())[0], 400)
        self.stop()
        with self.assertRaises(ValueError): self.adapter.make_server(self.root)
        # A parent-link escape cannot pass merely because the leaf itself is regular.
        kit = self.root/'renderer/kit'; outside = self.root.parent/'outside'; kit.rename(outside); kit.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): self.adapter.make_server(self.root)
        kit.unlink(); kit.mkdir();
        with self.assertRaises((ValueError, FileNotFoundError)): self.adapter.make_server(self.root)

    def test_cross_language_model_timeline_and_design_proposal(self):
        doc = self.review(); file = self.root/'input.json'; file.write_text(json.dumps(doc))
        runner = ROOT/'tests/spatial-review.test.mjs'
        result = subprocess.run([self.node, str(runner), str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

        doc = self.review(); doc['state'] = 'submitted'
        doc['comments'] = [{'id': 'cli-note', 'targetId': 'part/piston-B3', 'context': copy.deepcopy(doc['settings']), 'text': 'Keep original words', 'disposition': 'unresolved', 'decision': ''}]
        (self.root/'review.json').write_text(json.dumps({'revision': 1, 'review': doc}))
        decisions = self.root.parent/'decisions.json'; decisions.write_text(json.dumps([{'commentId': 'cli-note', 'disposition': 'accepted', 'reason': 'Approved synthetic fixture decision'}]))
        owner = self.root/'design.md'; before = owner.read_bytes(); output = self.root.parent/'proposal'
        cli = subprocess.run([self.node, str(self.root/'reconcile.mjs'), str(self.root), str(owner), str(decisions), str(output)], capture_output=True, text=True)
        self.assertEqual(cli.returncode, 0, cli.stderr); self.assertEqual(owner.read_bytes(), before)
        receipt = json.loads((output/'receipt.json').read_text()); self.assertFalse(receipt['designDocWritten']); self.assertIn('Keep original words', (output/'proposed-design.md').read_text())
