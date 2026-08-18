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
    'CDX6020': ('NOTE', '__record-set in a constructor field: other fields reading the same '
                        'record see the mutated value. This is finding 10 territory and '
                        'nobody has read these yet. Counted, not ignored, until someone has.'),
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


def judge(path):
    text = pathlib.Path(path).read_text(errors='replace')
    census = {}
    for line in text.splitlines():
        m = CODE.search(line)
        census.setdefault(m.group(0) if m else 'uncoded', []).append(line.strip())

    failures, notes, unknown = [], [], []
    for code, lines in sorted(census.items()):
        verdict, _ = POLICY.get(code, (None, None))
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

    for code, lines in notes:
        print(f'  NOTE {code} x{len(lines)}  {POLICY[code][1]}')
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

    return 1 if (failures or unknown) else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('usage: check_diags.py <file.diags> [...]')
    rc, judged = 0, 0
    for p in sys.argv[1:]:
        if pathlib.Path(p).exists():
            rc |= judge(p)
            judged += 1
    # A clean compile writes no .diags at all, which is legitimate. Say so
    # rather than exiting 0 in silence: a gate that cannot tell "nothing to
    # judge" from "never ran" is a gate that rots without anyone noticing.
    if judged == 0:
        print('  (no diagnostics emitted)')
    sys.exit(rc)
