#!/usr/bin/env python3
"""Split one still image into masks a shader can sample, from an authored JSON spec.

Reads one image and one spec. Writes a new directory holding maps.png, plate.png,
edge-check.png and layers.json, and never replaces an existing path. Runs no other
program and makes no network call. OpenCV is optional for the library and required
here; see references/still-to-layers.md for the spec and its limits.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

INSTALL = 'OpenCV is required for still_to_layers; install it with: python3 -m pip install opencv-python-headless'
SECTIONS = {
    'figure': {'foreground', 'background', 'probable', 'silhouette', 'iterations', 'feather_px'},
    'logo': {'hue', 'zones', 'min_saturation', 'min_value', 'feather_px'},
    'highlight': {'zones', 'sigma_px', 'floor', 'ceiling'},
}
LOW_CONTRAST_LEVELS = 14  # Mean 8-bit luma step across the edge, below which GrabCut has little to use.
LOW_CONTRAST_SHARE = 0.1
PLATE_EDGE = 640  # Telea fill is slow and smooth, so run it small and paste only the hole.


class LayerError(Exception):
    """A problem the caller can correct; main reports it and exits non-zero."""


def check_polygons(value, label):
    if not isinstance(value, list):
        raise LayerError(label + ' must be a list of polygons')
    for polygon in value:
        if not isinstance(polygon, list) or len(polygon) < 3:
            raise LayerError(label + ' needs at least 3 points in each polygon')
        for point in polygon:
            if not (isinstance(point, list) and len(point) == 2
                    and all(isinstance(c, (int, float)) and 0 <= c <= 1 for c in point)):
                raise LayerError(label + ' points must be [x, y] fractions of the image, from 0 to 1')


def load_spec(path):
    try:
        spec = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise LayerError('Cannot read spec: ' + str(error)) from error
    if not isinstance(spec, dict) or set(spec) - set(SECTIONS) or 'figure' not in spec:
        raise LayerError('Spec needs a figure section and may add only logo and highlight')
    for name, section in spec.items():
        if not isinstance(section, dict) or set(section) - SECTIONS[name]:
            raise LayerError('Unknown key in the {} section; expected {}'.format(name, sorted(SECTIONS[name])))
    figure = spec['figure']
    if not figure.get('foreground') or not figure.get('background'):
        raise LayerError('figure needs foreground and background seed polygons')
    for key in ['foreground', 'background', 'probable']:
        check_polygons(figure.get(key, []), 'figure.' + key)
    silhouette = figure.get('silhouette')
    if silhouette is not None:
        if not isinstance(silhouette, dict) or set(silhouette) != {'zones', 'shapes'} or not silhouette['zones']:
            raise LayerError('figure.silhouette needs zones and shapes')
        check_polygons(silhouette['zones'], 'figure.silhouette.zones')
        check_polygons(silhouette['shapes'], 'figure.silhouette.shapes')
    logo = spec.get('logo')
    if logo is not None:
        hue = logo.get('hue')
        if not isinstance(hue, list) or len(hue) != 2 or not all(isinstance(h, (int, float)) and 0 <= h <= 360 for h in hue):
            raise LayerError('logo.hue must be [low, high] in degrees; low above high wraps through red')
        check_polygons(logo.get('zones', []), 'logo.zones')
    highlight = spec.get('highlight')
    if highlight is not None:
        if not highlight.get('zones'):
            raise LayerError('highlight needs authored zones, because high-pass detail exists everywhere')
        check_polygons(highlight['zones'], 'highlight.zones')
    return spec


def load_opencv():
    try:
        import cv2
        import numpy
    except ImportError as error:
        raise LayerError(INSTALL) from error
    return cv2, numpy


def fill(cv2, np, polygons, shape):
    """Rasterize fractional polygons to a 0/255 mask."""
    height, width = shape[:2]
    mask = np.zeros((height, width), np.uint8)
    for polygon in polygons:
        points = np.rint(np.float32(polygon) * [width - 1, height - 1]).astype(np.int32)
        cv2.fillPoly(mask, [points], 255)
    return mask


def feather(cv2, mask, sigma):
    return cv2.GaussianBlur(mask, (0, 0), sigma) if sigma else mask


def figure_alpha(cv2, np, image, section):
    fore, back = (fill(cv2, np, section[key], image.shape) for key in ['foreground', 'background'])
    if ((fore > 0) & (back > 0)).any():
        raise LayerError('figure foreground and background seeds overlap')
    seeds = np.full(image.shape[:2], cv2.GC_PR_BGD, np.uint8)
    seeds[fill(cv2, np, section.get('probable', []), image.shape) > 0] = cv2.GC_PR_FGD
    seeds[fore > 0] = cv2.GC_FGD
    seeds[back > 0] = cv2.GC_BGD
    cv2.setRNGSeed(0)  # GrabCut clusters colours with OpenCV's shared generator.
    cv2.grabCut(image, seeds, None, np.zeros((1, 65)), np.zeros((1, 65)),
                int(section.get('iterations', 5)), cv2.GC_INIT_WITH_MASK)
    alpha = np.where((seeds == cv2.GC_FGD) | (seeds == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    authored = np.zeros_like(alpha)
    silhouette = section.get('silhouette')
    if silhouette:
        authored = fill(cv2, np, silhouette['zones'], image.shape)
        alpha[authored > 0] = fill(cv2, np, silhouette['shapes'], image.shape)[authored > 0]
    return feather(cv2, alpha, section.get('feather_px', 1.2)), authored


def logo_mask(cv2, np, image, section):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hue = hsv[..., 0] * 2  # OpenCV stores 8-bit hue as degrees / 2.
    low, high = section['hue']
    inside = (hue >= low) & (hue <= high) if low <= high else (hue >= low) | (hue <= high)
    inside &= hsv[..., 1] >= section.get('min_saturation', 0.35) * 255
    inside &= hsv[..., 2] >= section.get('min_value', 0.25) * 255
    if section.get('zones'):
        inside &= fill(cv2, np, section['zones'], image.shape) > 0
    return feather(cv2, np.where(inside, 255, 0).astype(np.uint8), section.get('feather_px', 0))


def highlight_mask(cv2, np, image, section):
    luma = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    detail = luma - cv2.GaussianBlur(luma, (0, 0), section.get('sigma_px', 6))
    floor, ceiling = section.get('floor', 8), section.get('ceiling', 60)
    if ceiling <= floor:
        raise LayerError('highlight ceiling must be above its floor')
    scaled = np.clip((detail - floor) / (ceiling - floor), 0, 1) * 255
    scaled[fill(cv2, np, section['zones'], image.shape) == 0] = 0
    return scaled.astype(np.uint8)


def low_contrast_edge_share(cv2, np, image, alpha, authored):
    """Return the share of the seeded outline whose two sides have nearly the same brightness."""
    radius = max(2, round(max(image.shape[:2]) / 200))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    solid = np.where(alpha >= 128, 255, 0).astype(np.uint8)
    edge = (cv2.dilate(solid, kernel) > 0) & (cv2.erode(solid, kernel) == 0) & (authored == 0)
    if not edge.any():
        return 0.0
    luma = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    def side(mask):
        weight = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), radius * 2)
        return cv2.GaussianBlur(luma * mask, (0, 0), radius * 2) / np.maximum(weight, 1e-3)
    step = np.abs(side(alpha >= 128) - side(alpha < 128))
    return float((step[edge] < LOW_CONTRAST_LEVELS).mean())


def background_plate(cv2, np, image, alpha):
    """Fill the figure's hole so a parallax shift reveals backdrop, not a duplicate edge."""
    height, width = image.shape[:2]
    radius = max(3, round(max(height, width) / 80))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    hole = cv2.dilate(np.where(alpha > 4, 255, 0).astype(np.uint8), kernel)
    scale = min(1, PLATE_EDGE / max(height, width))
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    small_image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    small_hole = cv2.resize(hole, size, interpolation=cv2.INTER_NEAREST)
    filled = cv2.resize(cv2.inpaint(small_image, small_hole, 3, cv2.INPAINT_TELEA), (width, height),
                        interpolation=cv2.INTER_LINEAR)
    plate = image.copy()
    plate[hole > 0] = filled[hole > 0]
    return plate


