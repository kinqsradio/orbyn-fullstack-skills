"""Model-sync CLI boundaries in disposable repositories; no inference or network."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ModelRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in ['docs/agents/models.json', 'docs/agents/model-policy.md',
                         'scripts/sync-agent-models.py', '.codex/config.toml',
                         '.claude/settings.json', '.codex/agents/orbyn-agent.toml',
                         '.codex/agents/orbyn-light.toml', '.codex/agents/orbyn-middle.toml',
                         '.claude/agents/orbyn-agent.md', '.claude/agents/orbyn-light.md']:
            dest = self.root/relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/relative, dest)
        self.source = self.root/'docs/agents/models.json'

    def change(self, mutate):
        data = json.loads(self.source.read_text())
        mutate(data)
        self.source.write_text(json.dumps(data))

    def run_sync(self, mode, ok=True):
        result = subprocess.run([sys.executable, str(self.root/'scripts/sync-agent-models.py'), mode],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout+result.stderr)
        return result

    def snapshot(self):
        return {str(p.relative_to(self.root)):p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_optional_codex_generation_preserves_defaults_claude_and_foreign_settings(self):
        claude = {str(p.relative_to(self.root)):p.read_bytes()
                  for p in (self.root/'.claude').rglob('*') if p.is_file()}
        config = self.root/'.codex/config.toml'
        config.write_text(config.read_text()+'\n[projects.fixture]\ntrust_level = "trusted"\n')
        self.run_sync('--write')
        settings = tomllib.loads(config.read_text())
        self.assertEqual((settings['model'],settings['model_reasoning_effort'],settings['service_tier']),
                         ('gpt-6.1-sol','medium','default'))
        self.assertEqual(settings['projects']['fixture']['trust_level'],'trusted')
        self.assertFalse(settings['features']['fast_mode'])
        self.assertFalse(settings['features']['ultrafast_mode'])
        self.assertEqual(set(settings['agents'])-{'max_threads'},
                         {'orbyn-agent','orbyn-light','orbyn-middle'})
        middle = tomllib.loads((self.root/'.codex/agents/orbyn-middle.toml').read_text())
        self.assertEqual((middle['model'],middle['model_reasoning_effort']),('gpt-6.1-terra','medium'))
        light = tomllib.loads((self.root/'.codex/agents/orbyn-light.toml').read_text())
        self.assertEqual((light['model'],light['model_reasoning_effort']),('gpt-6-luna','high'))
        self.assertEqual(claude,{str(p.relative_to(self.root)):p.read_bytes()
                                for p in (self.root/'.claude').rglob('*') if p.is_file()})
        self.assertFalse((self.root/'.claude/agents/orbyn-middle.md').exists())
        before=self.snapshot()
        self.run_sync('--write')
        self.run_sync('--check')
        self.assertEqual(before,self.snapshot())

    def test_trailing_comment_on_owned_key_is_not_drift_and_survives_update(self):
        self.run_sync('--write')
        config = self.root/'.codex/config.toml'
        lines = config.read_text().splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith('model = '))
        lines[index] += ' # reviewed "pin"'
        config.write_text('\n'.join(lines)+'\n')
        self.run_sync('--check')
        self.change(lambda data: data['agents']['orbyn-agent']['codex'].update(model='gpt-fixture'))
        self.run_sync('--write')
        self.assertIn('model = "gpt-fixture" # reviewed "pin"\n', config.read_text())
        self.assertEqual(tomllib.loads(config.read_text())['model'], 'gpt-fixture')

    def test_optional_cannot_be_default_for_either_host(self):
        original=self.source.read_bytes()
        for host in ['codex','claude']:
            with self.subTest(host=host):
                self.source.write_bytes(original)
                self.change(lambda d:d['defaults'].update({host:'orbyn-middle'}))
                before=self.snapshot()
                self.run_sync('--write',ok=False)
                self.assertEqual(before,self.snapshot())

    def test_optional_requires_explicit_selection_and_codex_only(self):
        original=self.source.read_bytes()
        mutations=[lambda a:a.update(selection='automatic'),lambda a:a.pop('selection'),
                   lambda a:a.update(claude={'model':'sonnet','effort':'medium'}),
                   lambda a:a.pop('codex')]
        for index,mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.source.write_bytes(original)
                self.change(lambda d:mutate(d['agents']['orbyn-middle']))
                before=self.snapshot()
                self.run_sync('--write',ok=False)
                self.assertEqual(before,self.snapshot())

    def test_optional_drift_check_is_read_only_and_write_repairs_it(self):
        self.run_sync('--write')
        path=self.root/'.codex/agents/orbyn-middle.toml'
        path.write_text(path.read_text().replace('gpt-6.1-terra','gpt-6-luna'))
        before=self.snapshot()
        result=self.run_sync('--check',ok=False)
        self.assertIn('orbyn-middle.toml',result.stderr)
        self.assertEqual(before,self.snapshot())
        self.run_sync('--write')
        self.run_sync('--check')

    def test_default_tiers_require_both_providers_before_any_writes(self):
        original=self.source.read_bytes()
        for name in ['orbyn-agent','orbyn-light']:
            for host in ['codex','claude']:
                with self.subTest(name=name,host=host):
                    self.source.write_bytes(original)
                    self.change(lambda d:d['agents'][name].pop(host))
                    before=self.snapshot()
                    result=self.run_sync('--write',ok=False)
                    self.assertIn('Both providers required',result.stderr)
                    self.assertEqual(before,self.snapshot())

    def test_accelerated_or_human_only_optional_model_is_rejected_atomically(self):
        original=self.source.read_bytes()
        for model in ['gpt-6-astra','gpt-6.1-terra-fast','priority-model']:
            with self.subTest(model=model):
                self.source.write_bytes(original)
                self.change(lambda d:d['agents']['orbyn-middle']['codex'].update(model=model))
                before=self.snapshot()
                self.run_sync('--write',ok=False)
                self.assertEqual(before,self.snapshot())

    def test_invalid_claude_metadata_does_not_partially_write_codex(self):
        self.change(lambda d:d['agents']['orbyn-agent'].update(purpose='Invalid: YAML metadata'))
        before=self.snapshot()
        self.run_sync('--write',ok=False)
        self.assertEqual(before,self.snapshot())

    def test_processing_cannot_be_accelerated(self):
        self.change(lambda d:d['processing'].update(codex_service_tier='priority'))
        before=self.snapshot()
        self.run_sync('--write',ok=False)
        self.assertEqual(before,self.snapshot())
