#!/usr/bin/env python3
"""Grade the prelude-last plug change against the whole corpus, without the plug.

The change (`prelude-last`, d9d68889) claims to be INERT: it moves `zig-prelude`
from the top of every emitted file to the bottom, behind a banner, on the
grounds that zig does not order declarations at container scope. The commit
verified that by hand-editing ONE emitted file. One file is a demonstration,
not a measurement -- the corpus is 589 emitted programs, and the question
"does zig care where the prelude sits" is exactly the kind of question a
corpus answers and a sample does not.

Running the changed plug over the corpus would cost two native builds (to A/B
at one base) plus two transpiles. This does not need any of that, because the
change is a pure text reordering and the reordering can be done here:

  1. TRANSFORM   move the prelude below the program and insert the banner,
                 mechanically, on an already-emitted .zig.
  2. CALIBRATE   prove that transform is what the plug does, byte for byte,
                 against a real before/after pair of plug output taken from
                 the codex-zig-transpiler repository's own history (the
                 `arith` sample, emitted at 8595322 and again at daf36cf).
                 If the transform reproduces the plug's file exactly, then
                 running it over the corpus IS running the changed plug over
                 the corpus, for the purpose of this question.
  3. GRADE       compile both variants of all 589 and compare, then run both
                 and compare stdout, stderr and exit status byte for byte.

Step 2 is the load-bearing one. Without it this grades a transform nobody
asked about; with it, every row is a statement about the plug.

Two things about step 3 are the instrument and not the subject, and both were
found by tripping over them. Zig qualifies type names in a diagnostic with the
file's BASENAME, so the two variants must be written into separate directories
under the SAME name or every type error reads as a difference. And a panic
backtrace names source positions, which the move shifts by construction, so a
run whose output is not byte-identical gets a second comparison with source
positions and monomorphisation counters normalised -- reported as its own
bucket, never folded into the identical one.

The noun this is an instance of -- an emitter change that rewrites every byte
of every emitted file, graded by asking whether the corpus still behaves
identically -- is about to have a second instance: tree-shaking the prelude
will need exactly this, with a different function at step 1.
"""

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from cite_resolve import resolve
from ladder_root import CODEX, LADDER

CORPUS = LADDER / 'corpus'
AST = LADDER / 'ast'
TESTS = CODEX / 'codex' / 'test'

# The three emitted programs in ast/ that carry the prelude. They are the
# compiler itself, transpiled through this plug, and they are 50x larger than
# anything in the corpus -- 4.6 MB against a 42 KB median -- so they exercise
# name resolution at a scale no corpus program reaches. f3_run.zig is hand
# written and carries no prelude, which is why it is not here.
AST_SUBJECTS = ('zigemit', 'codexir', 'codexzig')

# Each native reads its input on stdin and writes its answer on stderr. The
# input is produced ONCE, by the banked natives, and handed to both variants,
# so a difference in the output is a difference between the two builds and
# nothing else.
DRIVE_SUBJECT = 'sort-test'
TRANSPILER = pathlib.Path.home() / 'showell_repos' / 'codex-zig-transpiler'
BEFORE_REV, AFTER_REV = '8595322', 'daf36cf'
SAMPLE = 'generated/arith.zig'

# The last prelude declaration. Everything from the top of an emitted file
# through this function's closing brace is the fixed block.
PRELUDE_TAIL = 'fn cx_print(s: []const u8) void {'


def split_prelude(text):
    """(prelude, program) for a prelude-first emitted file."""
    k = text.index(PRELUDE_TAIL)
    end = text.index('\n}\n', k) + 3
    while text[end] == '\n':
        end += 1
    return text[:end], text[end:]


def to_postlude(text, banner):
    prelude, program = split_prelude(text)
    return program + banner + prelude


def read_banner():
    """The banner, lifted out of the plug's own output rather than retyped."""
    after = subprocess.run(['git', 'show', f'{AFTER_REV}:{SAMPLE}'], cwd=TRANSPILER,
                           capture_output=True, text=True, check=True).stdout
    return after[after.index('\n// ===='):after.index('const std = @import("std");')]


