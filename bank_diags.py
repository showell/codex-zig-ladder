#!/usr/bin/env python3
"""Bank the diagnostics population as a diffable set, the way truths are banked.

The census answers "did the pinned NOTE class move". It cannot answer "what
changed", because `check_diags.py --census` prints only codes whose POLICY
verdict is not OK -- and on Update 52 that hid 3,013 of 3,110 diagnostics.
Every optimiser-class count from every earlier Update was absorbed and thrown
away: when this file was written NOTHING in the tree, the bank, or git history
recorded a single OK-class count, so the first Update that wanted a comparison
had nothing to compare against.

What is banked is COUNTS PER UNIT PER CODE, never the diagnostic text. A
diagnostic carries `line:col`, and a depot line number is a per-Update fact --
the POLICY table already learned that the hard way, re-pinning CDX6020's cited
lines twice because the sites moved under it. Counts move when the compiler's
behaviour moves, which is the question.

ABSENCE IS RECORDED, not inferred. A clean compile writes no .diags at all,
which is legitimate, so "file missing" and "file empty" are the same thing to
a reader who only sees totals -- and that hid something real: every one of the
twelve `<unit>.ir.diags` is absent on every sweep, because the IR arm runs
`passes=text-plug` and emits no diagnostics, while `allcycles.sh` has always
said its counts were "taken over BOTH halves of every unit". Half of that
population has never existed. The `absent` block says so on every bank.

Usage:
    python3 bank_diags.py <ast-dir> [--slug uNN] [--out diags/]
    python3 bank_diags.py --diff diags/u51.txt diags/u52.txt
"""

import argparse
import collections
import pathlib
import re
import sys

CODE = re.compile(r'CDX\d{4}')

# The census population, and the reason it is spelled out here rather than
# globbed: a bare *.diags sweeps in whatever arith/irmem/guardprobe/codexir/
# ringplug last left behind, so the counts would move with which TOOLS had run
# lately rather than with the source. allcycles.sh carries the same list for
# the same reason; both read LADDER_UNITS from oracle_lib.sh.
def ladder_units(ladder):
    text = (ladder / 'ast' / 'oracle_lib.sh').read_text()
    m = re.search(r'^LADDER_UNITS="([^"]+)"', text, re.M)
    if not m:
        raise SystemExit('bank_diags: no LADDER_UNITS in ast/oracle_lib.sh')
    return m.group(1).split()


def tally(ast_dir, units):
    counts = collections.defaultdict(collections.Counter)
    absent, empty = [], []
    for unit in units:
        for name in (f'{unit}-subject.cdx.diags', f'{unit}.ir.diags'):
            p = ast_dir / name
            if not p.is_file():
                absent.append(name)
                continue
            lines = [l for l in p.read_text(errors='replace').splitlines() if l.strip()]
            if not lines:
                empty.append(name)
                continue
            for line in lines:
                m = CODE.search(line)
                counts[unit][m.group(0) if m else 'uncoded'] += 1
    return counts, absent, empty


def render(counts, absent, empty, slug, seed):
    out = [f'# diags bank {slug}',
           f'# seed {seed}',
           '#',
           '# counts per unit per code. Diagnostic TEXT is deliberately not banked:',
           '# a depot line:col is a per-Update fact and would move every row.']
    totals = collections.Counter()
    for unit in sorted(counts):
        for code, n in sorted(counts[unit].items()):
            totals[code] += n
    out.append('#')
    for unit in sorted(counts):
        for code, n in sorted(counts[unit].items()):
            out.append(f'{unit:<26} {code:<9} {n}')
    out.append('#')
    out.append('# totals')
    for code, n in sorted(totals.items()):
        out.append(f'{"*":<26} {code:<9} {n}')
    out.append('#')
    out.append(f'# total diagnostics {sum(totals.values())}')
    if empty:
        out.append(f'# empty (present, no diagnostics): {len(empty)}')
        for n in empty:
            out.append(f'#   {n}')
    if absent:
        out.append(f'# absent (no file written): {len(absent)}')
        for n in absent:
            out.append(f'#   {n}')
    return '\n'.join(out) + '\n'


def do_diff(a, b):
    def load(p):
        d = {}
        for line in pathlib.Path(p).read_text().splitlines():
            if line.startswith('#') or not line.strip():
                continue
            unit, code, n = line.split()
            d[(unit, code)] = int(n)
        return d
    da, db = load(a), load(b)
    moved = 0
    for key in sorted(set(da) | set(db)):
        x, y = da.get(key, 0), db.get(key, 0)
        if x != y:
            moved += 1
            unit, code = key
            print(f'  {unit:<26} {code:<9} {x:>6} -> {y:<6} ({y - x:+d})')
    print(f'--- {moved} row(s) moved' if moved else '--- identical: no row moved')
    return 1 if moved else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ast_dir', nargs='?', help='the sweep ast/ directory holding .diags')
    ap.add_argument('--slug', help='bank name (default: derived from the seed)')
    ap.add_argument('--out', default='diags', help='directory to write into')
    ap.add_argument('--diff', nargs=2, metavar=('OLD', 'NEW'))
    args = ap.parse_args()

    if args.diff:
        return do_diff(*args.diff)
    if not args.ast_dir:
        ap.error('an ast/ directory is required unless --diff is given')

    ast_dir = pathlib.Path(args.ast_dir).resolve()
    ladder = pathlib.Path(__file__).resolve().parent
    import seed_identity
    stamp = seed_identity.stamp()
    slug = args.slug or stamp['slug']

    counts, absent, empty = tally(ast_dir, ladder_units(ladder))
    if not counts:
        raise SystemExit(f'bank_diags: no .diags found under {ast_dir}')
    text = render(counts, absent, empty, slug, stamp['sha256'])
    out = ladder / args.out
    out.mkdir(exist_ok=True)
    dest = out / f'{slug}.txt'
    dest.write_text(text)
    print(text)
    print(f'banked {dest}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
