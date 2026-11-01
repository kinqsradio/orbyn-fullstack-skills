#!/usr/bin/env python3
"""Bake per-video-frame audio features with only Python's standard library.

Reads one audio file, runs FFmpeg to decode it to mono 16-bit PCM, and writes one new
JSON file: band energies, an RMS curve, an onset envelope and onset times. Nothing else
is installed, imported or fetched. Exit 0: written. Exit 2: nothing written.
"""
import argparse
from array import array
import cmath
from fractions import Fraction
import hashlib
from itertools import accumulate
import json
import math
from operator import mul
import os
from pathlib import Path
import subprocess
import sys

SAMPLE_RATE = 22050
WINDOW = 2048
HOP = 512
BANDS = (('sub', 20, 60), ('bass', 60, 250), ('lowMid', 250, 500), ('mid', 500, 2000), ('highMid', 2000, 6000), ('high', 6000, 11025))
FLUX_BANDS = 32
SILENCE = 1e-4
PEAK_REACH = 3  # Hops on each side an onset must beat, about 70 ms.
MEAN_REACH = 11  # Hops on each side of the running level, about 250 ms.
MIN_GAP = .07  # Seconds. Faster repeats read as one hit.
REFINE = .06  # Seconds either side of a flux peak to search for the attack.
RISE_WINDOW = 110  # Samples, about 5 ms.
LIMITS = ['Onsets come from spectral change, so they are candidates for a person to confirm, not beats or bars',
          'Soft attacks and slow swells can pass with no onset',
          'Band energies compare within a band; use bands[].peak to restore amplitude']


