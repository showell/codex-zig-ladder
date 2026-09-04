#!/usr/bin/env python3
"""Read a `codex/test/` test's answer off BARE METAL, to settle its .expected.

    ./bare_expected.py <stem> [<stem> ...]

A stem is a bare name, not a path: every one of the 1086 tests under
`codex/test/*/` has a unique stem, so the directory is derivable and asking for
it would be asking for something already known. `ops/` was the only directory
this could reach until 2026-08-30; `forewords/` holds 316 tests and the library
findings need it.

An `.expected` in the depot is a claim about what the SEED prints. Writing one
from what the zig arm prints, or from what the instruction set documents, is a
guess that looks exactly like a reading -- so this compiles the test with the
seed under QEMU and runs the result, which is the only thing that can answer.

PASS A CONTROL, ALWAYS, and put it first. A rig that emits plausible output is
indistinguishable from a correct one, and a NEW test's .expected has nothing to
check the rig against -- that is what makes it a claim in the first place. A
control is any test in the same family whose .expected is already the depot's:
if this reproduces that byte-for-byte the rig is proven on the spot, and if it
does not, the new answer means nothing and you learn it here instead of in a
PR. `real-saturating-finite` served for the real conversions.

Two guests per test, about fifteen seconds each: ring_compile turns the
cite-resolved unit into a .cdx, and codex_vm.run_cdx boots it.
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
import codex_vm, ring_compile, tier_run
from ladder_root import CODEX, LADDER

stems = sys.argv[1:]
if not stems:
    raise SystemExit(__doc__.strip().splitlines()[2].strip())

work = LADDER / 'src'
bad = 0
for stem in stems:
    found = sorted((CODEX / 'codex' / 'test').glob(f'*/{stem}.codex'))
    if not found:
        print(f'{stem}: no codex/test/*/{stem}.codex'); bad = 1; continue
    if len(found) > 1:
        # Stems are unique today. If that ever stops being true, say so rather
        # than picking one -- the wrong test settling an .expected is silent.
        print(f'{stem}: AMBIGUOUS, {len(found)} matches: '
              + ', '.join(str(f.relative_to(CODEX)) for f in found)); bad = 1; continue
    src = found[0]
    print(f'\n######## {stem}  ({src.parent.name}/, {src.stat().st_size} bytes)', flush=True)
    unit = tier_run.resolved_unit(src)
    blob = work / f'bm-{stem}.blob'
    blob.write_bytes(b'CDX map\n' + unit.encode() + b'\x04')
    cdx = work / f'bm-{stem}.cdx'
    if not ring_compile.compile_ring(str(blob), str(cdx)):
        print('  SEED COMPILE FAILED'); bad = 1; continue
    out = codex_vm.run_cdx(str(cdx))
    # The guest narrates its own state on the same channel as the program.
    lines = [l for l in out.decode('utf-8', 'replace').splitlines()
             if not l.startswith(('WD:', 'HEAP:', 'STACK:'))]
    got = '\n'.join(lines) + '\n'
    (work / f'bm-{stem}.out').write_text(got)
    exp = src.with_suffix('.expected')
    if exp.is_file():
        want = exp.read_text()
        if got == want:
            print(f'  MATCHES {exp.name} ({len(lines)} lines)')
        else:
            bad = 1
            print(f'  DIFFERS FROM {exp.name}')
            import difflib
            for d in difflib.unified_diff(want.splitlines(), lines, 'expected', 'bare-metal', lineterm=''):
                print('   ', d)
    else:
        print(f'  no {exp.name}; bare metal says:')
        for l in lines:
            print('   ', l)
sys.exit(bad)
