#!/usr/bin/env python3
"""Judge a compile's diagnostics against a list somebody maintains.

The ladder's premise is that a disagreement is evidence. That premise fails
quietly if the evidence arrives at a severity nobody reads, and it did: a
bundling bug of ours emitted 108-plus CDX3006 duplicate-definition warnings per
sweep for months, we learned to scroll past the class, and when a real duplicate
finally mattered it happened to be an error and stopped the build. Had it been
one more warning we would still be scrolling.

So no diagnostic code is ignored by habit here. Each one is either in the table
below with a reason, or it fails the rung. The important property is the one the
old arrangement lacked: **a code we have never seen before stops the build.**
Both Update 46 failures were new codes appearing, and so was CDX2053, which
turned up only because someone happened to run a census by hand.

This is deliberately not a linter. It does not know what the codes mean; it
knows which ones we have looked at. Adding an entry is cheap and is supposed to
be -- what must not be cheap is adding one without a reason next to it.
"""

import pathlib
import re
import sys

# verdict: OK    -- looked at, expected, not worth a line of output
#          NOTE  -- expected, but print a count; something we are watching
#          FAIL  -- stops the rung
#
# A third element pins the population: (verdict, why, expected_count). A class
# that fires constantly and benignly is the shape CDX3006 had right before it
# hid a real error from us, so for those the useful question is not "is this
# class benign" but "is this still the same set of instances". A count that
# moves is a new instance somebody should read.
#
# Every entry needs a why. An entry without one is the habit this file exists
# to break, wearing a table for a disguise.
POLICY = {
    'CDX4010': ('OK', 'bounds proven, check elided. Informational, emitted constantly '
                      'by the optimiser and says the optimiser worked.'),
    'CDX4011': ('OK', 'no-alias proven. Same family as CDX4010.'),
    'CDX4030': ('OK', 'pipeline info: names the passes that ran. One per compile, and '
                      'the rungs that run passes want it in the record.'),
    'CDX2053': ('OK', 'narrowing proven, bounds check elided. Informational. Was invisible '
                      'until the CDX3006 noise stopped displacing it.'),
    'CDX3005': ('OK', "a definition shadows a builtin. The compiler's own is-digit, "
                      'is-letter and is-whitespace do this; depot source, not ours, and '
                      'not something a subset bundle can fix.'),
    # Read all 37 on 2026-08-18, both sites. Benign at every one: the hazard is
    # a SIBLING field reading the record that was just mutated, and no site does.
    #   X86_64State, load-local:
    #       EmitResult { state = __record-set st1 ..., reg = scratch }
    #       scratch is an Integer, not a read of st1.
    #   Parser, attach-deriving:
    #       ParseTypeDefResult { maybe-type-def = Just (deck-record (__record-set td ...)),
    #                            state = st-deriv }
    #       st-deriv is a ParseState; td is a TypeDef.
    # Cited by enclosing function rather than by line, because both line numbers
    # this comment used to carry were wrong when re-read under seed 6CF4A8E0:
    # X86_64State's 923 was right at Update 48 and Update 49 pushed the site to
    # 930, and Parser's 764 never named the site at all (775 in all three
    # Updates). A depot line number is a per-Update fact and this pin outlives
    # Updates; a function name survives everything short of a rename.
    # Left as NOTE with the count pinned rather than promoted to OK, because
    # "benign in every instance we read" is a statement about a population, and
    # the population is what changes.
    'CDX6020': ('NOTE', '__record-set in a constructor field. All 37 read 2026-08-18 and '
                        'benign: no sibling field reads the mutated record. A change in '
                        'count means an instance nobody has read.\n'
                        '        The count is a function of WHICH UNITS EXIST, not only of the '
                        'source: it read 37 over fourteen compiles and 43 over the twelve the '
                        'merged ladder runs, for one unchanged set of sites. Re-pinned rather '
                        'than re-read. The right shape is a banked diagnostics set diffed like '
                        'a truth file, which would say what changed instead of that something '
                        'did; until then this number moves whenever the unit list does.', 43),
    # One instance, X86-64 Boot Infrastructure, emit-ata-wait's retry loop:
    #
    #   in let st7 = st-append-code st6 (sub-ri reg-rcx 1)
    #   in let st8 = st-append-code st7 (jcc cc-ne 0)
    #   in let st9 = patch-jcc-at st8 (st7.code-len) loop-top
    #
    # patch-jcc-at's second argument is the START of the six-byte jcc, so the
    # intent is the length BEFORE that append -- which is what the same
    # function captures into a let two lines earlier for dec-pos and
    # drdy-set-pos. Read inline after st8's append it is the length AFTER, so
    # the patch lands six bytes late. That is finding 10's hazard with a real
    # site attached and it is the depot's source, not ours; the ladder cannot
    # fix it and must not pretend it is not there. Filed as a finding.
    #
    # NOTE with the count pinned rather than FAIL, because failing every rung
    # on somebody else's warning trains us to pass -k.
    #
    # Pinned at 0: Update 47 closed issue 70 (the ATA jcc fix), and the
    # 2026-08-19 u47 rebank sweep confirmed the diagnostic is gone. The pin
    # stays in the table so a reappearance is a stopped rung, not scroll.
    # History: pinned at 2 under Update 46 for ONE site, counted once per
    # unit that bundles X86_64Boot; the first pin said 1 because it was set
    # from a partial sweep, which is the hazard this table exists to catch.
    'CDX2064': ('NOTE', 'a field read from a record after an in-place update bound to '
                        'another name. Was one emit-ata-wait site, filed as issue 70, '
                        'FIXED by Update 47; any instance now is new.', 0),
    'CDX3006': ('FAIL', 'duplicate definition across chapters. Every instance we have ever '
                        'seen was a bundle including the same chapter twice, which is ours '
                        'to fix. This is the code whose noise hid the CharClass duplicate.'),
    'CDX3001': ('FAIL', 'duplicate type definition. Same cause, already an error upstream.'),
    'CDX3002': ('FAIL', 'undefined name. In a subset bundle this means a chapter is missing.'),
    'CDX3008': ('FAIL', 'undefined type name. Update 46 added it; it is our finding 9. In a '
                        'subset bundle it means a chapter borrowed a type it never cited.'),
    'CDX9002': ('FAIL', 'deck overflow. A sizing number, not a defect, but it must stop.'),
}

