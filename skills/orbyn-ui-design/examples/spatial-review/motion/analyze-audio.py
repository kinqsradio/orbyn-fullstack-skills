#!/usr/bin/env python3
"""Analyze explicitly selected local audio; no providers or model downloads."""
import argparse
import importlib.metadata
import math
from pathlib import Path
import sys
from audio_tools import cancellation_signals, decode_audio, digest, new_output, receipt, regular_file, run, write_json


def analyze(y, sr, hop, bins, librosa, np):
    if y.ndim != 1 or not len(y) or not np.isfinite(y).all():
        raise ValueError('Expected nonempty finite mono samples')
    duration = len(y) / sr
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    silent = not bool(np.any(onset))
    tempo, beats = (0, np.array([])) if silent else librosa.beat.beat_track(
        onset_envelope=onset, sr=sr, hop_length=hop, units='time')
    times = [] if silent else librosa.onset.onset_detect(
        onset_envelope=onset, sr=sr, hop_length=hop, units='time').tolist()
    energy = librosa.feature.rms(y=y, hop_length=hop)[0]
    waveform = []
    for i, chunk in enumerate(np.array_split(y, min(bins, len(y)))):
        waveform.append({'time': i * duration / min(bins, len(y)),
                         'min': float(chunk.min()), 'max': float(chunk.max())})
    return {
        'duration': duration, 'status': 'silent' if silent else 'estimated',
        'tempo': None if silent else float(np.asarray(tempo).reshape(-1)[0]),
        'beats': [float(t) for t in beats if 0 <= t <= duration],
        'onsets': [float(t) for t in times if 0 <= t <= duration],
        'energy': [{'time': i * hop / sr, 'rms': float(energy[i])} for i in range(0, len(energy), max(1, math.ceil(len(energy) / bins))) if i * hop / sr <= duration],
        'waveform': waveform,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    parser.add_argument('--sample-rate', type=int, default=22050)
    parser.add_argument('--hop-length', type=int, default=512)
    parser.add_argument('--waveform-bins', type=int, default=512)
    parser.add_argument('--max-seconds', type=int, default=600)
    args = parser.parse_args()
    source = regular_file(args.input)
    if args.sample_rate not in [16000, 22050, 44100, 48000] or not 64 <= args.hop_length <= 4096 or not 16 <= args.waveform_bins <= 2048 or not 1 <= args.max_seconds <= 3600:
        raise ValueError('Invalid audio analysis budgets')
    output = new_output(args.out)
    original = digest(source)
    receipt(output, 'preparing', source)
    try:
        import librosa
        import numpy as np
        decoded, audio = decode_audio(source, output, args.ffmpeg, args.ffprobe,
                                      args.sample_rate, args.max_seconds)
        y, sr = librosa.load(decoded, sr=None, mono=True)
        result = analyze(y, sr, args.hop_length, args.waveform_bins, librosa, np)
        data = {'version': 1, 'audio': audio,
                'analysis': {'sampleRate': sr, 'hopLength': args.hop_length,
                             'units': 'seconds', **result},
                'manual': {'beats': None, 'words': []},
                'limits': ['Beat/tempo estimates may be ambiguous; manual corrections are authoritative.',
                           'Audio analysis does not transcribe words or establish media rights.']}
        write_json(output / 'audio-analysis.json', data)
        if digest(source) != original:
            raise ValueError('Audio source changed during analysis')
        receipt(output, 'completed', source,
                toolSources={p.name: digest(p) for p in [Path(__file__), Path(__file__).with_name('audio_tools.py')]}, decodedSha256=digest(decoded),
                dependencies={n: importlib.metadata.version(n) for n in ['librosa', 'numpy', 'scipy', 'soundfile']},
                ffmpeg=run([args.ffmpeg, '-version'], output, 'ffmpeg-version').splitlines()[0])
        print(output / 'audio-analysis.json')
        return 0
    except (Exception, KeyboardInterrupt) as error:
        receipt(output, 'cancelled' if isinstance(error, KeyboardInterrupt) else 'failed', source,
                error=type(error).__name__ + ': ' + str(error))
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    cancellation_signals()
    sys.exit(main())
