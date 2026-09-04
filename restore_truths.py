#!/usr/bin/env python3
"""Restore a bank's truths into the working tree, so a fresh sandbox can sweep.

A sweep asks one question -- does today's plug still reproduce the banked
measurement -- and `allcycles.sh` answers it by diffing each arm against
`src/<rung>.truth`. Those working files are gitignored, so a FRESH sandbox
has none, and the only way to make them used to be a full rebank: the whole
truth arm, bare-metal binary and subject run included, roughly 27 minutes of
re-measuring an answer that is already banked. That is the wrong price for
the question, and it was paid on 2026-08-23 and again on 2026-08-24.

The truths are already there. `truth/u<NN>/` is the ladder's oracle across
Updates and comparing today's plug against it is the PREMISE, not a
shortcut. What stopped a restore was provenance: a truth is keyed on the
seed AND the harness content it was measured under, `truth/u<NN>/SEED`
records only the seed, and a truth with no sidecar is refused at the rung
that would use it -- correctly, since a truth from another seed diffs just
as confidently as a fresh one.

So `bank_truth.py` now banks each sidecar beside its truth, and this copies
both back. **No gate is loosened by that.** The sidecar is the measurement's
own record and it travels with the measurement; the arms then run
`truth_prov.check_rung` against it exactly as they would against one a
rebank had just written. What changed is that something previously thrown
away is kept.

Read the two halves of a sidecar separately, because the codebase already
does. `check_rung` -- the gate `zig_verdict` calls -- checks the SEED half
only, and says why in its own docstring: an emitter hunt edits harnesses
deliberately and a verdict against the recorded truth is still the verdict
wanted. The harness-content half is `bank_truth`'s business, at bank time.
This follows that split rather than inventing a stricter one: a seed
mismatch refuses, and harness drift is REPORTED, because a reader of a
green sweep would otherwise have no way to know the truths under it were
measured against a harness that has since moved.

What this does NOT do is re-measure bare metal. A sweep run against restored
truths says "the plug still reproduces the bank"; it does not say "bare metal
still produces the bank". Those are different claims and only `rebank_all.sh`
makes the second, so the caller must not report a restored sweep as a full
one -- `allcycles.sh` prints which rungs were restored for exactly that
reason.

    ./restore_truths.py            restore what is missing, refuse on mismatch
    ./restore_truths.py --check    say what would happen, write nothing
"""

import argparse
import shutil
import sys

import truth_prov
from ladder_root import LADDER
from seed_identity import measurement_slug, stamp, truth_dir


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true',
                    help='report what would be restored and write nothing')
    ap.add_argument('--force', action='store_true',
                    help='overwrite a working truth that is already there')
    args = ap.parse_args()

    s = stamp()
    # NAMED BY THE MEASUREMENT, and there is deliberately NO FALLBACK to the
    # release's directory. Quietly restoring another tree's truths is how a
    # sweep reports green against answers measured somewhere else -- which is
    # what made an 11/14 look untrustworthy and a 6/14 look like a wall.
    slug = measurement_slug()
    bank = truth_dir(slug)
    ast = LADDER / 'src'

    print(f"seed   {s['sha256'][:16]}  (Update {s['update']})")
    print(f"bank   {bank}")

    if not bank.is_dir():
        print(f'NO BANK for this seed at {bank}; nothing to restore from')
        return 1

    # The bank's own seed must be this seed. Restoring across seeds is the
    # exact failure the sidecars exist to prevent, and the SEED file is the
    # cheapest place to catch it -- before any file is touched.
    seed_file = bank / 'SEED'
    if not seed_file.is_file():
        print(f'{bank.name}/SEED is missing; refusing to restore from a bank '
              'that cannot say what produced it')
        return 1
    banked_seed = seed_file.read_text().split('\n')[0].strip()
    if banked_seed != s['sha256']:
        print(f'SEED MISMATCH: bank was measured under {banked_seed[:12]}, '
              f'this tree has {s["sha256"][:12]}; refusing')
        return 1

    restored, present, missing, stale = [], [], [], []
    for m in _rungs():
        src = bank / f"{slug}-{m}.truth"
        src_prov = bank / f"{slug}-{m}.truth.prov"
        dst = ast / f'{m}.truth'
        dst_prov = truth_prov.sidecar(m)

        if not src.is_file():
            missing.append((m, 'no truth in the bank'))
            continue
        # A truth without its sidecar is exactly what this exists to stop
        # being guessed at. Banks taken before 2026-08-24 have none; say so
        # rather than restoring something the arms will refuse anyway.
        if not src_prov.is_file():
            missing.append((m, 'banked without a sidecar (re-bank to fix)'))
            continue
        if dst.is_file() and dst.stat().st_size and not args.force:
            present.append(m)
            continue
        restored.append((m, src, src_prov, dst, dst_prov))

    for m, why in missing:
        print(f'  CANNOT RESTORE {m}: {why}')
    for m in present:
        print(f'  keeping {m}: a working truth is already there (--force to replace)')

    if args.check:
        print(f'\n--check: {len(restored)} would be restored, {len(present)} kept, '
              f'{len(missing)} unavailable')
        return 1 if missing else 0

    for m, src, src_prov, dst, dst_prov in restored:
        shutil.copy2(src, dst)
        shutil.copy2(src_prov, dst_prov)

    # Prove it rather than assume it, and prove exactly what the arms will
    # ask. check_rung is the gate zig_verdict uses and it checks the SEED
    # half only -- deliberately, per its own docstring: an emitter hunt
    # edits harnesses on purpose and a verdict against the recorded truth
    # is still the verdict wanted. So a seed mismatch is a refusal here.
    for m, *_ in restored:
        if not _check_quiet(m):
            stale.append(m)

    # The harness half is bank_truth's business, not the arms'. It is not a
    # refusal, but a restored truth measured under a harness that has since
    # moved is worth SAYING, because the reader of a green sweep would
    # otherwise have no way to know.
    drifted = []
    for m, *_ in restored:
        prov = truth_prov.read_sidecar(m)
        if prov and prov[1] != truth_prov.set_hash(truth_prov.unit_of(m)):
            drifted.append(m)

    print(f'\nrestored {len(restored)} truths and their sidecars into src/')
    if stale:
        print('REFUSED after restore -- these do not pass the gate the arms '
              'use, so the sweep would refuse them one at a time:')
        for m in stale:
            print(f'    {m}')
        return 1
    print('all restored truths pass truth_prov.check_rung against this tree')
    if drifted:
        print('NOTE: the harness content has moved since these were banked, '
              'which the arms tolerate and bank_truth does not:')
        for m in drifted:
            print(f'    {m}')
        print('A sweep over them is still a verdict; a BANK taken from them '
              'would be refused. Re-bank if you want that.')
    if missing:
        return 1
    return 0


def _rungs():
    text = (LADDER / 'src' / 'oracle_lib.sh').read_text()
    for line in text.splitlines():
        if line.startswith('LADDER_RUNGS='):
            return line.split('"')[1].split()
    raise SystemExit('oracle_lib.sh: no LADDER_RUNGS= line')


def _check_quiet(rung):
    try:
        truth_prov.check_rung(rung)
        return True
    except SystemExit:
        return False


if __name__ == '__main__':
    sys.exit(main())
