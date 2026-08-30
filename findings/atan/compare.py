#!/usr/bin/env python3
"""Grade the Codex arc tangent against zig's, from two files of BIT PATTERNS.

    ./compare.py zig.txt bare.txt

Both files carry one line per input:

    atan  <t bits> <answer bits>
    atan2 <y bits> <x bits> <answer bits>

as decimal i64. Bits, not rendered decimals, because a rendering is a second
implementation: two correct float printers can disagree, and then the report is
grading the printers.

REFUSES if the two files do not name the same inputs in the same order. That is
the failure this file exists to catch -- a comparison whose two sides drifted
apart still prints a table of perfect agreement, because every row it compares
is a row it built by pairing position with position.
"""
import struct, sys, pathlib

def bits_to_f64(b): return struct.unpack('<d', struct.pack('<q', int(b)))[0]
def f64_to_bits(v): return struct.unpack('<q', struct.pack('<d', v))[0]

def ulps(a, b):
    """Distance in representable doubles. Monotone ordering across the sign."""
    ia, ib = f64_to_bits(a), f64_to_bits(b)
    if ia < 0: ia = -0x8000000000000000 - ia
    if ib < 0: ib = -0x8000000000000000 - ib
    return abs(ia - ib)

def load(path):
    rows = []
    for line in pathlib.Path(path).read_text().splitlines():
        f = line.split()
        if not f or f[0] not in ('atan', 'atan2'):
            continue
        rows.append((f[0], tuple(f[1:-1]), f[-1]))
    return rows

def main():
    ref, sub = load(sys.argv[1]), load(sys.argv[2])
    if len(ref) != len(sub):
        print(f'REFUSED: {len(ref)} reference rows, {len(sub)} subject rows'); return 1
    for i, (r, s) in enumerate(zip(ref, sub)):
        if r[0] != s[0] or r[1] != s[1]:
            print(f'REFUSED at row {i}: reference {r[0]}{r[1]}, subject {s[0]}{s[1]}')
            print('  the two arms are not measuring the same inputs'); return 1

    worst_abs = worst_ulp = 0.0
    worst_abs_row = worst_ulp_row = None
    print(f'{"":5} {"input":>26} {"zig":>22} {"codex":>22} {"abs err":>11} {"ulp":>8}')
    for (kind, args, want), (_, _, got) in zip(ref, sub):
        w, g = bits_to_f64(want), bits_to_f64(got)
        ae = abs(w - g)
        u = ulps(w, g)
        shown = ', '.join(f'{bits_to_f64(a):.10g}' for a in args)
        print(f'{kind:5} {shown:>26} {w:>22.15g} {g:>22.15g} {ae:>11.3e} {u:>8}')
        if ae > worst_abs: worst_abs, worst_abs_row = ae, (kind, shown)
        if u > worst_ulp: worst_ulp, worst_ulp_row = u, (kind, shown)

    n = len(ref)
    within = lambda tol: sum(
        1 for (k, a, w), (_, _, g) in zip(ref, sub)
        if abs(bits_to_f64(w) - bits_to_f64(g)) <= tol)
    print()
    print(f'{n} values: {len([r for r in ref if r[0] == "atan"])} atan, '
          f'{len([r for r in ref if r[0] == "atan2"])} atan2')
    print(f'  worst absolute error {worst_abs:.4e}   at {worst_abs_row[0]} {worst_abs_row[1]}')
    print(f'  worst ULP distance   {int(worst_ulp)}   at {worst_ulp_row[0]} {worst_ulp_row[1]}')
    for tol in (1e-15, 1e-12, 1e-11, 1e-10, 1e-9, 1e-8):
        print(f'  within {tol:.0e}: {within(tol)} of {n}')
    return 0

sys.exit(main())
