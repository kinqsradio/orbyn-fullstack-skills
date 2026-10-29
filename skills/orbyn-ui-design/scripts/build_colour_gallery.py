#!/usr/bin/env python3
"""Build an original, self-contained palette gallery; no network or target changes."""
import argparse
import hashlib
import json
import re
from pathlib import Path

OWNER = Path(__file__).resolve().parents[1]


def validate_catalogue(data):
    required = {'page', 'surface', 'text', 'muted', 'accent', 'onAccent', 'hoverAccent', 'border', 'focus', 'success', 'error'}
    palettes = data.get('palettes', [])
    if data.get('schema_version') != 1 or len(palettes) != 7 or len({p['id'] for p in palettes}) != 7:
        raise ValueError('Expected seven distinct reference palettes')
    for value, origin in data.get('added_colours', {}).items():
        if not re.fullmatch(r'#[0-9A-F]{6}', value) or not isinstance(origin, str) or not origin.strip():
            raise ValueError('Added colours need exact hex keys and nonempty origin descriptions')
    known = 0; unknown = []
    for palette in palettes:
        if len(palette['swatches']) != 6:
            raise ValueError('Preserve six ordered swatch positions per screenshot')
        for index, value in enumerate(palette['swatches'], 1):
            if value is None:
                unknown.append((palette['id'], index))
            elif isinstance(value, str) and re.fullmatch(r'#[0-9A-F]{6}', value):
                known += 1
            else:
                raise ValueError('Reference hex must be confirmed #RRGGBB or explicit null')
        if set(palette['role_proposals']) != {'light', 'dark'}:
            raise ValueError('Both illustrative role proposals are required')
        for roles in palette['role_proposals'].values():
            if set(roles) != required:
                raise ValueError('Missing or unknown semantic role')
            for value in roles.values():
                if not isinstance(value, str) or not re.fullmatch(r'#[0-9A-F]{6}', value):
                    raise ValueError('Role values must be known solid sRGB colours')
                if value not in palette['swatches'] and value not in data['added_colours']:
                    raise ValueError('Declare the origin of every added role colour')
    if known != 41 or unknown != [('blue-ice', 3)]:
        raise ValueError('Expected 41 confirmed labels and the unchanged unknown blue position 3')


def build(output):
    sources = {'catalog': OWNER/'assets/reference-palettes.json',
               'template': OWNER/'examples/colour-gallery/gallery.html',
               'script': OWNER/'examples/colour-gallery/gallery.mjs'}
    data = json.loads(sources['catalog'].read_text())
    validate_catalogue(data)
    page = sources['template'].read_text()
    page = page.replace('__CATALOG__', json.dumps(data).replace('<', '\\u003c')).replace('__GALLERY_SCRIPT__', sources['script'].read_text())
    output = Path(output)
    output.mkdir()  # new owned output only; never replace a previous gallery
    (output/'index.html').write_text(page)
    receipt = {'status': 'built; browser/interaction review separate',
               'sources': {k: {'path': str(v), 'sha256': hashlib.sha256(v.read_bytes()).hexdigest()} for k, v in sources.items()},
               'output_sha256': hashlib.sha256((output/'index.html').read_bytes()).hexdigest(),
               'scope': 'Original illustrative gallery, no target token adoption or screenshot assets.'}
    (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return output/'index.html'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(build(args.out))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, str(error)+'\n')
