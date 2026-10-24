"""Regression checks for discovered source aliases and broken handoffs."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_tools import ROOT, module, installer

contracts = module('skill_contracts', ROOT/'scripts/skill_contracts.py')


class SkillContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.skill = self.root/'skills/example/SKILL.md'
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text('# Example\n\n## Actual step\n\n## Actual step\n')

    def test_nested_upstream_entrypoint_is_rejected_even_with_valid_canonical_skill(self):
        source = self.skill.parent/'references/upstream/vendor/SKILL.md'
        source.parent.mkdir(parents=True)
        source.write_text('---\nname: foreign-alias\n---\nUse a missing upstream skill.')
        self.assertIn('Unexpected active', '\n'.join(contracts.check_discovery(self.root, {'example'}, [])))
        source.rename(source.with_name('SOURCE.md'))
        self.assertEqual(contracts.check_discovery(self.root, {'example'}, []), [])

    def test_missing_related_owner_is_rejected(self):
        self.assertIn('unknown related skill ghost', '\n'.join(contracts.check_discovery(
            self.root, {'example'}, [{'name':'example','related':['ghost']} ])))

    def test_links_validate_fragments_duplicates_and_escaping_paths(self):
        guide = self.root/'guide.md'
        guide.write_text('[Good](skills/example/SKILL.md#actual-step-1)\n[Wrong](skills/example/SKILL.md#missing)\n[Escape](../secret.md)\n[Remote](https://example.com/#absent)\n')
        errors = contracts.check_links(self.root, guide)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any('fragment' in e for e in errors))
        self.assertTrue(any('escaping' in e for e in errors))

    def test_installed_all_skills_exposes_only_canonical_entrypoints_for_both_hosts(self):
        names = {entry['name'] for entry in json.loads((ROOT/'skills/catalog.json').read_text())['skills']}
        installer.install(self.root, 'both', all_skills=True)
        for host in ['.agents', '.claude']:
            discovered = []
            # Host links point to canonical folders; recursively inspect each target.
            for link in (self.root/host/'skills').iterdir():
                discovered.extend(p for p in link.resolve().rglob('SKILL.md'))
            self.assertEqual(len(discovered), len(names))
            self.assertEqual({p.parent.name for p in discovered}, names)
            self.assertNotIn('marketingskills-social', {p.parent.name for p in discovered})
            self.assertNotIn('anthropic-canvas-design', {p.parent.name for p in discovered})

    def test_installer_refuses_nested_source_before_writing_project(self):
        (self.root/'skills/catalog.json').write_text((ROOT/'skills/catalog.json').read_text())
        base = self.root/'skills/how'
        base.mkdir()
        (base/'SKILL.md').write_text('Canonical entrypoint')
        nested = base/'references/SKILL.md'
        nested.parent.mkdir()
        nested.write_text('Unexpected active source')
        project = self.root/'consumer'
        project.mkdir()
        with mock.patch.object(installer, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Nested active entrypoints'):
                installer.install(project, 'both', ['how'])
        self.assertEqual(list(project.iterdir()), [])

    def test_source_checker_rejects_discoverable_filename_even_with_valid_hash(self):
        import shutil
        base = self.root/'skills/social-content/references/upstream/vendor'
        shutil.copytree(ROOT/'skills/social-content/references/upstream/marketingskills-social', base)
        manifest = base/'snapshot.json'
        data = json.loads(manifest.read_text())
        data['files']['SKILL.md'] = data['files'].pop('SOURCE.md')
        (base/'SOURCE.md').rename(base/'SKILL.md')
        manifest.write_text(json.dumps(data))
        checker = module('source_discovery_guard', ROOT/'skills/orbyn-skill-creator/scripts/check_sources.py')
        with self.assertRaisesRegex(ValueError, 'active SKILL.md'):
            checker.check(self.root)

    def test_audit_must_cover_current_catalog_once(self):
        docs = self.root/'docs'
        docs.mkdir()
        audit = docs/'skill-audit.md'
        row = '| [example](../skills/example/SKILL.md) | Reviewed | Input → result | Limit |\n'
        audit.write_text(row)
        self.assertEqual(contracts.check_audit(self.root, {'example'}), [])
        audit.write_text(row.replace(') |', ')       |'))
        self.assertEqual(contracts.check_audit(self.root, {'example'}), [])
        self.assertTrue(contracts.check_audit(self.root, {'example','new-skill'}))
        audit.write_text(row+row)
        self.assertTrue(contracts.check_audit(self.root, {'example'}))
