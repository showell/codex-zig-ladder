#!/usr/bin/env python3
"""Emit the depot's foreword test, with zig's answers embedded as the truth column.

The .expected is NOT written here -- it is settled by running this on bare metal.
Predicting it from zig and then confirming it on the seed is the cross-check; a
generator that writes both the test and its own expected output is a rig grading
itself.
"""
import struct, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
def b2f(b): return struct.unpack('<d', struct.pack('<q', int(b)))[0]

truth = {}
for line in (HERE / 'zig.txt').read_text().splitlines():
    f = line.split()
    if not f: continue
    if f[0] == 'atan':  truth[('atan', b2f(f[1]))] = b2f(f[2])
    if f[0] == 'atan2': truth[('atan2', b2f(f[1]), b2f(f[2]))] = b2f(f[3])

def nano(v):                       # round-half-away-from-zero, as the test does
    s = v * 1e9
    return int(s + (0.5 if s >= 0 else -0.5))

ATAN  = ["0.0","0.0001","0.1","0.25","0.5","0.7071067811865476","0.9","0.99",
         "1.0","1.0000001","1.1","1.5","2.0","3.0","10.0","1000000.0",
         "-0.5","-1.0","-1.5","-3.0"]
ATAN2 = [("1.0","1.0"),("1.0","-1.0"),("-1.0","1.0"),("-1.0","-1.0"),
         ("2.0","0.5"),("2.0","-0.5"),("-2.0","0.5"),("-2.0","-0.5"),
         ("1.0","0.0"),("-1.0","0.0"),("0.0","-1.0"),("0.0","0.0"),
         ("3.0","4.0"),("-4.0","3.0")]

def lit(s): return s if not s.startswith('-') else f'({s})'

L = [
'Chapter: FwdDeviceMathAtanTest',
'  cites Foreword chapter Console',
'  cites Gpu chapter DeviceMath',
'',
' Grades real-atan and real-atan2 against zig 0.16.0 std.math.atan and',
' std.math.atan2. The truth column is that library\'s answer, not this',
' implementation\'s remembered behaviour, so the test can fail on its first day',
' rather than only on a change.',
'',
' ANGLES ARE PRINTED IN NANO-RADIANS AND ROUNDED, NOT TRUNCATED, and the',
' rounding is load-bearing. Truncating puts atan of a billionth exactly on a',
' boundary -- the printed integer would then turn on the last bit of the answer,',
' and the test would be grading the rounding mode. Rounded, the closest any value',
' in this table comes to a boundary is 0.0088 of a unit against a measured error',
' of 0.00000067 of a unit: a margin of thirteen thousand.',
'',
' THE LAST LINE DOES NOT CONSULT ZIG AT ALL. Feeding each angle back through this',
' chapter\'s own real-sin and real-cos must return the argument, which grades the',
' arc tangent against a sine written by someone else for another purpose. A',
' reference table can be transcribed wrongly; that identity cannot.',
'',
' IT IS COUNTED AGAINST A TOLERANCE RATHER THAN RECORDED EXACTLY, deliberately.',
' The round trip measures real-sin\'s accuracy as much as real-atan\'s -- the',
' errors are 9 nano-radians and below, and they belong to the sine -- so pinning',
' them exactly would redden this test on any improvement to real-sin, which is',
' not a thing an arc tangent should be able to do. Fifty is loose enough to leave',
' the sine alone and five orders tighter than any real defect here.',
'',
'Section: Scaling',
'',
'  nano : Real -> Integer',
'  nano (v) = real-to-int (v * 1000000000.0 + (if v < 0.0 then 0.0 - 0.5 else 0.5))',
'',
'  agree : Integer, Integer -> Text',
'  agree (got) (want) = if got == want then "ok" else "MISMATCH want " & show want',
'',
'Section: Report',
'',
'  a : Text, Real, Integer -> Text',
'  a (name) (t) (want) =',
'    let got = nano (real-atan t)',
'    in "atan " & name & " = " & show got & "  " & agree got want',
'',
'  a2 : Text, Real, Real, Integer -> Text',
'  a2 (name) (y) (x) (want) =',
'    let got = nano (real-atan2 y x)',
'    in "atan2 " & name & " = " & show got & "  " & agree got want',
'',
' The round trip: tan of the angle is sine over cosine, and must give back t.',
'',
'  rt-abs : Integer -> Integer',
'  rt-abs (e) = if e < 0 then 0 - e else e',
'',
'  rt-ok : Real -> Integer',
'  rt-ok (t) =',
'    let ang = real-atan t',
'    in let back = real-sin ang / real-cos ang',
'    in if rt-abs (nano (back - t)) <= 50 then 1 else 0',
'',
'  rt-report : Text',
'  rt-report =',
'    let n = rt-ok 0.1 + rt-ok 0.25 + rt-ok 0.5 + rt-ok 1.0 + rt-ok 1.5 + rt-ok 3.0 + rt-ok (0.0 - 0.5) + rt-ok (0.0 - 1.5)',
'    in "round trip through real-sin and real-cos, within 50 nano: " & show n & " of 8"',
'',
'  opening : [Console] Nothing = act',
]
for v in ATAN:
    L.append(f'    print-line-uni (a "{v}" {lit(v)} {truth[("atan", float(v))] and nano(truth[("atan", float(v))])})'
             if truth[("atan", float(v))] != 0.0 else
             f'    print-line-uni (a "{v}" {lit(v)} 0)')
for y, x in ATAN2:
    t = truth[('atan2', float(y), float(x))]
    L.append(f'    print-line-uni (a2 "{y}, {x}" {lit(y)} {lit(x)} {nano(t)})')
RT = ["0.1", "0.25", "0.5", "1.0", "1.5", "3.0", "-0.5", "-1.5"]
L.append('    print-line-uni rt-report')
L += ['  end', '']
(HERE / 'gpu-devicemath-atan.codex').write_text('\n'.join(L))
print(f'wrote gpu-devicemath-atan.codex: {len(ATAN)} atan, {len(ATAN2)} atan2, 4 round-trips')
