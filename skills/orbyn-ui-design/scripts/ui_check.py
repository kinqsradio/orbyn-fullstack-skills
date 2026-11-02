#!/usr/bin/env python3
"""Find objective interface defects in source: things that break for someone, not taste.

Reads source files, writes nothing and prints JSON. Exit 0: no errors. Exit 1: an image
without alternative text, or zoom disabled. Exit 2: the check could not run. Everything else
is a warning to read against the code. It reads text, so a clean run proves nothing about
layout, contrast or how the screen looks. Standard library only.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

MARKUP = {'.tsx', '.jsx', '.html', '.vue', '.svelte', '.astro'}
STYLES = {'.css', '.scss'}
EMBEDDED_STYLE = {'.html', '.vue', '.svelte', '.astro'}
SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', '.next', 'generated', 'coverage', 'upstream'}
SKIP_NAME = re.compile(r'\.(test|spec|stories)\.|\.min\.')
TEXT_LIMIT = 2_000_000
ERRORS = {'image-without-alt', 'zoom-disabled'}

CSS_RULE = re.compile(r'([^{}]+)\{([^{}]*)\}')
OUTLINE_OFF = re.compile(r'outline(?:-style)?\s*:\s*(?:none|0(?:px)?)\b|outline-width\s*:\s*0(?:px)?\b')
RING = re.compile(r'\boutline\s*:\s*(?!none|0)\S|\bbox-shadow\s*:\s*(?!none)\S|\bborder(?:-[a-z]+)*\s*:\s*(?!none|0|transparent)\S|\bbackground(?:-color)?\s*:\s*(?!none|transparent|inherit)\S')
TRANSITION_ALL = re.compile(r'transition(?:-property)?\s*:\s*all\b|\btransition-all\b')
SCRIPT_FOCUS = re.compile(r'(?:^|[\s,>])(?:h[1-6]|main|section|article)(?![\w-])|\[tabindex=.?-1')
CONTROL = re.compile(r'(?:^|[\s,>+~])(?:\*|button|a|input|select|textarea)(?![\w-])')
CLASS_ATTR = re.compile(r'class(?:Name)?=(?:"([^"]*)"|\'([^\']*)\'|\{`([^`]*)`\}|\{(?:cn|clsx|cx|twMerge)\(([^)]*)\)\})')
TAILWIND_OUTLINE = re.compile(r'(?:^|[\s"\'])(?:focus(?:-visible)?:)?outline-(?:none|0)(?=[\s"\']|$)')
TAILWIND_FOCUS = re.compile(r'(?:focus(?:-visible|-within)?|data-\[focus[^\]]*\]|(?:group|peer)-focus\S*):(?:ring|outline(?!-none|-0)|border|bg|shadow)')
TAG_BEFORE = re.compile(r'<([A-Za-z][\w.]*)[^<]*$', re.S)
POSITIVE_TAB = re.compile(r'tab[iI]ndex=(?:"([1-9]\d*)"|\{([1-9]\d*)\})')
ANIMATES = re.compile(r'@keyframes|\banimation(?:-name)?\s*:|\banimate-[a-z]')
BLOCK_COMMENT = re.compile(r'/\*.*?\*/|<!--.*?-->', re.S)
LINE_COMMENT = re.compile(r'(?:(?<=[\s,;{}()])|^)//[^\n]*', re.M)
# A string value only starts after these, which keeps a closing quote from opening a match.
MARKUP_IN_STRING = re.compile(r"""([=(,:\[]\s*)(?:"[^"\n]*<(?:img|meta|button|a)\b[^"\n]*"|'[^'\n]*<(?:img|meta|button|a)\b[^'\n]*'|`[^`]*<(?:img|meta|button|a)\b[^`]*`)""")
NEXT_ZOOM = re.compile(r'\buserScalable\s*:\s*false\b|\bmaximumScale\s*:\s*1(?:\.0+)?(?![\d.])')
SPREAD = re.compile(r'\{\s*\.\.\.|\bv-bind\s*[=:]|\bv-bind\b')
HIDDEN = re.compile(r'aria-hidden=(?:"true"|\{true\})|\bhidden(?=[\s/>])|tab[iI]ndex=(?:"-1"|\{-1\})')


def blank(match):
    return re.sub(r'[^\n]', ' ', match.group(0))


def line_of(text, index):
    return text.count('\n', 0, index) + 1


def clean_source(text, suffix):
    """Same length and lines as the source, so reported lines stay true."""
    text = BLOCK_COMMENT.sub(blank, text)
    if suffix in STYLES:
        return LINE_COMMENT.sub(blank, text) if suffix == '.scss' else text
    if suffix not in ('.html', '.astro'):
        text = LINE_COMMENT.sub(blank, text)
    return MARKUP_IN_STRING.sub(lambda m: m.group(1) + re.sub(r'[^\n]', ' ', m.group(0)[len(m.group(1)):]), text)


def tag_end(text, start):
    """Index just past an opening tag, skipping braces and quotes in its attributes."""
    depth, quote, at = 0, '', start
    while at < len(text):
        char = text[at]
        if quote:
            quote = '' if char == quote else quote
        elif char in '"\'`':
            quote = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        elif char == '>' and depth <= 0:
            return at + 1
        at += 1
    return -1


def tags(text, name):
    """Yield (start, opening tag text, inner text) for each element called name."""
    for match in re.finditer(rf'<{name}(?=[\s/>])', text):
        end = tag_end(text, match.end())
        if end < 0:
            continue
        opening = text[match.start():end]
        if opening.endswith('/>'):
            yield match.start(), opening, ''
            continue
        closing = text.find(f'</{name}>', end)
        yield match.start(), opening, text[end:closing] if closing >= 0 else None


def attribute(name):
    return re.compile(rf'(?<![\w-]){name}\s*=')


NAME_ATTRIBUTES = re.compile(r'(?<![\w-])(?:aria-label|aria-labelledby|title)\s*=')
ALT = attribute('alt')
ROLE_NONE = re.compile(r'role=["\'](?:presentation|none)["\']')


def has_name(inner):
    """True when a child could supply a name: visible text, an expression or a titled image."""
    if re.search(r'<svg\b[^>]*(?<![\w-])aria-label\s*=|<title>\s*\S', inner):
        return True
    if re.search(r'<img\b[^>]*(?<![\w-])alt\s*=\s*(?:"[^"\s][^"]*"|\{)', inner):
        return True
    stripped = re.sub(r'<svg\b.*?</svg>', '', inner, flags=re.S)
    stripped = re.sub(r'<[A-Za-z][\w.]*\b(?:[^<>]|=>)*/>', '', stripped)  # A self-closed element shows no text here.
    stripped = re.sub(r'<(i|span)\b[^>]*>\s*</\1>', '', stripped)
    stripped = re.sub(r'\{/\*.*?\*/\}', '', stripped, flags=re.S).replace('&nbsp;', '')
    stripped = re.sub(r'</?[A-Za-z][^<>]*>', '', stripped)
    return bool(stripped.strip())


def replaced(base, rules):
    """A focus rule for the same selector, for every element or around this one shows focus."""
    wrapper = base.split()[0] if ' ' in base else None
    for other, inner, _ in rules:
        for part in other.split(','):
            part = part.strip()
            if wrapper and part == f'{wrapper}:focus-within' and inner.strip():
                return True
            if ':focus' in part and RING.search(inner) and re.sub(r':focus(?:-visible)?', '', part).strip() in (base, '', '*'):
                return True
    return False


def outline_finding(selector, block, rules):
    """The selector whose outline goes without a replacement, or None."""
    for part in selector.split(','):
        part = part.strip()
        focused = ':focus' in part and ':focus-within' not in part
        if re.search(r':(?:hover|active|focus-within)', part) or (not focused and not CONTROL.search(f' {part}')):
            continue
        if SCRIPT_FOCUS.search(part) and not CONTROL.search(f' {part}'):
            continue  # A heading or landmark focused by script needs no ring.
        if focused and RING.search(OUTLINE_OFF.sub('', block)):
            continue
        if not replaced(re.sub(r':focus(?:-visible)?', '', part).strip(), rules):
            return part
    return None


def check_styles(text):
    found = []
    body = re.sub(r'@media\s+print[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}', blank, text)
    rules = [(m.group(1).strip().split(';')[-1].strip(), m.group(2), m.start(2)) for m in CSS_RULE.finditer(body)]
    for selector, block, at in rules:
        part = outline_finding(selector, block, rules) if OUTLINE_OFF.search(block) else None
        if part:
            found.append(('focus-ring-removed', at, part[:70]))
    found += [('transition-all', m.start(), m.group(0)) for m in TRANSITION_ALL.finditer(body)]
    return found


def check_classes(text):
    found = []
    for match in CLASS_ATTR.finditer(text):
        classes = next(filter(None, match.groups()), '')
        if not TAILWIND_OUTLINE.search(classes) or TAILWIND_FOCUS.search(classes):
            continue
        tag = TAG_BEFORE.search(text[max(0, match.start() - 600):match.start()])
        name = tag.group(1) if tag else ''
        # A plain element takes script focus; a control or component is where a ring matters.
        if name in ('button', 'a', 'input', 'select', 'textarea') or name[:1].isupper():
            found.append(('focus-ring-removed', match.start(), classes[:70]))
    return found


def check_markup(text):
    found = []
    for name in ('button', 'a'):
        for start, opening, inner in tags(text, name):
            if inner is None or NAME_ATTRIBUTES.search(opening) or SPREAD.search(opening) or HIDDEN.search(opening) or has_name(inner):
                continue
            if name == 'a' and not attribute('(?:href|:href)').search(opening):
                continue
            found.append(('control-without-name', start, opening[:60].replace('\n', ' ')))
    for start, opening, _ in tags(text, 'img'):
        if not (ALT.search(opening) or re.search(r'\{alt\}|:alt\s*=', opening) or SPREAD.search(opening)
                or NAME_ATTRIBUTES.search(opening) or ROLE_NONE.search(opening) or HIDDEN.search(opening)):
            found.append(('image-without-alt', start, opening[:60].replace('\n', ' ')))
    for start, opening, _ in tags(text, 'div'):
        if re.search(r'\bon[cC]lick\s*=|@click\s*=', opening) and not re.search(r'\b(?:role|tab[iI]ndex)\s*=', opening) \
                and not SPREAD.search(opening):
            found.append(('clickable-div', start, opening[:60].replace('\n', ' ')))
    for start, opening, _ in tags(text, 'meta'):
        viewport = re.search(r'name=["\']viewport["\']', opening)
        locked = re.search(r'user-scalable\s*=\s*(?:no|0)\b|maximum-scale\s*=\s*1(?:\.0+)?(?![\d.])', opening)
        if viewport and locked:
            found.append(('zoom-disabled', start, opening[:60]))
    found += [('zoom-disabled', m.start(), m.group(0)) for m in NEXT_ZOOM.finditer(text)]
    found += [('positive-tabindex', m.start(), m.group(0)) for m in POSITIVE_TAB.finditer(text)]
    return found + check_classes(text)


def style_blocks(text):
    """Only the contents of <style>, at their original offsets."""
    kept = re.sub(r'[^\n]', ' ', text)
    for match in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S):
        kept = kept[:match.start(1)] + match.group(1) + kept[match.end(1):]
    return kept


def source_files(paths, skipped):
    for root in paths:
        root = Path(root)
        if not root.exists():
            raise ValueError(f'No such path: {root}')
        if root.is_file():
            yield root
            continue
        for path in sorted(root.rglob('*')):
            parts = set(path.relative_to(root).parts[:-1])
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in MARKUP | STYLES:
                continue
            if parts & {'node_modules', '.git'} or SKIP_NAME.search(path.name):
                continue
            if parts & SKIP_DIRS:
                skipped.append({'path': str(path), 'reason': f'in {sorted(parts & SKIP_DIRS)[0]}/'})
            elif path.stat().st_size > TEXT_LIMIT:
                skipped.append({'path': str(path), 'reason': 'over 2 MB'})
            else:
                yield path


def inventory(text, counts):
    counts['raw button'] += len(re.findall(r'<button(?=[\s>])', text))
    counts['raw input'] += len(re.findall(r'<input(?=[\s/>])', text))
    counts['raw select'] += len(re.findall(r'<select(?=[\s>])', text))
    counts['shared Button'] += len(re.findall(r'<Button(?=[\s/>])', text))
    counts['shared Input'] += len(re.findall(r'<(?:Input|TextInput)(?=[\s/>])', text))
    counts['shared Select'] += len(re.findall(r'<Select(?=[\s/>])', text))


def finding(rule, path, line, value):
    return {'rule': rule, 'severity': 'error' if rule in ERRORS else 'warn', 'path': str(path), 'line': line, 'value': value}


def check(paths):
    findings, counts, scanned, skipped = [], Counter(), 0, []
    animates, respects = None, False
    for path in source_files(paths, skipped):
        scanned += 1
        raw = path.read_text(errors='replace')
        suffix = path.suffix.lower()
        text = clean_source(raw, suffix)
        results = check_styles(text) if suffix in STYLES else check_markup(text)
        if suffix in EMBEDDED_STYLE:
            results += check_styles(style_blocks(text))
        if suffix in MARKUP:
            inventory(text, counts)
        findings += [finding(rule, path, line_of(raw, at), value) for rule, at, value in results]
        respects = respects or 'prefers-reduced-motion' in raw or 'useReducedMotion' in raw
        if animates is None and ANIMATES.search(text):
            animates = path
    if not scanned:
        raise ValueError('No interface source found, so nothing was checked')
    if animates and not respects:
        findings.append(finding('reduced-motion-missing', animates, 1, 'animation found, and prefers-reduced-motion appears nowhere'))
    rules = Counter(item['rule'] for item in findings)
    errors = sum(item['severity'] == 'error' for item in findings)
    return {'status': 'fail' if errors else 'pass', 'scanned': scanned, 'skipped': skipped[:50], 'skipped_count': len(skipped),
            'errors': errors, 'warnings': len(findings) - errors, 'rules': dict(rules.most_common()), 'inventory': dict(counts),
            'findings': findings,
            'limits': ['Reads source text, so it cannot see computed styles, layout or contrast',
                       'Only a missing alt and disabled zoom are errors; read every warning against the code',
                       'A control named by a spread is skipped, not proven named',
                       'Run orbyn-ui-design visual review as well; a pass says nothing about design']}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('paths', nargs='+')
    options = parser.parse_args()
    try:
        report = check(options.paths)
    except (OSError, ValueError) as error:
        print(f'ui_check: {error}', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
