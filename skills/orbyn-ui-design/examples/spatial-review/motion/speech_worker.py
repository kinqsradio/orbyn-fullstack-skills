"""Internal offline ASR + WhisperX forced-alignment worker; no model acquisition."""
import argparse
import importlib.metadata
import math
import os
from pathlib import Path
import sys
import wave
from audio_tools import digest, read_json, write_json
from speech_profile import verify_profile


def bounded_segments(segments, duration):
    """ASR times are estimates; retain raw input, bound alignment to real samples."""
    bounded, adjustments, missing = [], [], []
    for index, segment in enumerate(segments):
        start, end = segment['start'], segment['end']
        if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in [start, end]):
            raise ValueError('ASR returned nonfinite timing')
        a, b = max(0, start), min(duration, end)
        if a >= b:
            missing.extend(segment['text'].split())
            adjustments.append({'segment': index, 'status': 'outside-audio', 'originalStart': start, 'originalEnd': end})
        else:
            bounded.append({**segment, 'start': a, 'end': b})
            if a != start or b != end:
                adjustments.append({'segment': index, 'status': 'bounded-to-decoded-audio',
                                    'originalStart': start, 'originalEnd': end, 'start': a, 'end': b})
    return bounded, adjustments, missing


def worker(args):
    profile, roots = verify_profile(args.models)
    # This worker is a disposable CLI child. Refuse Python socket connections
    # as well as setting each loader's offline flag; model setup is separate.
    def offline(event, _arguments):
        if event in {'socket.connect', 'socket.getaddrinfo'}:
            raise RuntimeError('Speech runtime network acquisition is disabled')
    sys.addaudithook(offline)
    # Process-local settings only; caller/global host configuration is untouched.
    for key in ['HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY', 'DO_NOT_TRACK']:
        os.environ[key] = '1'
    os.environ['PYANNOTE_METRICS_ENABLED'] = '0'
    os.environ['NLTK_DATA'] = str(roots['nltk'])
    import nltk
    nltk.data.path[:] = [str(roots['nltk'])]
    def no_download(*_args, **_kwargs):
        raise ValueError('Runtime downloads are disabled; prepare the explicit tokenizer profile first')
    nltk.download = no_download
    nltk.data.find('tokenizers/punkt_tab/english/')
    import numpy as np
    import soundfile as sf
    import torch
    from whisperx.alignment import load_align_model, align
    torch.set_num_threads(args.threads)
    audio, sample_rate = sf.read(args.audio, dtype='float32')
    if sample_rate != 16000 or audio.ndim != 1 or not np.isfinite(audio).all():
        raise ValueError('Worker expects decoded finite mono16kHz')
    duration = len(audio) / sample_rate
    adjustments, missing = [], []
    if args.segments:
        segments = read_json(args.segments)
        if not isinstance(segments, list) or len(segments) > 1000:
            raise ValueError('Supplied transcript segment budget')
        for segment in segments:
            if set(segment) != {'start', 'end', 'text'} or not isinstance(segment['text'], str) or not segment['text'].strip() or len(segment['text']) > 10000 or not 0 <= segment['start'] < segment['end'] <= duration:
                raise ValueError('Invalid supplied transcript segment')
        origin = 'caller-supplied text; forced alignment does not verify the spoken words'
    else:
        from faster_whisper import WhisperModel
        import faster_whisper
        vad_path = Path(faster_whisper.__file__).parent / 'assets/silero_vad_v6.onnx'
        vad_sha = digest(vad_path)
        model = WhisperModel(str(roots['asr']), device=args.device,
                             compute_type='int8' if args.device == 'cpu' else 'float16',
                             local_files_only=True, cpu_threads=args.threads, num_workers=1)
        # faster-whisper's VAD ONNX is bundled locally; no pyannote/token/hub loader.
        result, info = model.transcribe(audio, language=profile['language'], beam_size=5,
                                        temperature=0, condition_on_previous_text=False,
                                        vad_filter=True, word_timestamps=False)
        segments = [{'start': float(s.start), 'end': float(s.end), 'text': s.text} for s in result]
        write_json(Path(args.out) / 'raw-asr.json', {'segments': segments, 'duration': duration})
        segments, adjustments, missing = bounded_segments(segments, duration)
        origin = 'faster-whisper ASR with bundled local VAD; model estimate'
        del model
    output = Path(args.out)
    if any((output / name).exists() for name in ['transcript.json', 'raw-alignment.json']):
        raise ValueError('Worker refuses to overwrite prior speech artifacts')
    if segments:
        model, metadata = load_align_model(profile['language'], args.device,
                                          model_name=str(roots['alignment']), model_cache_only=True)
        result = align(segments, model, metadata, audio, args.device,
                       return_char_alignments=True, interpolate_method='nearest')
        del model
    else:
        result = {'segments': [], 'word_segments': []}
    words = []
    for index, word in enumerate(result['word_segments']):
        text = word.get('word')
        if not isinstance(text, str) or not text.strip() or len(text) > 200:
            raise ValueError('Unrepresentable model token; inspect raw result')
        start, end, score = word.get('start'), word.get('end'), word.get('score')
        valid = all(isinstance(v, (int, float)) and math.isfinite(v) for v in [start, end]) and 0 <= start < end <= duration
        score = float(score) if isinstance(score, (int, float)) and math.isfinite(score) else None
        words.append({'id': 'word-' + str(index), 'text': text,
                      'start': float(start) if valid else None, 'end': float(end) if valid else None,
                      'status': ('aligned' if score is not None else 'inferred') if valid else 'missing',
                      'score': score})
    for text in missing:
        words.append({'id': 'word-' + str(len(words)), 'text': text, 'start': None,
                      'end': None, 'status': 'missing', 'score': None})
    # Raw results can contain library NaNs for unresolved timing; normalize to null.
    def clean(value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    write_json(output / 'raw-alignment.json', clean(result))
    transcript = {'version': 1, 'audioSha256': args.audio_sha, 'duration': duration,
                  'language': profile['language'], 'revision': 1, 'words': words, 'history': [],
                  'model': {'origin': origin,
                            'timingMeaning': 'Model estimates; interpolation may affect endpoints even when a score is present. Human corrections remain separate.',
                            'profileSha256': digest(args.models), 'segmentAdjustments': adjustments,
                            'bundledVadSha256': vad_sha if not args.segments else None,
                            'networkPolicy': 'Offline loader flags and process-local Python socket audit guard; not an OS network sandbox',
                            'revisions': {k: v['revision'] for k, v in profile['models'].items()},
                            'dependencies': {n: importlib.metadata.version(n) for n in ['whisperx', 'faster-whisper', 'torch', 'transformers', 'nltk']}}}
    write_json(output / 'transcript.json', transcript)
    # Models and their neighboring data must still match after the worker settles.
    verify_profile(args.models)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['audio', 'models', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--audio-sha', required=True)
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--segments', type=Path)
    args = parser.parse_args()
    try:
        sys.exit(worker(args))
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(2)