def coverage(np, mask, name):
    share = float((mask >= 128).mean())
    if share == 0:
        raise LayerError('The {} mask is empty; check its seeds, hue or zones'.format(name))
    return round(share, 6)


def build(cv2, np, image, spec):
    """Return {file name: BGR(A) array} and the receipt fields derived from them."""
    alpha, authored = figure_alpha(cv2, np, image, spec['figure'])
    black = np.zeros_like(alpha)
    logo = logo_mask(cv2, np, image, spec['logo']) if 'logo' in spec else black
    highlight = highlight_mask(cv2, np, image, spec['highlight']) if 'highlight' in spec else black
    shares = {'figure': coverage(np, alpha, 'figure')}
    if shares['figure'] > 0.995:
        raise LayerError('The figure mask fills the image; add background seeds')
    for name, mask in [('logo', logo), ('highlight', highlight)]:
        shares[name] = coverage(np, mask, name) if name in spec else None
    low_contrast = low_contrast_edge_share(cv2, np, image, alpha, authored)
    warnings = []
    if low_contrast > LOW_CONTRAST_SHARE:
        warnings.append('{:.0%} of the outline has almost no contrast with its backdrop. Inspect edge-check.png and '
                        'add a hand-authored silhouette there before lighting the figure from behind.'.format(low_contrast))
    weight = (alpha.astype(np.float32) / 255)[..., None]
    edge_check = np.rint(image * weight + 255 * (1 - weight)).astype(np.uint8)
    opaque = np.full_like(alpha, 255)
    # OpenCV orders channels BGRA, so this writes R=figure, G=logo, B=highlight.
    files = {'maps.png': cv2.merge([highlight, logo, alpha, opaque]),
             'plate.png': background_plate(cv2, np, image, alpha), 'edge-check.png': edge_check}
    return files, {'coverage': shares, 'lowContrastEdgeShare': round(low_contrast, 6), 'warnings': warnings}


