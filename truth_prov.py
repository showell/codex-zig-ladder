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

The same mechanism guards the other artifact the sweep does not create:
`ast/<unit>.ir`. `allcycles.sh` READS it and the truth arm WRITES it, so in
a shared checkout it persists from whatever ran last and the dependency is
invisible. A stale one means the zig arm transpiles yesterday's IR and diffs
it against today's bank -- a green that means nothing.

Its key is different from a truth's, and deliberately so. IR is a pure
function of the seed, the subject's own bytes and the mode flags: the PLUG
does not participate in producing it. So `ast/<unit>.ir.prov` records those
three and nothing else. Keying it on the Codex checkout's HEAD instead --
the first shape proposed -- would refuse on every plug commit, which is
every commit that cannot possibly have changed the IR, and a guard that
cries wolf gets switched off.

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
COMPOSITE = {'ir_to_x86': ['ir_to_x86_on_fib', 'ir_to_x86_on_cce'],
             'passes_to_x86': ['passes_to_x86_on_mid', 'passes_to_x86_on_arith']}


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


# ---------------------------------------------------------------------------
# A GUEST THAT FAULTED STILL PRODUCED OUTPUT, and that output is not a truth.
#
# `codex_vm.run_cdx` returns whatever came back over serial and raises only
# when the guest never finished. A #PF dump IS output, so it returns normally,
# `<unit>.raw` is non-empty, `split_truth.py` splits it happily, and
# `stamp_unit` -- which asked only "does the file exist and is it non-empty" --
# certified it. Measured 2026-09-02 on the U54 lex rung: 923 bytes of register
# and stack state, zero tokens, stamped with the correct seed and the correct
# harness hash, and `bank_truth.py` would have accepted it as the bare-metal
# oracle for that rung. Nothing in the ladder looked at `!EXC=` at all.
#
# That is worse than banking nothing. A truth is what every future zig arm is
# diffed against, so a banked fault dump reports the ARM as differing for as
# long as the bank stands, and reads as a plug defect rather than as a truth
# that was never a measurement. The only thing that caught it was a human
# noticing 923 bytes where 172 KB belongs.
#
# `!EXC=NN` is the GUEST'S OWN marker, not one invented here: the exception
# handler writes it to the serial stream, `tools/codex-vm.c` watches for
# `!EXC=03` to hand control to the debugger, and `Emit/X86_64Helpers.codex`
# and `X86_64Boot.codex` both describe failures as dying `!EXC=06`. An external
# format, which is why it is spelled out here rather than derived.

GUEST_FAULT = '!EXC='


def guest_fault(path):
    """The guest's fault line if this output is a fault dump, else None.

    Whole file, not the head: a subject can print for an hour and fault at the
    end, and that dump is at the bottom under real output. The line is returned
    rather than a boolean so a refusal can quote the exception and the faulting
    address instead of asserting that something went wrong.
    """
    p = AST / path if not str(path).startswith('/') else path
    try:
        text = open(p, errors='replace').read()
    except OSError:
        return None
    for line in text.splitlines():
        if GUEST_FAULT in line:
            return line.strip()
    return None


def sidecar(rung):
    return AST / f'{rung}.truth.prov'


def stamp_unit(unit):
    seed = seed_sha256()
    content = set_hash(unit)
    for r in unit_rungs(unit):
        truth = AST / f'{r}.truth'
        if not truth.is_file() or truth.stat().st_size == 0:
            raise SystemExit(f'cannot stamp {r}: no truth beside it')
        # NON-EMPTY IS NOT THE SAME AS MEASURED. This is the certifier, so it
        # is the last place a fault dump can be stopped before it becomes an
        # oracle. See the note above guest_fault.
        fault = guest_fault(f'{r}.truth')
        if fault:
            raise SystemExit(
                f'cannot stamp {r}: this is a GUEST FAULT DUMP, not a truth\n'
                f'  {fault}\n'
                f'  {truth} is {truth.stat().st_size:,} bytes and the run did '
                'not finish; the dump is kept for reading, the truth is not '
                'certified')
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


def ir_sidecar(unit):
    return AST / f'{unit}.ir.prov'


def ir_key(unit, flags):
    """(seed, subject bytes, mode flags) -- everything the IR depends on."""
    subject = AST / f'{unit}-subject.codex'
    if not subject.is_file():
        raise SystemExit(f'cannot key {unit}.ir: no {subject.name} beside it')
    return (seed_sha256(),
            hashlib.sha256(subject.read_bytes()).hexdigest(),
            flags.strip())


def stamp_ir(unit, flags):
    ir = AST / f'{unit}.ir'
    if not ir.is_file() or ir.stat().st_size == 0:
        raise SystemExit(f'cannot stamp {unit}.ir: it is missing or empty')
    seed, subj, fl = ir_key(unit, flags)
    ir_sidecar(unit).write_text(f'{seed}\n{subj}\n{fl}\n')
    return seed, subj


