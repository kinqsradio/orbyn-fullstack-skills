import sys

text = open('README.md').read()
if '--verbose' not in text or 'line' not in text.split('--verbose', 1)[1][:300].lower():
    sys.exit('README.md must explain --verbose')
