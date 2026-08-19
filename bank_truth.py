#!/usr/bin/env python3
"""Bank the working truths under the seed that produced them.

A truth is a measurement, not a build product. Everything else the ladder
writes regenerates from a script beside it, which is why `ast/*.truth` is in
.gitignore along with the subjects and the emitted zig -- but a truth
regenerates only by running the rung again, for an hour, against a seed that
may no longer be on disk. So the working copies stay unversioned beside the
rung, and a bank is taken deliberately, here.

Banking is what makes two Updates comparable. `truth/u45/u45-lower.truth` and
`truth/u46/u46-lower.truth` are the same measurement of the same rung under two
compilers, and the diff between them is the only artifact that says what an
Update actually changed in the emitted image. That is the capability the
separate repository was for, and it does not exist until something writes the
files down.

The Update prefix is in the name as well as the directory on purpose: a file
pulled out of its directory to be mailed, pasted or diffed still says what it
is. A bare `lower.truth` in a bug report names nothing.

A bank is a SET, and taking one from a mixed working tree is the one way to
make it lie. If some rungs ran under an older harness than others, the
directory looks like fourteen measurements of one compiler and is not. There is
no way to detect that from the files, so this refuses to bank rungs whose truth
is older than the newest harness or the newest bundler, and says which.
"""

import argparse
import pathlib
import shutil
import sys

from ladder_root import LADDER
from seed_identity import stamp, truth_dir

# What a bank must contain. Taken from oracle_lib.sh so the two cannot drift
# about what the ladder is: a rung missing from the bank is a rung whose truth
# quietly is not there when someone reaches for it.
def ladder_rungs():
    text = (LADDER / 'ast' / 'oracle_lib.sh').read_text()
    for line in text.splitlines():
        if line.startswith('LADDER_RUNGS='):
            return line.split('"')[1].split()
    raise SystemExit('oracle_lib.sh: no LADDER_RUNGS= line; cannot tell what the ladder is')


def newest_input(paths):
    """When the things a truth is downstream of last CHANGED.

    Asked of git, not the filesystem: the question is whether a truth was
    measured under the harness content that exists now, and mtime answers a
    different question -- a `git checkout --` that changes nothing still
    refreshes it, which blocked two clean banks in one day. A watched file
    with uncommitted changes has no commit time that describes it, so that
    refuses outright.
    """
    import subprocess
    existing = [p for p in paths if p.is_file()]
    rels = [str(p.relative_to(LADDER)) for p in existing]
    dirty = subprocess.run(
        ['git', '-C', str(LADDER), 'status', '--porcelain', '--'] + rels,
        capture_output=True, text=True).stdout.strip()
    if dirty:
        raise SystemExit('REFUSED: uncommitted changes in files truths depend on:\n'
                         + dirty + '\ncommit them, rerun the truth arms, then bank')
    times = []
    for p, rel in zip(existing, rels):
        out = subprocess.run(['git', '-C', str(LADDER), 'log', '-1',
                              '--format=%ct', '--', rel],
                             capture_output=True, text=True).stdout.strip()
        if out:
            times.append((int(out), p))
    return max(times) if times else (0, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--keep', type=int, default=3,
                    help='how many banked Updates to keep; older ones are removed (default 3)')
    ap.add_argument('--force', action='store_true',
                    help='bank even if a truth is older than the harness that would produce it')
    args = ap.parse_args()

    s = stamp()
    dest = truth_dir(s['slug'])
    ast = LADDER / 'ast'

    named = f"Update {s['update']}" if s['update'] is not None else 'no release note names it'
    print(f"seed   {s['sha256'][:16]}  ({s['bytes']:,} bytes)")
    print(f"update {named}")
    print(f"bank   {dest}\n")

    # The harnesses and bundlers every truth is downstream of. A truth older
    # than any of them was measured on a subject nobody would build today.
    # split_truth.py is in the list because since the units carry more than one
    # subject a truth file is its output, not the run's: a splitter that cut
    # the stream somewhere else would produce truths that are wrong in a way
    # no diff of the run can see.
    watermark, witness = newest_input(
        list(ast.glob('gen_*_harness.py')) + list(ast.glob('bundle_*.ps1'))
        + [ast / 'emit_harness.py', ast / 'oracle_lib.sh',
           ast / 'split_truth.py'])

    rungs = ladder_rungs()
    missing, stale, ready = [], [], []
    for m in rungs:
        src = ast / f'{m}.truth'
        if not src.is_file() or src.stat().st_size == 0:
            missing.append(m)
        elif src.stat().st_mtime < watermark:
            stale.append(m)
        else:
            ready.append((m, src))

    if missing:
        print(f'NOT BANKED: {len(missing)} rung(s) have no truth: {" ".join(missing)}')
    if stale:
        print(f'NOT BANKED: {len(stale)} rung(s) older than {witness.name}: {" ".join(stale)}')
    if (missing or stale) and not args.force:
        print('\nA partial bank reads as a whole one. Run rebank_all.sh, or pass '
              '--force if you mean to bank an incomplete set.')
        return 1

    dest.mkdir(parents=True, exist_ok=True)
    for m, src in ready:
        shutil.copy2(src, dest / f"{s['slug']}-{m}.truth")
    (dest / 'SEED').write_text(f"{s['sha256']}\n{s['bytes']}\n{s['update']}\n")
    print(f"banked {len(ready)} truths as {s['slug']}-<rung>.truth")

    # Keeping every Update forever is how a directory of measurements becomes a
    # directory nobody reads. Three is enough to see a trend and small enough
    # to scan.
    banks = sorted((p for p in (LADDER / 'truth').iterdir() if p.is_dir()),
                   key=lambda p: p.stat().st_mtime)
    for old in banks[:-args.keep] if len(banks) > args.keep else []:
        shutil.rmtree(old)
        print(f'removed old bank {old.name} (keeping {args.keep})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
