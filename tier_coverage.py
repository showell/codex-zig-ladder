#!/usr/bin/env python3
"""Rank the builtins by real use in the compiler, against what the tiers assert.

Objective 6 says coverage is chosen by COUNTING rather than by taste, and this
is the count. It reads three things and needs no arguments:

  - the plug's builtin table  (ZigEmitter.codex), for the surface that exists
  - src/passes_to_x86-subject.codex,  2.6 MB of real compiler, for how often each is used
  - findings/*.codex,         for what the tiers actually mention

and prints the gap, worst first. A builtin with hundreds of call sites and no
assertion is a bug waiting for a subject large enough to expose it -- which is
how findings 28, 29 and 30 were found, in a family (`substring`, the shifts)
that had no row anywhere.

The tier column is a mention count, not a coverage proof: a builtin used as an
INSTRUMENT scores high while never being the subject. `integer-to-text` was the
case that taught this -- 110 mentions across the tiers, every one of them
printing somebody else's number, and not one asserting its own answer until
tier 7. So read a high tier count as "look closer", not as "done".

THE `reached` COLUMN IS THE ONE THAT CHANGES DECISIONS. Counting occurrences in
the subject counts code the rungs never run: IR emission prunes to what the
`opening` reaches, and for `whole` that is 3,540 of 4,773 definitions -- a
quarter of the file is dead in every rung built from it. So this also counts
the plug's own `cx_` helper in the EMITTED zig (`src/*.zig`), which is the
pruned program. A builtin with heavy use in source and none in any emitted rung
is one **no rung can reach**, and a unit test is the only thing that will ever
cover it.

`address-of` is why this column exists: 65 in source, 4 emitted, and finding 31
sat under it undetected because 59 of its call sites live in `opening.codex` --
the one chapter a rung can never bundle, since a rung replaces it.

Caveat on `reached`: the map from builtin to helper is many-to-one -- `list-push`
and `__linked-list-push` both emit `cx_ll_push` -- so a shared helper inflates
both. Read a LOW reached count against a high source count; a high one only
says "something reaches this helper".

    ./tier_coverage.py            the ranking and the gap
    ./tier_coverage.py --all      every builtin, including the unused ones
"""

import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import CODEX, LADDER

import zig_pages

# THE EMITTER IS FOUR FILES. The ZigBuiltinEmitter table moved to page 2
# on 2026-09-03, so reading ZigEmitter.codex alone found zero builtins and
# reported full coverage of nothing.
EMITTER_TEXT = zig_pages.text()
SUBJECT = LADDER / 'src' / 'passes_to_x86-subject.codex'
FINDINGS = LADDER / 'findings'


def token_uses(hay, name):
    """Whole-token matches only: `list-at` must not count inside `list-at-x`,
    and codex names carry hyphens, so \\b is the wrong boundary here."""
    return len(re.findall(r'(?<![A-Za-z0-9_-])' + re.escape(name) + r'(?![A-Za-z0-9_-])', hay))


def main():
    show_all = '--all' in sys.argv
    if not SUBJECT.is_file():
        raise SystemExit(f'no {SUBJECT} -- bundle the passes_to_x86 unit first '
                         '(src/bundle_passes_to_x86.ps1), since the count is against real source')

    names = sorted(set(re.findall(r'ZigBuiltinEmitter \{ name = "([^"]+)"',
                                  EMITTER_TEXT)))
    subject = SUBJECT.read_text(errors='replace')
    tiers = ''.join(f.read_text(errors='replace') for f in sorted(FINDINGS.glob('*.codex')))

    helper = dict(re.findall(
        r'ZigBuiltinEmitter \{ name = "([^"]+)", emit = [^"]*"(cx_[a-z_0-9]+)\(',
        EMITTER_TEXT))
    zigs = [p.read_text(errors='replace') for p in sorted((LADDER / 'src').glob('*.zig'))]

    def reached(name):
        fn = helper.get(name)
        if fn is None or not zigs:
            return None
        return max(len(re.findall(re.escape(fn) + r'\(', z)) for z in zigs)

    rows = [(token_uses(subject, n), token_uses(tiers, n), reached(n), n) for n in names]
    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)

    total = sum(c for c, _, _, _ in rows)
    print(f'{len(names)} builtins in the plug; {total:,} call sites in '
          f'{len(subject):,} bytes of compiler; {len(zigs)} emitted rungs read\n')
    print(f'{"builtin":<24} {"source":>7} {"reached":>8} {"tiers":>6}   note')

    gap_sites = gap_names = 0
    for compiler, tier, rch, name in rows:
        if not compiler and not show_all:
            continue
        note = ''
        if compiler >= 10 and rch == 0:
            note = 'NO RUNG REACHES IT -- only a unit test can'
        elif compiler >= 15 and tier == 0:
            note = 'UNTESTED'
            gap_sites += compiler
            gap_names += 1
        elif compiler >= 15 and tier <= 2:
            note = 'barely'
        r = '-' if rch is None else str(rch)
        print(f'{name:<24} {compiler:>7} {r:>8} {tier:>6}   {note}')

    print()
    if gap_names:
        print(f'{gap_sites:,} call sites across {gap_names} builtins have no tier mention.')
        print('That is the work list, worst first.')
    else:
        print('Every builtin with 15+ call sites is mentioned by some tier.')


if __name__ == '__main__':
    main()
