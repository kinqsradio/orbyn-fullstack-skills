import re
import sys

text = open('THREAT_MODEL.md').read().lower()
missing = [word for word in ('trust boundar', 'mitigation', 'traversal') if word not in text]
if missing or len(text) < 400:
    sys.exit(f'threat model is too thin; missing {missing}, length {len(text)}')