CODE = re.compile(r'CDX\d{4}')


def judge(path, population=False):
    text = pathlib.Path(path).read_text(errors='replace')
    census = {}
    for line in text.splitlines():
        # Blank lines are not diagnostics. Skipping them is not cosmetic: the
        # census joins every rung's file with a newline, and each file already
        # ends in one, so thirteen files produced twelve empty lines, which
        # counted as twelve UNKNOWN uncoded diagnostics and failed the sweep.
        # A gate that fails on its own concatenation is worse than no gate.
        if not line.strip():
            continue
        m = CODE.search(line)
        census.setdefault(m.group(0) if m else 'uncoded', []).append(line.strip())

    failures, notes, unknown = [], [], []
    for code, lines in sorted(census.items()):
        entry = POLICY.get(code)
        verdict = entry[0] if entry else None
        if code == 'uncoded':
            # The compiler's own summary lines carry no CDX code. CODEGEN-ERRORS
            # and CODEGEN-HALTED mean the compile refused, which the SIZE-marker
            # check already catches; failing here too is belt and braces, and
            # cheap. Anything else uncoded is genuinely unrecognised.
            fatal = [l for l in lines if 'CODEGEN-' in l]
            if fatal:
                failures.append(('CODEGEN', fatal))
            rest = [l for l in lines if 'CODEGEN-' not in l]
            if rest:
                unknown.append((code, rest))
        elif verdict is None:
            unknown.append((code, lines))
        elif verdict == 'FAIL':
            failures.append((code, lines))
        elif verdict == 'NOTE':
            notes.append((code, lines))

    # A pinned population that vanishes is as much a change as one that grows,
    # and the loop below only visits codes that are PRESENT -- so a class going
    # to zero would have been silent. That is the same "cannot tell clean from
    # never-ran" hole this file closes in two other places, and I put it in
    # here. Only meaningful over a whole sweep, hence the population guard.
    drifted = False
    if population:
        for code, entry in sorted(POLICY.items()):
            expected = entry[2] if len(entry) > 2 else None
            if expected and code not in census:
                drifted = True
                print(f'  NOTE {code} x0  {entry[1]}'
                      f'  <-- POPULATION MOVED, was {expected}, now absent. '
                      f'Either the sweep did not reach the source that emits it, '
                      f'or something upstream changed; re-pin deliberately.')

    for code, lines in notes:
        entry = POLICY[code]
        expected = entry[2] if len(entry) > 2 else None
        # The pinned count is a SWEEP total, so it only means anything when
        # every rung's diagnostics are in front of us. Checking it per rung
        # would report a move on every rung and teach us to ignore the line,
        # which is the exact habit this file exists to break.
        moved = '' if (not population) or expected in (None, len(lines)) else \
            f'  <-- POPULATION MOVED, was {expected}; read the new ones and re-pin'
        if moved:
            drifted = True
        print(f'  NOTE {code} x{len(lines)}  {entry[1]}{moved}')
    for code, lines in unknown:
        print(f'  UNKNOWN {code} x{len(lines)} -- not in check_diags.py POLICY.')
        print(f'    {lines[0][:150]}')
        print('    Decide what it is and add it with a reason. A code nobody has '
              'looked at is exactly what this file exists to catch.')
    for code, lines in failures:
        why = POLICY[code][1] if code in POLICY else 'the compile refused'
        print(f'  FAIL {code} x{len(lines)}  {why}')
        for l in lines[:3]:
            print(f'    {l[:150]}')
        if len(lines) > 3:
            print(f'    ... {len(lines) - 3} more')

    # A moved pin fails the census run, not just the scroll: the CDX2064
    # comment promises "a reappearance is a stopped rung", and a promise a
    # return code does not keep is scroll with extra steps. Per-rung runs
    # (no population) never judge pins, so they cannot fail on them.
    return 1 if (failures or unknown or drifted) else 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--census']
    # --census judges every rung's diagnostics as one population, which is the
    # only scale at which the pinned counts mean anything. allcycles runs it
    # once at the end; a rung runs without it.
    census_mode = '--census' in sys.argv
    if not args:
        raise SystemExit('usage: check_diags.py [--census] <file.diags> [...]')
    rc, judged = 0, 0
    if census_mode:
        merged = '\n'.join(pathlib.Path(p).read_text(errors='replace')
                            for p in args if pathlib.Path(p).exists())
        if merged.strip():
            tmp = pathlib.Path('/tmp/.ladder-census.diags')
            tmp.write_text(merged)
            rc = judge(tmp, population=True)
            judged = 1
    else:
        for p in args:
            if pathlib.Path(p).exists():
                rc |= judge(p)
                judged += 1
    # A clean compile writes no .diags at all, which is legitimate. Say so
    # rather than exiting 0 in silence: a gate that cannot tell "nothing to
    # judge" from "never ran" is a gate that rots without anyone noticing.
    if judged == 0:
        print('  (no diagnostics emitted)')
    sys.exit(rc)