def check_ir(unit, flags):
    """Refuse IR that no run under this seed and this subject produced.

    Called by the zig arm before it transpiles, so the refusal names the
    rung about to be judged rather than surfacing hours later as a bank
    mismatch -- or not at all, which is the case this exists for.
    """
    ir = AST / f'{unit}.ir'
    if not ir.is_file() or ir.stat().st_size == 0:
        raise SystemExit(f'NO IR for {unit}: ast/{unit}.ir is missing or '
                         'empty, and the zig arm does not produce it '
                         '(rerun the truth arm)')
    p = ir_sidecar(unit)
    if not p.is_file():
        raise SystemExit(f'UNPROVENANCED IR for {unit}: no {p.name}. It may '
                         'predate this guard or have been carried in from '
                         'another checkout (rerun the truth arm)')
    got = p.read_text().split('\n')
    want = ir_key(unit, flags)
    if len(got) < 3 or tuple(x.strip() for x in got[:3]) != want:
        raise SystemExit(
            f'STALE IR for {unit}: recorded under seed {got[0][:12]} / '
            f'subject {got[1][:12] if len(got) > 1 else "?"} / flags '
            f'"{got[2] if len(got) > 2 else "?"}", disk has '
            f'{want[0][:12]} / {want[1][:12]} / "{want[2]}" '
            '(rerun the truth arm)')


# ---------------------------------------------------------------------------
# The ZIG ARM's verdict, which had no provenance at all.
#
# `bank_truth.arm_verdict` reads ast/<rung>.diff by EXISTENCE and SIZE: absent
# means the arm never reached a verdict, empty means it agreed, non-empty means
# it differed. That reading is correct only if a `.diff` on disk was written by
# THIS run -- and it was not guaranteed to be. `zig_verdict` writes the file on
# its `diff` line and nothing else; a stale-truth refusal, a transport failure
# or a zig build failure all return BEFORE it, leaving the previous run's
# `.diff` untouched under exactly the name the next reader looks for. A fresh
# sandbox hides this because it carries no artifacts; a second run in the same
# sandbox does not, and that is the ordinary way a red rung gets re-run.
#
# Two changes close it, and the first is the one that matters. The arm now
# DELETES the verdict before it can fail, so ABSENT is honest again -- the root
# cause was that absence was load-bearing and nothing enforced it. The sidecar
# here is the second: it records what the verdict was a function of, so a
# `.diff` carried in from another tree or taken under another seed is refused
# rather than counted.
#
# The key is (seed, truth bytes, emitted zig bytes) -- not the plug fingerprint.
# The fingerprint is guarded DURING the run by plug_provenance/ring_provenance,
# and it answers a different question: which emitter built the plug. What the
# verdict is actually a function of is the two files that were compared and the
# seed that produced both sides, and keying on those means the check still works
# for either arm without either arm having to say which it was.

def diff_sidecar(rung):
    return AST / f'{rung}.diff.prov'


def _sha_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ''


def diff_key(rung, unit):
    return (seed_sha256(), _sha_of(AST / f'{rung}.truth'), _sha_of(AST / f'{unit}.zig'))


def stamp_diff(rung, unit):
    seed, truth, zig = diff_key(rung, unit)
    if not truth or not zig:
        raise SystemExit(f'cannot stamp {rung}.diff: '
                         + ('no truth beside it' if not truth
                            else f'no ast/{unit}.zig beside it'))
    diff_sidecar(rung).write_text(f'{seed}\n{truth}\n{zig}\n')


def check_diff(rung, unit):
    """Is ast/<rung>.diff a verdict THIS tree produced? Returns a reason, or None.

    Not a SystemExit like its siblings: this is read at BANK time over every
    rung, and the caller reports each rung's state rather than dying on the
    first. A missing `.diff` is not this function's business -- absent is a
    legitimate third state and `arm_verdict` names it.
    """
    p = diff_sidecar(rung)
    if not p.is_file():
        return 'no provenance sidecar beside the diff'
    got = [x.strip() for x in p.read_text().split('\n')]
    want = diff_key(rung, unit)
    if len(got) < 3 or tuple(got[:3]) != want:
        if len(got) > 0 and got[0] != want[0]:
            return f'verdict taken under seed {got[0][:12]}, disk has {want[0][:12]}'
        if len(got) > 1 and got[1] != want[1]:
            return 'the truth it was diffed against has moved since'
        return 'the emitted zig has moved since the verdict was taken'
    return None


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'stamp':
        seed, content = stamp_unit(sys.argv[2])
        print(f'provenance stamped for {sys.argv[2]}: '
              f'seed {seed[:12]}, harness {content[:12]}')
    elif len(sys.argv) == 3 and sys.argv[1] == 'check':
        check_rung(sys.argv[2])
    elif len(sys.argv) in (3, 4) and sys.argv[1] == 'stamp-ir':
        seed, subj = stamp_ir(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '')
        print(f'IR provenance stamped for {sys.argv[2]}: '
              f'seed {seed[:12]}, subject {subj[:12]}')
    elif len(sys.argv) in (3, 4) and sys.argv[1] == 'check-ir':
        check_ir(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '')
    elif len(sys.argv) == 4 and sys.argv[1] == 'stamp-diff':
        stamp_diff(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == 'fault':
        f = guest_fault(sys.argv[2])
        if f:
            print(f'GUEST FAULT in {sys.argv[2]}:\n  {f}')
            raise SystemExit(1)
    else:
        raise SystemExit('usage: truth_prov.py stamp|check <unit|rung>\n'
                         '       truth_prov.py stamp-ir|check-ir <unit> [flags]\n'
                         '       truth_prov.py stamp-diff <rung> <unit>\n'
                         '       truth_prov.py fault <file>')
