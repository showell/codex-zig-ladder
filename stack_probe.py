#!/usr/bin/env python3
"""How much thread stack does the transpiled compiler need to read a document?

Every emitted program runs its entry point on a thread the emitter sizes,
and that size is a constant in ZigEmitter (`zig-main`, 512 MB since Update
43). The number was chosen to make a symptom go away and nothing has ever
measured what it holds up, so it cannot say whether an Update made the
compiler's recursion shallower, deeper, or moved it somewhere else.

This measures it. For each document below, the emitted `codexir.zig` is
rebuilt with one constant changed -- the same one-constant methodology
JUSTIFICATIONS uses for the deck -- and run, bisecting to the smallest
stack that still compiles the document. When a size fails, the backtrace's
repeated frames are counted, so the answer is not just "24 MB dies" but
which cycle was on the stack when it did.

Two numbers per document, and the second is the one that ages well:

    min    the smallest ladder step that passes
    cycle  the functions the failing trace repeats, most frequent first

A recursion that is flattened upstream shows up as `min` collapsing. A
recursion that MOVES shows up as `min` holding while `cycle` names
different functions, which a pass/fail arm would report as no change at
all. Finding 37 is the worked example: the 512 MB stack was documented as
holding up a lexer cycle that measures flat, and what it actually holds up
is the parser's header scan, one turn per top-level definition.

Banked per Update under `findings/gold/<slug>/stack.txt`, read back on the
next run, and rewritten only with --bank: the benchmark pattern, so a
number that moves is a question rather than a surprise.

    ./stack_probe.py            measure and diff against the bank
    ./stack_probe.py --bank     measure and write the bank

Needs `ast/codexir.zig`, which `native_build.sh` leaves behind; this does
not build it, because rebuilding the natives is the expensive half and a
probe that quietly did it would hide which emitter the number belongs to.
"""

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

from ladder_root import LADDER
from seed_identity import seed_sha256, stamp

# The ladder of sizes, in MB. Bisection walks this list rather than a
# continuous range: the answer wanted is "which step do we need", and a
# step is what a reader can act on. 512 is the emitter's own constant and
# is the last step on purpose -- a document that needs more than the
# emitter grants is the finding, not a measurement error.
STEPS = [1, 2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]

# What to read, and why each one is here. Paths under the checkout are
# resolved through ladder_root; paths under the ladder are relative to it.
DOCUMENTS = {
    # The largest real document the ladder has: the whole x86-64 back end
    # bundled, 4,511 top-level definitions. This is the one that decides
    # whether the emitter's constant is enough for real work.
    'back-end-unit': ('ladder', 'ast/ir_to_x86-subject.codex'),
    # One ordinary chapter, for scale: if the big document's cost is per
    # definition, this should land many steps below it rather than near it.
    'one-chapter': ('codex', 'codex/compiler/Syntax/Lexer.codex'),
}

STACK_RE = re.compile(r'const stack_bytes: usize = [^;]+;')
FRAME_RE = re.compile(r'\bin ([A-Za-z_][A-Za-z_0-9]*) \(')
# Frames from zig's own std and from the allocator shim are not the
# program's recursion; they are wherever the stack happened to run out.
NOT_RECURSION = {'main', 'callMain', 'posixCallMainAndExit', 'start',
                 'cx_bump_alloc', 'rawAlloc', 'alloc', 'forward', 'call'}


def zig():
    found = shutil.which('zig') or str(pathlib.Path.home() / 'zig-0.16.0' / 'zig')
    if not pathlib.Path(found).is_file():
        raise SystemExit('no zig on PATH and none at ~/zig-0.16.0/zig')
    return found


def document(kind, rel):
    if kind == 'ladder':
        return LADDER / rel
    from ladder_root import CODEX
    return CODEX / rel


def build(src_text, mb, work):
    """One binary at one stack size. Returns its path."""
    patched = STACK_RE.sub(f'const stack_bytes: usize = {mb} * 1024 * 1024;', src_text, count=1)
    if patched == src_text:
        raise SystemExit('stack_probe: the stack constant did not change; '
                         'zig-main\'s shape moved and this probe is reading '
                         'the wrong line. Fix STACK_RE before trusting a number.')
    zsrc = work / f'stack{mb}.zig'
    zsrc.write_text(patched)
    out = work / f'stack{mb}'
    r = subprocess.run([zig(), 'build-exe', str(zsrc), '-femit-bin', str(out)],
                       capture_output=True, text=True, cwd=work)
    if r.returncode != 0:
        raise SystemExit(f'stack_probe: zig refused the patched source at {mb} MB:\n'
                         + r.stderr[:800])
    return out