def calibrate(banner):
    """Step 2. The transform must reproduce real plug output byte for byte."""
    def show(rev):
        return subprocess.run(['git', 'show', f'{rev}:{SAMPLE}'], cwd=TRANSPILER,
                              capture_output=True, text=True, check=True).stdout
    before, after = show(BEFORE_REV), show(AFTER_REV)
    got = to_postlude(before, banner)
    ok = got == after
    print(f'CALIBRATION against real plug output ({SAMPLE}, {BEFORE_REV} -> {AFTER_REV})')
    print(f'  before {len(before)}  after {len(after)}  delta {len(after)-len(before)}'
          f'  banner {len(banner)}')
    print(f'  transform reproduces the plug byte for byte: {"YES" if ok else "NO"}')
    if not ok:
        for i in range(min(len(got), len(after))):
            if got[i] != after[i]:
                print(f'  first difference at {i}:\n    got   {got[i-70:i+70]!r}\n'
                      f'    plug  {after[i-70:i+70]!r}')
                break
    return ok


# What the move is ALLOWED to change in a program's output: where in the file
# a frame sits, and the counter zig appends to a monomorphised name (which
# follows declaration order). Nothing else.
POSITION = re.compile(rb'(\.zig):\d+:\d+')
ANON = re.compile(rb'__anon_\d+')
THREAD = re.compile(rb'thread \d+ panic')


def normalise(out):
    if not isinstance(out, tuple):
        return out
    rc, so, se = out
    f = lambda b: THREAD.sub(b'thread N panic', ANON.sub(b'__anon_N', POSITION.sub(rb'\1:L:C', b)))
    return rc, f(so), f(se)


def build_and_run(src, workdir, tag):
    """(build_ok, diagnostics, run_result) -- run only if the build succeeded."""
    exe = workdir / f'exe-{tag}'
    b = subprocess.run(['zig', 'build-exe', '-femit-bin=' + str(exe), str(src),
                        '--cache-dir', str(workdir / ('cache-' + tag))],
                       capture_output=True, text=True)
    diag = (b.stderr + b.stdout).replace(str(src), '<src>').replace(str(workdir), '<work>')
    if b.returncode != 0:
        return False, diag, None
    try:
        r = subprocess.run([str(exe)], capture_output=True, timeout=60)
        run = (r.returncode, r.stdout, r.stderr)
    except subprocess.TimeoutExpired as t:
        run = ('timeout', t.stdout or b'', t.stderr or b'')
    exe.unlink(missing_ok=True)
    return True, diag, run


def ast_inputs():
    """stdin for each ast subject: the same bytes go to both variants."""
    src = TESTS / f'{DRIVE_SUBJECT}.codex'
    unit, missing = resolve(src)
    if missing:
        raise SystemExit(f'{DRIVE_SUBJECT}: unresolved cites, pick another subject')
    ir = subprocess.run([str(LADDER / 'native' / 'codexir')], input=unit.encode(),
                        capture_output=True, timeout=300)
    if ir.returncode != 0 or not ir.stderr:
        raise SystemExit(f'{DRIVE_SUBJECT}: the banked codexir would not produce IR')
    return {'codexir': unit.encode(), 'codexzig': unit.encode(), 'zigemit': ir.stderr}


