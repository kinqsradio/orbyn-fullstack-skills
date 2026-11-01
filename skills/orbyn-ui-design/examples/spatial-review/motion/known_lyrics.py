"""Time supplied lyrics against heard words. Displayed text only ever comes from the lyrics."""
from collections import defaultdict
import difflib
import re

SECTION_MARKER = re.compile(r'^\[[^\]]*\]$')
PROMPT_CHARS = 600  # Roughly 150 tokens: below the 223 faster-whisper keeps from a prompt.
MIN_WORD_SECONDS, MIN_COLLAPSED_RUN, COLLAPSED_GAP_SECONDS = .04, 2, .1
MIN_TEMPLATE_SECONDS, REPEAT_THRESHOLD = .25, .6


def parse_lyrics(text):
    lines = []
    for raw in text.splitlines():
        line = ' '.join(raw.split())
        if line and not SECTION_MARKER.match(line):
            lines.append({'id': 'line-' + str(len(lines)), 'text': line, 'words': line.split()})
    if not lines or sum(len(l['words']) for l in lines) > 10000:
        raise ValueError('Expected a bounded nonempty lyric text')
    return lines


def lyric_prompt(lines, limit=PROMPT_CHARS):
    """Unique whole lines: a repeat spends prompt budget without adding vocabulary."""
    kept, seen, size = [], set(), 0
    for line in lines:
        key = normalize(line['text'])
        if key in seen:
            continue
        seen.add(key)
        if size + len(line['text']) + bool(kept) > limit:
            continue
        kept.append(line['text'])
        size += len(line['text']) + (len(kept) > 1)
    return ' '.join(kept)


def normalize(word):
    return re.sub(r"[^\w]", '', word.casefold())


def align_supplied(lines, heard):
    """Map heard words onto supplied words. Unmatched heard words are returned, never shown."""
    words = []
    for number, line in enumerate(lines):
        for text in line['words']:
            words.append({'id': 'word-' + str(len(words)), 'text': text, 'line': number, 'start': None,
                          'end': None, 'status': 'missing', 'score': None})
    supplied = [normalize(w['text']) for w in words]
    spoken = [normalize(w['word']) for w in heard]
    rejected = []
    matcher = difflib.SequenceMatcher(None, supplied, spoken, autojunk=False)
    for tag, a, b, c, d in matcher.get_opcodes():
        if tag == 'equal':
            for word, source in zip(words[a:b], heard[c:d]):
                word.update(start=source['start'], end=source['end'], status='aligned', score=source.get('probability'))
        elif tag == 'replace' and b - a == d - c:  # Misheard in place: keep our spelling.
            for word, source in zip(words[a:b], heard[c:d]):
                word.update(start=source['start'], end=source['end'], status='inferred', score=None)
        else:
            rejected.extend({**w, 'word': w['word'].strip()} for w in heard[c:d])
    return words, rejected


def mark_collapsed(words):
    """Clear runs of implausibly short neighbours: a run of real words does not fit in 40 ms each."""
    collapsed, run = [], []
    def flush():
        if len(run) >= MIN_COLLAPSED_RUN:
            for word in run:
                collapsed.append({'id': word['id'], 'originalStart': word['start'], 'originalEnd': word['end']})
                word.update(start=None, end=None, status='missing', score=None)
        run.clear()
    for word in words:
        short = word['start'] is not None and word['end'] - word['start'] <= MIN_WORD_SECONDS
        if run and (not short or word['start'] - run[-1]['end'] > COLLAPSED_GAP_SECONDS):
            flush()
        if short:
            run.append(word)
    flush()
    return collapsed