class RealFFT:
    """Power spectrum of a real frame, through a half-size complex FFT."""

    def __init__(self, size):
        if size < 4 or size & (size - 1):
            raise ValueError('FFT size must be a power of two')
        self.half = half = size // 2
        bits = int(math.log2(half))
        self.order = [int(format(i, f'0{bits}b')[::-1], 2) for i in range(half)]
        self.turns = [cmath.exp(-2j * math.pi * k / half) for k in range(half // 2)]
        self.unpack = [-.5j * cmath.exp(-2j * math.pi * k / size) for k in range(half // 2 + 1)]

    def power(self, frame):
        half, turns = self.half, self.turns
        data = [complex(frame[2 * i], frame[2 * i + 1]) for i in self.order]
        span = 1
        while span < half:
            step = half // (span * 2)
            for start in range(0, half, span * 2):
                turn = 0
                for low in range(start, start + span):
                    high = low + span
                    twisted = data[high] * turns[turn]
                    data[high] = data[low] - twisted
                    data[low] += twisted
                    turn += step
            span *= 2
        result = [0.] * (half + 1)
        for k in range(half // 2 + 1):
            first, second = data[k % half], data[(half - k) % half].conjugate()
            even, odd = .5 * (first + second), self.unpack[k] * (first - second)
            forward, mirror = even + odd, (even - odd).conjugate()
            result[k] = forward.real ** 2 + forward.imag ** 2
            result[half - k] = mirror.real ** 2 + mirror.imag ** 2
        return result


def spectra(samples, rate):
    """Yield one normalized power spectrum per hop, centred on hop * index."""
    fft, count = RealFFT(WINDOW), len(samples) // HOP + 1
    hann = [.5 - .5 * math.cos(2 * math.pi * i / WINDOW) for i in range(WINDOW)]
    scale = 4 / sum(hann) ** 2  # A full-scale sine reads about 1 at its peak bin.
    pad = array('f', bytes(4 * (WINDOW // 2)))
    padded = pad + samples + pad + array('f', bytes(4 * WINDOW))
    for index in range(count):
        start = index * HOP
        yield [value * scale for value in fft.power(list(map(mul, padded[start:start + WINDOW], hann)))]


def edge_bins(low, high, rate):
    width = rate / WINDOW
    return max(1, round(low / width)), min(WINDOW // 2 + 1, max(round(low / width) + 1, round(high / width)))


def frame_span(index, fps):
    return Fraction(index) / fps, Fraction(index + 1) / fps


def hops_in(index, fps, rate, count):
    """Hop numbers whose centres fall inside a frame, or the nearest one."""
    start, end = frame_span(index, fps)
    first, last = math.ceil(start * rate / HOP), math.ceil(end * rate / HOP)
    return range(min(first, count - 1), min(max(last, first + 1), count))


def pick_onsets(envelope, rate):
    """Local peaks that stand clear of the running level around them."""
    peaks, size = [], len(envelope)
    for hop, value in enumerate(envelope):
        near = envelope[max(0, hop - MEAN_REACH):hop + MEAN_REACH + 1]
        reach = envelope[max(0, hop - PEAK_REACH):hop + PEAK_REACH + 1]
        if value >= .08 and value == max(reach) and value > 1.5 * sum(near) / len(near) and (hop == 0 or value > envelope[hop - 1]):
            peaks.append(hop)
    return [hop for hop in peaks if hop < size]


def refine(energy, centre, rate):
    """Move a flux peak to the sharpest rise in short-time energy near it, or None if the sound is falling."""
    low = max(RISE_WINDOW, round((centre - REFINE) * rate))
    high = min(len(energy) - RISE_WINDOW - 1, round((centre + REFINE) * rate))

    def rise(sample):
        return energy[sample + RISE_WINDOW] - 2 * energy[sample] + energy[sample - RISE_WINDOW]

    if high <= low:
        return centre
    coarse = max(range(low, high, RISE_WINDOW // 5), key=rise)
    at = max(range(max(low, coarse - RISE_WINDOW // 5), min(high, coarse + RISE_WINDOW // 5)), key=rise)
    reach = round(REFINE * rate)
    before = energy[at] - energy[max(0, at - reach)]
    after = energy[min(len(energy) - 1, at + reach)] - energy[at]
    return None if after < before else at / rate  # A sound stopping also makes spectral change.


def analyze(samples, rate, fps):
    """Return the features for a mono float array of samples."""
    if not samples:
        raise ValueError('Audio has no samples')
    duration = Fraction(len(samples), rate)
    frames = max(1, math.ceil(duration * fps))
    energy = array('d', [0.])
    energy.extend(accumulate(map(mul, samples, samples)))
    peak_sample = max(max(samples), -min(samples))
    edges = [10 ** (math.log10(40) + (math.log10(10000) - math.log10(40)) * i / FLUX_BANDS) for i in range(FLUX_BANDS + 1)]
    flux_bins = [edge_bins(edges[i], edges[i + 1], rate) for i in range(FLUX_BANDS)]
    band_bins = [edge_bins(low, high, rate) for _name, low, high in BANDS]
    level, previous, flux = [[] for _ in BANDS], [0.] * FLUX_BANDS, []
    for power in spectra(samples, rate):
        running = [0., *accumulate(power)]
        for store, (low, high) in zip(level, band_bins):
            store.append(math.sqrt(running[high] - running[low]))
        current = [math.log1p(1000 * math.sqrt((running[high] - running[low]) / (high - low))) for low, high in flux_bins]
        flux.append(sum(max(0., now - before) for now, before in zip(current, previous)))
        previous = current
    count = len(flux)
    top = max(flux) or 1.
    envelope = [value / top for value in flux]
    silent = peak_sample < SILENCE
    # A Hann window sees a click fastest a quarter of a window before it arrives.
    delay = Fraction(WINDOW, 4 * rate)
    onsets = []
    if not silent:
        for hop in pick_onsets(envelope, rate):
            time = refine(energy, float(Fraction(hop * HOP, rate) + delay), rate)
            if time is None or (onsets and time - onsets[-1]['time'] < MIN_GAP):
                continue
            onsets.append({'time': round(time, 4), 'gain': round(envelope[hop], 4)})
    onset_frames = [0.] * frames
    for hop, value in enumerate(envelope):
        # Half a hop later still, so the envelope never leads the picture ahead of the sound.
        frame = min(frames - 1, math.floor((Fraction(hop * HOP, rate) + delay + Fraction(HOP, 2 * rate)) * fps))
        onset_frames[frame] = max(onset_frames[frame], value)
    for onset in onsets:
        onset['frame'] = min(frames - 1, math.floor(Fraction(onset['time']) * fps))
        onset_frames[onset['frame']] = max(onset_frames[onset['frame']], onset['gain'])
    band_energy, bands = {}, []
    for (name, low, high), store in zip(BANDS, level):
        curve = [sum(store[hop] for hop in hops) / len(hops)
                 for hops in (hops_in(index, fps, rate, count) for index in range(frames))]
        peak = max(curve)
        band_energy[name] = [round(value / peak, 5) if peak > SILENCE else 0. for value in curve]
        bands.append({'name': name, 'lowHz': low, 'highHz': high, 'peak': round(peak, 6)})
    rms = []
    for index in range(frames):
        start, end = (min(len(samples), math.floor(t * rate)) for t in frame_span(index, fps))
        end = max(end, min(len(samples), start + 1))
        rms.append(round(math.sqrt(max(0., energy[end] - energy[start]) / max(1, end - start)), 5))
    return {'version': 1, 'kind': 'audio-bake', 'status': 'silent' if silent else 'measured', 'fps': str(fps), 'frames': frames,
            'sampleRate': rate, 'duration': float(duration), 'bands': bands, 'bandEnergy': band_energy, 'rms': rms,
            'onsetEnvelope': [round(value, 5) for value in onset_frames], 'onsets': onsets, 'limits': LIMITS}


def parse_fps(text):
    try:
        fps = Fraction(text)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f'Frame rate must be a number or a ratio such as 30000/1001: {text}') from None
    if not 1 <= fps <= 240:
        raise ValueError('Frame rate must be between 1 and 240')
    return fps


def decode(path, ffmpeg, rate, max_seconds):
    command = [ffmpeg, '-nostdin', '-v', 'error', '-t', str(max_seconds), '-i', str(path), '-map', '0:a:0', '-ac', '1', '-ar', str(rate),
               '-f', 's16le', '-acodec', 'pcm_s16le', 'pipe:1']
    try:
        result = subprocess.run(command, capture_output=True, timeout=max(60, max_seconds))
    except FileNotFoundError:
        raise ValueError(f'FFmpeg not found: {ffmpeg}') from None
    except subprocess.TimeoutExpired:
        raise ValueError('FFmpeg timed out decoding the audio') from None
    if result.returncode:
        raise ValueError('FFmpeg could not decode the audio: ' + result.stderr.decode(errors='replace').strip()[-400:])
    pcm = array('h')
    pcm.frombytes(result.stdout[:len(result.stdout) // 2 * 2])
    if sys.byteorder == 'big':
        pcm.byteswap()
    return array('f', (value / 32768 for value in pcm))


def write_new(path, value):
    """Write beside the target, then move it into place, so a failure leaves nothing."""
    temporary = path.with_name(path.name + '.partial')
    with temporary.open('x') as target:
        json.dump(value, target, allow_nan=False, separators=(',', ':'))
        target.write('\n')
    if path.exists():
        temporary.unlink()
        raise ValueError(f'Output already exists: {path}')
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('input', type=Path)
    parser.add_argument('--out', type=Path, required=True, help='New JSON file; an existing file is refused')
    parser.add_argument('--fps', default='30', help='Video frame rate, such as 30 or 30000/1001')
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--max-seconds', type=int, default=1800)
    options = parser.parse_args()
    try:
        fps = parse_fps(options.fps)
        if not options.input.is_file():
            raise ValueError(f'Audio file not found: {options.input}')
        if options.out.exists() or not options.out.parent.is_dir():
            raise ValueError(f'Output must be a new file in an existing folder: {options.out}')
        if options.max_seconds < 1:
            raise ValueError('--max-seconds must be at least 1')
        samples = decode(options.input, options.ffmpeg, SAMPLE_RATE, options.max_seconds)
        bake = analyze(samples, SAMPLE_RATE, fps)
        bake['sourceSha256'] = hashlib.sha256(options.input.read_bytes()).hexdigest()
        write_new(options.out, bake)
    except (OSError, ValueError) as error:
        print(f'audio-bake: {error}', file=sys.stderr)
        return 2
    print(options.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
