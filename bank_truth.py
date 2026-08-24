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
make it lie. If some rungs ran under a different seed or older harness content
than others, the directory looks like fourteen measurements of one compiler
and is not. Each truth carries a provenance sidecar (truth_prov.py, written by
the truth arm: the seed sha and the harness-content sha it was measured
under), and this refuses to bank any truth whose sidecar is missing or
disagrees with what is on disk now -- content identity, not timestamps. The
bank itself is written to a temp directory and renamed into place, so a crash
or a --force can never leave a directory that is half one measurement and
half another.
"""

import argparse
import pathlib
import re
import shutil
import sys

import truth_prov
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

    # A truth is bankable when its recorded provenance -- the seed it ran
    # under and the harness content its subject was built from, stamped by
    # the truth arm -- matches what is on disk NOW. split_truth.py is in the
    # watched set because a truth file is the splitter's output, not the
    # run's: a splitter that cut the stream somewhere else would produce
    # truths wrong in a way no diff of the run can see.
    rungs = ladder_rungs()
    missing, stale, ready = [], [], []
    for m in rungs:
        src = ast / f'{m}.truth'
        if not src.is_file() or src.stat().st_size == 0:
            missing.append(m)
            continue
        prov = truth_prov.read_sidecar(m)
        if prov is None:
            stale.append((m, 'no provenance sidecar (rerun the truth arm)'))
            continue
        pseed, pset = prov
        if pseed != s['sha256']:
            stale.append((m, f'ran under seed {pseed[:12]}, disk has '
                             f'{s["sha256"][:12]}'))
        elif pset != truth_prov.set_hash(truth_prov.unit_of(m)):
            stale.append((m, 'harness content moved since it ran'))
        else:
            ready.append((m, src))

    if missing:
        print(f'NOT BANKED: {len(missing)} rung(s) have no truth: {" ".join(missing)}')
    for m, why in stale:
        print(f'NOT BANKED: {m}: {why}')
    if (missing or stale) and not args.force:
        print('\nA partial bank reads as a whole one. Run rebank_all.sh, or pass '
              '--force if you mean to bank an incomplete set.')
        return 1

    # --force is destructive, not convenient: the rename REPLACES the whole
    # bank with the ready subset. Confirm by the count, so agreeing requires
    # having read it (C3). Non-interactive stdin refuses rather than assumes.
    if (missing or stale) and args.force:
        print(f'\n--force: about to REPLACE {dest.name} with {len(ready)} of '
              f'{len(rungs)} rungs; the {len(rungs) - len(ready)} others '
              'vanish from the bank.')
        try:
            answer = input(f'type the ready count ({len(ready)}) to confirm: ')
        except EOFError:
            answer = ''
        if answer.strip() != str(len(ready)):
            print('confirmation mismatch; nothing banked')
            return 1

    # Since the rename REPLACES the destination, an empty ready set must stop
    # here even under --force: a SEED-only directory renamed over a full bank
    # would destroy fourteen measurements to record zero.
    if not ready:
        print('NOTHING TO BANK: no rung is ready; refusing to replace '
              f'{dest.name} with an empty set')
        return 1

    # Built complete in a temp directory, then renamed over the old bank, so
    # the destination is only ever a whole set -- never last bank's files
    # beside this one's after a crash or a --force of a subset.
    tmp = dest.parent / (dest.name + '.tmp')
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    banked_prov = 0
    for m, src in ready:
        shutil.copy2(src, tmp / f"{s['slug']}-{m}.truth")
        # The sidecar travels WITH the truth. A banked truth without its
        # provenance is a measurement nobody can place afterwards: SEED
        # below records the seed, but a truth is keyed on the seed AND the
        # harness content it was measured under, and only the sidecar
        # carries the second. Restoring a bank into a fresh sandbox is
        # then a copy rather than a re-measurement, and it stays HONEST
        # because truth_prov.check still validates the restored sidecar
        # against what is on disk now -- a harness that moved since the
        # bank was taken refuses exactly as it always did. Nothing is
        # loosened here; something previously thrown away is kept.
        prov = truth_prov.sidecar(m)
        if prov.is_file():
            shutil.copy2(prov, tmp / f"{s['slug']}-{m}.truth.prov")
            banked_prov += 1
    (tmp / 'SEED').write_text(f"{s['sha256']}\n{s['bytes']}\n{s['update']}\n")
    if dest.exists():
        shutil.rmtree(dest)
    tmp.rename(dest)
    print(f"banked {len(ready)} truths as {s['slug']}-<rung>.truth")
    # Say it either way. A bank whose sidecars are missing still works as a
    # bank and CANNOT be restored from, and a reader who is told only the
    # truth count has no way to know which kind they have.
    if banked_prov == len(ready):
        print(f"       {banked_prov} provenance sidecars beside them "
              "(this bank can be restored into a fresh sandbox)")
    else:
        print(f"       {banked_prov} of {len(ready)} provenance sidecars -- "
              "this bank CANNOT be restored from; re-bank from a tree that "
              "has them if you want that")

    # Keeping every Update forever is how a directory of measurements becomes a
    # directory nobody reads. Three is enough to see a trend and small enough
    # to scan. Pruning goes by the NAME, oldest Update number first -- never by
    # directory mtime, which re-banking does not bump -- and touches nothing
    # but u<N> directories, so seed-<hex> banks (deliberate, unreleased) and
    # anything else living under truth/ are left alone.
    banks = sorted((int(m.group(1)), p)
                   for p in (LADDER / 'truth').iterdir()
                   if p.is_dir() and (m := re.fullmatch(r'u(\d+)', p.name)))
    for _, old in banks[:-args.keep] if len(banks) > args.keep else []:
        shutil.rmtree(old)
        print(f'removed old bank {old.name} (keeping {args.keep})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
