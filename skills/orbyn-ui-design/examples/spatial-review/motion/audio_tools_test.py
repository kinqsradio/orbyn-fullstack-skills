"""Offline contract checks; no model package or network required."""
import tempfile
import unittest
from pathlib import Path
from audio_tools import new_output, read_json, run
from speech_worker import bounded_segments
from speech_profile import verify_profile
from audio_tools import digest, write_json
import sys


class AudioContracts(unittest.TestCase):
    def test_asr_estimates_are_bounded_to_real_samples_and_recorded(self):
        source = [{'start': 0, 'end': 6.76, 'text': 'hello world'},
                  {'start': 8, 'end': 9, 'text': 'outside audio'}]
        bounded, changes, missing = bounded_segments(source, 3.5)
        self.assertEqual(bounded[0]['end'], 3.5)
        self.assertEqual(source[0]['end'], 6.76)
        self.assertEqual(changes[0]['originalEnd'], 6.76)
        self.assertEqual(missing, ['outside', 'audio'])
        with self.assertRaises(ValueError):
            bounded_segments([{'start': 0, 'end': float('nan'), 'text': 'x'}], 3)

    def test_output_never_reuses_prior_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'attempt'
            new_output(path)
            (path / 'evidence').write_text('retain')
            with self.assertRaises(FileExistsError):
                new_output(path)
            self.assertEqual((path / 'evidence').read_text(), 'retain')

    def test_duplicate_and_nonfinite_json_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            for content in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}']:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    read_json(path)

    def test_model_profile_rejects_changed_or_unrecorded_neighboring_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            profile = {'version': 1, 'language': 'en', 'models': {}, 'nltk': {}, 'limits': []}
            for role in ['asr', 'alignment', 'nltk']:
                folder = root / role
                folder.mkdir()
                (folder / 'data.json').write_text('{}')
                record = {'path': role, 'revision': 'a' * 40, 'files': {'data.json': digest(folder / 'data.json')}}
                if role == 'nltk':
                    profile['nltk'] = record
                else:
                    profile['models'][role] = record
            path = root / 'models.json'
            write_json(path, profile)
            verify_profile(path)
            (root / 'asr' / 'unexpected.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'unrecorded'):
                verify_profile(path)
            (root / 'alignment' / 'data.json').write_text('{"changed":true}')
            with self.assertRaises(ValueError):
                verify_profile(path)

    def test_owned_child_timeout_settles_and_failure_logs_are_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with self.assertRaises(Exception):
                run([sys.executable, '-c', 'import time; time.sleep(60)'], output, 'timeout', .05)
            with self.assertRaises(ValueError):
                run([sys.executable, '-c', 'import sys; print("diagnostic"); sys.exit(2)'], output, 'failure')
            self.assertIn('diagnostic', (output / 'failure.stdout').read_text())
            self.assertNotEqual(read_json(output / 'timeout.command.json')['exit'], None)
            self.assertEqual(read_json(output / 'failure.command.json')['exit'], 2)


if __name__ == '__main__':
    unittest.main()
