#!/usr/bin/env python3
"""Small opaque-sRGB/known-alpha contrast calculation; not an accessibility audit."""
import argparse
import json
import math
import re
import sys

THRESHOLDS = {'normal': 4.5, 'large': 3.0, 'nontext': 3.0, 'focus-adjacency': 3.0}


def rgb(value):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
        raise ValueError('Supply an exact #RRGGBB value; missing/ambiguous, gradients and other CSS forms are not inferred')
    return tuple(int(value[i:i+2], 16) / 255 for i in (1, 3, 5))


def luminance(channels):
    if len(channels) != 3 or any(not math.isfinite(c) or not 0 <= c <= 1 for c in channels):
        raise ValueError('sRGB channels must be finite values in 0..1')
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return sum(c * weight for c, weight in zip(linear, (.2126, .7152, .0722)))


def composite(foreground, background, alpha):
    if not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError('Alpha must be a finite value in 0..1')
    return tuple(f * alpha + b * (1-alpha) for f, b in zip(rgb(foreground), rgb(background)))


def contrast(foreground, background, alpha=1):
    first, second = luminance(composite(foreground, background, alpha)), luminance(rgb(background))
    return (max(first, second) + .05) / (min(first, second) + .05)


def qualifies(ratio, kind):
    if kind not in THRESHOLDS or not math.isfinite(ratio) or not 1 <= ratio <= 21.00000000001:
        raise ValueError('Unknown criterion or invalid contrast ratio')
    return ratio >= THRESHOLDS[kind]  # compare unrounded; formatting is presentation only


def assess(foreground, background, kind='normal', alpha=1):
    ratio = contrast(foreground, background, alpha)
    return {'foreground': foreground, 'background': background, 'alpha': alpha,
            'ratio': ratio, 'display_ratio': f'{ratio:.2f}:1', 'criterion': kind,
            'threshold': THRESHOLDS[kind], 'numeric_target_met': qualifies(ratio, kind),
            'scope': 'Known solid sRGB foreground over one opaque background. Not full WCAG compliance; focus area/visibility, font qualification, gradients, blend/filter effects and actual surface composition require separate review.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('foreground'); parser.add_argument('background')
    parser.add_argument('--kind', choices=THRESHOLDS, default='normal')
    parser.add_argument('--alpha', type=float, default=1)
    args = parser.parse_args()
    try:
        result = assess(args.foreground, args.background, args.kind, args.alpha)
        print(json.dumps(result, indent=2))
        return 0 if result['numeric_target_met'] else 1
    except ValueError as error:
        parser.exit(2, str(error)+'\n')


if __name__ == '__main__':
    sys.exit(main())
