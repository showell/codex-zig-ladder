#!/usr/bin/env python3
"""Run one small Codex program on BOTH arms and diff the two columns.

The tier files (`findings/prim-*.codex`) are written so that every line is
either relational -- printing yes or no -- or a small integer whose expected
value can be worked out on paper. So the interesting output is not either
column on its own, it is which lines DISAGREE. This script produces that.

    ./tier_run.py findings/prim-text.codex

Two arms, neither involving a ladder rung:

  bare metal   cite-resolve, wrap as a `CDX map` blob, compile with the u48
               seed under QEMU via ring_compile, run the .cdx. ~4s+ per
               program. This is the ORACLE: it is upstream's own compiler
               answering, with no plug in the path.

  zig          cite-resolve, `native/codexir` for the IR, `native/zigemit`
               for the .zig, `zig run`. Seconds, no QEMU. This is the plug
               under test, through the real natives -- never a hand-patched
               artifact.

Both emitted programs print to stderr, because `print-text` is
`std.debug.print` in the emitted runtime and the bare-metal console lands
there too; that is a wart the plug should fix, not a design.

One command, so that which natives ran and which seed answered are properties
of the script rather than of whoever typed the pipeline that day.
"""

import argparse
import hashlib
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from cite_resolve import resolve
from ladder_root import LADDER

CODEXIR = LADDER / 'native' / 'codexir'
ZIGEMIT = LADDER / 'native' / 'zigemit'

# @compileError texts that are prelude preconditions rather than plug
# refusals; the file says which and why. Shared with native_build.sh.
PRELUDE_GUARDS = [
    ln.strip()
    for ln in (LADDER / 'findings' / 'prelude-comptime-guards.txt')
    .read_text().splitlines()
    if ln.strip() and not ln.startswith('#')
]


def resolved_unit(src):
    """The program with its cites inlined. codexir resolves nothing, so
    without this a call into a cited chapter arrives as an undefined name and
    the plug's fallback fires -- which looks exactly like an emitter gap."""
    unit, missing = resolve(src)
    if missing:
        raise SystemExit('unresolved cites: ' + '; '.join(
            f'{q} chapter {n}' for _, q, n in missing))
    return unit


def run_zig(src, work):
    unit = resolved_unit(src)
    ir = subprocess.run([str(CODEXIR)], input=unit.encode(),
                        capture_output=True, timeout=300)
    if ir.returncode != 0 or not ir.stderr:
        raise SystemExit(f'codexir failed: rc={ir.returncode}\n'
                         f'{ir.stdout.decode(errors="replace")[-2000:]}')
    (work / f'{src.stem}.ir').write_bytes(ir.stderr)

    zg = subprocess.run([str(ZIGEMIT)], input=ir.stderr,
                        capture_output=True, timeout=300)
    if zg.returncode != 0 or not zg.stderr:
        raise SystemExit(f'zigemit failed: rc={zg.returncode}')
    zig_path = work / f'{src.stem}.zig'
    zig_path.write_bytes(zg.stderr)

    text = zg.stderr.decode('utf-8', 'replace')
    if '@compileError' in text:
        # Report them rather than letting `zig run` bury one in a wall of
        # notes: an emitter gap here means the tier is untestable on this arm,
        # which is a different answer from a red line.
        #
        # Prelude preconditions are not gaps, and reporting them is worse
        # than useless: one of them printed on EVERY run from the day it
        # landed, which is how a real gap would go unread. Same list the
        # native build's blocking scan uses, so the two cannot drift.
        for line in text.splitlines():
            if '@compileError' in line and not any(g in line for g in PRELUDE_GUARDS):
                print('  gap:', line.strip(), file=sys.stderr)

    out = subprocess.run(['zig', 'run', str(zig_path)],
                         capture_output=True, timeout=900, cwd=work)
    if out.returncode != 0 and not out.stderr:
        raise SystemExit(f'zig run failed: rc={out.returncode}')
    return out.stderr.decode('utf-8', 'replace').splitlines()


def gold_path(src):
    return src.parent / 'gold' / f'{src.stem}.txt'


def gold_key(src):
    """What the bare-metal column depends on, and nothing else: the program's
    own text and the seed that compiles it. The plug is not in that list --
    bare metal is the oracle precisely because no plug is in its path -- so a
    banked column stays valid across every emitter change, which is the whole
    point of banking it. A seed re-pin invalidates every column at once."""
    import seed_identity
    return hashlib.sha256(
        src.read_bytes() + seed_identity.seed_sha256().encode()).hexdigest()[:16]


def run_bare(src, work):
    """QEMU, unless the identical program has already been run against the
    identical seed, in which case the banked column is the same bytes for
    four fewer minutes."""
    gold = gold_path(src)
    key = gold_key(src)
    if gold.is_file():
        head, _, body = gold.read_text().partition('\n')
        if head == f'# key {key}':
            print(f'bare metal: banked at {gold}', file=sys.stderr)
            return body.splitlines()
        print(f'bare metal: banked column is stale, re-running', file=sys.stderr)

    import codex_vm
    import ring_compile

    unit = resolved_unit(src)
    blob = work / f'{src.stem}.blob'
    blob.write_bytes(b'CDX map\n' + unit.encode() + b'\x04')
    cdx = work / f'{src.stem}.cdx'
    if not ring_compile.compile_ring(str(blob), str(cdx)):
        raise SystemExit('seed compile failed')
    out = codex_vm.run_cdx(str(cdx))
    lines = out.decode('utf-8', 'replace').splitlines()
    # The guest narrates its own state on the same channel as the program.
    lines = [l for l in lines if not l.startswith(('WD:', 'HEAP:', 'STACK:'))]

    gold.parent.mkdir(parents=True, exist_ok=True)
    gold.write_text(f'# key {key}\n' + '\n'.join(lines) + '\n')
    print(f'bare metal: banked to {gold}', file=sys.stderr)
    return lines


def report(bare, zig):
    """Side by side, with a marker on every line that moved. Lines are
    matched by index, not by content: these programs print a fixed sequence,
    so an index mismatch IS the finding."""
    n = max(len(bare), len(zig))
    width = max([len(l) for l in bare] or [0]) + 2
    reds = 0
    for i in range(n):
        b = bare[i] if i < len(bare) else '<no line>'
        z = zig[i] if i < len(zig) else '<no line>'
        same = b == z
        reds += not same
        print(f'{"  " if same else "!!"} {b:<{width}} | {z}')
    print()
    print(f'{n} lines, {reds} differ' if reds else f'{n} lines, byte-identical')
    return reds


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('program', type=pathlib.Path)
    ap.add_argument('--zig', action='store_true', help='zig arm only')
    ap.add_argument('--bare', action='store_true', help='bare-metal arm only')
    ap.add_argument('--work', type=pathlib.Path,
                    help='where artifacts land (default: beside the program)')
    a = ap.parse_args()

    src = a.program.resolve()
    work = (a.work or src.parent / '.tier-run').resolve()
    work.mkdir(parents=True, exist_ok=True)

    both = not (a.zig or a.bare)
    bare = run_bare(src, work) if (both or a.bare) else None
    zig = run_zig(src, work) if (both or a.zig) else None

    if bare is not None and zig is not None:
        sys.exit(1 if report(bare, zig) else 0)
    for line in (bare if bare is not None else zig):
        print(line)


if __name__ == '__main__':
    main()
