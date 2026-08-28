#!/usr/bin/env python3
"""Every tier, both arms, one verdict line each -- the unit tests as a set.

    ./tiers_run.py                 all tiers and the listed probes
    ./tiers_run.py --bare          bare-metal columns only (bank them; seconds
                                   each under QEMU, run right after a re-pin)
    ./tiers_run.py --zig           after a natives rebuild: the zig columns
                                   are re-run and every bare column MUST come
                                   from gold. It refuses up front if any is
                                   missing or stale rather than paying QEMU
                                   for it, which is the only thing separating
                                   it from a bare run of this script.
    ./tiers_run.py prim-text       one or more stems

Each tier is one tier_run.py invocation; this adds only the set, the
summary and the exit code. The verdict per tier:

    green    byte-identical
    noted    differs only on rows findings/gold/EXPECTED.txt names
    RED      an unexpected disagreement
    STALE    a ledger row whose arms now agree (act on it: close the
             finding or delete the row)
    GAP      the zig arm could not build it (emitter refusal)

A set is green only if every tier is green or noted. The probes that kill
an arm on purpose are excluded by name below, with the reason -- except
the ZIG_REFUSALS class, where the kill is the property under test and the
probe runs zig-only with the expected panic marker as its green. The
zig column records which native build answered so a branch regression is
attributable without re-running by hand.
"""
import argparse
import compute_lock
import hashlib
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import LADDER

HERE = LADDER
FINDINGS = HERE / 'findings'

# Probes that are part of the set. The rest are single-question probes that
# either trap an arm on purpose or need a by-hand reading; they keep their
# own tier_run invocations and are not a regression set.
PROBES = [
    'probe-memory-model',   # the quadratic detector; predates the tiers
    'probe-fresh-span',
    'probe-peek-qword',
    'probe-record-layout',
    'probe-char-ops',
    'probe-char-literal',
    'probe-approx-eq',
    'probe-recursive-eq',   # finding 66; the path Update 52 opened
    'probe-shake',          # the tree-shaking closure, target-agnostic
    'probe-scancost',       # what a 96-name root scan costs, on this venue
    'probe-prelude-collide',# finding 67: a top-level named cx-print
    'probe-cxlist',         # finding 67, the CamelCase half
]
# Zig-only refusal probes: the property IS a plug-arm refusal, and bare
# metal has no oracle for it -- upstream corrupts silently in the same
# shape, which is why the guard exists. The arm runs alone and green means
# it DIED with the named marker before reaching its REFUSAL MISSED line;
# a run that prints that line survived past the guard and is a regression.
ZIG_REFUSALS = {
    'probe-deck-overrun': 'the two cursors met',
}
EXCLUDED = {
    'probe-shift-count':    'kills the bare-metal arm on purpose (finding 30)',
    'probe-substring-trap': 'kills the zig arm on purpose (finding 28)',
    'probe-deck-substring': 'needs a rewind and a clobber read by hand (finding 29)',
    'probe-arith-edges':    'abs minInt kills the zig arm on purpose, at compile time now (its own prose, finding 18 family)',
    'probe-deck-init':      'declares its own deck-record; the zig arm brackets it by name and faults (finding 25) -- re-include when the gate is ported',
}


def run_refusal(stem):
    """One zig-only refusal probe: the arm must die with the named marker.
    There is no bare column to bank and no gold; the marker and the absent
    REFUSAL MISSED line are the whole verdict."""
    src = FINDINGS / f'{stem}.codex'
    if not src.is_file():
        return 'MISSING', f'{src} does not exist'
    marker = ZIG_REFUSALS[stem]
    r = subprocess.run([sys.executable, str(HERE / 'tier_run.py'), str(src), '--zig'],
                       capture_output=True, text=True, timeout=1800)
    lines = r.stdout.splitlines()
    missed = [l for l in lines if 'REFUSAL MISSED' in l]
    if missed:
        return 'RED', missed[0].strip()[:160]
    hits = [l for l in lines if marker in l]
    if hits:
        return 'green', hits[0].strip()[:160]
    tail = (r.stdout.strip().splitlines() or ['?'])[-1]
    return 'RED', f'no refusal and no survivor line: {tail}'[:160]


def natives_stamp():
    """Which build answered the zig column: sha of the two native binaries.
    The emitter sha would name the SOURCE; the binaries name what ran."""
    h = hashlib.sha256()
    for name in ('codexir', 'zigemit'):
        p = HERE / 'native' / name
        if not p.is_file():
            return 'no-natives'
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


