"""Per-video-frame audio features and beat-grid checks; needs numpy, no model."""
from collections import Counter
from fractions import Fraction
import math

BANDS = (('sub', 20, 60), ('bass', 60, 250), ('lowMid', 250, 500), ('mid', 500, 2000),
         ('highMid', 2000, 4000), ('high', 4000, None))
KICK_FFT, KICK_HOP, KICK_LOW_HZ, KICK_HIGH_HZ = 1024, 256, 30, 150
BAR_LOW_HZ, BAR_HIGH_HZ = 40, 16000
MAX_BARS, MAX_VALUES = 256, 8_000_000
RMS_HOP, RMS_WINDOW, RMS_EDGE_DB, RMS_MIN_GAP, RMS_FLOOR_DB = .05, 1.5, 6, 3, -80
GRID_MIN_BEATS, GRID_MAX_RESIDUAL = 4, .12
ACCENT_WINDOW, ACCENT_CONTRAST, ACCENT_MIN_BARS = .035, .35, 4
BOUNDARY_MIN, BOUNDARY_MAJORITY = 3, 2 / 3


def round4(value):
    return round(float(value), 4)


def frame_count(samples, sr, fps):
    return samples * fps.numerator // (sr * fps.denominator)


def frame_sample(index, sr, fps):
    """Nearest sample with ties upward, matching the composition clock."""
    return (2 * index * sr * fps.denominator + fps.numerator) // (2 * fps.numerator)


