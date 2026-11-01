"""Internal offline faster-whisper word timing for supplied lyrics; no model acquisition."""
import argparse
import importlib.metadata
import os
from pathlib import Path
import sys
import wave
from audio_tools import digest, write_json


def transcribe_words(model, audio, prompt, language):
    """Hand the model samples, not a path: its own decoder breaks on some PyAV versions."""
    import numpy as np
    if not isinstance(audio, np.ndarray):
        raise TypeError('Pass decoded numpy samples; a path reaches faster_whisper.decode_audio')
    if audio.ndim != 1 or audio.dtype != np.float32:
        raise TypeError('Expected mono float32 samples')
    # initial_prompt reaches only the first window here, so hotwords carries the
    # vocabulary onward. Neighbouring text conditioning would repeat invented words.
    options = {'language': language, 'initial_prompt': prompt, 'hotwords': prompt, 'word_timestamps': True,
               'condition_on_previous_text': False, 'temperature': 0, 'beam_size': 5, 'vad_filter': False}
    segments, _info = model.transcribe(audio, **options)
    words = [{'word': w.word, 'start': float(w.start), 'end': float(w.end), 'probability': float(w.probability)}
             for segment in segments for w in segment.words or []]  # Lazy: this loop runs the model.
    return words, {**options, 'initial_prompt': bool(prompt), 'hotwords': bool(prompt)}


def model_closure(folder):
    """Hash every file; a converted model is data, so code in it is refused."""
    folder = Path(folder).resolve(strict=True)
    if not folder.is_dir():
        raise ValueError('Model directory required')
    hashes = {}
    for path in sorted(p for p in folder.rglob('*') if not p.is_dir()):
        relative = path.relative_to(folder)
        if path.is_symlink() or path.suffix in {'.py', '.so', '.dylib', '.dll'} or any(p.startswith('.') for p in relative.parts):
            raise ValueError('Unsafe model file: ' + str(relative))
        hashes[str(relative)] = digest(path)
    if 'model.bin' not in hashes:
        raise ValueError('Expected a converted faster-whisper model directory')
    return hashes


def read_samples(path):
    import numpy as np
    with wave.open(str(path), 'rb') as source:
        if source.getnchannels() != 1 or source.getsampwidth() != 2 or source.getframerate() != 16000:
            raise ValueError('Worker expects decoded mono 16-bit 16 kHz audio')
        return np.frombuffer(source.readframes(source.getnframes()), dtype='<i2').astype(np.float32) / 32768


def worker(args):
    closure = model_closure(args.model_dir)
    def offline(event, _arguments):
        if event in {'socket.connect', 'socket.getaddrinfo'}:
            raise RuntimeError('Lyric runtime network acquisition is disabled')
    sys.addaudithook(offline)
    for key in ['HF_HUB_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY', 'DO_NOT_TRACK']:
        os.environ[key] = '1'
    from faster_whisper import WhisperModel
    compute = 'int8' if args.device == 'cpu' else 'float16'
    model = WhisperModel(str(args.model_dir), device=args.device, compute_type=compute,
                         local_files_only=True, cpu_threads=args.threads, num_workers=1)
    prompt = Path(args.prompt).read_text()
    words, options = transcribe_words(model, read_samples(args.audio), prompt, args.language)
    write_json(args.out / 'raw-asr.json', {'words': words})
    write_json(args.out / 'asr-runtime.json', {
        'kind': 'faster-whisper', 'modelRun': True, 'modelName': args.model_dir.name, 'modelFiles': closure,
        'device': args.device, 'computeType': compute, 'options': options, 'promptSha256': digest(args.prompt),
        'audioInput': 'FFmpeg-decoded numpy float32 mono 16 kHz',
        'dependencies': {n: importlib.metadata.version(n) for n in ['faster-whisper', 'ctranslate2', 'numpy']},
        'networkPolicy': 'Offline loader flags and process-local Python socket audit guard; not an OS network sandbox'})
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['audio', 'prompt', 'model-dir', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--language', default='en')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    parser.add_argument('--threads', type=int, default=2)
    args = parser.parse_args()
    try:
        sys.exit(worker(args))
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(2)
