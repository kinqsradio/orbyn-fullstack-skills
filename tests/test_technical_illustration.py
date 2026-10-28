"""Executable distribution and non-destructive packaging contracts, no browser/inference."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    item = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(item)
    return item


inventory = module(ROOT/'scripts/library_manifest.py', 'illustration_inventory')
packager = module(ROOT/'skills/technical-illustration/scripts/package_figure.py', 'illustration_packager')


class PinnedIllustrationAssets(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        (self.root/'skills').mkdir()
        (self.root/'skills/catalog.json').write_text(json.dumps({'skills': [{'name': 'unit'}]}))

    def asset(self, name, manifest_root, declared=True):
        target = self.root/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('controlled asset')
        parent = self.root/manifest_root
        parent.mkdir(parents=True, exist_ok=True)
        (parent/'snapshot.json').write_text(json.dumps({'files': {target.relative_to(parent).as_posix(): {}} if declared else {}}))
        return target

    def test_declared_canonical_types_are_allowed(self):
        for suffix in ['ts', 'tsx', 'css', 'png']:
            target = self.asset('skills/unit/references/upstream/sample/view.'+suffix, 'skills/unit/references/upstream/sample')
            self.assertTrue(inventory.pinned_support_asset(target, self.root))

    def test_noncanonical_and_misplaced_ancestor_cannot_admit_extra_type(self):
        target = self.asset('skills/unit/references/nested/upstream/sample/view.tsx', 'skills/unit/references/nested/upstream/sample')
        self.assertFalse(inventory.pinned_support_asset(target, self.root))
        target = self.asset('skills/unit/references/upstream/sample/view.tsx', 'skills/unit')
        self.assertFalse(inventory.pinned_support_asset(target, self.root))

    def test_undeclared_and_foreign_owner_cannot_admit_extra_type(self):
        target = self.asset('skills/unit/references/upstream/sample/view.tsx', 'skills/unit/references/upstream/sample', False)
        self.assertFalse(inventory.pinned_support_asset(target, self.root))
        target = self.asset('skills/foreign/references/upstream/sample/view.tsx', 'skills/foreign/references/upstream/sample')
        self.assertFalse(inventory.pinned_support_asset(target, self.root))


class IllustrationPackaging(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()

    def test_each_mode_copies_exact_selected_modules_not_shared_instructions(self):
        model = self.root/'model.mjs'
        model.write_text('export const value=13;')
        for mode in ['core', 'react', 'print', 'webgl', '3d', 'full']:
            dest = self.root/('artifact-'+mode)
            result = packager.package(dest, mode=mode, inputs={'model': model})
            self.assertEqual(result['status'], 'complete selected-byte copy')
            self.assertEqual(result['declared_model_style_asset_inputs']['model'], hashlib.sha256(model.read_bytes()).hexdigest())
            for name, expected in result['maintained_files'].items():
                self.assertEqual(hashlib.sha256((dest/name).read_bytes()).hexdigest(), expected)
            self.assertFalse(list(dest.rglob('SKILL.md')))
            self.assertFalse(list(dest.rglob('SOURCE.md')))
            self.assertNotIn(str(self.root), (dest/'illustration-support.json').read_text())

    def test_existing_destination_and_source_drift_preserve_user_work(self):
        dest = self.root/'existing'
        dest.mkdir()
        (dest/'keep.txt').write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            packager.package(dest)
        self.assertEqual((dest/'keep.txt').read_text(), 'preserve')
        cloned = self.root/'controlled-support'
        shutil.copytree(packager.SUPPORT, cloned)
        (cloned/'kit/iso-kit.mjs').write_text('altered source')
        with patch.object(packager, 'SUPPORT', cloned):
            with self.assertRaisesRegex(ValueError, 'differs'):
                packager.package(self.root/'new')
        self.assertFalse((self.root/'new').exists())
