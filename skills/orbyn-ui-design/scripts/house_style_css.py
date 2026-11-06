#!/usr/bin/env python3
"""Generate the Orbyn house style tokens.css from tokens.json (stdlib only).

Usage: house_style_css.py [--check]
  default  write references/house-style/tokens.css
  --check  exit 1 when tokens.css differs from the generated output
"""
import json
import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parents[1] / 'references/house-style'
HEADER = '/* Generated from tokens.json by scripts/house_style_css.py. Do not edit. */\n'


def value(raw):
    """Turn a token value into CSS; '{name}' is an alias of another token."""
    alias = re.fullmatch(r'\{([\w.-]+)\}', raw)
    return f'var(--{alias.group(1)})' if alias else raw


def split_tokens(data):
    """Return (themed, shared): themed maps theme id to [(name, css)], shared is [(name, css)]."""
    themes = [t['id'] for t in data['color']['themes']]
    themed = {t: [] for t in themes}
    shared = []
    for group in ('color', 'shadow'):
        for tok in data[group]['tokens']:
            val = tok['value']
            if isinstance(val, dict):
                for t in themes:
                    themed[t].append((tok['name'], value(val[t])))
            else:
                shared.append((tok['name'], value(val)))
    for group in ('spacing', 'radius', 'size'):
        shared += [(t['name'], t['value']) for t in data[group]['tokens']]
    shared += [('font-sans', data['type']['families']['sans']),
               ('font-mono', data['type']['families']['mono'])]
    return themes, themed, shared


def ident(name):
    """Escape dots so names like space-0.5 are valid custom properties."""
    return name.replace('.', '\\.')


def block(selector, items):
    body = ''.join(f'  --{ident(n)}: {v};\n' for n, v in items)
    return f'{selector} {{\n{body}}}\n'


def generate(data):
    themes, themed, shared = split_tokens(data)
    out = [HEADER]
    # Aliases (shadcn names) and shared scales live in :root; themed colours below.
    out.append(block(':root', shared))
    for t in themes:
        sel = f':root[data-theme="{t}"]'
        if t == 'light':
            sel = f':root,\n{sel}'
        out.append(block(sel, themed[t]))
    return '\n'.join(out)


def main(argv):
    data = json.loads((DIR / 'tokens.json').read_text(encoding='utf-8'))
    css = generate(data)
    target = DIR / 'tokens.css'
    if '--check' in argv:
        return 0 if target.exists() and target.read_text(encoding='utf-8') == css else 1
    target.write_text(css, encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
