#!/usr/bin/env python3
"""Where does ZigEmitter name a prelude builtin, and is it somewhere sanctioned?

The tree shaker takes its roots from a substring scan of the emitted program.
That works, and it is sound in a way an accumulator is not automatically:
the scan reads FINISHED TEXT, so it cannot miss an emission site. An
accumulator threaded through the emitter is only correct if every site that
names a builtin records it.

Steve's point, and it is the right one: that does not have to be discipline.
Make the helper the ONLY way to spell a builtin and forgetting stops being
possible. This is the check that turns "the only way" from an intention into
a fact -- it refuses a new hand-written site, so the surface can shrink to
zero and never grow back.

Four places a `"cx_..."` or `"Cx..."` literal can sit, and only one is a
problem:

    zig-prelude-decls       the reserved-name list. Not emission.
    zig-builtin-emitters    the table. One uniform shape,
                            `\\args ctx d ty -> "cx_..."`, so threading an
                            accumulator through it is mechanical.
    zig-prelude-parts       the prelude's own text, HAND-WRITTEN. It was
                            migrated once by shake_parts.py, which is gone;
                            this table is the source now. Not emission
                            either -- this is the library, not a call into it.
    everything else         HAND-WRITTEN EMISSION SITES. These are the ones
                            that would each have to remember.

The ratchet is a number in this file rather than a list of line numbers,
because line numbers move on every edit and a stale allowlist fails in the
direction that lets a new site through.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import LADDER

# The count of hand-written sites at the last deliberate look. It may FALL
# freely -- that is the work. It may not rise without someone changing this
# number on purpose and saying why in the commit.
BASELINE = 21

NAME = re.compile(r'"(cx_[a-z0-9_]+|Cx[A-Za-z0-9]+)')


def span(lines, header):
    """The line range of a definition, from its header to its closing `]`."""
    i = next(k for k, l in enumerate(lines) if l.startswith(header))
    j = i
    while j < len(lines) and ']' not in lines[j]:
        j += 1
    return i, j + 1


def audit(path):
    lines = path.read_text(errors='replace').split('\n')
    di, dj = span(lines, '  zig-prelude-decls : List Text')
    bi, bj = span(lines, '  zig-builtin-emitters : List ZigBuiltinEmitter')
    try:
        pi = next(k for k, l in enumerate(lines) if l.startswith('  zig-p-'))
    except StopIteration:
        pi = len(lines)          # not restructured yet: no generated table

    counts = {'reserved list': 0, 'builtin-emitters table': 0,
              'generated prelude text': 0}
    loose = []
    for k, l in enumerate(lines):
        for m in NAME.finditer(l):
            if di <= k < dj:
                counts['reserved list'] += 1
            elif bi <= k < bj:
                counts['builtin-emitters table'] += 1
            elif k >= pi:
                counts['generated prelude text'] += 1
            else:
                loose.append((k + 1, m.group(1), l.strip()))
    return counts, loose


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if path is None:
        print('usage: check_builtin_sites.py <ZigEmitter.codex>', file=sys.stderr)
        return 2
    counts, loose = audit(path)
    for k, v in counts.items():
        print(f'  {v:5}  {k}')
    print(f'  {len(loose):5}  HAND-WRITTEN EMISSION SITES '
          f'({len(set(n for _, n, _ in loose))} distinct names)')

    by_name = {}
    for ln, nm, txt in loose:
        by_name.setdefault(nm, []).append(ln)
    print()
    for nm in sorted(by_name, key=lambda n: (-len(by_name[n]), n)):
        lns = by_name[nm]
        print(f'    {nm:22} x{len(lns):<3} lines {", ".join(str(x) for x in lns)}')

    print()
    if len(loose) > BASELINE:
        print(f'  REFUSED: {len(loose)} hand-written sites, baseline {BASELINE}. '
              f'A new site was added by hand.')
        print('  Route it through the builtin helper, or raise BASELINE on '
              'purpose and say why.')
        return 1
    if len(loose) < BASELINE:
        print(f'  OK, and BETTER than the baseline: {len(loose)} sites against '
              f'{BASELINE}. Lower BASELINE to {len(loose)} to keep the ground '
              f'that was just won.')
        return 0
    print(f'  OK: {len(loose)} hand-written sites, at the baseline.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
