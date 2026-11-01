#!/usr/bin/env python3
"""Fail a film source folder that depends on anything but code we wrote.

Reads every file under the folder, except a top-level .git directory, and writes
nothing. Exit 0: clean. Exit 1: findings. Exit 2: the check could not run or found
nothing to scan. Only list an allowance the user approved for this job.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

MEDIA = {'.png', '.apng', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.bmp', '.tif', '.tiff', '.heic', '.exr', '.hdr',
         '.ico', '.jxl', '.tga', '.dds', '.ktx', '.ktx2', '.ppm', '.pgm', '.pbm', '.pnm', '.svgz', '.pdf',
         '.mp4', '.m4v', '.mov', '.webm', '.mkv', '.avi', '.mpg', '.mpeg', '.wmv', '.flv', '.swf',
         '.wav', '.mp3', '.flac', '.ogg', '.oga', '.opus', '.m4a', '.aac', '.aif', '.aiff', '.wma', '.mid', '.midi', '.sf2',
         '.ttf', '.otf', '.ttc', '.woff', '.woff2', '.eot', '.pfb',
         '.glb', '.gltf', '.fbx', '.obj', '.mtl', '.blend', '.dae', '.usd', '.usda', '.usdc', '.usdz', '.ply', '.stl',
         '.3ds', '.abc', '.vrm', '.x3d', '.bvh', '.cube',
         '.riv', '.lottie', '.psd', '.ai', '.aep', '.spine', '.skel', '.atlas', '.moc3', '.unitypackage',
         '.wasm', '.zip', '.tar', '.gz', '.tgz', '.bz2', '.xz', '.7z', '.rar'}
MANIFESTS = {'package.json', 'package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock', 'pnpm-lock.yaml', 'pnpm-workspace.yaml',
             'bun.lock', 'bun.lockb', 'bower.json', 'deno.json', 'deno.jsonc', 'deno.lock', 'importmap.json',
             'requirements.txt', 'pyproject.toml', 'setup.py', 'setup.cfg', 'pipfile', 'pipfile.lock', 'poetry.lock',
             'uv.lock', 'environment.yml', 'environment.yaml', 'cargo.toml', 'cargo.lock', 'go.mod', 'go.sum',
             'gemfile', 'gemfile.lock', 'composer.json', 'composer.lock'}
VENDOR_DIRS = {'node_modules', 'bower_components', 'jspm_packages', 'web_modules', 'site-packages', 'dist-packages',
               '__pypackages__', '.venv', 'venv', 'vendor', 'third_party'}
REQUIREMENTS_FILE = re.compile(r'requirements[-_.\w]*\.(?:txt|in)$')
# The names are distinctive and the suffix must look like a release, so a film file
# called three-body.mjs or spine.mjs stays ours.
LIBRARY_FILE = re.compile(
    r'(?:three|gsap|lottie|lottie-web|lottie-player|bodymovin|pixi|pixijs|babylon|babylonjs|p5|d3|jquery|lodash|phaser|'
    r'howler|tfjs|tensorflow|ammo|cannon-es|matter-js|animejs|tone-js|spine-core|spine-webgl|pixi-spine|rive-canvas|rive-wasm|'
    r'twgl|regl|ogl|react|react-dom|vue|svelte)'
    r'(?:[.@-]v?\d[\w.-]*)?(?:\.(?:module|min|esm|cjs|umd|core|prod|production|development|global|bundle|all|full|slim))*'
    r'\.(?:m?js|cjs|ts|mts)$')
BUILT_FILE = re.compile(r'\.min\.(?:m?js|cjs|css)$|\.(?:m?js|cjs|css)\.map$')

PYTHON = {'.py', '.pyw', '.pyi'}
SCRIPT = {'.mjs', '.js', '.cjs', '.ts', '.mts', '.cts', '.tsx', '.jsx', '.glsl', '.frag', '.vert', '.wgsl'}
MARKUP = {'.html', '.htm', '.xhtml', '.svg', '.vue', '.svelte', '.astro'}
STYLE = {'.css', '.scss', '.sass', '.less', '.styl'}
LINE_COMMENT_STYLE = {'.scss', '.sass', '.less', '.styl'}
MAX_BYTES = 32 * 1024 * 1024

# Signatures with non-text bytes are searched through the whole file. ASCII ones would
# match a comment that names the format, so those are read at the start, where a real
# file has them; the bytes after them fail the NUL or UTF-8 test anyway.
BINARY_SIGNATURES = (
    (b'\x89PNG\r\n\x1a\n', 'PNG'), (b'\xff\xd8\xff', 'JPEG'), (b'\x1aE\xdf\xa3', 'Matroska or WebM'),
    (b'wOFF\0', 'WOFF font'), (b'\x00\x01\x00\x00\x00', 'TrueType font'), (b'\x00asm', 'WebAssembly'),
    (b'PK\x03\x04', 'zip archive'), (b'\x1f\x8b\x08', 'gzip archive'), (b'7z\xbc\xaf\x27\x1c', '7z archive'),
    (b'\xfd7zXZ\0', 'xz archive'), (b'Rar!\x1a\x07', 'rar archive'), (b'v/1\x01', 'OpenEXR'))
START_SIGNATURES = (
    (b'GIF87a', 'GIF'), (b'GIF89a', 'GIF'), (b'OggS', 'Ogg'), (b'fLaC', 'FLAC'), (b'ID3', 'MP3'), (b'wOF2', 'WOFF2 font'),
    (b'OTTO', 'OpenType font'), (b'glTF', 'glTF model'), (b'8BPS', 'Photoshop file'), (b'%PDF-', 'PDF'),
    (b'#?RADIANCE', 'Radiance HDR'), (b'II*\0', 'TIFF'), (b'MM\0*', 'TIFF'), (b'ply\n', 'PLY model'), (b'ply\r\n', 'PLY model'),
    (b'P3\n', 'PPM image'), (b'P6\n', 'PPM image'))

DATA_URI = re.compile(r'(?<![\w.-])data:(?:(?:application|audio|font|image|message|model|multipart|text|video)/[\w.+-]+)?'
                      r'(?:;[\w=.-]+)*,', re.I)
BASE64_RUN = re.compile(r'(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{1024,}={0,2}')
LICENCE_TEXT = re.compile(r'permission is hereby granted|apache license|gnu (?:lesser |affero )?general public license|'
                          r'mozilla public license|redistribution and use in source and binary forms', re.I)
LICENCE_HEADER = re.compile(r'^\s*(?:/\*+!?|//+|\*|#|<!--)\s*(?:@license\b|@preserve\b|spdx-license-identifier\b|'
                            r'licensed under\b|copyright\s+(?:\(c\)|©|\d{4}))', re.I | re.M)
BANNER = re.compile(r'^\s*/\*!\s*\S.*\bv?\d+\.\d+', re.M)

SCHEME_URL = re.compile(r'''(?<![a-z0-9+.-])[a-z][a-z0-9+.-]*://[^\s'"`<>)\\]+''', re.I)
# A protocol-relative URL only counts where a value starts, and must end like a
# host. Without both, the comment //gl.enable(...) reads as a host called gl.enable.
BARE_URL = re.compile(r'''(?<=['"`(=])//(?:[^\s/'"`@]+@)?(?:\[[0-9a-f:.]+\]|[a-z0-9-]+(?:\.[a-z0-9-]+)+)(?::\d+)?(?=[/'"`)\s?#>]|$)''', re.I)
EXEMPT_HOSTS = {'www.w3.org', 'localhost', '127.0.0.1', '::1'}

SCRIPT_TAG = re.compile(r'<script\b([^>]*)>(.*?)</script\s*>', re.I | re.S)
STYLE_TAG = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.I | re.S)
HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)
ATTRIBUTE = re.compile(r'''(?<![\w-])(?:src|srcset|href|xlink:href|poster|data|action)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))''', re.I)
CSS_URL = re.compile(r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^)\s]*))''', re.I)
CSS_IMPORT = re.compile(r'''@(?:import|use|forward)\s+(?:"([^"]*)"|'([^']*)')''', re.I)

IDENTIFIER = re.compile(r'[^\W\d][\w$]*|\$[\w$]*')
NUMBER = re.compile(r'\.?\d[\w.]*')
ESCAPE = re.compile(r'\\(?:x([0-9a-fA-F]{2})|u([0-9a-fA-F]{4})|u\{([0-9a-fA-F]{1,6})\}|([\s\S]))')
# After these a slash starts a regular expression, not a division.
REGEX_AFTER_PUNCTUATION = set('(,=:[!&|?{};+-*%<>~^')
REGEX_AFTER_WORD = {'return', 'typeof', 'case', 'in', 'of', 'do', 'else', 'void', 'delete', 'throw', 'new', 'await', 'yield'}
LIMITS = [
    'Reads source, so it cannot judge where drawn content came from: traced coordinates or shapes copied into our own code pass',
    'Cannot follow a name built at run time, so a fetch of a computed string or a URL assembled from pieces passes',
    'Cannot follow an alias such as const load = require',
    'Sees data: and long base64 runs, but not bytes written as number arrays or encoded another way',
    'Finds a vendored library by its filename and licence text, so renamed code with its notice removed passes',
    'Finds Lottie, glTF and Spine shapes in JSON text, but not the same data written as a JavaScript object',
]


def unescape(text):
    def replace(match):
        code = match.group(1) or match.group(2) or match.group(3)
        if code:
            value = int(code, 16)
            return chr(value) if value <= 0x10ffff else ''
        return {'n': '\n', 't': '\t', 'r': '\r', '\n': ''}.get(match.group(4), match.group(4))
    return ESCAPE.sub(replace, text)


def js_tokens(text):
    """Split script into (kind, value) with comments gone, so strings and code stay distinct."""
    tokens, holes, i, size = [], [], 0, len(text)

    def template(start, whole):
        j = start
        while j < size and text[j] != '`' and text[j:j + 2] != '${':
            j += 2 if text[j] == '\\' else 1
        hole = text[j:j + 2] == '${'
        tokens.append(('template' if hole or not whole else 'string', unescape(text[start:j])))
        if hole:
            holes.append(0)
        return j + (2 if hole else 1)

    def regex_allowed():
        if not tokens:
            return True
        kind, value = tokens[-1]
        return value in REGEX_AFTER_WORD if kind == 'word' else kind == 'punct' and value in REGEX_AFTER_PUNCTUATION

    while i < size:
        char = text[i]
        if char.isspace():
            i += 1
        elif text.startswith('//', i):
            end = text.find('\n', i)
            i = size if end < 0 else end
        elif text.startswith('/*', i):
            end = text.find('*/', i + 2)
            i = size if end < 0 else end + 2
        elif char in '\'"':
            j = i + 1
            while j < size and text[j] != char and text[j] != '\n':  # A newline ends a stray JSX apostrophe.
                j += 2 if text[j] == '\\' else 1
            tokens.append(('string', unescape(text[i + 1:j])))
            i = j + 1
        elif char == '`':
            i = template(i + 1, True)
        elif char == '/' and regex_allowed():
            j, in_class = i + 1, False
            while j < size and text[j] != '\n' and (in_class or text[j] != '/'):
                if text[j] == '\\':
                    j += 1
                elif text[j] in '[]':
                    in_class = text[j] == '['
                j += 1
            if j < size and text[j] == '/':
                tokens.append(('regex', ''))
                i = j + 1
            else:
                tokens.append(('punct', char))
                i += 1
        elif char == '}' and holes and holes[-1] == 0:
            holes.pop()
            i = template(i + 1, False)
        else:
            if holes and char in '{}':
                holes[-1] += 1 if char == '{' else -1
            match = IDENTIFIER.match(text, i) or NUMBER.match(text, i)
            if match:
                tokens.append(('word' if match.re is IDENTIFIER else 'number', match.group()))
                i = match.end()
            else:
                tokens.append(('punct', char))
                i += 1
    return tokens


def url_findings(text):
    found = []
    for url in SCHEME_URL.findall(text):
        try:
            parts = urlsplit(url)
            host = (parts.hostname or '').lower()
            exempt = (parts.scheme.lower() in {'http', 'https', 'ws', 'wss'} and host in EXEMPT_HOSTS
                      and not parts.username and not parts.password)
        except ValueError:
            exempt = False
        if not exempt:
            found.append(f'remote URL: {url}')
    return found + [f'remote URL: {url}' for url in BARE_URL.findall(text) if host_of(url) not in EXEMPT_HOSTS]


def host_of(url):
    try:
        return (urlsplit('http:' + url).hostname or '').lower()
    except ValueError:
        return ''


def leaves_root(path, root, reference):
    target = unquote(reference.split('#')[0].split('?')[0])
    if target.startswith('/'):
        return not (root/target.lstrip('/')).exists()
    joined = os.path.normpath(os.path.join(path.parent, target))
    return joined != str(root) and not joined.startswith(str(root) + os.sep)


def reference_findings(path, root, reference):
    """Check one src, href or url() value that a file loads."""
    reference = reference.strip()
    if not reference or reference.startswith('#') or re.match(r'[a-z][a-z0-9+.-]*:', reference, re.I) or reference.startswith('//'):
        return []
    return [f'path leaves the folder: {reference}'] if leaves_root(path, root, reference) else []


def module_findings(path, root, name, allowed):
    if name.startswith('node:') or '://' in name:  # A URL is reported from the string itself.
        return []
    if name.startswith(('./', '../', '/')) or name in ('.', '..'):
        return reference_findings(path, root, name)
    top = '/'.join(name.split('/')[:2]) if name.startswith('@') else name.split('/')[0]
    return [] if top in allowed else [f'package import: {name}']


def script_findings(path, root, text, allowed, prose=False):
    """Read imports from tokens. Prose keeps literal import forms, because a sentence can say 'require (see above)'."""
    tokens, found = js_tokens(text), []
    at = lambda k: tokens[k] if 0 <= k < len(tokens) else ('end', '')

    def literal_argument(k):
        first, follow = at(k + 1), at(k + 2)
        return first[1] if first[0] == 'string' and follow[1] in (')', ',') else None

    def from_clause(k):
        for j in range(k, min(k + 400, len(tokens))):
            kind, value = tokens[j]
            if kind == 'word' and value == 'from' and at(j + 1)[0] == 'string':
                return at(j + 1)[1]
            if not (kind == 'word' or kind == 'string' or value in ('{', '}', ',', '*')):
                return None
        return None

    def loaded(k, label):
        name = literal_argument(k)
        if name is not None:
            found.extend(module_findings(path, root, name, allowed))
        elif not prose:
            found.append(f'{label} of a computed name')

    for k, (kind, value) in enumerate(tokens):
        if kind in ('string', 'template') and not prose:
            found.extend(url_findings(f'"{value}"'))
            if kind == 'string' and value.startswith(('../', './../')):
                found.extend(reference_findings(path, root, value))
        if kind != 'word':
            continue
        before, after = at(k - 1), at(k + 1)
        member = before[1] == '.' and at(k - 2)[1] != '.'
        owner = at(k - 2)[1] if member else ''
        if value == 'import' and not member:
            if after[1] == '(':
                loaded(k + 1, 'dynamic import')
            elif after[1] == '.':
                continue  # import.meta
            elif after[0] == 'string':
                found.extend(module_findings(path, root, after[1], allowed))
            else:
                name = from_clause(k + 1)
                if name is not None:
                    found.extend(module_findings(path, root, name, allowed))
        elif value == 'export' and not member and after[1] in ('{', '*'):
            name = from_clause(k + 1)
            if name is not None:
                found.extend(module_findings(path, root, name, allowed))
        elif value in ('require', 'importScripts') and (not member or owner in ('module', 'globalThis', 'window', 'self')) and after[1] == '(':
            loaded(k + 1, value)
        elif value == 'eval' and not member and after[1] == '(' and not prose:
            found.append('eval of generated code')
        elif value == 'Function' and before[1] == 'new' and not prose:
            found.append('new Function of generated code')
    return found


def css_text(text, line_comments):
    """Drop comments only, so selectors such as `* {` and `#hero {` are still read."""
    kept, i, size = [], 0, len(text)
    while i < size:
        char = text[i]
        if char in '"\'':
            j = i + 1
            while j < size and text[j] != char and text[j] != '\n':
                j += 2 if text[j] == '\\' else 1
            kept.append(text[i:j + 1])
            i = j + 1
        elif text.startswith('/*', i):
            end = text.find('*/', i + 2)
            i = size if end < 0 else end + 2
            kept.append(' ')
        elif text[i:i + 4].lower() == 'url(':
            end = text.find(')', i)
            end = size if end < 0 else end + 1
            kept.append(text[i:end])
            i = end
        elif line_comments and text.startswith('//', i):
            end = text.find('\n', i)
            i = size if end < 0 else end
        else:
            kept.append(char)
            i += 1
    return ''.join(kept)


def style_findings(path, root, text):
    found = url_findings(text)
    for pattern in (CSS_URL, CSS_IMPORT):
        for groups in pattern.findall(text):
            found.extend(reference_findings(path, root, next(filter(None, groups), '')))
    return found


def markup_findings(path, root, text, allowed):
    found = []

    def script(match):
        found.extend(script_findings(path, root, match.group(2), allowed))
        return f'<script{match.group(1)}></script>'

    def style(match):
        found.extend(style_findings(path, root, css_text(match.group(1), False)))
        return ''

    rest = STYLE_TAG.sub(style, SCRIPT_TAG.sub(script, HTML_COMMENT.sub(' ', text)))
    found.extend(style_findings(path, root, rest))
    for groups in ATTRIBUTE.findall(rest):
        for item in re.split(r'[,\s]+', next(filter(None, groups), '')):
            found.extend(reference_findings(path, root, item))
    return found


def python_findings(path, root, text, allowed):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError) as error:
        return [f'Python does not parse: {getattr(error, "msg", error)}']
    names, found, docs = [], [], set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docs.add(id(first.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module)
        elif isinstance(node, ast.Constant) and id(node) not in docs and isinstance(node.value, (str, bytes)):
            value = node.value if isinstance(node.value, str) else node.value.decode('latin-1')
            found.extend(url_findings(f'"{value}"'))
        elif isinstance(node, ast.Call):
            function = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', '')
            if function in ('import_module', '__import__'):
                argument = node.args[0] if node.args else None
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    names.append(argument.value)
                else:
                    found.append(f'{function} of a computed name')
    tops = {name.split('.')[0] for name in names}
    siblings = (path.parent, root)
    ours = {name for name in tops for folder in siblings if (folder/f'{name}.py').is_file() or (folder/name).is_dir()}
    return found + [f'third-party Python module: {name}' for name in sorted(tops - ours)
                    if name not in sys.stdlib_module_names and name not in allowed]


def json_strings(value):
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            yield item
            pending += item.values()
            pending += [key for key in item if isinstance(key, str) and '/' in key]
        elif isinstance(item, list):
            pending += item
        elif isinstance(item, str):
            yield item


def data_shape(item):
    keys = set(item)
    if {'v', 'fr', 'ip', 'op', 'layers'} <= keys:
        return 'Lottie animation'
    asset = item.get('asset')
    if isinstance(asset, dict) and 'version' in asset and keys & {'scenes', 'nodes', 'meshes', 'buffers', 'accessors'}:
        return 'glTF model'
    if {'skeleton', 'bones'} <= keys:
        return 'Spine rig'
    return None


def json_findings(path, text):
    stripped = text.lstrip()
    if not stripped.startswith(('{', '[')) and path.suffix.lower() != '.json':
        return []
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        return ['JSON does not parse'] if path.suffix.lower() == '.json' else []
    found = []
    for item in json_strings(data):
        if isinstance(item, str):
            found.extend(url_findings(f'"{item}"'))  # Decoded, so an escaped https:\/\/ is seen.
        elif data_shape(item):
            found.append(f'{data_shape(item)} data')
    return found


def payload_findings(text):
    """Things no comment excuses: embedded files and third-party notices."""
    found = [f'embedded data: payload: {match.group()[:40]}' for match in DATA_URI.finditer(text)]
    found += ['embedded base64 blob' for _ in BASE64_RUN.finditer(text)]
    if LICENCE_TEXT.search(text) or LICENCE_HEADER.search(text) or BANNER.search(text):
        found.append('vendored library: third-party licence notice')
    return found


def text_findings(path, root, text, allowed):
    suffix = path.suffix.lower()
    shebang = text.split('\n', 1)[0] if text.startswith('#!') else ''
    found = payload_findings(text)
    if suffix in PYTHON or 'python' in shebang:
        return found + python_findings(path, root, text, allowed)
    if suffix in SCRIPT or re.search(r'\b(?:node|deno|bun)\b', shebang):
        return found + script_findings(path, root, text, allowed)
    if suffix in MARKUP:
        return found + markup_findings(path, root, text, allowed)
    if suffix in STYLE:
        return found + style_findings(path, root, css_text(text, suffix in LINE_COMMENT_STYLE))
    found += url_findings(text) + json_findings(path, text)
    return found + script_findings(path, root, text, allowed, prose=True)


def binary_finding(data):
    for signature, name in BINARY_SIGNATURES:
        if signature in data:
            return f'media bytes: {name}'
    if data[8:12] in (b'WEBP', b'WAVE', b'AVI ', b'AIFF') and data[:4] in (b'RIFF', b'FORM'):
        return f'media bytes: {data[8:12].decode().strip()}'
    if data[4:8] == b'ftyp':
        return 'media bytes: MP4 family'
    if data[257:262] == b'ustar':
        return 'media bytes: tar archive'
    for signature, name in START_SIGNATURES:
        if data.startswith(signature):
            return f'media bytes: {name}'
    return 'binary file' if b'\0' in data else None


def inspect(path, relative, root, allowed):
    name = path.name.lower()
    if path.is_symlink():
        return ['symbolic link']
    if any(part.lower() in VENDOR_DIRS for part in relative.parts[:-1]):
        return ['vendored package']
    if not path.is_file():
        return ['not a regular file']
    if name in MANIFESTS or REQUIREMENTS_FILE.fullmatch(name):
        return ['package manifest']
    if LIBRARY_FILE.fullmatch(name) or BUILT_FILE.search(name):
        return [f'vendored library: {path.name}']
    if path.suffix.lower() in MEDIA:
        return ['media, font or model file']
    if path.stat().st_size > MAX_BYTES:
        return ['file too large to be source']
    data = path.read_bytes()
    finding = binary_finding(data)
    if finding:
        return [finding]
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return ['binary file']
    return list(dict.fromkeys(text_findings(path, root, text, allowed)))


def walk(root):
    """List every entry below root, without following links. Only root/.git is left out."""
    pending = [root]
    while pending:
        folder = pending.pop()
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    if not (folder == root and entry.name == '.git'):
                        pending.append(Path(entry.path))
                else:
                    yield Path(entry.path)


def allowed_files(root, allow):
    paths = set()
    for name in allow:
        path = Path(os.path.normpath(root/name))
        if root not in path.parents:
            raise ValueError(f'Allowed path leaves the folder: {name}')
        if not os.path.lexists(path):
            raise ValueError(f'Allowed path does not exist: {name}')
        if path.is_dir():
            raise ValueError(f'Allowed path must be one file: {name}')
        paths.add(path)
    return paths


def check(root, allow=(), modules=()):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f'Not a directory: {root}')
    allowed_paths, allowed_modules = allowed_files(root, allow), set(modules)
    findings, scanned = [], 0
    for path in sorted(walk(root)):
        if path in allowed_paths and not path.is_symlink():
            continue
        scanned += 1
        relative = path.relative_to(root)
        findings += [{'file': str(relative), 'problem': problem} for problem in inspect(path, relative, root, allowed_modules)]
    if not scanned:
        raise ValueError(f'Nothing to scan in {root}')
    return {'status': 'pass' if not findings else 'fail', 'scanned': scanned, 'findings': findings,
            'allowed_paths': sorted(allow), 'allowed_modules': sorted(modules), 'limits': LIMITS}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('folder')
    parser.add_argument('--allow', action='append', default=[], help='Relative path of one file the user supplied for this job')
    parser.add_argument('--allow-module', action='append', default=[], help='Module the user approved for this job')
    options = parser.parse_args()
    try:
        report = check(options.folder, options.allow, options.allow_module)
    except (OSError, ValueError) as error:
        print(f'check-code-only: {error}', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
