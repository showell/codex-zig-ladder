#!/usr/bin/env python3
"""Check what a bundle assembled, before anything compiles it.

Two of the three Update 46 failures were visible in the bundled subject text and
cost a compile to find anyway: `scope` failed four minutes into a sweep and
`ir_to_x86` twenty-five. Bundling is cheap and needs no QEMU, so the cheap questions
should be asked at bundling time.

The check here is the double-include, which is the one this ladder has actually
been bitten by, twice. A plug bundle acquires chapters through two doors that do
not know about each other:

  Add-PlugChapter        the file list in bundle_<m>.ps1, renamed to
                         `<Quire>--<name>` under the quire it was added to
  Resolve-PlugForewords  every `cites <Quire> chapter <Name>` found in what was
                         bundled, resolved through build/quire-map.ps1 and
                         prepended under the quire the CITE named

Each de-duplicates within itself and neither checks the other, so naming a file
AND citing it puts the chapter in twice under two names. `CCE` did that and
Update 46's CDX3001 made it fatal; `ListUtils` did it in eleven bundles and
produced 108-plus warnings a sweep for months.

The rule is precise, which is what makes it worth automating: the same chapter
NAME under two different QUIRES. Same-quire repeats are legitimate and common --
several X86_64*.codex files all declare `Chapter: X86-64 Code Generator` -- so
comparing quires rather than names is what keeps this free of false positives.
"""

import collections
import pathlib
import re
import sys

from ladder_root import CODEX, LADDER

CHAPTER = re.compile(r'^Chapter:\s*(?:([^-\n]+(?:-[^-\n]+)*)--)?(.+?)\s*$', re.M)


def check(subject):
    """Chapter names appearing under more than one quire in one unit."""
    seen = collections.defaultdict(set)
    for quire, name in CHAPTER.findall(subject.read_text(errors='replace')):
        seen[name].add(quire or '<no quire>')
    return {n: q for n, q in seen.items() if len(q) > 1}


def newest_input(ast, m):
    """(mtime, path) of the newest thing m's subject is built from.

    The path comes back with the time because "stale" without a witness is a
    line nobody can act on: the answer to "stale against what" is the whole
    content of the report.

    A bundled subject older than the scripts that produce it describes a bundle
    nobody would build today. Reporting on one is reporting history as if it
    were current: the first run of this check flagged `zigc`, whose artifact
    predated the ListUtils fix by two days. Same discipline as bank_truth's
    refusal to bank a mixed set.

    The set is per subject and not a global max, which is a correction. A global
    max meant editing the ad-hoc `bundle_min.ps1` -- a bisect tool no rung goes
    near -- reported all sixteen other subjects stale at once. A staleness
    warning that fires on subjects nothing touched is the cry-wolf this file
    exists to avoid, so the walk follows delegation: `bundle_passes_to_x86.ps1`
    invokes `bundle_ir_to_x86.ps1`, so its stubs count for both, and the depot's
    plug-build-lib.ps1 counts for every subject because every bundle is built
    through it.
    """
    top = ast / f'bundle_{m}.ps1'
    scripts, seen, inputs = [top], set(), []
    while scripts:
        p = scripts.pop()
        if p in seen or not p.is_file():
            continue
        seen.add(p)
        inputs.append(p)
        text = p.read_text(errors='replace')
        for name in re.findall(r'bundle_(\w+)\.ps1', text):
            scripts.append(ast / f'bundle_{name}.ps1')
        # A DELEGATED bundler's parameter defaults are not this subject's
        # inputs. bundle_passes_to_x86.ps1 calls bundle_ir_to_x86.ps1 with -Harness
        # 'WholeHarness.codex', overriding `[string]$Harness =
        # 'IrToX86Harness.codex'`, a file the passes_to_x86 bundle never opens.
        # Counting it reported passes_to_x86 stale every time ir_to_x86's harness was regenerated:
        # the cry-wolf this walk was narrowed to avoid, reintroduced by
        # widening it. The top script's defaults DO count -- that is where the
        # ir_to_x86 unit names its own harness.
        if p != top:
            text = '\n'.join(l for l in text.splitlines()
                             if not re.match(r'\s*\[[\w\[\]]+\]\$\w+\s*=', l))
        # The generated harnesses and stubs a bundler names are inputs too, and
        # they are the ladder's own files rather than the depot's, so they move
        # whenever we change a rung. Only the ones in ast/ count: a bundler also
        # names thirty compiler chapters, and treating those as inputs would
        # report every subject stale whenever a checkout touched their mtimes.
        inputs += [ast / name for name in re.findall(r'(\w+\.codex)', text)]
    inputs.append(CODEX / 'codex' / 'plugs' / 'common' / 'plug-build-lib.ps1')
    return max(((p.stat().st_mtime, p) for p in inputs if p.is_file()),
               default=(0, None))


def main():
    ast = LADDER / 'ast'
    names = sys.argv[1:] or sorted(
        p.name[:-len('-subject.codex')] for p in ast.glob('*-subject.codex'))

    bad, stale, checked, absent = 0, 0, 0, 0
    for m in names:
        subject = ast / f'{m}-subject.codex'
        if not subject.is_file():
            print(f'{m:10s} no bundled subject; run bundle_{m}.ps1')
            absent += 1
            continue
        newest, witness = newest_input(ast, m)
        if subject.stat().st_mtime < newest:
            print(f'{m:10s} STALE -- {witness.name} has changed since it was '
                  f'bundled; rebundle before trusting this')
            stale += 1
            continue
        dupes = check(subject)
        if dupes:
            bad += 1
            print(f'{m:10s} DOUBLE-INCLUDED:')
            for name, quires in sorted(dupes.items()):
                print(f'           {name!r} under {sorted(quires)}')
                print(f'           drop it from bundle_{m}.ps1 if a cite already '
                      f'pulls it in, or keep it if the explicit copy is the only one')
        else:
            print(f'{m:10s} ok')
            checked += 1

    if bad:
        print(f'\n{bad} bundle(s) carry a chapter twice. Check each bundled subject '
              f'rather than deleting every explicit listing: parse, desugar and irmem '
              f'name ListUtils and are RIGHT to, because nothing there cites it.')
    # Stale and absent are failures, not asides. Skipping a subject and then
    # printing OK is a positive claim about bundles nobody opened, which is the
    # shape of green this file exists to refuse -- and it was in this file.
    if stale:
        print(f'\n{stale} bundled subject(s) are stale and were NOT checked. They '
              f'are regenerable: run the bundle script, or a rung that does.')
    if absent:
        print(f'\n{absent} named subject(s) have no bundled file at all.')
    if bad or stale or absent:
        return 1
    if not checked:
        print('\nnothing to check: no bundled subjects found')
        return 1
    print(f'\nOK: no chapter appears under two quires in any of {checked} bundles')
    return 0


if __name__ == '__main__':
    sys.exit(main())
