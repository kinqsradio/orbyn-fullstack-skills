"""Library integrity and renderer behavior with disposable fixtures."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


sync = module('library_inventory', ROOT/'scripts/library_manifest.py')
selection = module('skill_selection', ROOT/'scripts/skill_selection.py')
renderer = module('skill_render', ROOT/'skills/social-preview/scripts/render_preview.py')


def copy_fixture(source, destination, files):
    """Build synthetic asset fixtures, not a supported project installation."""
    for relative in files:
        src = sync.safe_path(source, relative)
        dst = sync.safe_path(destination, relative)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())


# Backwards-compatible test fixture name; deliberately absent from production.
sync.copy_changes = copy_fixture


class LibraryInventoryTests(unittest.TestCase):
    def test_inventory_matches_and_has_no_target_sync_api(self):
        self.assertEqual(sync.inventory(ROOT),sync.manifest(ROOT))
        self.assertFalse(hasattr(sync,'LOCK'))
        self.assertFalse(hasattr(sync,'write_lock'))
        self.assertFalse((ROOT/'scripts/install.py').exists())
        self.assertFalse((ROOT/'scripts/sync-public-skills.py').exists())
        for command in ('pin','pull','export','check'):
            with self.assertRaisesRegex(ValueError,'Only library'):
                sync.run(command,ROOT)

    def test_runnable_formal_sample_is_in_the_managed_library(self):
        assets = sync.inventory(ROOT)
        for name in ['LeasedJob.tla', 'fixed.cfg', 'broken.cfg', 'job.mjs', 'replay.mjs', 'demo.py']:
            self.assertIn('skills/architect/examples/leased-job/' + name, assets)
        self.assertIn('skills/architect/package.json', assets)
        self.assertIn('skills/architect/references/upstream/pstack-statechart/compiler/statechart.ts', assets)

    def test_colour_reference_gallery_assets_are_managed_without_screenshots(self):
        assets=sync.inventory(ROOT)
        for relative in ['assets/reference-palettes.json','references/colour-palettes.md',
                         'scripts/colour_contrast.py','scripts/build_colour_gallery.py',
                         'examples/colour-gallery/gallery.html','examples/colour-gallery/gallery.mjs',
                         'examples/colour-gallery/guide.md']:
            self.assertIn('skills/orbyn-ui-design/'+relative,assets)
        self.assertFalse(any(p.suffix.lower() in {'.jpg','.jpeg','.png'}
                             for p in (ROOT/'skills/orbyn-ui-design/examples/colour-gallery').rglob('*')))

    def test_asset_paths_cannot_escape_or_read_targets(self):
        for relative in ('../secret','/secret','repo/widget/skills/how/SKILL.md',
                         'project-skills/acme/acme-release/SKILL.md','skills/how/../../secret'):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                sync.safe_path(ROOT,relative)


class RendererTests(unittest.TestCase):


    def test_renderer_preserves_caption_and_escapes_html(self):
        post='<script>untrusted()</script>\n@@FEEDS@@ & literal text'
        html, result=renderer.render({'post':post,'slides':[]},ROOT)
        self.assertEqual(result,post)
        self.assertNotIn('<script>untrusted()</script>',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('@@FEEDS@@',html)

    def test_renderer_rejects_invalid_briefs_and_missing_alt(self):
        for brief in [{'post':'x','slieds':[]},{'post':'x','accent':'red; display:none'},
                      {'post':'x','slides':[{'title':'x','image':'missing.png'}]}]:
            with self.subTest(brief=brief), self.assertRaises(ValueError):
                renderer.render(brief,ROOT)

    def test_preview_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);brief=base/'brief.json';target=base/'existing'
            brief.write_text(json.dumps({'post':'Example'}));target.mkdir()
            marker=target/'owned.txt';marker.write_text('preserve')
            import sys
            result=subprocess.run([sys.executable,str(ROOT/'skills/social-preview/scripts/render_preview.py'),
                                   '--brief',str(brief),'--output',str(target)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertEqual(marker.read_text(),'preserve')
            self.assertFalse((target/'preview.html').exists())


if __name__ == '__main__':
    unittest.main()
