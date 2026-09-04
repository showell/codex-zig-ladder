#!/usr/bin/env python3
"""How much deck the hosted compiler needs, and what happens when it runs out.

Two claims in JUSTIFICATIONS ("The deck costs 145 MB per MB of source") and
one finding (45, the reservation is advisory) were measured by hand once.
This is the runner behind them, so neither is a number that was true once.

WHAT IT MEASURES. Every `src/*-subject.codex` through `native/codexzig`,
reading the `CX-DECK used=` trace the emitted runtime prints on stdout, and
byte-comparing the emitted zig against `codexir | zigemit`. The deck peak is
near-linear in source size; the reservation is 512 MB; the largest subject is
codexzig's own bundle, which is the one that will cross the line first.

WHAT IT THEN PROVES. The last step lowers the reservation in an emitted zig
-- it is a literal, `cx_heap_advance(536870912)` -- rebuilds with
`zig build-exe`, and feeds it a subject that wants more. That costs about ten
seconds and no VM, and it is the whole reproduction of finding 45: the tracer
prints negative headroom, nothing acts on it, the program reaches twice the
reservation and dies with a General protection exception in `cx_list_at`. If
that ever turns into a clean refusal, this run is what notices.

No arguments, no flags, and no guest: everything here is a native process.
`native/codexzig` and the two natives must already be built.
"""
import pathlib
import re
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
import compute_lock
import corpus_run
from ladder_root import LADDER

CODEXZIG = LADDER / 'native' / 'codexzig'
EXPECT_SUBJECTS = 14     # the rung bundlers' output; fewer means a partial tree
SQUEEZE_MB = 16          # small enough that parse-subject cannot fit
SQUEEZE_SUBJECT = 'parse-subject.codex'


def deck_peak(trace):
    used = [int(m) for m in re.findall(r'used=(\d+)', trace)]
    reserved = [int(m) for m in re.findall(r'reserved=(\d+)', trace)]
    return (max(used) if used else 0), (max(reserved) if reserved else 0)


