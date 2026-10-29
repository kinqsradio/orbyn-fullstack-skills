"""Source-label integrity, contrast boundaries and offline gallery packaging."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT/'skills/orbyn-ui-design'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec); spec.loader.exec_module(loaded)
    return loaded


math = module('colour_contrast', OWNER/'scripts/colour_contrast.py')
builder = module('colour_gallery', OWNER/'scripts/build_colour_gallery.py')
CATALOGUE = json.loads((OWNER/'assets/reference-palettes.json').read_text())
EXPECTED = [
 ['#06141B','#11212D','#253745','#4A5C6A','#9BA8AB','#CCD0CF'],
 ['#190019','#2B124C','#522B5B','#854F6C','#DFB6B2','#FBE4D8'],
 ['#021024','#052659',None,'#5483B3','#7DA0CA','#C1E8FF'],
 ['#F7CBCA','#DDD3D3','#F1F7F7','#D5E5E5','#B0D7D8','#5D6B6B'],
 ['#1A120E','#3A2418','#6B4A2E','#A88462','#D5C4AE','#4A4A46'],
 ['#0E0B1D','#2A1E4D','#5A3B8C','#8B7CC7','#C9C2E3','#3A3A52'],
 ['#0F1F17','#1E3A2E','#3E5A3F','#6B7F67','#C7CBB8','#3D4337'],
]
PAIRS = [('text','page','normal'),('text','surface','normal'),('muted','page','normal'),('muted','surface','normal'),('onAccent','accent','normal'),('onAccent','hoverAccent','normal'),('border','surface','nontext'),('focus','page','focus-adjacency'),('focus','surface','focus-adjacency'),('success','surface','normal'),('error','surface','normal'),('accent','surface','nontext')]


class ContrastTests(unittest.TestCase):
    def test_opaque_oracles_and_symmetry(self):
        self.assertEqual(math.contrast('#000000','#FFFFFF'),21)
        self.assertEqual(math.contrast('#ABCDEF','#ABCDEF'),1)
        self.assertAlmostEqual(math.contrast('#777777','#FFFFFF'),4.478089453577214,places=12)
        for palette in EXPECTED:
            known = [c for c in palette if c]
            for i,a in enumerate(known):
                for b in known[i+1:]:
                    self.assertAlmostEqual(math.contrast(a,b),math.contrast(b,a),places=12)

    def test_unrounded_boundary_stays_below_even_when_display_rounds_up(self):
        result = math.assess('#81737A','#FFFFFF')
        self.assertEqual(result['display_ratio'],'4.50:1')
        self.assertAlmostEqual(result['ratio'],4.499922485663913,places=12)
        self.assertFalse(result['numeric_target_met'])
        self.assertFalse(math.qualifies(4.499,'normal'))
        self.assertTrue(math.qualifies(4.5,'normal'))
        self.assertFalse(math.qualifies(2.999,'nontext'))
        self.assertTrue(math.qualifies(3,'large'))

    def test_known_alpha_composition_not_opaque_contrast(self):
        self.assertEqual(math.contrast('#000000','#FFFFFF',0),1)
        self.assertEqual(math.contrast('#000000','#FFFFFF',1),21)
        self.assertGreater(math.contrast('#000000','#FFFFFF',.5),3.9)
        self.assertLess(math.contrast('#000000','#FFFFFF',.5),4.1)
        self.assertFalse(math.assess('#000000','#FFFFFF',alpha=.5)['numeric_target_met'])

    def test_unknown_and_unsupported_composition_never_gain_a_ratio(self):
        for value in [None,'unknown','#123','#12345678','rgba(0,0,0,.5)','linear-gradient(#000000,#FFFFFF)']:
            with self.subTest(value=value), self.assertRaises(ValueError): math.contrast(value,'#FFFFFF')
        for alpha in [float('nan'),float('inf'),-.1,1.1]:
            with self.assertRaises(ValueError): math.contrast('#000000','#FFFFFF',alpha)
        with self.assertRaises(ValueError): math.qualifies(4.5,'palette-accessible')

    def test_cli_preserves_pass_fail_and_invalid_exits(self):
        script = OWNER/'scripts/colour_contrast.py'
        for foreground, expected in [('#000000',0),('#81737A',1),('unknown',2)]:
            result = subprocess.run([sys.executable,str(script),foreground,'#FFFFFF'],capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,expected,result.stderr)
            if expected == 1:
                self.assertFalse(json.loads(result.stdout)['numeric_target_met'])


class PaletteCatalogueTests(unittest.TestCase):
    def test_all_reference_labels_and_unknown_position_are_preserved(self):
        self.assertEqual([p['swatches'] for p in CATALOGUE['palettes']],EXPECTED)
        self.assertEqual(CATALOGUE['source']['visible_credit'],'@uiuxaadi')
        self.assertIsNone(CATALOGUE['source']['post_url'])
        self.assertIsNone(CATALOGUE['source']['image_reuse_license'])
        builder.validate_catalogue(CATALOGUE)

    def test_every_proposal_pair_meets_its_named_numeric_target(self):
        for palette in CATALOGUE['palettes']:
            for mode,roles in palette['role_proposals'].items():
                for fg,bg,kind in PAIRS:
                    with self.subTest(palette=palette['id'],mode=mode,pair=(fg,bg)):
                        self.assertTrue(math.assess(roles[fg],roles[bg],kind)['numeric_target_met'])
                for value in roles.values():
                    self.assertTrue(value in palette['swatches'] or value in CATALOGUE['added_colours'])

    def test_pastel_collection_does_not_imply_every_raw_pair_passes(self):
        values = EXPECTED[3]
        passed = [(a,b) for i,a in enumerate(values) for b in values[i+1:] if math.qualifies(math.contrast(a,b),'normal')]
        self.assertEqual(passed,[('#F1F7F7','#5D6B6B')])

    def test_guessed_missing_label_and_undeclared_added_role_are_rejected(self):
        changed=copy.deepcopy(CATALOGUE); changed['palettes'][2]['swatches'][2]='#123456'
        with self.assertRaises(ValueError):builder.validate_catalogue(changed)
        changed=copy.deepcopy(CATALOGUE); changed['palettes'][0]['role_proposals']['light']['text']='#123456'
        with self.assertRaisesRegex(ValueError,'origin'):builder.validate_catalogue(changed)

    def test_added_origin_cannot_be_blank(self):
        changed=copy.deepcopy(CATALOGUE); changed['added_colours']['#FFFFFF']=''
        with self.assertRaisesRegex(ValueError,'origin'):builder.validate_catalogue(changed)

    def test_gallery_build_is_self_contained_and_preserves_prior_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'gallery'; page=builder.build(out); source=page.read_text()
            self.assertNotIn('__CATALOG__',source);self.assertNotIn('__GALLERY_SCRIPT__',source)
            self.assertNotIn('<script src=',source);self.assertNotIn('<img',source)
            self.assertIn('@uiuxaadi',source);self.assertIn('unknown label',source)
            receipt=json.loads((out/'receipt.json').read_text())
            self.assertEqual(receipt['output_sha256'],hashlib.sha256(page.read_bytes()).hexdigest())
            before=page.read_bytes()
            with self.assertRaises(FileExistsError):builder.build(out)
            self.assertEqual(page.read_bytes(),before)


if __name__=='__main__':unittest.main()
