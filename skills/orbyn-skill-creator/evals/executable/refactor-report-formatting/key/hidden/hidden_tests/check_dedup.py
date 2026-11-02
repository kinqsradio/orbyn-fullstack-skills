import sys

source = open('report.py').read()
if source.count('%-12s') != 1:
    sys.exit('the row format must appear exactly once')