def find_repeats(y, sr, start, end, threshold=REPEAT_THRESHOLD):
    """Normalized waveform correlation: finds the same audio, not the same words sung again."""
    import numpy as np
    y = np.asarray(y, dtype=np.float64)
    first, last = round(start * sr), round(end * sr)
    template = y[first:last]
    if last - first < MIN_TEMPLATE_SECONDS * sr or last > len(y) or not np.any(template):
        raise ValueError('Template must be a nonsilent range of at least %.2f seconds' % MIN_TEMPLATE_SECONDS)
    template = template - template.mean()
    size = len(template)
    length = len(y) + size
    product = np.fft.irfft(np.fft.rfft(y, length) * np.conj(np.fft.rfft(template, length)), length)[:len(y) - size + 1]
    total, square = np.concatenate([[0], np.cumsum(y)]), np.concatenate([[0], np.cumsum(y * y)])
    mean = (total[size:] - total[:-size]) / size
    energy = np.maximum(0, square[size:] - square[:-size] - size * mean * mean)
    scale = np.sqrt(energy * np.sum(template ** 2))
    floor = 1e-9 * scale.max()
    score = np.divide(product, scale, out=np.zeros_like(product), where=scale > floor)
    found = []
    for index in np.argsort(-score):
        if score[index] < threshold:
            break
        if all(abs(index - other) >= size / 2 for other, _ in found):
            found.append((int(index), float(score[index])))
    return [{'time': round(i / sr, 5), 'score': round(value, 4)} for i, value in sorted(found)]


def clean_words(words):
    return bool(words) and all(w['status'] == 'aligned' and w['start'] is not None for w in words)


def repair_repeats(y, sr, words, lines, threshold=REPEAT_THRESHOLD):
    """Fill untimed lines from a clean repeat, using measured offsets from its first word."""
    by_line, groups = defaultdict(list), defaultdict(list)
    for word in words:
        by_line[word['line']].append(word)
    for number, line in enumerate(lines):
        groups[normalize(line['text'])].append(number)
    repaired, unresolved, provenance = [], [], {}
    for numbers in groups.values():
        targets = [n for n in numbers if any(w['start'] is None for w in by_line[n])]
        if not targets:
            continue
        sources = [n for n in numbers if clean_words(by_line[n])]
        if not sources:
            unresolved.extend({'line': n, 'reason': 'no clean repeat of this line'} for n in targets)
            continue
        source = max(sources, key=lambda n: min(w['score'] or 0 for w in by_line[n]))
        anchor = by_line[source][0]['start']
        matches = find_repeats(y, sr, anchor, by_line[source][-1]['end'], threshold)
        for target in targets:
            low, high = line_gap(words, by_line[target])
            options = [m for m in matches if low <= m['time'] < high]
            if len(options) != 1:
                unresolved.append({'line': target, 'reason': 'no repeat inside the gap' if not options else 'several repeats inside the gap'})
                continue
            for word, model in zip(by_line[target], by_line[source]):
                if word['start'] is None:
                    word.update(start=round(options[0]['time'] + model['start'] - anchor, 5),
                                end=round(options[0]['time'] + model['end'] - anchor, 5), status='inferred', score=None)
                    provenance[word['id']] = {'method': 'repeat-offset', 'sourceWord': model['id']}
            repaired.append({'line': target, 'sourceLine': source, 'method': 'repeat-offset', 'anchor': options[0]['time'], 'score': options[0]['score']})
    return {'repaired': repaired, 'unresolved': unresolved, 'provenance': provenance}


def line_gap(words, line):
    """Times a line must fall between: the nearest timed neighbours in sung order."""
    first, last = words.index(line[0]), words.index(line[-1])
    before = [w['end'] for w in words[:first] if w['end'] is not None]
    after = [w['start'] for w in words[last + 1:] if w['start'] is not None]
    return (max(before) if before else 0, min(after) if after else float('inf'))


def validate_heard(words, duration):
    if not isinstance(words, list) or len(words) > 50000:
        raise ValueError('Heard word budget')
    last = 0
    for word in words:
        if not isinstance(word, dict) or not isinstance(word.get('word'), str) or not word['word'].strip():
            raise ValueError('Heard word needs text')
        start, end = word.get('start'), word.get('end')
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in [start, end]) or not 0 <= start < end <= duration or start < last - 1e-3:
            raise ValueError('Heard word times must be ordered and inside the audio')
        last = start
    return words