def grade_ast(banner):
    """The compiler itself, both ways: built, then driven with real input."""
    print(f'\nGRADING the {len(AST_SUBJECTS)} emitted programs in ast/ -- the compiler '
          f'transpiled through this plug\n')
    feed = ast_inputs()
    problems = []
    with tempfile.TemporaryDirectory(prefix='postlude-ast-') as td:
        work = pathlib.Path(td)
        (work / 'a').mkdir(); (work / 'b').mkdir()
        for name in AST_SUBJECTS:
            src = AST / f'{name}.zig'
            text = src.read_text()
            a_src, b_src = work / 'a' / f'{name}.zig', work / 'b' / f'{name}.zig'
            a_src.write_text(text)
            b_src.write_text(to_postlude(text, banner))
            row = [f'  {name:9s} {len(text):>9,} bytes']
            outs = {}
            for tag, path in (('a', a_src), ('b', b_src)):
                exe = work / f'exe-{name}.{tag}'
                b = subprocess.run(['zig', 'build-exe', '-femit-bin=' + str(exe), str(path),
                                    '--cache-dir', str(work / f'cache-{tag}')],
                                   capture_output=True, text=True)
                if b.returncode != 0:
                    outs[tag] = ('BUILD FAILED', (b.stderr + b.stdout)[-400:])
                    continue
                r = subprocess.run([str(exe)], input=feed[name], capture_output=True, timeout=600)
                outs[tag] = ('ran', (r.returncode, r.stdout, r.stderr))
                exe.unlink(missing_ok=True)
            a_src.unlink(); b_src.unlink()
            (ka, va), (kb, vb) = outs['a'], outs['b']
            if ka != kb:
                row.append(f'  DISAGREES: prelude-first {ka}, prelude-last {kb}')
                problems.append((name, f'{ka} vs {kb}'))
            elif ka == 'BUILD FAILED':
                row.append('  both REFUSED by zig (identically)' if va == vb
                           else '  both refused, DIFFERENT diagnostics')
                if va != vb:
                    problems.append((name, 'refusal diagnostics differ'))
            else:
                same = va == vb
                verdict = ('YES' if same else
                           'only where the file says a frame is'
                           if normalise(va) == normalise(vb) else 'NO')
                row.append(f'  built both ways; exit {va[0]}, '
                           f'{len(va[2]):,} bytes on stderr; '
                           f'output byte-identical: {verdict}')
                if verdict == 'NO':
                    problems.append((name, 'output differs'))
            print(''.join(row))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='first N programs only')
    args = ap.parse_args()

    banner = read_banner()
    if not calibrate(banner):
        print('\nSTOP: the transform is not what the plug does. Nothing below would mean anything.')
        return 1

    srcs = sorted(CORPUS.glob('*.zig'))
    if args.limit:
        srcs = srcs[:args.limit]
    print(f'\nGRADING {len(srcs)} emitted programs, prelude-first vs prelude-last\n')

    same_build = same_diag = same_run = moved_only = 0
    built = ran = 0
    problems = []
    with tempfile.TemporaryDirectory(prefix='postlude-') as td:
        work = pathlib.Path(td)
        (work / 'a').mkdir(); (work / 'b').mkdir()
        for n, src in enumerate(srcs, 1):
            text = src.read_text()
            if PRELUDE_TAIL not in text:
                problems.append((src.name, 'no prelude found')); continue
            # Same basename, different directory: zig puts the basename into
            # every type it names in a diagnostic.
            a_src, b_src = work / 'a' / src.name, work / 'b' / src.name
            a_src.write_text(text)
            b_src.write_text(to_postlude(text, banner))

            ok_a, diag_a, run_a = build_and_run(a_src, work, 'a')
            ok_b, diag_b, run_b = build_and_run(b_src, work, 'b')
            a_src.unlink(); b_src.unlink()

            if ok_a != ok_b:
                problems.append((src.name, f'build disagrees: before={ok_a} after={ok_b}')); continue
            same_build += 1
            if ok_a:
                built += 1
            # diagnostics carry line numbers, which the move is expected to shift;
            # compare the message text only.
            msgs_a = sorted(l.split(':', 3)[-1] for l in diag_a.splitlines() if 'error:' in l)
            msgs_b = sorted(l.split(':', 3)[-1] for l in diag_b.splitlines() if 'error:' in l)
            if msgs_a == msgs_b:
                same_diag += 1
            else:
                problems.append((src.name, f'diagnostics differ:\n      {msgs_a}\n      {msgs_b}'))
                continue
            if run_a is not None:
                ran += 1
                if run_a == run_b:
                    same_run += 1
                elif normalise(run_a) == normalise(run_b):
                    moved_only += 1
                else:
                    problems.append((src.name, f'behaviour differs: {run_a[0]!r} vs {run_b[0]!r}'))
            if n % 25 == 0:
                print(f'  {n}/{len(srcs)}  built {built}  ran {ran}  identical {same_run}')

    print(f'\n{"="*66}')
    print(f'  programs graded          {len(srcs)}')
    print(f'  build outcome agrees     {same_build}')
    print(f'  of which built           {built}')
    print(f'  zig diagnostics agree    {same_diag}')
    print(f'  ran both ways            {ran}')
    print(f'  output byte-identical    {same_run}')
    print(f'  identical but for source positions in a panic backtrace  {moved_only}')
    print(f'  disagreements            {len(problems)}')
    if srcs and not built:
        print('\n  REFUSED: nothing built on either side, so every agreement above is '
              'vacuous.\n  A run that grades no program is a broken instrument, not a pass.')
        for name, why in problems[:3]:
            print(f'    {name}: {why}')
        return 3
    for name, why in problems:
        print(f'    {name}: {why}')

    problems += grade_ast(banner)
    return 0 if not problems else 2


if __name__ == '__main__':
    sys.exit(main())
