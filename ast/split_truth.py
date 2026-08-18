#!/usr/bin/env python3
"""Split one unit's run into one file per rung.

A unit is what gets compiled; a rung is what gets claimed. Since 2026-08-18 a
back-end unit carries more than one subject and prints a mark before each dump,
so both arms produce ONE stream holding several rungs' answers. This cuts that
stream back into the per-rung files everything downstream already reads:
`<rung>.truth` from the bare-metal run, `<rung>.zigout` from the zig one.

The marks are emit_harness's, imported rather than spelled again here. A
harness that changed its delimiter and a splitter that did not would produce
one enormous section under the first rung's name and an empty file for the
rest, which is the kind of green nobody reads twice.

Everything this refuses is a way the split could look like it worked:

  a rung with no mark          the harness did not run it, or died before it
  a mark for an unknown rung   the unit carries a subject nobody banks
  output before the first mark the run printed something the split would
                               silently drop
  an empty section             a subject that produced no output at all

A single-subject unit prints no marks and is passed through whole, which is
how every front-end rung still works.
"""

import pathlib
import sys

from emit_harness import SUBJECT_MARK, subject_mark


def split(text, rungs):
    """Return {rung: section text} for the marks found in `text`."""
    want = {subject_mark(r): r for r in rungs}
    lines = text.splitlines()
    marked = [i for i, l in enumerate(lines) if l.strip().startswith(SUBJECT_MARK)]

    if not marked:
        if len(rungs) == 1:
            return {rungs[0]: text}
        raise SystemExit(
            f'no subject marks in {len(lines)} lines of output, but this unit '
            f'carries {rungs}. Either the harness is the old single-subject '
            f'one or the run died before its first mark; check the raw output '
            f'rather than trusting a split of it.')

    if marked[0] != 0:
        raise SystemExit(
            f'{marked[0]} line(s) before the first subject mark. Nothing should '
            f'print ahead of a dump, so this is output the split would drop:\n'
            f'  {lines[0][:120]}')

    out, seen = {}, []
    for n, start in enumerate(marked):
        mark = lines[start].strip()
        if mark not in want:
            raise SystemExit(
                f'unknown subject mark {mark!r}; this unit banks {rungs}. A '
                f'subject nobody banks is a measurement nobody reads.')
        rung = want[mark]
        if rung in out:
            raise SystemExit(f'subject {rung} marked twice; the driver runs '
                             f'each subject once')
        end = marked[n + 1] if n + 1 < len(marked) else len(lines)
        body = lines[start + 1:end]
        if not body:
            raise SystemExit(f'subject {rung} printed nothing between its mark '
                             f'and the next; the run did not get that far')
        out[rung] = '\n'.join(body) + '\n'
        seen.append(rung)

    missing = [r for r in rungs if r not in out]
    if missing:
        raise SystemExit(
            f'no dump for {missing}. The unit compiled and ran, so this is a '
            f'subject that faulted or was never reached; read the raw output '
            f'for {seen[-1]}, which is where it stopped.')
    return out


def main():
    if len(sys.argv) < 4:
        raise SystemExit('usage: split_truth.py <raw-file> <suffix> <rung>...')
    raw, suffix, rungs = sys.argv[1], sys.argv[2], sys.argv[3:]
    here = pathlib.Path(raw).parent
    for rung, body in split(pathlib.Path(raw).read_text(errors='replace'), rungs).items():
        dest = here / f'{rung}.{suffix}'
        dest.write_text(body)
        print(f'  {dest.name}: {body.count(chr(10))} lines')
    return 0


if __name__ == '__main__':
    sys.exit(main())
