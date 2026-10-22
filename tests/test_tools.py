"""Observable sync/install boundaries using disposable repositories and files."""
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


sync = module('skill_sync', ROOT/'scripts/sync-public-skills.py')
installer = module('skill_install', ROOT/'scripts/install.py')
renderer = module('skill_render', ROOT/'skills/social-preview/scripts/render_preview.py')


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.upstream, self.consumer = self.base/'upstream', self.base/'consumer'
        (self.upstream/'skills/example').mkdir(parents=True)
        (self.upstream/'skills/example/SKILL.md').write_text('---\nname: example\ndescription: A real fixture\n---\nInitial behavior.\n')
        (self.upstream/'skills/example/LICENSE').write_text('MIT fixture')
        (self.upstream/'skills/catalog.json').write_text(json.dumps({'skills':[{'name':'example'}]}))
        (self.upstream/'skills/README.md').write_text('Fixture skill index\n')
        self.invoke('manifest', self.upstream, write=True)
        self.git('init', '-b', 'main')
        self.commit()
        shutil.copytree(self.upstream/'skills', self.consumer/'skills')
        self.invoke('pin', self.consumer, self.upstream)

    def git(self, *args):
        return subprocess.check_output(['git','-C',str(self.upstream),*args],stderr=subprocess.STDOUT,text=True)

    def commit(self):
        self.git('add','skills','distribution')
        self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Fixture change','--no-verify')

    def invoke(self, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return sync.run(*args, **kwargs)

    def edit(self, root, text):
        (root/'skills/example/SKILL.md').write_text(text)

    def test_pin_check_and_drift(self):
        self.invoke('check', self.consumer)
        self.edit(self.consumer, 'A changed local contract')
        with self.assertRaisesRegex(ValueError, 'differ from upstream'):
            self.invoke('check', self.consumer)

    def test_pull_updates_content_and_preserves_private_files(self):
        private = self.consumer/'private.txt'
        private.write_text('consumer-only payload')
        self.edit(self.upstream, 'Reviewed public update')
        self.invoke('manifest', self.upstream, write=True)
        self.commit()
        self.invoke('pull', self.consumer, self.upstream)
        self.assertEqual((self.consumer/'skills/example/SKILL.md').read_text(), 'Reviewed public update')
        self.assertEqual(private.read_text(), 'consumer-only payload')
        self.invoke('check', self.consumer)

    def test_pull_refuses_local_edits_before_mutation(self):
        self.edit(self.consumer, 'Local work')
        with self.assertRaisesRegex(ValueError, 'local skill edits'):
            self.invoke('pull', self.consumer, self.upstream)
        self.assertEqual((self.consumer/'skills/example/SKILL.md').read_text(), 'Local work')

    def test_export_dry_run_and_allowlist(self):
        self.edit(self.consumer, 'Public-safe contribution')
        (self.consumer/'private.txt').write_text('not exported')
        self.git('checkout','-b','feat/contract-improvement')
        self.invoke('export', self.consumer, self.upstream)
        self.assertIn('Initial behavior', (self.upstream/'skills/example/SKILL.md').read_text())
        self.invoke('export', self.consumer, self.upstream, write=True)
        self.assertEqual((self.upstream/'skills/example/SKILL.md').read_text(), 'Public-safe contribution')
        self.assertFalse((self.upstream/'private.txt').exists())
        sync.manifest(self.upstream)

    def test_export_requires_contribution_branch(self):
        self.edit(self.consumer, 'A contribution')
        with self.assertRaisesRegex(ValueError, 'contribution branch'):
            self.invoke('export', self.consumer, self.upstream, write=True)
        self.assertIn('Initial behavior', (self.upstream/'skills/example/SKILL.md').read_text())

    def test_divergent_edits_are_conflicts(self):
        self.edit(self.consumer, 'Consumer design')
        self.edit(self.upstream, 'Different public design')
        self.invoke('manifest', self.upstream, write=True)
        self.commit()
        self.git('checkout','-b','feat/conflicting-improvement')
        with self.assertRaisesRegex(ValueError, 'Both consumer and upstream'):
            self.invoke('export', self.consumer, self.upstream, write=True)
        self.assertEqual((self.upstream/'skills/example/SKILL.md').read_text(), 'Different public design')

    def test_reconciled_consumer_can_adopt_merged_pin(self):
        self.edit(self.consumer, 'Same reviewed design')
        self.edit(self.upstream, 'Same reviewed design')
        self.invoke('manifest', self.upstream, write=True)
        self.commit()
        self.invoke('pull', self.consumer, self.upstream)
        self.invoke('check', self.consumer)

    def test_manifest_paths_cannot_escape(self):
        for path in ['../private.txt','/tmp/outside','skills/example/../../private.txt','backend/config.json','skills/example/.env']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                sync.safe_path(self.consumer, path)

    def test_skill_symlink_and_control_symlink_are_refused(self):
        outside = self.base/'outside'
        outside.write_text('do not touch')
        (self.consumer/'skills/example/escape.md').symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            sync.inventory(self.consumer)
        (self.consumer/'skills/example/escape.md').unlink()
        (self.consumer/sync.LOCK).unlink()
        (self.consumer/sync.LOCK).symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.invoke('pin', self.consumer, self.upstream)
        self.assertEqual(outside.read_text(), 'do not touch')

    def test_manifest_tampering_is_refused(self):
        data = json.loads((self.upstream/sync.MANIFEST).read_text())
        data['files']['backend/config.json'] = '0'*64
        (self.upstream/sync.MANIFEST).write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'allowlist'):
            sync.manifest(self.upstream)


class InstallerAndRendererTests(unittest.TestCase):
    def test_install_is_idempotent_and_preserves_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            (project/'AGENTS.md').write_text('Local policy')
            self.assertEqual(installer.install(project,'both',['how']),2)
            self.assertEqual(installer.install(project,'both',['how']),0)
            self.assertEqual((project/'AGENTS.md').read_text(),'Local policy')
            self.assertFalse((project/'.codex/config.toml').exists())

    def test_install_preflights_all_hosts(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            (project/'.claude').write_text('existing user file')
            with self.assertRaises(ValueError):
                installer.install(project,'both',['how'])
            self.assertFalse((project/'.agents').exists())

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
