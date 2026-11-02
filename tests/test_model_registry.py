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
                         '.claude/settings.json', '.codex/agents/orbyn-lead.toml',
                         '.codex/agents/orbyn-scout.toml', '.codex/agents/orbyn-worker.toml',
                         '.claude/agents/orbyn-lead.md', '.claude/agents/orbyn-scout.md',
                         '.claude/agents/orbyn-worker.md',
                         'skills/orbyn-workflow/scripts/harness.py',
                         'skills/orbyn-workflow/references/harness-defaults.json']:
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

    def test_generation_preserves_foreign_settings_and_writes_three_tiers(self):
        config = self.root/'.codex/config.toml'
        config.write_text(config.read_text()+'\n[projects.fixture]\ntrust_level = "trusted"\n')
        settings_path = self.root/'.claude/settings.json'
        settings = json.loads(settings_path.read_text())
        settings['permissions'] = {'allow': ['Bash(ls)']}
        settings['env']['FOREIGN'] = 'kept'
        settings_path.write_text(json.dumps(settings))
        self.run_sync('--write')
        loaded = tomllib.loads(config.read_text())
        self.assertEqual((loaded['model'],loaded['model_reasoning_effort'],loaded['service_tier']),
                         ('gpt-6.1-sol','medium','default'))
        self.assertEqual(loaded['projects']['fixture']['trust_level'],'trusted')
        self.assertFalse(loaded['features']['fast_mode'])
        self.assertFalse(loaded['features']['ultrafast_mode'])
        self.assertEqual(set(loaded['agents'])-{'max_concurrent_threads_per_session'},
                         {'orbyn-lead','orbyn-worker','orbyn-scout'})
        for name,model,effort in [('lead','gpt-6.1-sol','medium'),('worker','gpt-6.1-terra','medium'),
                                  ('scout','gpt-6-luna','medium')]:
            agent = tomllib.loads((self.root/f'.codex/agents/orbyn-{name}.toml').read_text())
            self.assertEqual((agent['model'],agent['model_reasoning_effort']),(model,effort))
        for name,model in [('lead','opus'),('worker','sonnet'),('scout','haiku')]:
            text = (self.root/f'.claude/agents/orbyn-{name}.md').read_text()
            self.assertIn(f'model: {model}\n',text)
            self.assertIn('disallowedTools: Agent, Task',text)
        after = json.loads(settings_path.read_text())
        self.assertEqual(after['permissions'],{'allow':['Bash(ls)']})
        self.assertEqual(after['env']['FOREIGN'],'kept')
        self.assertEqual(after['env']['CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS'],'2')
        self.assertEqual(after['env']['CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH'],'1')
        before=self.snapshot()
        self.run_sync('--write')
        self.run_sync('--check')
        self.assertEqual(before,self.snapshot())

    def test_retired_max_threads_is_replaced_by_the_current_codex_key(self):
        config = self.root/'.codex/config.toml'
        config.write_text(config.read_text().replace('max_concurrent_threads_per_session = 2','max_threads = 5'))
        self.run_sync('--write')
        agents = tomllib.loads(config.read_text())['agents']
        self.assertNotIn('max_threads',agents)
        self.assertEqual(agents['max_concurrent_threads_per_session'],2)

    def test_delegation_defaults_drive_both_hosts(self):
        self.change(lambda d:d['delegation'].update(max_children=3,max_depth=2,read_only_children_extra=1))
        self.run_sync('--write')
        env = json.loads((self.root/'.claude/settings.json').read_text())['env']
        self.assertEqual((env['CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS'],env['CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH']),('4','2'))
        codex = tomllib.loads((self.root/'.codex/config.toml').read_text())
        self.assertEqual(codex['agents']['max_concurrent_threads_per_session'],4)
        self.assertNotIn('max_depth',codex['agents'])
        defaults = json.loads((self.root/'skills/orbyn-workflow/references/harness-defaults.json').read_text())
        self.assertEqual(defaults['delegation']['max_children'],3)

    def test_host_enforceable_delegation_range_is_required(self):
        original=self.source.read_bytes()
        for patch in [dict(max_children=0),dict(max_children=9),dict(max_depth=4),dict(max_depth=0),
                      dict(read_only_children_extra=-1),dict(max_children=8,read_only_children_extra=1),
                      dict(max_children=True)]:
            with self.subTest(patch=patch):
                self.source.write_bytes(original)
                self.change(lambda d:d['delegation'].update(patch))
                before=self.snapshot()
                self.run_sync('--write',ok=False)
                self.assertEqual(before,self.snapshot())

    def test_trailing_comment_on_owned_key_is_not_drift_and_survives_update(self):
        self.run_sync('--write')
        config = self.root/'.codex/config.toml'
        lines = config.read_text().splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith('model = '))
        lines[index] += ' # reviewed "pin"'
        config.write_text('\n'.join(lines)+'\n')
        self.run_sync('--check')
        self.change(lambda data: (data['agents']['orbyn-lead']['codex'].update(model='gpt-fixture'),
                                  data['allowed_models']['codex'].update(lead=['gpt-fixture'])))
        self.run_sync('--write')
        self.assertIn('model = "gpt-fixture" # reviewed "pin"\n', config.read_text())
        self.assertEqual(tomllib.loads(config.read_text())['model'], 'gpt-fixture')

    def test_parent_default_must_be_the_lead_tier_for_either_host(self):
        original=self.source.read_bytes()
        for host in ['codex','claude']:
            for name in ['orbyn-worker','orbyn-scout']:
                with self.subTest(host=host,name=name):
                    self.source.write_bytes(original)
                    self.change(lambda d:d['defaults'].update({host:name}))
                    before=self.snapshot()
                    self.run_sync('--write',ok=False)
                    self.assertEqual(before,self.snapshot())

    def test_each_agent_must_declare_its_tier_and_nothing_else(self):
        original=self.source.read_bytes()
        mutations=[lambda a:a.update(tier='lead'),lambda a:a.pop('tier'),
                   lambda a:a.update(selection='explicit'),lambda a:a.update(tier='scout')]
        for index,mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.source.write_bytes(original)
                self.change(lambda d:mutate(d['agents']['orbyn-worker']))
                before=self.snapshot()
                self.run_sync('--write',ok=False)
                self.assertEqual(before,self.snapshot())

    def test_worker_drift_check_is_read_only_and_write_repairs_it(self):
        self.run_sync('--write')
        path=self.root/'.codex/agents/orbyn-worker.toml'
        path.write_text(path.read_text().replace('gpt-6.1-terra','gpt-6-luna'))
        before=self.snapshot()
        result=self.run_sync('--check',ok=False)
        self.assertIn('orbyn-worker.toml',result.stderr)
        self.assertEqual(before,self.snapshot())
        self.run_sync('--write')
        self.run_sync('--check')

    def test_portable_defaults_drift_is_reported_and_repaired(self):
        path=self.root/'skills/orbyn-workflow/references/harness-defaults.json'
        path.write_text(path.read_text().replace('"max_children": 2','"max_children": 5'))
        result=self.run_sync('--check',ok=False)
        self.assertIn('harness-defaults.json',result.stderr)
        self.run_sync('--write')
        self.run_sync('--check')

    def test_every_agent_requires_both_providers_before_any_writes(self):
        original=self.source.read_bytes()
        for name in ['orbyn-lead','orbyn-worker','orbyn-scout']:
            for host in ['codex','claude']:
                with self.subTest(name=name,host=host):
                    self.source.write_bytes(original)
                    self.change(lambda d:d['agents'][name].pop(host))
                    before=self.snapshot()
                    self.run_sync('--write',ok=False)
                    self.assertEqual(before,self.snapshot())

    def test_accelerated_or_human_only_model_in_any_tier_is_rejected_atomically(self):
        original=self.source.read_bytes()
        for name in ['orbyn-lead','orbyn-worker','orbyn-scout']:
            for model in ['gpt-6-astra','gpt-6.1-terra-fast','priority-model']:
                with self.subTest(name=name,model=model):
                    self.source.write_bytes(original)
                    self.change(lambda d:d['agents'][name]['codex'].update(model=model))
                    before=self.snapshot()
                    self.run_sync('--write',ok=False)
                    self.assertEqual(before,self.snapshot())

    def test_effort_above_a_models_cap_is_rejected_atomically(self):
        original=self.source.read_bytes()
        for name,host in [('orbyn-lead','codex'),('orbyn-worker','codex'),('orbyn-worker','claude')]:
            with self.subTest(name=name,host=host):
                self.source.write_bytes(original)
                self.change(lambda d:d['agents'][name][host].update(effort='high'))
                before=self.snapshot()
                result=self.run_sync('--write',ok=False)
                self.assertIn('cap',result.stderr)
                self.assertEqual(before,self.snapshot())

    def test_caps_must_cover_the_expensive_models_and_fable_records_its_cap(self):
        original=self.source.read_bytes()
        mutations=[lambda d:d['effort_caps'].pop('fable'),lambda d:d['human_only']['claude'].pop('effort_cap'),
                   lambda d:d['effort_caps'].update({'fable':'high'}),lambda d:d['effort_caps'].update({'sonnet':'extreme'})]
        for index,mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.source.write_bytes(original)
                self.change(mutate)
                before=self.snapshot()
                self.run_sync('--write',ok=False)
                self.assertEqual(before,self.snapshot())

    def test_routing_must_keep_security_at_the_lead_tier(self):
        self.change(lambda d:d['routing'].update(security='worker'))
        before=self.snapshot()
        self.run_sync('--write',ok=False)
        self.assertEqual(before,self.snapshot())

    def test_invalid_claude_metadata_does_not_partially_write_codex(self):
        self.change(lambda d:d['agents']['orbyn-lead'].update(purpose='Invalid: YAML metadata'))
        before=self.snapshot()
        self.run_sync('--write',ok=False)
        self.assertEqual(before,self.snapshot())

    def test_processing_cannot_be_accelerated(self):
        self.change(lambda d:d['processing'].update(codex_service_tier='priority'))
        before=self.snapshot()
        self.run_sync('--write',ok=False)
        self.assertEqual(before,self.snapshot())

    def test_generated_agent_bodies_drift_is_reported_and_repaired(self):
        self.run_sync('--write')
        for relative, old in [('.claude/agents/orbyn-scout.md', 'You never decide, design, debug or write new logic.'),
                              ('.codex/agents/orbyn-worker.toml', 'Do not decide architecture'),
                              ('.claude/agents/orbyn-lead.md', 'disallowedTools: Agent, Task'),
                              ('.claude/agents/orbyn-worker.md', 'Do not run tests unless authorized.')]:
            with self.subTest(relative=relative):
                path = self.root/relative
                original = path.read_text()
                path.write_text(original.replace(old, 'You may decide and design.' if 'disallowed' not in old else 'disallowedTools: Task'))
                self.assertIn(Path(relative).name, self.run_sync('--check', ok=False).stderr)
                self.run_sync('--write')
                self.assertEqual(path.read_text(), original)

    def test_unexpected_agent_definitions_are_refused_before_any_write(self):
        for relative in ['.claude/agents/orbyn-agent.md', '.codex/agents/orbyn-astra.toml']:
            with self.subTest(relative=relative):
                stray = self.root/relative
                stray.write_text('model: fable\n')
                before = self.snapshot()
                self.assertIn('Unexpected agent definitions', self.run_sync('--write', ok=False).stderr)
                self.assertIn('Unexpected agent definitions', self.run_sync('--check', ok=False).stderr)
                self.assertEqual(before, self.snapshot())
                stray.unlink()

    def test_codex_max_depth_is_not_generated_and_is_removed(self):
        config = self.root/'.codex/config.toml'
        config.write_text(config.read_text().replace('[agents]\n', '[agents]\nmax_depth = 5\n', 1))
        self.assertIn('.codex/config.toml', self.run_sync('--check', ok=False).stderr)
        self.run_sync('--write')
        self.assertNotIn('max_depth', tomllib.loads(config.read_text())['agents'])

    def test_a_lead_child_is_told_not_to_delegate_and_the_harness_path_is_absolute(self):
        for relative in ['.claude/agents/orbyn-lead.md', '.codex/agents/orbyn-lead.toml']:
            text = (self.root/relative).read_text()
            self.assertIn('If you were spawned as a child', text)
            self.assertIn('do not delegate', text)
            self.assertIn('by absolute path', text)
            self.assertIn('never fall back to defaults', text)
            self.assertNotIn('As a lead, delegate', text)

    def test_allowed_models_must_start_with_the_tier_model_and_avoid_human_only_names(self):
        original = self.source.read_bytes()
        mutations = [lambda d: d['allowed_models']['claude']['worker'].reverse(),
                     lambda d: d['allowed_models']['claude']['worker'].append('fable'),
                     lambda d: d['allowed_models']['codex']['scout'].append('gpt-6.1-luna-fast'),
                     lambda d: d['allowed_models']['codex'].pop('lead'),
                     lambda d: d.pop('allowed_models')]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.source.write_bytes(original)
                self.change(mutate)
                before = self.snapshot()
                self.run_sync('--write', ok=False)
                self.assertEqual(before, self.snapshot())

    def test_the_security_roles_must_stay_on_the_lead_tier(self):
        original = self.source.read_bytes()
        for role in ['security_verifier', 'security_engineer']:
            with self.subTest(role=role):
                self.source.write_bytes(original)
                self.change(lambda d: d['routing'].update({role: 'worker'}))
                before = self.snapshot()
                self.run_sync('--write', ok=False)
                self.assertEqual(before, self.snapshot())
