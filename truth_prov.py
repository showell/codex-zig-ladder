#!/usr/bin/env python3
"""Provenance for working truths: which seed ran, and which harness content.

A truth is a measurement, and ast/<rung>.truth records only the measured
bytes -- nothing in it says which seed ran or which harness built the
subject. Banking used to infer both (the seed from whatever is on disk at
bank time, freshness from timestamps), and each inference had a documented
way to lie: repoint CODEX_ROOT between run and bank and the bank stamps the
wrong seed; switch branches to older harness content and mtimes call stale
truths fresh. So the truth arm RECORDS them instead: after a successful
split it writes ast/<rung>.truth.prov beside each truth --

    line 1: sha256 of the seed that ran
    line 2: sha256 over the harness content the subject was built from
            (the unit's generator + bundler + the shared pipeline files)

and bank_truth.py refuses any truth whose sidecar is missing or disagrees
with the seed and harness content on disk at bank time. Content identity,
not time: a checkout that changes nothing changes nothing here, and an edit
that changes anything changes the hash however the clock reads.

The composite-unit mapping is duplicated from oracle_lib.sh's unit_rungs
and cross-checked against LADDER_RUNGS/LADDER_UNITS at import, both
directions -- the same check oracle_lib performs on its own two lists.
"""

import hashlib
import sys

from ladder_root import LADDER
from seed_identity import seed_sha256

AST = LADDER / 'ast'
SHARED = ['emit_harness.py', 'oracle_lib.sh', 'split_truth.py']
COMPOSITE = {'fibx': ['fibx', 'scale'], 'whole': ['whole', 'clamp']}


def _lists():
    rungs = units = None
    for line in (AST / 'oracle_lib.sh').read_text().splitlines():
        if line.startswith('LADDER_RUNGS='):
            rungs = line.split('"')[1].split()
        if line.startswith('LADDER_UNITS='):
            units = line.split('"')[1].split()
    if not rungs or not units:
        raise SystemExit('oracle_lib.sh: LADDER_RUNGS/LADDER_UNITS not found')
    return rungs, units


def unit_rungs(unit):
    return COMPOSITE.get(unit, [unit])


def unit_of(rung):
    for u, rs in COMPOSITE.items():
        if rung in rs:
            return u
    return rung


_RUNGS, _UNITS = _lists()
_covered = sorted(r for u in _UNITS for r in unit_rungs(u))
if _covered != sorted(_RUNGS):
    raise SystemExit(f'unit mapping drift: units cover {_covered}, '
                     f'the ladder is {sorted(_RUNGS)}')


def watched(unit):
    files = ([AST / f'gen_{unit}_harness.py', AST / f'bundle_{unit}.ps1']
             + [AST / s for s in SHARED])
    missing = [f.name for f in files if not f.is_file()]
    if missing:
        raise SystemExit(f'cannot stamp {unit}: watched files missing: '
                         + ' '.join(missing))
    return files


def set_hash(unit):
    h = hashlib.sha256()
    for f in sorted(watched(unit)):
        h.update(f.name.encode() + b'\0' + hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def sidecar(rung):
    return AST / f'{rung}.truth.prov'


def stamp_unit(unit):
    seed = seed_sha256()
    content = set_hash(unit)
    for r in unit_rungs(unit):
        truth = AST / f'{r}.truth'
        if not truth.is_file() or truth.stat().st_size == 0:
            raise SystemExit(f'cannot stamp {r}: no truth beside it')
        sidecar(r).write_text(f'{seed}\n{content}\n')
    return seed, content


def read_sidecar(rung):
    p = sidecar(rung)
    if not p.is_file():
        return None
    lines = p.read_text().split()
    return (lines[0], lines[1]) if len(lines) >= 2 else None


def check_rung(rung):
    """Refuse a truth whose sidecar is missing or names another seed.

    Called per-use by zig_verdict, so a mixed working tree is caught at
    the rung that would diff against it, not hours later at bank time
    (process review C4). The harness-content half of the sidecar stays
    bank_truth's business: an emitter hunt edits harnesses deliberately
    and a verdict against the recorded truth is still the verdict wanted.
    """
    prov = read_sidecar(rung)
    if prov is None:
        raise SystemExit(f'STALE TRUTH for {rung}: no provenance sidecar '
                         '(rerun the truth arm)')
    if prov[0] != seed_sha256():
        raise SystemExit(f'STALE TRUTH for {rung}: recorded under seed '
                         f'{prov[0][:12]}, disk has {seed_sha256()[:12]} '
                         '(rerun the truth arm)')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'stamp':
        seed, content = stamp_unit(sys.argv[2])
        print(f'provenance stamped for {sys.argv[2]}: '
              f'seed {seed[:12]}, harness {content[:12]}')
    elif len(sys.argv) == 3 and sys.argv[1] == 'check':
        check_rung(sys.argv[2])
    else:
        raise SystemExit('usage: truth_prov.py stamp|check <unit|rung>')
