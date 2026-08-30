#!/usr/bin/env python3
"""Compare two corpus sweeps whose ONLY difference is the plug.

    ./two_arm_diff.py <baseline-sandbox> <fixed-sandbox>

A verdict diff against the BANK measures our change and every base change
since the bank together, and no reading of the rows can separate them --
`dup_baseline.sh` says so at length and it is the reason that run exists. The
answer is a second sweep over the same programs with the plug reverted, and
then this: a direct comparison of the two, where the emitter is the only
thing that moved.

TWO QUESTIONS, AND THE SECOND IS THE SHARPER ONE.

  VERDICTS -- did any program's answer change (match/differ/refused/...).
  This is what a reader wants, and it is COARSE: a program can emit
  different zig and still land on the same verdict, which is how the
  dup-arms run nearly filed a real change as inert.

  EMITTED TEXT -- is each program's `.zig` byte-identical across the arms.
  This sees a change the verdict cannot, and for a prelude edit it is the
  question that matters: a part added to `zig-prelude-parts` reaches every
  emitted file if the shaker is not doing its job, and reaches none if it
  is. Verdicts would say 'inert' either way.

Both are read from what `corpus_run.py --run` leaves in each sandbox's
`corpus/`: `transpile.json` (stage and zig_sha per program), `run.jsonl`
(one verdict per line), and the emitted `.zig` files themselves. The shas
are compared, and any pair that disagrees is diffed on disk so the report
says WHAT moved and not merely that something did.
"""
import json, pathlib, sys, difflib

def load(sandbox):
    work = pathlib.Path(sandbox) / 'ladder' / 'corpus'
    if not work.is_dir():
        raise SystemExit(f'no corpus/ under {sandbox} -- did the sweep run?')
    tr = {r['name']: r for r in json.loads((work / 'transpile.json').read_text())}
    vd = {}
    jl = work / 'run.jsonl'
    if jl.is_file():
        for line in jl.read_text().splitlines():
            if line.strip():
                e = json.loads(line)
                vd[e['name']] = e.get('verdict', '?')
    return work, tr, vd

def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__.strip().splitlines()[2].strip())
    base_dir, fixed_dir = sys.argv[1], sys.argv[2]
    bw, btr, bvd = load(base_dir)
    fw, ftr, fvd = load(fixed_dir)

    print(f'baseline {base_dir}\n   fixed {fixed_dir}\n')
    names = sorted(set(btr) | set(ftr))
    print(f'{len(names)} programs in the union '
          f'(baseline {len(btr)}, fixed {len(ftr)})')
    only_b = sorted(set(btr) - set(ftr))
    only_f = sorted(set(ftr) - set(btr))
    for tag, lst in (('baseline only', only_b), ('fixed only', only_f)):
        if lst:
            print(f'  *** {tag}: {len(lst)} -- {", ".join(lst[:8])}')
    if not only_b and not only_f:
        print('  same population on both arms')

    # STAGE: how far each program got. A stage move is a coverage change.
    print('\n--- stage')
    stage_moves = [(n, btr[n].get('stage'), ftr[n].get('stage'))
                   for n in names if n in btr and n in ftr
                   and btr[n].get('stage') != ftr[n].get('stage')]
    print(f'{len(stage_moves)} stage moves')
    for n, o, e in stage_moves:
        print(f'  {n:34s} {o} -> {e}')

    # VERDICTS: the coarse answer, and the one a PR table quotes.
    print('\n--- verdicts')
    vnames = sorted(set(bvd) | set(fvd))
    moves = [(n, bvd.get(n, '(not run)'), fvd.get(n, '(not run)'))
             for n in vnames if bvd.get(n) != fvd.get(n)]
    print(f'{len(bvd)} baseline verdicts, {len(fvd)} fixed; {len(moves)} moved')
    for n, o, e in moves:
        print(f'  {n:34s} {o} -> {e}')

    # EMITTED TEXT: the sharp answer. Compare the shas, then diff the files
    # that disagree -- 'something changed' is not a finding until it is read.
    print('\n--- emitted zig')
    both = [n for n in names if n in btr and n in ftr]
    have = [n for n in both if btr[n].get('zig_sha') and ftr[n].get('zig_sha')]
    same = [n for n in have if btr[n]['zig_sha'] == ftr[n]['zig_sha']]
    diff = [n for n in have if btr[n]['zig_sha'] != ftr[n]['zig_sha']]
    print(f'{len(same)} of {len(have)} byte-identical; {len(diff)} differ')
    for n in diff:
        bf, ff = bw / f'{n}.zig', fw / f'{n}.zig'
        print(f'\n  === {n}')
        if not (bf.is_file() and ff.is_file()):
            print('    (a .zig is missing on one arm; shas differ, cannot diff)')
            continue
        d = list(difflib.unified_diff(
            bf.read_text().splitlines(), ff.read_text().splitlines(),
            'baseline', 'fixed', n=1, lineterm=''))
        added = sum(1 for l in d if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in d if l.startswith('-') and not l.startswith('---'))
        print(f'    +{added} -{removed} lines')
        for line in d[:40]:
            print(f'    {line}')
        if len(d) > 40:
            print(f'    ... {len(d) - 40} more diff lines')

    print('\n--- the one line')
    print(f'stage moves {len(stage_moves)}, verdict moves {len(moves)}, '
          f'zig differs {len(diff)} of {len(have)}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
