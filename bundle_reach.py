#!/usr/bin/env python3
"""How much of a bundled subject does the seed's pruner actually keep?

A unit's subject is sixty-odd compiler chapters concatenated, and the ring
carries it into the guest a megabyte at a time. The obvious saving is to
stop bundling what nothing reaches -- but IR emission ALREADY prunes to
what the opening reaches (`ir-prune-unreachable-roots`), so the question
is not "is there dead weight" but "where is it paid for":

  - a definition dropped by the pruner still cost the seed a lex, a
    parse, a scope, a check and a lower, and still crossed the ring;
  - a CHAPTER none of whose definitions survive cost all of that and
    contributed nothing at all, and is what a source-level shaker would
    remove.

This counts both, per chapter, so the decision to build a shaker is made
against a number. It reads only files a rung has already produced, runs
no compiler, and needs no QEMU.

    ./bundle_reach.py                    the ir_to_x86 unit
    ./bundle_reach.py passes_to_x86      any unit that has a .ir beside it

**Read the caveat before quoting the number.** Definitions are matched by
NAME, and `ChapterScoper` mangles names that collide across chapters, so
a surviving definition whose name was rewritten reads here as dropped.
The report says how many IR names it could not attribute; if that count
is not small, the per-chapter figures below it are not trustworthy and
the matching needs to learn the rename table before anyone acts on them.
"""

import pathlib
import re
import sys

from ladder_root import LADDER

sys.path.insert(0, str(LADDER))  # ladder-root-bootstrap: cce lives at the top
import cce

CHAPTER_RE = re.compile(r'^Chapter:\s*(.+?)\s*$')
# A definition's type signature: two spaces, a name, a colon. The body line
# that follows repeats the name, so signatures are what gets counted.
SIGNATURE_RE = re.compile(r'^  ([a-z][A-Za-z0-9_-]*)\s*:\s')
IRDEF_RE = re.compile(r'\(def "([^"]+)"')


def ir_text(path):
    """The IR as text, whether the seed wrote CCE or a native wrote plain."""
    raw = path.read_bytes()
    if raw[:8].lstrip().startswith(b'(chapter'):
        return raw.decode('utf-8', 'replace')
    return cce.decode(raw)


def source_defs(path):
    """{chapter: [definition name, ...]} in bundle order."""
    out, chapter = {}, '(before any chapter header)'
    for line in path.read_text(errors='replace').splitlines():
        m = CHAPTER_RE.match(line)
        if m:
            chapter = m.group(1)
            out.setdefault(chapter, [])
            continue
        m = SIGNATURE_RE.match(line)
        if m:
            out.setdefault(chapter, []).append(m.group(1))
    return out


def main():
    unit = sys.argv[1] if len(sys.argv) > 1 else 'ir_to_x86'
    ast = LADDER / 'src'
    subject, ir = ast / f'{unit}-subject.codex', ast / f'{unit}.ir'
    for p in (subject, ir):
        if not p.is_file():
            raise SystemExit(f'bundle_reach: no {p.name}. Run the unit\'s truth '
                             'arm first -- this reads what a rung leaves behind '
                             'and produces nothing of its own.')

    by_chapter = source_defs(subject)
    src_names = {n for ns in by_chapter.values() for n in ns}
    kept = set(IRDEF_RE.findall(ir_text(ir)))

    unattributed = sorted(kept - src_names)
    print(f'{unit}: {subject.stat().st_size:,} bytes of source, '
          f'{ir.stat().st_size:,} bytes of IR')
    print(f'  chapters bundled        {len(by_chapter)}')
    print(f'  definitions in source   {len(src_names)}')
    print(f'  definitions in the IR   {len(kept)}')
    print(f'  IR names not in source  {len(unattributed)}'
          + ('   <- renames; per-chapter figures are unsafe while this is large'
             if len(unattributed) > len(kept) // 20 else '   (small: matching holds)'))

    rows = []
    for chapter, names in by_chapter.items():
        if not names:
            continue
        alive = sum(1 for n in names if n in kept)
        rows.append((alive, len(names), chapter))
    dead = [r for r in rows if r[0] == 0]
    rows.sort(key=lambda r: (r[0] / r[1], -r[1]))

    print(f'\n  chapters contributing NOTHING to the IR: {len(dead)} of {len(rows)}')
    for _, total, chapter in sorted(dead, key=lambda r: -r[1])[:20]:
        print(f'    {total:>4} defs   {chapter}')

    print('\n  least-used chapters that do contribute:')
    for alive, total, chapter in [r for r in rows if r[0]][:12]:
        print(f'    {alive:>4}/{total:<4} {100*alive//total:>3}%   {chapter}')

    src_total = sum(len(v) for v in by_chapter.values())
    print(f'\n  {len(kept)} of {src_total} definitions survive pruning '
          f'({100*len(kept)//max(src_total,1)}%).')
    print('  A source shaker saves the seed\'s front end on the dropped ones,')
    print('  and the ring the bytes of the dead CHAPTERS; it saves nothing on')
    print('  the IR, which is already pruned. Decide against these numbers.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