def gold_gaps(stems):
    """Which tiers have no usable banked bare column, and why.

    The key is the program's bytes plus the seed, so a stale column is a tier
    whose source was edited or a seed that was re-pinned; both mean the bank
    owes a `--bare` run before a zig-only pass can mean anything."""
    import tier_run
    gaps = []
    for stem in stems:
        src = FINDINGS / f'{stem}.codex'
        if not src.is_file():
            gaps.append((stem, f'{src} does not exist'))
            continue
        gold = tier_run.gold_path(src)
        if not gold.is_file():
            gaps.append((stem, f'no {gold}'))
            continue
        head = gold.read_text().partition('\n')[0]
        if head != f'# key {tier_run.gold_key(src)}':
            gaps.append((stem, f'stale key in {gold}'))
    return gaps


def run_one(stem, mode):
    src = FINDINGS / f'{stem}.codex'
    if not src.is_file():
        return 'MISSING', f'{src} does not exist'
    cmd = [sys.executable, str(HERE / 'tier_run.py'), str(src)]
    if mode:
        cmd.append(mode)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    out, err = r.stdout, r.stderr
    if mode == '--bare':
        return ('banked' if r.returncode == 0 else 'RED'), err.strip().splitlines()[-1:] and err.strip().splitlines()[-1]
    if 'gap:' in err:
        gaps = [l.strip() for l in err.splitlines() if l.strip().startswith('gap:')]
        return 'GAP', '; '.join(gaps)[:160]
    if r.returncode != 0 and 'lines,' not in out:
        tail = (err.strip().splitlines() or ['?'])[-1]
        return 'RED', tail[:160]
    summary = [l for l in out.splitlines() if 'lines,' in l]
    summary = summary[-1] if summary else out.strip().splitlines()[-1:] and out.strip().splitlines()[-1]
    if 'byte-identical' in summary:
        return 'green', summary
    if 'expected-but-agreeing' in summary and not summary.startswith('0'):
        # "N lines, R unexpected, E expected, S expected-but-agreeing"
        parts = summary.split(', ')
        reds = int(parts[1].split()[0]); stale = int(parts[3].split()[0])
        if reds:
            return 'RED', summary
        if stale:
            return 'STALE', summary
        return 'noted', summary
    return 'RED', summary


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('stems', nargs='*')
    ap.add_argument('--bare', action='store_true')
    ap.add_argument('--zig', action='store_true')
    a = ap.parse_args()
    compute_lock.require_venue()
    # NOT '--zig': that flag means "the zig arm ALONE" to tier_run.py, which
    # prints a column and never compares it to anything. Passed down, every
    # tier came back with no summary line to parse and run_one's last branch
    # called all 21 of them RED -- a set runner that cannot report anything
    # but failure, from the commit that introduced it (6fc3841) until
    # 2026-08-25, because nothing had run it. What --zig means HERE is a
    # normal two-column run with the bare column pinned to gold, and that is
    # enforced before any tier runs rather than requested by a flag.
    mode = '--bare' if a.bare else None

    stems = a.stems or (sorted(p.stem for p in FINDINGS.glob('prim-*.codex'))
                        + PROBES + sorted(ZIG_REFUSALS))
    shown = '--bare' if mode == '--bare' else (
        'zig re-measured, bare from gold' if a.zig else 'both arms')
    print(f'### tiers_run: {len(stems)} tiers, mode {shown}, natives {natives_stamp()}')
    for stem, why in EXCLUDED.items():
        if stem in stems:
            print(f'  excluded {stem}: {why}')
            stems.remove(stem)
    if mode == '--bare':
        for stem in [s for s in stems if s in ZIG_REFUSALS]:
            print(f'  skipped {stem}: zig-only refusal probe, no bare column')
            stems.remove(stem)
    if a.zig:
        missing = gold_gaps([s for s in stems if s not in ZIG_REFUSALS])
        if missing:
            for stem, why in missing:
                print(f'  no gold  {stem:<24} {why}')
            print(f'### {len(missing)} bare columns are not banked -- '
                  '`./tiers_run.py --bare` first, or drop --zig to pay QEMU for them')
            sys.exit(1)
    counts = {}
    bad = 0
    for stem in stems:
        verdict, detail = run_refusal(stem) if stem in ZIG_REFUSALS else run_one(stem, mode)
        counts[verdict] = counts.get(verdict, 0) + 1
        if verdict in ('RED', 'STALE', 'GAP', 'MISSING'):
            bad += 1
        print(f'{verdict:<7} {stem:<24} {detail}')
        sys.stdout.flush()
    print('###', ', '.join(f'{k} {v}' for k, v in sorted(counts.items())),
          '-- SET GREEN' if not bad else '-- SET RED')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
