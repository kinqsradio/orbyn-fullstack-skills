"""tally: count lines in a file."""
import argparse


def build_parser():
    parser = argparse.ArgumentParser(prog='tally')
    parser.add_argument('path')
    parser.add_argument('--verbose', action='store_true', help='print each counted line')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    with open(args.path) as handle:
        lines = handle.read().splitlines()
    if args.verbose:
        for line in lines:
            print(line)
    print(len(lines))
    return 0