def write_output(cv2, output, files, receipt):
    """Stage in a sibling directory and rename, so a failure leaves no partial output."""
    staged = Path(tempfile.mkdtemp(prefix='.' + output.name + '-', dir=output.parent))
    try:
        for name, array in files.items():
            ok, encoded = cv2.imencode('.png', array)
            if not ok:
                raise LayerError('OpenCV could not encode ' + name)
            (staged / name).write_bytes(encoded.tobytes())
        (staged / 'layers.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        os.chmod(staged, 0o755)
        os.rename(staged, output)
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise


def run(image_path, spec_path, output_path):
    image_path, output = Path(image_path), Path(output_path).absolute()
    if output.exists() or output.is_symlink():
        raise LayerError('Output already exists; preserve it and choose a new path: ' + str(output))
    if not output.parent.is_dir():
        raise LayerError('Output parent is not a directory: ' + str(output.parent))
    if not image_path.is_file():
        raise LayerError('Image is not a regular file: ' + str(image_path))
    spec = load_spec(spec_path)
    cv2, np = load_opencv()
    source = image_path.read_bytes()
    image = cv2.imdecode(np.frombuffer(source, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise LayerError('OpenCV could not decode the image: ' + str(image_path))
    try:
        files, derived = build(cv2, np, image, spec)
    except cv2.error as error:
        raise LayerError('OpenCV failed: ' + str(error).strip()) from error
    receipt = {
        'version': 1,
        'sourceSha256': hashlib.sha256(source).hexdigest(),
        'specSha256': hashlib.sha256(Path(spec_path).read_bytes()).hexdigest(),
        'size': [int(image.shape[1]), int(image.shape[0])],
        'opencv': cv2.__version__,
        'channels': {'r': 'figure alpha', 'g': 'logo', 'b': 'highlight', 'a': 'opaque'},
        **derived,
        'limits': ['Coverage counts pixels at or above half strength; it says nothing about edge quality.',
                   'Low-contrast edges need a hand-authored silhouette; GrabCut has no colour step to follow there.'],
    }
    write_output(cv2, output, files, receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description='Split one still image into shader masks from an authored JSON spec.')
    parser.add_argument('--image', required=True, help='Source image to read')
    parser.add_argument('--spec', required=True, help='JSON spec of seed polygons, hue range and zones')
    parser.add_argument('--output', required=True, help='New directory to create; an existing path is refused')
    args = parser.parse_args(argv)
    try:
        receipt = run(args.image, args.spec, args.output)
    except (LayerError, OSError) as error:
        print('error: ' + str(error), file=sys.stderr)
        raise SystemExit(1) from error
    for warning in receipt['warnings']:
        print('warning: ' + warning, file=sys.stderr)
    print(json.dumps({'output': args.output, 'coverage': receipt['coverage'], 'warnings': len(receipt['warnings'])}))


if __name__ == '__main__':
    main()