def main():
    for t in (CODEXZIG, corpus_run.CODEXIR, corpus_run.ZIGEMIT):
        if not t.is_file():
            raise SystemExit(f'MISSING {t} -- build it first '
                             f'(codexzig_build.sh, native_build.sh)')
    compute_lock.take()
    subs = sorted((LADDER / 'src').glob('*-subject.codex'),
                  key=lambda p: p.stat().st_size)
    # A GLOB THAT MATCHES NOTHING MUST NOT PASS. The subjects are gitignored
    # build artifacts of fourteen separate bundlers, so a sandbox where only
    # codexzig_build.sh has run finds ONE and would otherwise report
    # "1/1 byte-identical" in the same happy voice as a full sweep --
    # the exact shape JUSTIFICATIONS warns about, in the file that feeds it.
    if len(subs) < EXPECT_SUBJECTS:
        print(f'### ONLY {len(subs)} of {EXPECT_SUBJECTS} unit subjects are '
              f'bundled in src/ -- refusing to report a partial sweep as a '
              f'sweep.\n    Bundle the rungs (src/ensure_ir.sh, or a full '
              f'cycle) or accept that this table is not comparable.')
        return 2
    print(f'### {len(subs)} unit subjects through codexzig')
    print(f"{'subject':<34}{'MB':>6}{'secs':>6}{'deck':>8}{'free':>7}  vs pipeline")
    rows = []
    for s in subs:
        src = s.read_bytes()
        t0 = time.time()
        one = subprocess.run([str(CODEXZIG)], input=src,
                             capture_output=True, timeout=1800)
        secs = time.time() - t0
        peak, reserved = deck_peak(one.stdout.decode('utf-8', 'replace'))
        ir = subprocess.run([str(corpus_run.CODEXIR)], input=src,
                            capture_output=True, timeout=1800)
        duo = subprocess.run([str(corpus_run.ZIGEMIT)], input=ir.stderr,
                             capture_output=True, timeout=1800)
        if not one.stderr:
            verdict = 'CODEXZIG EMITTED NOTHING'
        elif not duo.stderr:
            verdict = 'pipeline emitted nothing (codexzig did)'
        else:
            verdict = 'same' if one.stderr == duo.stderr else 'DIFFERS'
        free = f'{100 * (reserved - peak) / reserved:.0f}%' if reserved else '-'
        print(f'{s.name:<34}{len(src)/1e6:>6.2f}{secs:>5.0f}s'
              f'{peak/1e6:>7.0f}M{free:>7}  {verdict}', flush=True)
        rows.append((len(src), peak, verdict))
    per_mb = [p / (n / 1e6) for n, p, _ in rows if n > 300_000 and p]
    if per_mb:
        avg = sum(per_mb) / len(per_mb) / 1e6
        print(f'\n    ~{avg:.0f} MB of deck per MB of source; the 512 MB '
              f'reservation runs out near {512/avg:.1f} MB of source')
    moved = [v for _, _, v in rows if v != 'same']
    print(f'    {len(rows) - len(moved)}/{len(rows)} byte-identical to the pipeline')

    # --- finding 45: what running out of deck looks like ---
    print(f'\n### squeezing the deck to {SQUEEZE_MB} MB (finding 45)')
    zig = LADDER / 'src' / 'codexzig.zig'
    if not zig.is_file():
        print(f'    no {zig} to squeeze -- finding 45 NOT re-checked this run')
        return 2
    work = LADDER / 'corpus' / '.codexzig'
    work.mkdir(parents=True, exist_ok=True)
    small = work / f'squeeze{SQUEEZE_MB}.zig'
    text = zig.read_text(errors='replace')
    want = 'cx_heap_advance(536870912)'
    if text.count(want) != 1:
        print(f'    {want} appears {text.count(want)} times, expected 1 -- '
              f'the deck prologue moved; squeeze skipped')
        return 1
    small.write_text(text.replace(want, f'cx_heap_advance({SQUEEZE_MB * 1024 * 1024})'))
    exe = work / f'squeeze{SQUEEZE_MB}'
    b = subprocess.run(['zig', 'build-exe', str(small), '-femit-bin=' + str(exe)],
                       capture_output=True, timeout=900)
    if b.returncode != 0:
        print('    SQUEEZE BUILD FAILED:',
              b.stderr.decode('utf-8', 'replace')[:200])
        return 1
    subj = LADDER / 'src' / SQUEEZE_SUBJECT
    if not subj.is_file():
        print(f'    no {subj} to squeeze -- finding 45 NOT re-checked this run')
        return 2
    src = subj.read_bytes()
    # BOUNDED, because this program is built to run out of memory: an
    # unbounded runaway livelocked a whole host on 2026-08-19 and the
    # resident bound is what corpus_run calls not optional.
    r = subprocess.run(corpus_run.BOUNDED + ['timeout', '600', str(exe)],
                       input=src, capture_output=True, timeout=900)
    peak, reserved = deck_peak(r.stdout.decode('utf-8', 'replace'))
    err = r.stderr.decode('utf-8', 'replace')
    emitted = sum(1 for l in err.splitlines()
                  if l.startswith('const ') or l.startswith('fn '))
    over = f'{100 * peak / reserved:.0f}%' if reserved else '?'
    print(f'    {SQUEEZE_SUBJECT} into a {SQUEEZE_MB} MB deck: rc={r.returncode}, '
          f'reached {over} of the reservation')
    print(f'    stderr carries {len(err)} bytes and {emitted} lines of emitted zig')
    first = next((l for l in err.splitlines()
                  if 'exception' in l or 'panic' in l or 'cx heap' in l), '')
    print(f'    {first[:110]}')
    if r.returncode == 0:
        print('    REFUSING: it SUCCEEDED, so the squeeze no longer squeezes '
              'and finding 45 went UNCHECKED this run. Either the deck got '
              'cheaper or SQUEEZE_MB is too generous; re-read the finding.')
        return 2
    elif emitted:
        print('    NOTE: emitted zig reached stderr before the fault. Finding 45 '
              'says none does; a partial transpile CAN now look like a whole one.')
    return 1 if moved else 0


if __name__ == '__main__':
    sys.exit(main())
