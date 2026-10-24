"""Language routing and installed offline behavior, using disposable consumers."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'skills/language-best-practices'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


router = load('language_router', GUIDE / 'scripts/language_guides.py')
installer = load('language_installer', ROOT / 'scripts/install.py')


class LanguageRoutingTests(unittest.TestCase):
    def test_polyglot_contract_selects_local_typescript_guide(self):
        result = router.route(['api/main.go', 'ui/state.ts', 'db/change.sql', 'README.md'])
        selected = {row['language']: row['reference'] for row in result['guides']}
        self.assertEqual(set(selected), {'go', 'typescript', 'sql'})
        self.assertEqual(selected['typescript'], 'references/typescript.md')
        self.assertEqual(result['unmatched'], ['README.md'])

    def test_header_is_ambiguous_and_uppercase_c_is_cpp(self):
        result = router.route(['shared/contract.h', 'native/entry.C', 'native/types.hpp', 'native/api.c'])
        self.assertEqual(result['ambiguous'], [{'path': 'shared/contract.h', 'candidates': ['c', 'cpp']}])
        selected = {row['language']: row['paths'] for row in result['guides']}
        self.assertEqual(selected['cpp'], ['native/entry.C', 'native/types.hpp'])
        self.assertEqual(selected['c'], ['native/api.c'])

    def test_relative_path_boundary(self):
        for path in ('', '.', '../secret.py', '/tmp/code.py', 'drive:code.py', 'a\\code.py', 'bad\x00.py'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                router.route([path])

    def test_paths_are_data_not_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / 'executed'
            name = f'code$(touch {marker.name}).py'
            result = subprocess.run([sys.executable, str(GUIDE / 'scripts/language_guides.py'), name],
                                    cwd=folder, check=True, capture_output=True, text=True)
            self.assertFalse(marker.exists())
            self.assertEqual(json.loads(result.stdout)['guides'][0]['paths'], [name])

    def test_guides_are_portable_offline_assets(self):
        registry = json.loads((GUIDE / 'references/routes.json').read_text())
        self.assertEqual(len(registry['guides']), 13)
        for relative in registry['guides'].values():
            resolved = (GUIDE / relative).resolve()
            self.assertTrue(resolved.is_relative_to(ROOT / 'skills'))
            self.assertTrue(resolved.is_file(), relative)
            self.assertTrue(resolved.read_text().strip())

    def test_unmatched_language_does_not_choose_a_stack(self):
        result = router.route(['main.ex', 'Dockerfile', 'Makefile', '.env'])
        self.assertEqual(result['guides'], [])
        self.assertEqual(len(result['unmatched']), 4)

    def test_additive_install_routes_from_both_hosts(self):
        with tempfile.TemporaryDirectory() as folder:
            consumer = Path(folder)
            policy = consumer / 'AGENTS.md'
            policy.write_text('Existing company ownership stays here.')
            installer.install(consumer, 'both', presets=['core'])
            for host in ('.agents', '.claude'):
                link = consumer / host / 'skills/language-best-practices'
                run = subprocess.run([sys.executable, str(link / 'scripts/language_guides.py'), 'service/main.py'],
                                     check=True, capture_output=True, text=True)
                reference = json.loads(run.stdout)['guides'][0]['reference']
                self.assertTrue((link / reference).is_file())
                self.assertTrue((consumer / host / 'skills/orbyn-stack-selection/SKILL.md').is_file())
            self.assertEqual(policy.read_text(), 'Existing company ownership stays here.')

    def test_duplicate_paths_have_one_owner_entry(self):
        result = router.route(['src/main.rs', 'src/main.rs'])
        self.assertEqual(result['guides'][0]['paths'], ['src/main.rs'])


if __name__ == '__main__':
    unittest.main()
