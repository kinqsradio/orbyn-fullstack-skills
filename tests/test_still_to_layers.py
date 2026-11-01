"""Still-to-layers contracts on an image generated here; no supplied artwork is read."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('still_to_layers', ROOT/'skills/technical-illustration/scripts/still_to_layers.py')
layers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layers)

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = np = None

WIDTH, HEIGHT = 640, 480
BACKDROP = (46, 34, 26)  # BGR, near-black navy.
COAT = (70, 150, 215)
MAGENTA = (200, 40, 210)


def box(left, top, right, bottom):
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


def pixel_box(left, top, right, bottom):
    return box(left/(WIDTH-1), top/(HEIGHT-1), right/(WIDTH-1), bottom/(HEIGHT-1))


def scene(dark_hair=False):
    """Return a BGR image and the ground truth for each authored mask."""
    random = np.random.default_rng(7)
    ramp = np.linspace(0, 12, HEIGHT, dtype=np.float32)[:, None, None]
    image = np.clip(np.float32(BACKDROP)+ramp+random.normal(0, 1.5, (HEIGHT, WIDTH, 3)), 0, 255).astype(np.uint8)
    backdrop = image.copy()
    figure = np.zeros((HEIGHT, WIDTH), np.uint8)
    cv2.ellipse(figure, (320, 350), (130, 210), 0, 0, 360, 255, -1)
    cv2.circle(figure, (320, 120), 80, 255, -1)
    image[figure > 0] = COAT
    hair = np.zeros_like(figure)
    if dark_hair:  # The worst case: hair pixels are the backdrop's own colour and noise.
        hair[:120] = figure[:120]
        image[hair > 0] = backdrop[hair > 0]
    logo = np.zeros_like(figure)
    logo[300:360, 280:360] = 255
    image[logo > 0] = MAGENTA
    highlight = np.zeros_like(figure)
    highlight[400:402, 250:390] = 255
    image[highlight > 0] = (250, 250, 250)
    # Decoys that an authored zone must exclude: a logo-coloured patch and a bright line.
    image[40:80, 40:100] = MAGENTA
    image[440:442, 20:120] = (250, 250, 250)
    return image, {'figure': figure, 'hair': hair, 'logo': logo, 'highlight': highlight, 'backdrop': backdrop}


def authored(head_top=60):
    return {
        'figure': {
            'foreground': [pixel_box(250, 240, 390, 450), pixel_box(280, head_top, 360, 180)],
            'background': [pixel_box(0, 0, 150, 479), pixel_box(490, 0, 639, 479), pixel_box(150, 0, 490, 25)],
            'feather_px': 0,
        },
        'logo': {'hue': [290, 310], 'zones': [pixel_box(240, 280, 400, 380)]},
        'highlight': {'zones': [pixel_box(240, 390, 400, 412)]},
    }


def iou(left, right):
    left, right = left > 127, right > 127
    return (left & right).sum() / max((left | right).sum(), 1)


def recall(found, truth):
    return ((found > 127) & (truth > 127)).sum() / max((truth > 127).sum(), 1)


class Workspace(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()

    def write_spec(self, data, name='spec.json'):
        path = self.root/name
        path.write_text(json.dumps(data), encoding='utf-8')
        return path

    def fail_with(self, arguments):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            layers.main(arguments)
        self.assertNotIn(caught.exception.code, (0, None))
        return stderr.getvalue()


class BoundaryWithoutOpenCV(Workspace):
    def test_missing_opencv_names_the_install_and_writes_nothing(self):
        image = self.root/'still.png'
        image.write_bytes(b'not decoded')
        path = self.write_spec(authored())
        with patch.dict(sys.modules, {'cv2': None}):
            message = self.fail_with(['--image', str(image), '--spec', str(path), '--output', str(self.root/'out')])
        self.assertIn('OpenCV', message)
        self.assertIn('pip install', message)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['spec.json', 'still.png'])

    def test_spec_mistakes_stop_before_any_image_work(self):
        image = self.root/'still.png'
        image.write_bytes(b'not decoded')
        for label, change in [
            ('outside', lambda s: s['figure']['foreground'].append([[0, 0], [1.2, 0], [1, 1]])),
            ('typo', lambda s: s['figure'].update(foregound=[])),
            ('no seeds', lambda s: s['figure'].update(background=[])),
            ('short', lambda s: s['figure']['background'].append([[0, 0], [1, 1]])),
            ('hue', lambda s: s['logo'].update(hue=[290])),
            ('no zones', lambda s: s['highlight'].update(zones=[])),
        ]:
            with self.subTest(label):
                data = authored()
                change(data)
                self.fail_with(['--image', str(image), '--spec', str(self.write_spec(data)), '--output', str(self.root/'out')])
                self.assertFalse((self.root/'out').exists())

    def test_existing_output_is_preserved(self):
        image = self.root/'still.png'
        image.write_bytes(b'not decoded')
        output = self.root/'out'
        output.mkdir()
        (output/'kept.txt').write_text('owner data', encoding='utf-8')
        self.assertIn('exists', self.fail_with(['--image', str(image), '--spec', str(self.write_spec(authored())), '--output', str(output)]))
        self.assertEqual((output/'kept.txt').read_text(encoding='utf-8'), 'owner data')


@unittest.skipIf(cv2 is None, 'OpenCV is an optional dependency of still_to_layers')
class SyntheticStill(Workspace):
    def run_layers(self, data, image, name='out'):
        source = self.root/(name+'.png')
        self.assertTrue(cv2.imwrite(str(source), image))
        output = self.root/name
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            layers.main(['--image', str(source), '--spec', str(self.write_spec(data, name+'.json')), '--output', str(output)])
        return output

    def load(self, output):
        maps = cv2.imread(str(output/'maps.png'), cv2.IMREAD_UNCHANGED)
        self.assertEqual(maps.shape, (HEIGHT, WIDTH, 4))
        return maps, json.loads((output/'layers.json').read_text(encoding='utf-8'))

    def test_masks_cover_the_known_shapes_in_their_channels(self):
        image, truth = scene()
        maps, receipt = self.load(self.run_layers(authored(), image))
        blue, green, red, alpha = cv2.split(maps)
        self.assertGreater(iou(red, truth['figure']), 0.97)
        self.assertEqual(iou(green, truth['logo']), 1.0)
        self.assertEqual(iou(blue, truth['highlight']), 1.0)
        self.assertEqual(alpha.min(), 255)  # A shader never loses RGB to premultiplication.
        for name in ['figure', 'logo', 'highlight']:
            self.assertAlmostEqual(receipt['coverage'][name], (truth[name] > 0).mean(), delta=0.01)
        self.assertEqual(receipt['warnings'], [])
        self.assertEqual(receipt['sourceSha256'], hashlib.sha256((self.root/'out.png').read_bytes()).hexdigest())

    def test_plate_removes_the_figure_and_keeps_the_backdrop(self):
        image, truth = scene()
        output = self.run_layers(authored(), image)
        plate = cv2.imread(str(output/'plate.png'))
        hole = truth['figure'] > 0
        self.assertLess(np.abs(plate[hole].astype(float)-truth['backdrop'][hole]).mean(), 12)
        self.assertTrue((plate[:, :60] == image[:, :60]).all())

    def test_edge_check_composites_the_cutout_over_white(self):
        image, truth = scene()
        check = cv2.imread(str(self.run_layers(authored(), image)/'edge-check.png'))
        self.assertTrue((check[truth['figure'] == 0][:100] >= 250).all())
        self.assertTrue((check[350, 300] == image[350, 300]).all())

    def test_output_is_deterministic(self):
        image, _ = scene()
        first = self.run_layers(authored(), image, 'first')
        second = self.run_layers(authored(), image, 'second')
        self.assertEqual((first/'maps.png').read_bytes(), (second/'maps.png').read_bytes())

    def test_the_guide_example_spec_is_accepted(self):
        guide = (ROOT/'skills/technical-illustration/references/still-to-layers.md').read_text()
        example = guide.split('```json\n', 1)[1].split('```', 1)[0]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'spec.json'
            path.write_text(example)
            self.assertIn('figure', layers.load_spec(path))

    def test_seeded_dark_hair_warns_and_a_hand_silhouette_recovers_it(self):
        image, truth = scene(dark_hair=True)
        maps, receipt = self.load(self.run_layers(authored(), image, 'seeded'))
        self.assertLess(recall(maps[:, :, 2], truth['hair']), 0.8)
        self.assertTrue(any('hand-authored silhouette' in warning for warning in receipt['warnings']))
        points = cv2.ellipse2Poly((320, 120), (80, 80), 0, 180, 360, 5)
        data = authored()
        data['figure']['silhouette'] = {
            'zones': [pixel_box(200, 30, 440, 119)],
            'shapes': [[[x/(WIDTH-1), y/(HEIGHT-1)] for x, y in points.tolist()]],
        }
        maps, receipt = self.load(self.run_layers(data, image, 'authored'))
        self.assertGreater(recall(maps[:, :, 2], truth['hair']), 0.97)
        self.assertEqual(receipt['warnings'], [])

    def test_unseeded_dark_hair_is_lost_without_a_warning(self):
        # The cut lands on the sharp hairline, so the reference tells authors to seed dark parts.
        image, truth = scene(dark_hair=True)
        maps, receipt = self.load(self.run_layers(authored(head_top=125), image))
        self.assertLess(recall(maps[:, :, 2], truth['hair']), 0.05)
        self.assertEqual(receipt['warnings'], [])

    def test_a_mask_that_finds_nothing_fails_and_leaves_no_output(self):
        image, _ = scene()
        data = authored()
        data['logo']['hue'] = [100, 120]
        source = self.root/'still.png'
        cv2.imwrite(str(source), image)
        output = self.root/'out'
        message = self.fail_with(['--image', str(source), '--spec', str(self.write_spec(data)), '--output', str(output)])
        self.assertIn('logo', message)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['spec.json', 'still.png'])

    def test_undecodable_image_is_named(self):
        source = self.root/'still.png'
        source.write_bytes(b'not an image')
        self.assertIn('decode', self.fail_with(['--image', str(source), '--spec', str(self.write_spec(authored())), '--output', str(self.root/'out')]))


if __name__ == '__main__':
    unittest.main()
