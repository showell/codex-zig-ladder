#!/usr/bin/env python3
"""Rank the builtins by real use in the compiler, against what the tiers assert.

Objective 6 says coverage is chosen by COUNTING rather than by taste, and this
is the count. It reads three things and needs no arguments:

  - the plug's builtin table  (ZigEmitter.codex), for the surface that exists
  - ast/whole-subject.codex,  2.6 MB of real compiler, for how often each is used
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

    ./tier_coverage.py            the ranking and the gap
    ./tier_coverage.py --all      every builtin, including the unused ones
"""

import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import CODEX, LADDER

EMITTER = CODEX / 'codex' / 'plugs' / 'zig' / 'ZigEmitter.codex'
SUBJECT = LADDER / 'ast' / 'whole-subject.codex'
FINDINGS = LADDER / 'findings'


def token_uses(hay, name):
    """Whole-token matches only: `list-at` must not count inside `list-at-x`,
    and codex names carry hyphens, so \\b is the wrong boundary here."""
    return len(re.findall(r'(?<![A-Za-z0-9_-])' + re.escape(name) + r'(?![A-Za-z0-9_-])', hay))


def main():
    show_all = '--all' in sys.argv
    if not SUBJECT.is_file():
        raise SystemExit(f'no {SUBJECT} -- bundle the whole unit first '
                         '(ast/bundle_whole.ps1), since the count is against real source')

    names = sorted(set(re.findall(r'ZigBuiltinEmitter \{ name = "([^"]+)"',
                                  EMITTER.read_text())))
    subject = SUBJECT.read_text(errors='replace')
    tiers = ''.join(f.read_text(errors='replace') for f in sorted(FINDINGS.glob('*.codex')))

    rows = [(token_uses(subject, n), token_uses(tiers, n), n) for n in names]
    rows.sort(reverse=True)

    total = sum(c for c, _, _ in rows)
    print(f'{len(names)} builtins in the plug; {total:,} call sites in '
          f'{len(subject):,} bytes of compiler\n')
    print(f'{"builtin":<24} {"compiler":>8} {"tiers":>6}   note')

    gap_sites = gap_names = 0
    for compiler, tier, name in rows:
        if not compiler and not show_all:
            continue
        note = ''
        if compiler >= 15 and tier == 0:
            note = 'UNTESTED'
            gap_sites += compiler
            gap_names += 1
        elif compiler >= 15 and tier <= 2:
            note = 'barely'
        print(f'{name:<24} {compiler:>8} {tier:>6}   {note}')

    print()
    if gap_names:
        print(f'{gap_sites:,} call sites across {gap_names} builtins have no tier mention.')
        print('That is the work list, worst first.')
    else:
        print('Every builtin with 15+ call sites is mentioned by some tier.')


if __name__ == '__main__':
    main()
