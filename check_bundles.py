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
import os
import pathlib
import re
import subprocess
import sys

from ladder_root import CODEX, LADDER

# `xref bundle` answers "what does this bundle read that it does not define"
# from the bundled text, in about four seconds and with no guest. It is NAMED
# rather than guessed, the same rule $CODEX_GOLDS follows, and a missing binary
# says so rather than skipping quietly -- a check that silently does not run is
# the failure mode this whole file exists to close.
XREF = pathlib.Path(os.environ.get(
    'CODEX_XREF',
    pathlib.Path.home() / 'showell_repos' / 'rust-codex-compiler' /
    'target' / 'release' / 'xref'))

CHAPTER = re.compile(r'^Chapter:\s*(?:([^-\n]+(?:-[^-\n]+)*)--)?(.+?)\s*$', re.M)


def check(subject):
    """Chapter names appearing under more than one quire in one unit."""
    seen = collections.defaultdict(set)
    for quire, name in CHAPTER.findall(subject.read_text(errors='replace')):
        seen[name].add(quire or '<no quire>')
    return {n: q for n, q in seen.items() if len(q) > 1}


def missing_cites(subject):
    """Names the bundle uses and no chapter in it defines.

    Bundling is cheap and a guest is not: finding the driver's chapter list by
    compiling cost three guests and about nine minutes on 2026-09-03, and every
    one of those failures was visible in the bundled text. This asks the same
    question in four seconds.

    It answers NAMES, not types -- a bundle this calls complete can still fail
    on a shape, so a green line here is not a promise that the compile passes.
    """
    if not XREF.is_file():
        return None, (f'no xref at {XREF}; set CODEX_XREF or build '
                      'rust-codex-compiler (missing-cite check NOT run)')
    r = subprocess.run([str(XREF), 'bundle', str(subject), str(CODEX / 'codex')],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return [], None
    if r.returncode != 1:
        return None, f'xref bundle failed: {(r.stderr or r.stdout).strip()[:200]}'
    return [l for l in r.stdout.splitlines() if l.strip()], None


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



# THE PLUG BUNDLES ARE NOT `ast/<m>-subject.codex` AND SO WERE NEVER CHECKED.
# That is the gap this file existed to close and did not: on 2026-09-03 the
# emitter became four files, the ladder's bundlers still named one, and the
# plug bundle went to a guest missing three chapters. It came back 23 seconds
# of QEMU later as 17 x CDX3002, and the sweep died 398 seconds in. `xref
# bundle` answers it from the text in milliseconds AND names the remedy:
#
#     ADD zig/ZigEmitterExpressions.codex
#           emit-zig-expr
#
# Their staleness witness is the plug source itself, not a bundle_<m>.ps1
# walk, because these are built by cycle.sh and ringplug_build.sh.
def plug_bundles():
    out = []
    tcp = CODEX / 'codex' / 'plugs' / 'zig' / 'build-output' / 'plug-source.codex'
    if tcp.is_file():
        out.append(('zig-plug', tcp))
    ring = LADDER / 'ast' / 'ringplug-source.codex'
    if ring.is_file():
        out.append(('ringplug', ring))
    return out


def plug_inputs():
    """Everything a zig plug bundle is assembled from, for the mtime check."""
    d = CODEX / 'codex' / 'plugs' / 'zig'
    ins = sorted(d.glob('*.codex'))
    for extra in (CODEX / 'codex' / 'plugs' / 'common' / 'plug-build-lib.ps1',
                  LADDER / 'zig_plug_pages.txt'):
        if extra.is_file():
            ins.append(extra)
    return ins


def main():
    ast = LADDER / 'ast'
    # An explicit argument list selects from BOTH families -- the ast/ rung
    # subjects and the plug bundles. cycle.sh passes `zig-plug` because it has
    # just built that one and nothing else; treating the name as a missing rung
    # subject would have made it fail for the wrong reason.
    wanted = set(sys.argv[1:])
    plugs = [(l, s) for l, s in plug_bundles() if not wanted or l in wanted]
    names = sorted(
        p.name[:-len('-subject.codex')] for p in ast.glob('*-subject.codex'))
    if wanted:
        names = [m for m in names if m in wanted]
        unknown = wanted - set(names) - {l for l, _ in plugs}
        if unknown:
            print(f'no such bundle: {", ".join(sorted(unknown))}')
            return 2

    bad, stale, checked, absent = 0, 0, 0, 0
    # A double-include and a short bundle are different failures with
    # different remedies, and one counter made the summary say the wrong
    # one out loud.
    short = 0
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
            gaps, why = missing_cites(subject)
            if why is not None:
                bad += 1
                print(f'{m:10s} CANNOT CHECK CITES -- {why}')
            elif gaps:
                short += 1
                print(f'{m:10s} MISSING CITES:')
                for line in gaps[2:]:
                    print(f'      {line}')
            else:
                print(f'{m:10s} ok')
            checked += 1

    # The plug bundles, through the same two questions.
    for label, subject in plugs:
        ins = plug_inputs()
        newest = max((f.stat().st_mtime for f in ins), default=0)
        witness = max(ins, key=lambda f: f.stat().st_mtime) if ins else None
        if subject.stat().st_mtime < newest:
            print(f'{label:10s} STALE -- {witness.name} has changed since it was '
                  f'bundled; rebundle before trusting this')
            stale += 1
            continue
        dupes = check(subject)
        if dupes:
            bad += 1
            print(f'{label:10s} DOUBLE-INCLUDED:')
            for name, quires in sorted(dupes.items()):
                print(f'           {name!r} under {sorted(quires)}')
            continue
        gaps, why = missing_cites(subject)
        if why is not None:
            bad += 1
            print(f'{label:10s} CANNOT CHECK CITES -- {why}')
        elif gaps:
            bad += 1
            short += 1
            print(f'{label:10s} MISSING CITES -- the bundle is short a chapter:')
            for line in gaps[2:]:
                print(f'      {line}')
        else:
            checked += 1
            print(f'{label:10s} ok')

    if bad:
        print(f'\n{bad} bundle(s) carry a chapter twice. Check each bundled subject '
              f'rather than deleting every explicit listing: parse, desugar and irmem '
              f'name ListUtils and are RIGHT to, because nothing there cites it.')
    if short:
        print(f'\n{short} bundle(s) are SHORT A CHAPTER -- they read names nothing in '
              f'them defines. Each ADD line above names the file to add to the '
              f'bundler; for the zig plug that is zig_plug_pages.txt.')
    # Stale and absent are failures, not asides. Skipping a subject and then
    # printing OK is a positive claim about bundles nobody opened, which is the
    # shape of green this file exists to refuse -- and it was in this file.
    if stale:
        print(f'\n{stale} bundled subject(s) are stale and were NOT checked. They '
              f'are regenerable: run the bundle script, or a rung that does.')
    if absent:
        print(f'\n{absent} named subject(s) have no bundled file at all.')
    if bad or short or stale or absent:
        return 1
    if not checked:
        print('\nnothing to check: no bundled subjects found')
        return 1
    print(f'\nOK: {checked} bundle(s) -- no chapter under two quires, and none reads a\n    name it does not define')
    return 0


if __name__ == '__main__':
    sys.exit(main())
