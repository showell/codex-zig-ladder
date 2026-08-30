#!/usr/bin/env python3
"""Emit codex/test/forewords/math-cordic-accuracy, with the true column computed.

The .expected is NOT written here -- bare metal settles it. Predicting the
output from the model and confirming it on the seed is the cross-check; a
generator that writes both a test and its own expected output grades itself.
"""
import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from model import sincos, SCALE

# Spread over the turn, plus the two worst points the sweep found. Every
# quadrant, both signs, and the axes where a fold could hide a sign error.
ANGLES = [0, 300, 500, 785, 1000, 1571, 1800, 2000, 2500, 3000,
          3141, 3163, 3255, 3500, 4000, 4712, 5000, 5500, 6000, 6283]

def rnd(v):                       # nearest, ties away from zero
    return int(math.floor(v + 0.5)) if v >= 0 else -int(math.floor(-v + 0.5))

rows = []
for a in ANGLES:
    c, s = sincos(a)
    ts, tc = rnd(math.sin(a/SCALE)*SCALE), rnd(math.cos(a/SCALE)*SCALE)
    rows.append((a, s, ts, c, tc))

worst = max(max(abs(s-ts), abs(c-tc)) for _, s, ts, c, tc in rows)
BOUND = 6                          # the docstring figure this test pins

L = [
'Chapter: FwdCordicAccuracyTest',
'  cites Foreword chapter Console',
'  cites Math chapter Cordic',
'',
' Pins the accuracy this chapter CLAIMS, which nothing did before. math-cordic',
' is a one-line smoke and math-cordic-quadrants checks values against a true',
' column with a 1.5 per cent invariant -- three times the worst error, so a',
' docstring figure could drift a long way without either of them noticing.',
'',
' THE TRUE COLUMN IS THE REAL SINE AND COSINE, rounded to nearest at scale 1000,',
' not this implementation remembered. So the test can fail on its first day.',
'',
' The bound is stated as an ABSOLUTE error at full scale because that is the',
' only reading under which a single number is meaningful here: near a zero',
' crossing the relative error reaches several per cent while the absolute error',
' stays small, and near a peak the reverse. A chapter that claims one figure',
' without saying which is claiming something unfalsifiable.',
'',
'Section: Sample',
'',
'  acc-angles : List Integer',
'  acc-angles = [' + ', '.join(str(a) for a, *_ in rows) + ']',
'',
'  acc-true-sin : List Integer',
'  acc-true-sin = [' + ', '.join(str(ts) for _, _, ts, _, _ in rows) + ']',
'',
'  acc-true-cos : List Integer',
'  acc-true-cos = [' + ', '.join(str(tc) for *_, tc in rows) + ']',
'',
'Section: Report',
'',
'  acc-abs : Integer -> Integer',
'  acc-abs (x) = if x < 0 then 0 - x else x',
'',
'  acc-err-at : Integer -> Integer',
'  acc-err-at (i) =',
'    let a = list-at acc-angles i',
'    in let es = acc-abs (cordic-sin a - list-at acc-true-sin i)',
'    in let ec = acc-abs (cordic-cos a - list-at acc-true-cos i)',
'    in if es > ec then es else ec',
'',
'  acc-worst : Integer, Integer -> Integer',
'  acc-worst (i) (so-far) =',
'    if i >= list-length acc-angles then so-far',
'    else let e = acc-err-at i',
'    in acc-worst (i + 1) (if e > so-far then e else so-far)',
'',
'  acc-within : Integer, Integer -> Integer',
'  acc-within (i) (n) =',
'    if i >= list-length acc-angles then n',
'    else acc-within (i + 1) (if acc-err-at i <= ' + str(BOUND) + ' then n + 1 else n)',
'',
'  acc-line : Integer -> Text',
'  acc-line (i) =',
'    let a = list-at acc-angles i',
'    in "  " & show a & " sin " & show (cordic-sin a) & " true " & show (list-at acc-true-sin i)'
'  & "   cos " & show (cordic-cos a) & " true " & show (list-at acc-true-cos i)'
'  & "   err " & show (acc-err-at i)',
'',
'  acc-report : Text',
'  acc-report =',
'    let w = acc-worst 0 0',
'    in "worst absolute error over the sample: " & show w & " of 1000 full scale"',
'',
'  acc-count : Text',
'  acc-count =',
'    let n = acc-within 0 0',
'    in "within ' + str(BOUND) + ' of 1000: " & show n & " of " & show (list-length acc-angles)',
'',
'  opening : [Console] Nothing = act',
]
for i in range(len(rows)):
    L.append(f'    print-line-uni (acc-line {i})')
L += ['    print-line-uni acc-report',
      '    print-line-uni acc-count',
      '  end', '']
out = pathlib.Path(__file__).resolve().parent / 'math-cordic-accuracy.codex'
out.write_text('\n'.join(L))
print(f'wrote {out.name}: {len(rows)} angles, model worst error {worst} of 1000, bound {BOUND}')
