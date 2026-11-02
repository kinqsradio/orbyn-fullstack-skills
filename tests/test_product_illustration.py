#!/usr/bin/env python3
"""Static licensing and integrity contract for product-illustration; needs no npm install."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('skills/product-illustration')
KIT = SKILL/'references/upstream/stageshow'

EXCLUDED_PATHS = (
    'assets', 'kit/brands', 'package-lock.json', 'SKILL.md', 'AGENTS.md', 'node_modules',
    *(f'examples/{name}' for name in (
        'figma', 'linear', 'slack', 'raycast', 'finder', 'finder-glass', 'spotify', 'notion',
        'gmail', 'google-calendar', 'google-docs', 'powerpoint', 'excel', 'wikipedia',
        'telegram', 'imessage', 'brand-marks', 'monochrome')),
)
EXCLUDED_IMPORT = re.compile(
    r'(app-icons|/brands(/|$)|(^|/)(figma|linear|slack|raycast|finder|finder-glass|spotify|notion|gmail'
    r'|google-calendar|google-docs|powerpoint|excel|wikipedia|telegram|imessage|brand-marks|monochrome)/)')
EXCLUDED_MEDIA = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.otf'}
ANY_CASE = (
    'figma', 'slack', 'raycast', 'spotify', 'notion', 'gmail', 'google', 'powerpoint', 'excel', 'wikipedia',
    'telegram', 'imessage', 'iphone', 'ipad', 'macbook', 'macos', 'safari', 'android', 'microsoft', 'apple',
    'stripe', 'paypal', 'mastercard', 'american express', 'dropbox', 'github', 'vercel', 'shopify', 'radix',
    'tailwind', 'northwind', 'globex', 'hooli', 'initech', 'vandelay', 'claude', 'anthropic', 'openai',
    'dynamic island', 'liquid glass', 'testflight', 'blue bottle', 'portless', 'sf pro', 'sf mono', 'segoe',
)
BRANDS = re.compile(r'\b(?:(?i:' + '|'.join(ANY_CASE) + r')|Linear|Finder|Chase|Visa|iOS)\b|-apple-system|BlinkMac')
# Records that must name what was left out, and the gate's detection data.
BRAND_RECORDS = {'SOURCE.md', 'source-manifest.json', 'guides.json', 'snapshot.json'}
DETECTOR = re.compile(r'^\s*const BRANDS = /')
EXPECTED_DEPENDENCIES = {'react', 'react-dom', 'lucide-react'}
EXPECTED_DEV = {'@types/react', '@types/react-dom', '@vitejs/plugin-react', 'vite', 'typescript',
                'playwright-core', 'postcss'}
IMPORTS = re.compile(
    r"""(?:^|[\s;])import\s+(?:[^'"\n]*?\s+from\s+)?['"]([^'"]+)['"]"""
    r"""|^\s*export\s+[^'"\n]*?\s+from\s+['"]([^'"]+)['"]"""
    r"""|\bimport\(\s*['"]([^'"]+)['"]\s*\)"""
    r"""|new URL\(\s*['"]([^'"]+)['"]\s*,\s*import\.meta\.url"""
    r"""|@import\s+(?:url\()?['"]([^'"]+)['"]""", re.M)


def specifiers(text):
    return [next(group for group in match if group) for match in IMPORTS.findall(text)]


def source_files(kit):
    return [p for p in sorted(kit.rglob('*')) if p.is_file() and p.suffix in {'.ts', '.tsx', '.css', '.mjs'}]


def resolves(path, specifier):
    target = path.parent/specifier
    return any(c.is_file() for c in (
        target, *(Path(f'{target}{suffix}') for suffix in ('.ts', '.tsx', '.css', '.mjs')),
        target/'index.ts', target/'index.tsx'))


def import_violations(root):
    """Relative imports that dangle or reach excluded material, from any kept source."""
    found = []
    kit = root/KIT
    for path in source_files(kit):
        for specifier in specifiers(path.read_text(encoding='utf-8')):
            name = path.relative_to(kit)
            if EXCLUDED_IMPORT.search(specifier):
                found.append(f'{name}: imports excluded {specifier}')
            elif specifier.startswith('.') and not resolves(path, specifier):
                found.append(f'{name}: unresolved {specifier}')
    return found


