#!/usr/bin/env python3
"""Run the depot's own test battery through the plug, natively.

`codex/test/` holds about 1,500 Codex programs, 1,300 of them beside a
hand-verified `.expected` file. That is an oracle per program, written by
someone with no knowledge of this plug, which is the one property our own probes
can never have: a probe tests what we already suspect.

Two stages, cheap first, because they answer different questions.

  --transpile   .codex -> IR -> .zig for every program, and histogram the
                @compileError markers. No zig compilation at all, so this is
                minutes for the whole corpus. The output is a census of the
                emitter's coverage RANKED BY HOW OFTEN each gap actually bites,
                which is the number that says what to fix first.

  --run         for the programs that transpiled clean, build and run the zig
                and diff against `.expected`. Hours, unattended, and this is the
                conformance answer.

Both stages go through native/codexir and native/zigemit, so no QEMU is
involved. That is the whole reason this is affordable: the same questions asked
through the ladder would each cost a bundle, a seed compile and a plug boot.

The circularity is worth stating rather than hiding: codexir is the compiler AS
TRANSPILED BY THE PLUG under test, so this is the plug grading its own homework
at one remove. Fine for finding divergences, useless as a trust claim. Anything
this turns up gets confirmed against the seed before it is believed, exactly the
way the ladder banks.
"""

import argparse
import collections
import json
import pathlib
import re
import resource
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from cite_resolve import resolve
from ladder_root import CODEX, LADDER

TESTS = CODEX / 'codex' / 'test'
CODEXIR = LADDER / 'native' / 'codexir'
ZIGEMIT = LADDER / 'native' / 'zigemit'
WORK = LADDER / 'corpus'
MARKER = re.compile(r'@compileError\("zig plug: ([^"]*)"\)')


def need_tools():
    for t in (CODEXIR, ZIGEMIT):
        if not t.is_file():
            raise SystemExit(f'{t} missing; run native_build.sh (it needs QEMU once)')


def transpile(src, out_dir):
    """One program from Codex source to zig. Returns a verdict dict."""
    r = {'name': src.stem}
    # Resolve cites first. A test is usually a driver and the function it calls
    # lives in a cited chapter; codexir resolves nothing, so without this the
    # call arrives as an undefined name and the plug's fallback fires, which
    # looks exactly like an emitter gap and is not one.
    unit, missing = resolve(src)
    if missing:
        r['stage'] = 'unresolved'
        r['detail'] = '; '.join(f'{q} chapter {n}' for _, q, n in missing[:3])
        return r
    ir = subprocess.run([str(CODEXIR)], input=unit.encode(),
                        capture_output=True, timeout=120)
    # Output lands on stderr because print-text is std.debug.print in the
    # emitted runtime. That is a wart the plug should fix, not a design.
    if ir.returncode != 0 or not ir.stderr:
        r['stage'] = 'codexir'
        r['detail'] = f'rc={ir.returncode} signal={-ir.returncode if ir.returncode < 0 else 0}'
        return r
    (out_dir / f'{src.stem}.ir').write_bytes(ir.stderr)

    zg = subprocess.run([str(ZIGEMIT)], input=ir.stderr,
                        capture_output=True, timeout=120)
    if zg.returncode != 0 or not zg.stderr:
        r['stage'] = 'zigemit'
        r['detail'] = f'rc={zg.returncode}'
        return r
    zig = zg.stderr.decode('utf-8', 'replace')
    (out_dir / f'{src.stem}.zig').write_text(zig)

    marks = MARKER.findall(zig)
    r['stage'] = 'markers' if marks else 'clean'
    r['markers'] = marks
    return r


def stage_transpile(names, out_dir):
    results, hist = [], collections.Counter()
    for i, src in enumerate(names, 1):
        try:
            r = transpile(src, out_dir)
        except subprocess.TimeoutExpired:
            r = {'name': src.stem, 'stage': 'timeout', 'detail': 'over 120s'}
        except Exception as e:                      # a crash here is data too
            r = {'name': src.stem, 'stage': 'error', 'detail': repr(e)[:120]}
        results.append(r)
        # Count PROGRAMS, not occurrences. A builtin used 76 times in one
        # program and one used once in 76 programs are very different facts,
        # and the second is the one that says what to implement first.
        for m in set(r.get('markers', ())):
            hist[m] += 1
        if i % 100 == 0:
            print(f'  {i}/{len(names)}', flush=True)

    by = collections.Counter(r['stage'] for r in results)
    print(f'\n{len(results)} programs: ' +
          ', '.join(f'{k} {v}' for k, v in by.most_common()))

    # The histogram is the point of this stage. A gap that bites 400 programs
    # and a gap that bites one are the same line of missing code and very
    # different priorities, and nothing else we have measures that.
    if hist:
        print(f'\nemitter gaps, by how many programs hit them '
              f'({len(hist)} distinct):')
        for name, n in hist.most_common(40):
            print(f'  {n:5d}  {name}')
    return results, hist


