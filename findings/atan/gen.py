#!/usr/bin/env python3
"""Generate the zig reference and the Codex subject from values.py, then say so.

    ./gen.py            writes atan_ref.zig and AtanProbe.codex beside this file

Both print ONE line per input: the input's f64 bit pattern and the answer's, as
decimal i64. Bits rather than a rendered decimal because a rendering is a second
implementation -- two float printers can disagree about a value they both hold
correctly, and then the report is measuring the printers.
"""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from values import ATAN_INPUTS, ATAN2_INPUTS

# std.debug.print, hence stderr: zig 0.16 retired std.io.getStdOut, and the
# port's own probes already write this way.
zig = ['const std = @import("std");', '',
       'pub fn main() void {']
for v in ATAN_INPUTS:
    zig.append(f'    emit1({v});')
zig.append('')
for y, x in ATAN2_INPUTS:
    zig.append(f'    emit2({y}, {x});')
zig += ['}', '',
        'fn emit1(t: f64) void {',
        '    std.debug.print("atan {d} {d}\\n", .{ @as(i64, @bitCast(t)), @as(i64, @bitCast(std.math.atan(t))) });',
        '}', '',
        'fn emit2(y: f64, x: f64) void {',
        '    std.debug.print("atan2 {d} {d} {d}\\n", .{ @as(i64, @bitCast(y)), @as(i64, @bitCast(x)), @as(i64, @bitCast(std.math.atan2(y, x))) });',
        '}', '']
(HERE / 'atan_ref.zig').write_text('\n'.join(zig))

# The Codex subject carries the implementation inline rather than citing
# DeviceMath, so this measures the code as WRITTEN before it is anywhere near
# the depot. The depot version is the same body under the chapter's names.
cx = ['Chapter: AtanProbe',
      '  cites Gpu chapter DeviceMath',
      '',
      ' The arc tangent offered to the foreword, measured against zig here before',
      ' it goes into DeviceMath. Argument halving, then a six-term series: the',
      ' series alone converges hopelessly near |t| = 1, which is where the callers',
      ' sample it.',
      '',
      ' We say:',
      '',
      'Section: Arc Tangent',
      '',
      '  dm-atan-half-step : Real -> Real',
      '  dm-atan-half-step (t) = t / (1.0 + real-sqrt (1.0 + t * t))',
      '',
      '  dm-atan-halve : Real, Integer -> Real',
      '  dm-atan-halve (t) (n) =',
      '    if n <= 0 then t',
      '    else dm-atan-halve (dm-atan-half-step t) (n - 1)',
      '',
      '  dm-atan-series : Real -> Real',
      '  dm-atan-series (u) =',
      '    let u2 = u * u',
      '    in let u3 = u2 * u',
      '    in let u5 = u3 * u2',
      '    in let u7 = u5 * u2',
      '    in let u9 = u7 * u2',
      '    in let u11 = u9 * u2',
      '    in u - u3 / 3.0 + u5 / 5.0 - u7 / 7.0 + u9 / 9.0 - u11 / 11.0',
      '',
      '  dm-atan-core : Real -> Real',
      '  dm-atan-core (t) = 16.0 * dm-atan-series (dm-atan-halve t 4)',
      '',
      '  real-atan : Real -> Real',
      '  real-atan (t) =',
      '    if t > 1.0 then dm-half-pi - dm-atan-core (1.0 / t)',
      '    else if t < 0.0 - 1.0 then (0.0 - dm-half-pi) - dm-atan-core (1.0 / t)',
      '    else dm-atan-core t',
      '',
      '  real-atan2 : Real, Real -> Real',
      '  real-atan2 (y) (x) =',
      '    if x > 0.0 then real-atan (y / x)',
      '    else if x < 0.0 then (if y >= 0.0 then real-atan (y / x) + dm-pi else real-atan (y / x) - dm-pi)',
      '    else if y > 0.0 then dm-half-pi',
      '    else if y < 0.0 then 0.0 - dm-half-pi',
      '    else 0.0',
      '',
      'Section: Report',
      '',
      '  a1 : Real -> Text',
      '  a1 (t) = "atan " & show (real-to-bits t) & " " & show (real-to-bits (real-atan t))',
      '',
      '  a2 : Real, Real -> Text',
      '  a2 (y) (x) = "atan2 " & show (real-to-bits y) & " " & show (real-to-bits x) & " " & show (real-to-bits (real-atan2 y x))',
      '',
      '  opening : [Console] Nothing = act']
for v in ATAN_INPUTS:
    cx.append(f'    print-line-uni (a1 {v})' if not v.startswith('-')
              else f'    print-line-uni (a1 ({v}))')
for y, x in ATAN2_INPUTS:
    ys = y if not y.startswith('-') else f'({y})'
    xs = x if not x.startswith('-') else f'({x})'
    cx.append(f'    print-line-uni (a2 {ys} {xs})')
cx += ['  end', '']
(HERE / 'AtanProbe.codex').write_text('\n'.join(cx))

print(f'wrote atan_ref.zig and AtanProbe.codex: '
      f'{len(ATAN_INPUTS)} atan, {len(ATAN2_INPUTS)} atan2, '
      f'{len(ATAN_INPUTS) + len(ATAN2_INPUTS)} lines each')