def attempt(binary, doc, work):
    """Run one binary on one document. Returns (ok, frame census)."""
    with open(doc, 'rb') as fh:
        r = subprocess.run(
            ['systemd-run', '--user', '--scope', '-p', 'MemoryMax=6G', '--quiet',
             str(binary)],
            stdin=fh, capture_output=True, timeout=1800, cwd=work)
    if r.returncode == 0:
        return True, []
    frames = [f for f in FRAME_RE.findall(r.stderr.decode(errors='replace'))
              if f not in NOT_RECURSION]
    counts = {}
    for f in frames:
        counts[f] = counts.get(f, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
    return False, top


def bisect(src_text, doc, work):
    """Smallest step in STEPS that passes. Returns (min_mb, cliff_mb, cycle)."""
    lo, hi = 0, len(STEPS) - 1
    best, cliff, cycle = None, None, []
    # Confirm the top of the ladder passes at all before bisecting toward it;
    # a document that fails at 512 has no minimum and the bisection would
    # report the ladder's last step as if it were an answer.
    ok, top = attempt(build(src_text, STEPS[hi], work), doc, work)
    if not ok:
        return None, STEPS[hi], top
    best = STEPS[hi]
    while lo <= hi:
        mid = (lo + hi) // 2
        mb = STEPS[mid]
        ok, top = attempt(build(src_text, mb, work), doc, work)
        print(f'    {mb:>4} MB  {"ok" if ok else "died"}', flush=True)
        if ok:
            best = mb
            hi = mid - 1
        else:
            cliff, cycle = mb, top
            lo = mid + 1
    return best, cliff, cycle


def render(rows, slug):
    out = [f'# stack_probe, seed {seed_sha256()[:16]}, bank {slug}',
           '# min = smallest passing step; cliff = largest failing step below it',
           '# cycle = repeated frames in the failing trace, most frequent first']
    for name, (mb, cliff, cycle) in rows.items():
        c = ' '.join(f'{f}x{n}' for f, n in cycle) or '(none recorded)'
        out.append(f'{name}\tmin={mb}MB\tcliff={cliff}MB\tcycle={c}')
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bank', action='store_true',
                    help='write the measurement as the new gold for this seed')
    args = ap.parse_args()

    emitted = LADDER / 'ast' / 'codexir.zig'
    if not emitted.is_file():
        raise SystemExit('stack_probe: no ast/codexir.zig. Run native_build.sh '
                         'first -- this probe measures the emitter that built '
                         'it and will not build one itself.')
    src_text = emitted.read_text()

    s = stamp()
    gold_dir = LADDER / 'findings' / 'gold' / s['slug']
    gold = gold_dir / 'stack.txt'
    work = LADDER / 'ast' / '.stack-probe'
    work.mkdir(exist_ok=True)

    print(f"seed {s['sha256'][:16]}  bank {s['slug']}")
    rows = {}
    for name, (kind, rel) in DOCUMENTS.items():
        doc = document(kind, rel)
        if not doc.is_file():
            print(f'  {name}: MISSING {doc} -- skipped')
            continue
        print(f'  {name}  ({doc.stat().st_size:,} bytes)')
        rows[name] = bisect(src_text, doc, work)

    if not rows:
        raise SystemExit('stack_probe: no document was readable; nothing measured')

    text = render(rows, s['slug'])
    print('\n' + text)

    if args.bank:
        gold_dir.mkdir(parents=True, exist_ok=True)
        gold.write_text(text)
        print(f'banked {gold}')
        return 0

    if not gold.is_file():
        print(f'NO GOLD for {s["slug"]}: run with --bank to record this as the '
              'first measurement under this seed')
        return 0

    was = gold.read_text()
    if was == text:
        print('MATCHES the bank')
        return 0
    print('MOVED against the bank:')
    for a, b in zip(was.splitlines(), text.splitlines()):
        if a != b and not a.startswith('#'):
            print(f'  was {a}')
            print(f'  now {b}')
    print('\nA stack number that moves is a question: read the cycle column '
          'before the min column, because a recursion that MOVED reports the '
          'same min under different frames.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