def excluded_paths(root):
    kit = root/KIT
    found = [name for name in EXCLUDED_PATHS if (kit/name).exists()]
    found += [p.relative_to(kit).as_posix() for p in kit.rglob('*')
              if p.is_file() and p.suffix.lower() in EXCLUDED_MEDIA]
    return found


def brand_hits(root):
    found = []
    for path in sorted((root/SKILL).rglob('*')):
        if not path.is_file() or path.name in BRAND_RECORDS:
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if BRANDS.search(line) and not DETECTOR.match(line):
                found.append(f'{path.relative_to(root/SKILL)}:{number}: {BRANDS.search(line).group()}')
    return found


class ProductIllustrationContract(unittest.TestCase):
    def test_excluded_material_is_absent(self):
        self.assertEqual(excluded_paths(ROOT), [])

    def test_real_brand_names_are_absent(self):
        self.assertEqual(brand_hits(ROOT), [])

    def test_every_kept_import_resolves_and_avoids_excluded_files(self):
        self.assertEqual(import_violations(ROOT), [])

    def test_a_planted_excluded_import_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parts = root/KIT/'kit'
            parts.mkdir(parents=True)
            (parts/'good.ts').write_text("export const a = 1\n")
            (parts/'planted.ts').write_text(
                "import { mark } from '../assets/app-icons'\nimport './brands'\nimport './missing'\n"
                "export { a } from './good'\nconst p = new URL('../examples/wikipedia/fuji.jpg', import.meta.url)\n")
            found = import_violations(root)
            self.assertEqual(len(found), 4, found)
            self.assertTrue(all('planted.ts' in line for line in found))

    def test_planted_excluded_file_and_brand_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/KIT/'examples/figma').mkdir(parents=True)
            (root/KIT/'examples/kept.css').write_text('/* the Stripe look */\n')
            self.assertIn('examples/figma', excluded_paths(root))
            self.assertTrue(brand_hits(root))

    def test_declared_dependencies_are_only_those_expected(self):
        package = json.loads((ROOT/KIT/'package.json').read_text())
        self.assertEqual(set(package['dependencies']), EXPECTED_DEPENDENCIES)
        self.assertEqual(set(package['devDependencies']), EXPECTED_DEV)
        self.assertNotIn('optionalDependencies', package)
        bare = {s.split('/')[0] if not s.startswith('@') else '/'.join(s.split('/')[:2])
                for p in source_files(ROOT/KIT) for s in specifiers(p.read_text(encoding='utf-8'))
                if not s.startswith(('.', 'node:', '/'))}
        self.assertLessEqual(bare, EXPECTED_DEPENDENCIES | EXPECTED_DEV)

    def test_guides_name_only_kept_examples(self):
        for path in (ROOT/SKILL/'references').glob('*.md'):
            for name in re.findall(r'examples/([a-z0-9-]+)', path.read_text(encoding='utf-8')):
                if name != 'x':
                    self.assertTrue((ROOT/KIT/'examples'/name).is_dir(), f'{path.name}: {name}')
        for name in re.findall(r"id: '([a-z-]+)'", (ROOT/KIT/'playground/catalog.ts').read_text()):
            if name != 'contrasts':
                self.assertTrue((ROOT/KIT/'examples'/name).is_dir(), name)

    def test_license_keeps_upstream_notice(self):
        for path in (ROOT/SKILL/'LICENSE', ROOT/KIT/'LICENSE'):
            self.assertIn('Copyright (c) 2026 Benji Taylor', path.read_text())

    def test_manifest_matches_maintained_bytes(self):
        manifest = json.loads((ROOT/KIT/'source-manifest.json').read_text())
        self.assertEqual(manifest['revision'], '802057409787133703c56001080169e347305572')
        for name, entry in manifest['files'].items():
            digest = hashlib.sha256((ROOT/KIT/name).read_bytes()).hexdigest()
            self.assertEqual(digest, entry['sha256'], name)
            if entry['relationship'] == 'byte-identical-selected-source':
                self.assertEqual(digest, entry['original_sha256'], name)


if __name__ == '__main__':
    unittest.main()