# Address-space cap for each `zig run` and the program it executes. Emitted
# binaries have ballooned to 3 GB anon RSS on a 3.8 GB guest, and on 2026-08-19
# one such run livelocked the whole WSL VM instead of drawing a clean OOM kill.
# Under the cap the allocation fails inside the child, the arena's
# @panic("oom") fires, and the balloon becomes a recorded verdict. A compile
# needs ~130 MB, so the cap only ever bites the runaway.
RUN_MEM_CAP = 2_560 * 1024 * 1024


def _cap_memory():
    resource.setrlimit(resource.RLIMIT_AS, (RUN_MEM_CAP, RUN_MEM_CAP))


def stage_run(results, out_dir, persist=True):
    """Build and run what transpiled clean, diff against the depot's .expected."""
    clean = [r for r in results if r['stage'] == 'clean']
    print(f'\n{len(clean)} clean programs; building and running')
    tally = collections.Counter()
    detail = []
    # One line per verdict, flushed as it lands: run.json at the end of the
    # loop kept nothing when the 2026-08-19 run died at program 101 of 250.
    jsonl = (out_dir / 'run.jsonl').open('w') if persist else None

    def verdict(name, kind, note=''):
        tally[kind] += 1
        if kind not in ('match', 'no-expected'):
            detail.append((name, kind, note))
        if jsonl:
            jsonl.write(json.dumps({'name': name, 'verdict': kind, 'detail': note}) + '\n')
            jsonl.flush()

    for i, r in enumerate(clean, 1):
        name = r['name']
        exp = TESTS / f'{name}.expected'
        zig = out_dir / f'{name}.zig'
        if not exp.is_file():
            verdict(name, 'no-expected')
            continue
        try:
            p = subprocess.run(['zig', 'run', str(zig)],
                               capture_output=True, timeout=300,
                               preexec_fn=_cap_memory)
        except subprocess.TimeoutExpired:
            verdict(name, 'timeout')
            continue
        if p.returncode != 0:
            # A zig compile error here is a real finding: the plug emitted
            # something it believed in and zig refused it. A panic is a
            # different finding: zig accepted it and the program died running.
            stderr = p.stderr.decode('utf-8', 'replace')
            kind = 'crashed' if 'panic:' in stderr else 'refused'
            first = next((l for l in stderr.splitlines()
                          if 'error:' in l or 'panic:' in l), '')
            verdict(name, kind, first[:160])
            continue
        got = p.stderr.decode('utf-8', 'replace')
        # Compare program text, not capture-channel bytes. 76 of the depot's
        # .expected files open with one 0x01 the console capture wrote, and a
        # subset of exactly those use CRLF -- every CRLF file is 0x01-marked,
        # no unmarked file holds a CR, and marked/unmarked siblings (vec-array
        # vs vec-pattern) have identical prints and openings, so both bytes
        # are the capture path's line discipline, not output. The depot's own
        # adjudicator (build/test.ps1 phase 2) already strips every CR before
        # comparing; the zig arm has no serial console to write either byte.
        want = exp.read_text(errors='replace').replace('\r', '')
        want = want[1:] if want.startswith('\x01') else want
        if got.strip() == want.strip():
            verdict(name, 'match')
        else:
            verdict(name, 'differ', f'want {want.strip()[:60]!r} got {got.strip()[:60]!r}')
        if i % 50 == 0:
            print(f'  {i}/{len(clean)}  {dict(tally)}', flush=True)

    if jsonl:
        jsonl.close()
    print('\n' + ', '.join(f'{k} {v}' for k, v in tally.most_common()))
    return tally, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--transpile', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--limit', type=int, default=0, help='first N programs only')
    ap.add_argument('--all', action='store_true', help='(kept for the runner scripts; '
                    'cites are resolved now, so every program is in scope)')
    a = ap.parse_args()
    if not (a.transpile or a.run):
        a.transpile = True

    need_tools()
    WORK.mkdir(exist_ok=True)
    names = sorted(TESTS.glob('*.codex'))
    # A test that cites another chapter is a DRIVER: the function it calls lives
    # in the cited chapter, and codexir resolves no cites, so every such call
    # comes out as an undefined name and the plug's fallback fires. The first
    # histogram over this corpus was 64 markers of that shape and none of them
    # was an emitter gap. Until there is a resolver, the honest corpus is the
    # self-contained programs.
    if a.limit:
        names = names[:a.limit]
    print(f'corpus: {len(names)} programs from {TESTS}')

    # A limited run is a smoke test; the json files are the full-corpus census
    # and a slice must not overwrite them (one did, 2026-08-19).
    persist = not a.limit
    results, hist = stage_transpile(names, WORK)
    if persist:
        (WORK / 'transpile.json').write_text(json.dumps(results, indent=1))
        (WORK / 'gaps.json').write_text(json.dumps(hist.most_common(), indent=1))
    else:
        print('\n--limit run: census json left untouched')

    if a.run:
        tally, detail = stage_run(results, WORK, persist=persist)
        if persist:
            (WORK / 'run.json').write_text(json.dumps(
                {'tally': dict(tally), 'detail': detail}, indent=1))
        print('\nfindings worth reading first:')
        for name, kind, why in detail[:25]:
            print(f'  {kind:8s} {name:32s} {why}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
