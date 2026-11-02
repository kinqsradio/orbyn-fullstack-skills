#!/usr/bin/env python3
"""Reduce an untrusted SVG to static drawing content before it enters a page.

Reads bytes and returns bytes; touches no file or network and never executes the
SVG. Elements pass an allowlist. Scripts, foreignObject, animation, event
attributes and every reference that leaves the document are removed.
"""
import re
from xml.etree import ElementTree as ET
from xml.parsers import expat

MAX_SVG_BYTES = 2 * 1024 * 1024
SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'
XML_NS = 'http://www.w3.org/XML/1998/namespace'
ET.register_namespace('', SVG_NS)
ET.register_namespace('xlink', XLINK_NS)

ELEMENTS = frozenset("""
    svg g defs symbol use switch title desc
    path rect circle ellipse line polyline polygon text tspan image
    linearGradient radialGradient stop pattern clipPath mask marker style
    filter feBlend feColorMatrix feComponentTransfer feComposite feFlood feFuncA
    feFuncB feFuncG feFuncR feGaussianBlur feMerge feMergeNode feMorphology feOffset
""".split())
TEXT_ONLY = frozenset({'title', 'desc'})  # An HTML parser would run markup inside these.
MAX_DEPTH = 64
REFERENCE_ATTRIBUTES = frozenset({'href'})
ATTRIBUTES = frozenset("""
    id class style viewBox preserveAspectRatio xmlns version width height x y x1 y1 x2 y2 cx cy
    r rx ry fx fy d points transform gradientTransform gradientUnits patternTransform patternUnits
    patternContentUnits spreadMethod offset stop-color stop-opacity fill fill-opacity fill-rule stroke
    stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-miterlimit stroke-dasharray
    stroke-dashoffset opacity clip-path clip-rule clipPathUnits mask maskUnits maskContentUnits filter
    filterUnits primitiveUnits color color-interpolation color-interpolation-filters display visibility
    font-family font-size font-weight font-style text-anchor dominant-baseline letter-spacing dx dy
    in in2 result stdDeviation values type mode operator k1 k2 k3 k4 radius flood-color flood-opacity
    tableValues slope intercept amplitude exponent markerWidth markerHeight markerUnits orient refX refY
    shape-rendering image-rendering text-rendering vector-effect paint-order overflow pointer-events
    aria-hidden aria-label aria-labelledby role focusable href
""".split())
CSS_FUNCTIONS = frozenset({'url', 'rgb', 'rgba', 'hsl', 'hsla', 'oklch', 'matrix',
                           'translate', 'rotate', 'scale'})
EXTERNAL_URL = re.compile(r"""url\s*\(\s*(?!['"]?\s*#)""", re.I)
EMBEDDED_RASTER = re.compile(r'data:image/(?:png|jpeg|webp|gif);base64,[A-Za-z0-9+/=\s]+')


class UnsafeSvg(ValueError):
    """The bytes cannot be reduced to a safe static SVG."""


def css_is_static(text):
    """Accept only colours, geometry and same-document url(#id) paints."""
    if '\\' in text or '<' in text or EXTERNAL_URL.search(text):
        return False
    if re.search(r'@(?!media\b)', text, re.I) or re.search(r'javascript:', text, re.I):
        return False
    rules = re.sub(r'@media[^{]*\{', '{', text, flags=re.I)
    return all(name.lower() in CSS_FUNCTIONS
               for name in re.findall(r'([a-zA-Z_-][a-zA-Z0-9_-]*)\s*\(', rules))


def sheet_is_contained(text):
    """A stylesheet reaches the whole page once inlined, so selectors stay on drawing elements."""
    body = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    body = re.sub(r'@media[^{]*\{', '', body)
    for selectors in re.findall(r'([^{}]+)\{', body):
        for part in re.split(r'[\s,>+~]+', selectors.strip()):
            match = re.fullmatch(r'([a-zA-Z][\w-]*)?(?:[.#][\w-]+)*(?::[a-z-]+)?', part)
            if not match or not part or (match.group(1) and match.group(1) not in ELEMENTS):
                return False
    return True


def reference_is_local(value):
    value = value.strip()
    return value.startswith('#') or bool(EMBEDDED_RASTER.fullmatch(value))


def refuse_entities(raw):
    """Run expat first: it honours the declared encoding, so UTF-16 cannot hide them."""
    def refuse(*_):
        raise UnsafeSvg('SVG declares XML entities')
    parser = expat.ParserCreate()
    parser.EntityDeclHandler = refuse
    try:
        parser.Parse(raw, True)
    except expat.ExpatError as error:
        raise UnsafeSvg(f'SVG is not well-formed XML: {error}') from error


def split_name(name):
    if name.startswith('{'):
        namespace, _, local = name[1:].partition('}')
        return namespace, local
    return '', name


def clean_attributes(element, removed):
    for name, value in list(element.attrib.items()):
        namespace, local = split_name(name)
        lowered = local.lower()
        keep = True
        if namespace == XLINK_NS:
            keep = lowered == 'href' and reference_is_local(value)
        elif namespace:
            keep = namespace == XML_NS and lowered == 'space'
        elif lowered.startswith('on'):
            keep = False
        elif local not in ATTRIBUTES:
            keep = False
        elif lowered in REFERENCE_ATTRIBUTES:
            keep = reference_is_local(value)
        elif lowered == 'style':
            keep = css_is_static(value)
            local = 'style'
        elif EXTERNAL_URL.search(value) or 'javascript:' in value.lower():
            keep = False
        if not keep:
            del element.attrib[name]
            removed.add('style' if local == 'style' else f'attribute:{local}')


def clean_children(root, removed):
    """Walk with a stack: a hostile file can nest deeper than Python can recurse."""
    stack = [(root, 1)]
    while stack:
        parent, depth = stack.pop()
        if depth > MAX_DEPTH:
            raise UnsafeSvg(f'SVG nests deeper than {MAX_DEPTH} levels')
        for child in list(parent):
            namespace, local = split_name(child.tag) if isinstance(child.tag, str) else ('', '')
            if namespace != SVG_NS or local not in ELEMENTS:
                parent.remove(child)
                removed.add(f'element:{local}')
                continue
            if local == 'style' and (len(child) or not css_is_static(child.text or '') or not sheet_is_contained(child.text or '')):
                parent.remove(child)
                removed.add('style')
                continue
            clean_attributes(child, removed)
            if local in TEXT_ONLY:
                for inner in list(child):
                    child.remove(inner)
                    removed.add(f'element:{split_name(inner.tag)[1] if isinstance(inner.tag, str) else ""}')
            stack.append((child, depth + 1))


def sanitise_svg(raw):
    """Return (clean bytes, sorted names of what was removed); raise UnsafeSvg to reject.

    The entry 'style' means author styling was dropped, which can change colours.
    """
    if len(raw) > MAX_SVG_BYTES:
        raise UnsafeSvg(f'SVG exceeds {MAX_SVG_BYTES} bytes')
    refuse_entities(raw)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as error:
        raise UnsafeSvg(f'SVG is not well-formed XML: {error}') from error
    if root.tag != f'{{{SVG_NS}}}svg':
        raise UnsafeSvg('root element is not an SVG')
    removed = set()
    clean_attributes(root, removed)
    clean_children(root, removed)
    try:
        return ET.tostring(root, encoding='utf-8'), sorted(removed)
    except RecursionError as error:
        raise UnsafeSvg('SVG nests too deeply to write') from error
