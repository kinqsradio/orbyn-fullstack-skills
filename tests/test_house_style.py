"""Orbyn house style: tokens.css matches tokens.json and every colour covers all themes."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT/'skills/orbyn-ui-design'
STYLE = OWNER/'references/house-style'

spec = importlib.util.spec_from_file_location('house_style_css', OWNER/'scripts/house_style_css.py')
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
DATA = json.loads((STYLE/'tokens.json').read_text(encoding='utf-8'))


class HouseStyleTests(unittest.TestCase):
    def test_css_is_regenerated_from_tokens(self):
        self.assertEqual((STYLE/'tokens.css').read_text(encoding='utf-8'), gen.generate(DATA))

    def test_every_colour_has_a_value_in_all_themes(self):
        themes = [t['id'] for t in DATA['color']['themes']]
        self.assertEqual(themes, ['light', 'dark', 'dim'])
        names = {t['name'] for t in DATA['color']['tokens']}
        for tok in DATA['color']['tokens']:
            val = tok['value']
            if isinstance(val, dict):
                self.assertEqual(sorted(val), sorted(themes), tok['name'])
                self.assertTrue(all(isinstance(v, str) and v for v in val.values()), tok['name'])
            elif val.startswith('{'):
                self.assertIn(val[1:-1], names, f"alias {tok['name']}")
        css = (STYLE/'tokens.css').read_text(encoding='utf-8')
        for t in themes:
            self.assertIn(f':root[data-theme="{t}"]', css)

    def test_fonts_are_hosted_and_not_bundled(self):
        self.assertEqual(DATA['name'], 'Orbyn')
        self.assertEqual([f['family'] for f in DATA['type']['fonts']], ['Geist', 'JetBrains Mono'])
        self.assertTrue(all('file' not in f for f in DATA['type']['fonts']))
        self.assertFalse([p for p in STYLE.rglob('*') if p.suffix in {'.woff', '.woff2', '.ttf', '.otf'}])


if __name__ == '__main__':
    unittest.main()
