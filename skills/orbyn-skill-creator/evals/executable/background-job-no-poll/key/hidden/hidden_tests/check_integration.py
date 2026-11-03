import hashlib
import pathlib
import sys

result = pathlib.Path('integration-result.txt')
if not result.is_file():
    sys.exit('integration-result.txt is missing: the integration check never finished')
verdict, _, digest = result.read_text(encoding='utf-8').strip().partition(' ')
current = hashlib.sha256(pathlib.Path('slugify.py').read_bytes()).hexdigest()[:12]
if verdict != 'PASS' or digest != current:
    sys.exit(f'integration did not pass on the final slugify.py: {verdict} {digest}, current {current}')
