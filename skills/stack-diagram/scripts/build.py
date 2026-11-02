#!/usr/bin/env python3
"""Inline icons and the source credit into a diagram draft (HTML or TSX).

Usage:
  python3 build.py DRAFT ICONDIR OUT

Replaces:
  %%ICON_<name>%%  data URI of ICONDIR/<name>.(svg|png|webp|jpg|jpeg)
  %%CREDITS%%      icon sources from ICONDIR/manifest.json, for the icons DRAFT uses

Reads DRAFT and ICONDIR; writes only OUT, atomically. Every SVG passes the sanitiser
again here, so a file placed in ICONDIR by hand gets the same treatment as a fetched
one. Exits non-zero, writing nothing, on an unresolved %%TOKEN%%, a missing credit or a
reference that would load at view time.
"""
import argparse
import base64
import html
import json
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_guard import require_ignored  # noqa: E402
from sanitise_svg import MAX_SVG_BYTES, UnsafeSvg, sanitise_svg  # noqa: E402

MIME = {'.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp',
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
ICON_TOKEN = re.compile(r'%%ICON_([A-Za-z0-9_-]+)%%')
GROUP_LABEL_ICON = re.compile(r'<div class="g-label">(?=<img src="%%ICON_([A-Za-z0-9_-]+)%%" alt="">)(<img src="%%ICON_[A-Za-z0-9_-]+%%" alt="">)')
ANY_TOKEN = re.compile(r'%%[A-Za-z0-9_-]+%%')
LOADING_ATTRIBUTES = {'src', 'srcset', 'poster', 'data', 'background', 'xlink:href', 'ping', 'action', 'formaction'}
BLOCKED_TAGS = {'script', 'link', 'iframe', 'object', 'embed', 'base', 'audio', 'video', 'source', 'track', 'frame', 'applet', 'portal'}
CSS_LOAD = re.compile(r"""@import\b|image-set\s*\(|url\(\s*(?!["']?\s*(?:#|data:))""", re.I)
LOGO_MARKER = '<meta name="stack-diagram-logos" content="fetched">'
LABELS = {'svgl': 'svgl', 'devicon': 'devicon', 'gilbarbara': 'gilbarbara/logos', 'lucide': 'Lucide',
          'aws': 'AWS Architecture Icons', 'generic': 'neutral pictograms',
          'supplied': 'files supplied for this diagram'}
NOT_LOGOS = {'lucide', 'generic'}


def data_uri(path):
    raw = path.read_bytes()
    if len(raw) > MAX_SVG_BYTES:
        raise UnsafeSvg(f'{path.name} exceeds {MAX_SVG_BYTES} bytes')
    if path.suffix.lower() == '.svg':
        raw, removed = sanitise_svg(raw)
        if removed:
            print(f"sanitised {path.name}: removed {', '.join(removed)}")
    return f'data:{MIME[path.suffix.lower()]};base64,{base64.b64encode(raw).decode()}'


def label_for(entry):
    source = entry.get('source', 'supplied')
    if source == 'explicit':
        return urllib.parse.urlsplit(str(entry.get('url', ''))).hostname or 'supplied URL'
    return LABELS.get(source, source)


def credits(icondir, names):
    """Credit only what this diagram embeds, as escaped text."""
    path = icondir/'manifest.json'
    manifest = json.loads(path.read_text()) if path.exists() else {}
    entries = {base: manifest.get(base, {}) for base in {name.removesuffix('_dark') for name in names}}
    labels = sorted({label_for(entry) for entry in entries.values()}) or ['none']
    text = 'icons: ' + ' / '.join(labels)
    missing = sum(bool(entry.get('fallback')) for entry in entries.values())
    if missing:
        text += f' ({missing} logo{"s" * (missing > 1)} unavailable)'
    if any(entry.get('source', 'supplied') not in NOT_LOGOS for entry in entries.values()):
        text += ' · logos remain the trademarks of their owners'
    return html.escape(text, quote=False)


class LoadFinder(HTMLParser):
    """Name anything that would load at view time. Visible text and data-* attributes never count."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag in BLOCKED_TAGS:
            self.found.append(f'<{tag}>')
        if tag == 'meta' and any(k == 'http-equiv' and (v or '').lower() == 'refresh' for k, v in attrs):
            self.found.append('<meta refresh>')
        self.in_style = tag == 'style'
        for name, value in attrs:
            value = (value or '').strip()
            if name == 'style' and CSS_LOAD.search(value):
                self.found.append(f'style on <{tag}>')
            elif name.startswith('on'):
                self.found.append(f'{name} on <{tag}>')
            elif name in LOADING_ATTRIBUTES or (name == 'href' and tag != 'a'):
                if value and not value.startswith(('#', 'data:')):
                    self.found.append(f'{name} on <{tag}>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.in_style = False

    def handle_endtag(self, tag):
        self.in_style = False

    def handle_data(self, data):
        if self.in_style and CSS_LOAD.search(data):
            self.found.append('a stylesheet rule')


def view_time_loads(text):
    finder = LoadFinder()
    finder.feed(text)
    finder.close()
    return finder.found


def uses_fetched_logos(icondir, names):
    try:
        manifest = json.loads((icondir/'manifest.json').read_text())
    except (OSError, ValueError):
        return False
    entries = manifest if isinstance(manifest, dict) else {}
    used = [entries.get(name.removesuffix('_dark')) for name in names]
    return any(isinstance(entry, dict) and entry.get('source') not in NOT_LOGOS | {None} for entry in used)


def pair_group_labels(text, icondir):
    """Give a group label both logos: it sits on the tint, where a dark mark vanishes."""
    def pair(match):
        name = match.group(1)
        if name.endswith('_dark') or not list(Path(icondir).glob(f'{name}_dark.*')):
            return match.group(0)
        return (f'{match.group(0)[:-len(match.group(2))]}<img class="lt" src="%%ICON_{name}%%" alt="">'
                f'<img class="dk" src="%%ICON_{name}_dark%%" alt="">')
    return GROUP_LABEL_ICON.sub(pair, text)


def build(draft, icondir, out, allow_tracked=False):
    text = draft.read_text(encoding='utf-8')
    if '%%CREDITS%%' not in text:
        raise ValueError(f'{draft.name} has no %%CREDITS%% token; the footer must credit icon sources')
    text = pair_group_labels(text, icondir)
    names = set(ICON_TOKEN.findall(text))
    for name in names:
        matches = sorted(path for path in icondir.glob(f'{name}.*')
                         if path.suffix.lower() in MIME and path.is_file() and not path.is_symlink())
        if matches:
            text = text.replace(f'%%ICON_{name}%%', data_uri(matches[0]))
    text = text.replace('%%CREDITS%%', credits(icondir, names))
    leftover = sorted(set(ANY_TOKEN.findall(text)))
    if leftover:
        raise ValueError(f"unresolved tokens: {', '.join(leftover)} (fill the placeholder, or add the icon to {icondir})")
    loads = view_time_loads(text) if out.suffix.lower() in ('.html', '.htm') else []
    if loads:
        raise ValueError(f"{draft.name} loads something at view time ({', '.join(sorted(set(loads)))}); the output must be self-contained")
    if uses_fetched_logos(icondir, names):
        if not allow_tracked:
            require_ignored(out.parent)
        text = text.replace('</head>', f'{LOGO_MARKER}</head>', 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_name(f'.{out.name}.{os.getpid()}.partial')
    partial.write_text(text, encoding='utf-8')
    os.replace(partial, out)
    print(f'built {out} ({len(text) // 1024} KB)')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('draft', type=Path)
    parser.add_argument('icondir', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--allow-tracked', action='store_true',
                        help='write fetched logos to a folder Git may commit; only when the user asked')
    args = parser.parse_args(argv)
    if args.draft.resolve() == args.out.resolve():
        parser.exit(2, 'OUT must differ from DRAFT: the draft keeps the tokens\n')
    try:
        build(args.draft, args.icondir, args.out, args.allow_tracked)
    except (OSError, ValueError) as error:
        parser.exit(1, f'build failed: {error}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