def power_rows(y, centers, size, np):
    """Hann power spectrum centered on each sample, zero-padded at both ends."""
    pad = size // 2
    padded = np.pad(y, pad)
    window = np.hanning(size)
    rows = np.empty((len(centers), size // 2 + 1))
    for first in range(0, len(centers), 512):  # Bounded memory for long tracks.
        chunk = centers[first:first + 512]
        slices = np.stack([padded[c:c + size] for c in chunk])
        rows[first:first + len(chunk)] = np.abs(np.fft.rfft(slices * window, axis=1)) ** 2
    # Scaled so a sine of amplitude A reports band amplitude A.
    return rows * 4 / (size * np.sum(window ** 2))


def band_slices(sr, size):
    resolution = sr / size
    result = []
    for name, low, high in BANDS:
        high = sr / 2 if high is None else min(high, sr / 2)
        first, last = math.ceil(low / resolution), math.floor(high / resolution)
        if last <= first:
            raise ValueError('FFT size leaves band without bins: ' + name)
        result.append((name, low, high, first, last))
    return result


def kick_curve(y, sr, np):
    """Half-wave rectified low-band flux; finer than video so short kicks survive."""
    count = max(1, math.ceil(len(y) / KICK_HOP))
    power = power_rows(y, [i * KICK_HOP for i in range(count)], KICK_FFT, np)
    resolution = sr / KICK_FFT
    low, high = math.ceil(KICK_LOW_HZ / resolution), math.floor(KICK_HIGH_HZ / resolution)
    level = np.sqrt(power[:, low:high + 1]).sum(axis=1)
    flux = np.maximum(0, np.diff(level, prepend=0))
    peak = flux.max()
    return flux / peak if peak > 0 else flux


def log_bars(power, sr, size, count, floor_db, high_hz, np):
    edges = np.geomspace(BAR_LOW_HZ, min(high_hz, sr / 2), count + 1)
    resolution = sr / size
    values = np.empty((len(power), count))
    for index in range(count):
        first, last = math.ceil(edges[index] / resolution), math.floor(edges[index + 1] / resolution)
        if last >= first:
            values[:, index] = power[:, first:last + 1].max(axis=1)
        else:  # Narrower than one FFT bin: interpolate rather than leave a gap.
            position = math.sqrt(edges[index] * edges[index + 1]) / resolution
            below = math.floor(position)
            values[:, index] = power[:, below] + (power[:, below + 1] - power[:, below]) * (position - below)
    peak = values.max()
    if peak <= 0:
        return edges, np.zeros_like(values), None
    decibels = 10 * np.log10(np.maximum(values / peak, 10 ** (-floor_db / 10)))
    return edges, 1 + decibels / floor_db, peak


def bake_frames(y, sr, fps, fft_size=2048, bar_count=32, floor_db=60):
    import numpy as np
    if fps <= 0 or fps > 240:
        raise ValueError('Invalid fps')
    if not 8 <= bar_count <= MAX_BARS or fft_size not in (256, 512, 1024, 2048, 4096, 8192) or not 20 <= floor_db <= 120:
        raise ValueError('Invalid feature budget')
    y = np.asarray(y, dtype=np.float64)
    if y.ndim != 1 or not len(y) or not np.isfinite(y).all():
        raise ValueError('Expected nonempty finite mono samples')
    frames = frame_count(len(y), sr, fps)
    if not frames or frames * (bar_count + len(BANDS) + 1) > MAX_VALUES:
        raise ValueError('Feature output outside budget')
    bands = band_slices(sr, fft_size)
    centers = [frame_sample(i, sr, fps) for i in range(frames)]
    power = power_rows(y, centers, fft_size, np)
    energy, records = {}, []
    for name, low, high, first, last in bands:
        level = np.sqrt(power[:, first:last + 1].sum(axis=1))
        peak = level.max()
        energy[name] = [round4(v) for v in (level / peak if peak > 0 else level)]
        records.append({'name': name, 'lowHz': low, 'highHz': high, 'peak': round(float(peak), 6)})
    curve = kick_curve(y, sr, np)
    hop_seconds = KICK_HOP / sr
    kick = []
    for i in range(frames):
        first = centers[i] // KICK_HOP
        last = (centers[i + 1] if i + 1 < frames else len(y)) // KICK_HOP
        kick.append(round4(curve[first:max(first + 1, last)].max()))
    edges, bars, peak = log_bars(power, sr, fft_size, bar_count, floor_db, BAR_HIGH_HZ, np)
    return {'frames': frames, 'fftSize': fft_size, 'status': 'silent' if peak is None else 'estimated',
            'bands': records, 'bandEnergy': energy, 'kick': kick,
            'barEdgesHz': [round(float(v), 3) for v in edges], 'barFloorDb': floor_db,
            'bars': [[round4(v) for v in row] for row in bars],
            'onsetCurve': [float(v) for v in curve], 'onsetHopSeconds': hop_seconds}


def fit_grid(beats):
    """Fit a regular grid. Its origin is phase only; it says nothing about bars."""
    import numpy as np
    if len(beats) < GRID_MIN_BEATS:
        return {'status': 'unknown', 'beatCount': len(beats), 'bpm': None, 'periodSeconds': None,
                'offsetSeconds': None, 'phase': None, 'residualMs': None}
    times = np.asarray(beats, dtype=np.float64)
    period, origin = float(np.median(np.diff(times))), float(times[0])
    for _ in range(3):  # Re-index so a dropped beat cannot shear the fit.
        index = np.round((times - origin) / period)
        period, origin = (float(v) for v in np.polyfit(index, times, 1))
    residual = float(np.sqrt(np.mean((times - (origin + index * period)) ** 2)))
    offset = round(origin % period, 6)
    if offset >= round(period, 6):
        offset = 0.0
    return {'status': 'irregular' if residual > GRID_MAX_RESIDUAL * period else 'fitted',
            'beatCount': len(beats), 'bpm': round(60 / period, 3), 'periodSeconds': round(period, 6),
            'offsetSeconds': offset, 'phase': round(offset / period, 4), 'residualMs': round(residual * 1000, 3)}


def manual_downbeat(grid, time, beats_per_bar):
    if grid['status'] != 'fitted':
        raise ValueError('Manual downbeat needs a fitted grid')
    period, offset = grid['periodSeconds'], grid['offsetSeconds']
    index = round((time - offset) / period)
    if abs(time - (offset + index * period)) > beat_tolerance(period):
        raise ValueError('Manual downbeat is off the fitted grid')
    return {'status': 'manual', 'time': time, 'beatsPerBar': beats_per_bar,
            'barOffsetBeats': index % beats_per_bar, 'method': 'manual'}


def estimate_downbeat(grid, curve, hop_seconds, beats_per_bar=4, manual=None):
    """Bar lines need accent evidence; an even or ambiguous pattern stays unknown."""
    if manual is not None:
        return manual_downbeat(grid, manual, beats_per_bar)
    result = {'status': 'unknown', 'time': None, 'beatsPerBar': beats_per_bar,
              'barOffsetBeats': None, 'method': 'low-band accent by bar position'}
    if grid['status'] != 'fitted':
        return result
    period, offset = grid['periodSeconds'], grid['offsetSeconds']
    reach = max(1, round(ACCENT_WINDOW / hop_seconds))
    totals, counts = [0.0] * beats_per_bar, [0] * beats_per_bar
    index = 0
    while (center := round((offset + index * period) / hop_seconds)) < len(curve):
        totals[index % beats_per_bar] += max(curve[max(0, center - reach):center + reach + 1])
        counts[index % beats_per_bar] += 1
        index += 1
    if min(counts) < ACCENT_MIN_BARS:
        return result
    scores = [round4(a / b) for a, b in zip(totals, counts)]
    result['scores'] = scores
    ranked = sorted(scores, reverse=True)
    if ranked[0] <= 0 or (ranked[0] - ranked[1]) / ranked[0] < ACCENT_CONTRAST:
        return result
    best = scores.index(ranked[0])
    return {**result, 'status': 'estimated', 'barOffsetBeats': best, 'time': round(offset + best * period, 6)}


def rms_edges(y, sr):
    """Level steps from wide power windows, so regular beats do not register."""
    import numpy as np
    hop = max(1, round(RMS_HOP * sr))
    energy = np.concatenate([[0], np.cumsum(np.asarray(y, dtype=np.float64) ** 2)])
    span = round(RMS_WINDOW / RMS_HOP)
    count = len(y) // hop
    if count < 2 * span + 1:
        return []
    def level(start, stop):
        return (energy[stop * hop] - energy[start * hop]) / ((stop - start) * hop)
    floor = 10 ** (RMS_FLOOR_DB / 10)
    candidates = []
    for i in range(span, count - span + 1):
        change = 10 * math.log10(max(level(i, i + span), floor) / max(level(i - span, i), floor))
        if abs(change) >= RMS_EDGE_DB:
            candidates.append((abs(change), i, change))
    edges = []
    for _, i, change in sorted(candidates, key=lambda item: (-item[0], item[1])):
        if all(abs(i - other) * RMS_HOP >= RMS_MIN_GAP for other, _ in edges):
            edges.append((i, change))
    return [{'time': round4(i * hop / sr), 'source': 'rms', 'direction': 'up' if change > 0 else 'down',
             'deltaDb': round(change, 2)} for i, change in sorted(edges)]


def beat_tolerance(period):
    return min(.06, period / 6)


def check_boundaries(boundaries, grid, downbeat):
    """Place each boundary on the grid; bar agreement stays null without a bar line."""
    results = []
    bar = downbeat['beatsPerBar']
    for boundary in boundaries:
        check = {**boundary, 'gridBeat': None, 'beatErrorMs': None, 'onBeat': None, 'gridBeatModBar': None,
                 'beatsIntoBar': None, 'barsFromDownbeat': None, 'onBar': None}
        if grid['status'] == 'fitted':
            period, offset = grid['periodSeconds'], grid['offsetSeconds']
            index = round((boundary['time'] - offset) / period)
            error = boundary['time'] - (offset + index * period)
            check.update(gridBeat=index, beatErrorMs=round(error * 1000, 2), gridBeatModBar=index % bar,
                         onBeat=abs(error) <= beat_tolerance(period))
            if downbeat['time'] is not None:
                beats = round((boundary['time'] - downbeat['time']) / period)
                check.update(beatsIntoBar=beats % bar, barsFromDownbeat=beats // bar,
                             onBar=check['onBeat'] and beats % bar == 0)
        results.append(check)
    return results


def boundary_rotation(checks, beats_per_bar):
    """Which grid position boundaries favour: evidence for the real bar line."""
    positions = [c['gridBeatModBar'] for c in checks if c['onBeat']]
    counts = [Counter(positions)[i] for i in range(beats_per_bar)]
    ranked = sorted(counts, reverse=True)
    clear = len(positions) >= BOUNDARY_MIN and ranked[0] > ranked[1] and ranked[0] / len(positions) >= BOUNDARY_MAJORITY
    return {'counts': counts, 'best': counts.index(ranked[0]) if clear else None, 'boundaries': len(positions)}


def reconcile_downbeat(downbeat, rotation):
    if rotation['best'] is None:
        return downbeat
    result = {**downbeat, 'boundaryBarOffsetBeats': rotation['best']}
    if downbeat['status'] == 'estimated' and downbeat['barOffsetBeats'] != rotation['best']:
        result.update(status='conflict', time=None, estimatedTime=downbeat['time'])
    return result


def bake_features(y, sr, fps, beats, beats_per_bar=4, downbeat=None, sections=(), **options):
    baked = bake_frames(y, sr, fps, **options)
    curve, hop_seconds = baked.pop('onsetCurve'), baked.pop('onsetHopSeconds')
    grid = fit_grid(beats)
    bar = estimate_downbeat(grid, curve, hop_seconds, beats_per_bar, downbeat)
    supplied = [{'time': s['start'], 'source': 'supplied', 'label': s['label']} for s in sections]
    boundaries = check_boundaries(rms_edges(y, sr) + supplied, grid, bar)
    rotation = boundary_rotation(boundaries, beats_per_bar)
    bar = reconcile_downbeat(bar, rotation)
    if bar['status'] == 'conflict':
        boundaries = check_boundaries([{k: b[k] for k in ('time', 'source', 'label', 'direction', 'deltaDb') if k in b}
                                       for b in boundaries], grid, bar)
    boundaries.sort(key=lambda b: b['time'])
    return {**baked, 'fps': {'num': fps.numerator, 'den': fps.denominator}, 'sampleRate': sr,
            'grid': grid, 'downbeat': bar, 'boundaries': boundaries, 'boundaryRotation': rotation}


def parse_fps(text):
    value = Fraction(text)
    if value <= 0:
        raise ValueError('Invalid fps')
    return value
