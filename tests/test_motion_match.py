#!/usr/bin/env python3
"""motion-match: rights boundary, exclusions, source records and the node:test suite."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT/'skills/motion-match'
RECORDS = SKILL/'references/upstream/reanimate'
UPSTREAM_REVISION = '3f7a55a2986a84ca2173e86ee9127eefe31d046d'
SCRIPTS = sorted((SKILL/'scripts').rglob('*.mjs'))
EXCLUDED_FILES = ('gl.ts', 'gl.mjs', 'gl-hooks.js', 'gl-hooks.mjs', 'webgl.md', 'setup.sh', 'bun.lock', 'package.json', 'package-lock.json')
RETIRED_FLAGS = re.compile(r"--gl\b|--assets\b|'gl'|'assets'|getShaderSource|\bfetch\(|https?\.get\(|curl |wget ")
LIBRARY_ADVICE = re.compile(r'GSAP|Framer Motion|framer-motion|three\.js|pixelmatch|pngjs|ffmpeg-static|\bbun\b', re.I)
IMPORTS = re.compile(r"""(?:^|\s)from\s+['"]([^'"]+)['"]|\bimport\(\s*['"]([^'"]+)['"]\s*\)|^import\s+['"]([^'"]+)['"]""", re.M)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MotionMatchTests(unittest.TestCase):
    def test_node_suite(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('node is not available')
        files = sorted(str(path) for path in (SKILL/'tests').glob('*.test.mjs'))
        self.assertGreaterEqual(len(files), 7)
        result = subprocess.run([node, '--test', *files], capture_output=True, text=True, timeout=240, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout[-6000:] + result.stderr[-2000:])

    def test_entrypoint_leads_with_rights_and_keeps_the_method(self):
        text = (SKILL/'SKILL.md').read_text()
        front, body = re.fullmatch(r'---\n(.*?\n)---\n(.*)', text, re.S).groups()
        self.assertLessEqual(len(body.split()), 1200)
        description = re.search(r'^description: "(.*)"$', front, re.M).group(1)
        self.assertLessEqual(len(description), 300)
        for neighbour in ('orbyn-ui-design', 'technical-illustration', 'product-illustration'):
            self.assertIn(neighbour, description)
        headings = re.findall(r'^## (.+)$', body, re.M)
        self.assertEqual(headings[0], 'Rights come first')
        self.assertLess(headings.index('Fidelity'), headings.index('Method'))
        self.assertEqual(headings[-1], 'Read when needed')
        for rule in ('Never copy their code, shaders, assets, fonts, brand, layout or copy',
                     'Never download someone else', 'stay closed', 'ignored local folder',
                     'Only the written numbers carry forward', 'Stop after 5 rounds'):
            self.assertIn(rule, body)
        self.assertIn('### Worked failure', body)

    def test_excluded_capabilities_are_absent(self):
        for name in EXCLUDED_FILES:
            self.assertEqual(list(SKILL.rglob(name)), [], name)
        self.assertFalse((SKILL/'site').exists())
        for path in SCRIPTS:
            self.assertIsNone(RETIRED_FLAGS.search(path.read_text()), path.name)
        for path in [SKILL/'SKILL.md', *sorted((SKILL/'references').glob('*.md')), *SCRIPTS]:
            self.assertIsNone(LIBRARY_ADVICE.search(path.read_text()), path.name)

    def test_scripts_import_only_node_and_relative_modules(self):
        for path in SCRIPTS:
            for match in IMPORTS.findall(path.read_text()):
                specifier = next(group for group in match if group)
                self.assertTrue(specifier.startswith(('node:', './', '../')), f'{path.name}: {specifier}')
                if specifier.startswith('.'):
                    self.assertTrue((path.parent/specifier).is_file(), f'{path.name}: {specifier}')

    def test_licence_and_records_pin_real_bytes(self):
        self.assertEqual((SKILL/'LICENSE').read_bytes(), (RECORDS/'LICENSE').read_bytes())
        self.assertIn('Copyright (c) 2026 Niaz Morshed', (SKILL/'LICENSE').read_text())
        snapshot = json.loads((RECORDS/'snapshot.json').read_text())
        self.assertEqual(snapshot['revision'], UPSTREAM_REVISION)
        for name, entry in snapshot['files'].items():
            self.assertEqual(sha256(RECORDS/name), entry['sha256'], name)
        manifest = json.loads((RECORDS/'source-manifest.json').read_text())
        self.assertEqual(manifest['revision'], UPSTREAM_REVISION)
        for name, entry in manifest['files'].items():
            self.assertEqual(sha256(SKILL/name), entry['sha256'], name)
            if entry['relationship'] == 'byte-identical-selected-source':
                self.assertEqual(entry['sha256'], entry['original_sha256'], name)
            self.assertIsNotNone(re.fullmatch('[0-9a-f]{64}', entry['original_sha256'] or '0'*64), name)
        adapted = {name for name, entry in manifest['files'].items() if entry['original_sha256']}
        expected = {'LICENSE', 'SKILL.md', 'references/capture.md', 'references/analysis.md',
                    'references/implementation.md', 'references/verify.md', 'scripts/capture.mjs',
                    'scripts/compare.mjs', 'scripts/easing.mjs', 'scripts/frames.mjs', 'scripts/lib.mjs',
                    'scripts/sheet.mjs', 'scripts/inpage/clock.mjs', 'scripts/inpage/inspect.mjs'}
        self.assertEqual(adapted, expected)
        tracked = {path.relative_to(SKILL).as_posix() for path in SKILL.rglob('*')
                   if path.is_file() and 'references/upstream' not in path.as_posix()
                   and '__pycache__' not in path.parts}
        self.assertEqual(tracked, set(manifest['files']), 'source-manifest.json must list every skill file')


if __name__ == '__main__':
    unittest.main()
