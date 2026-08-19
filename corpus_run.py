#!/usr/bin/env python3
"""Run the depot's own test battery through the plug, natively.

`codex/test/` holds ~560 top-level Codex programs (566 at Update 47), most
beside a hand-verified `.expected` file. That is an oracle per program,
written by someone with no knowledge of this plug, which is the one property
our own probes can never have: a probe tests what we already suspect.

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
import datetime
import hashlib
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
CENSUS = WORK / 'census.json'
MARKER = re.compile(r'@compileError\("zig plug: ([^"]*)"\)')


def expected_text(name):
    """The .expected content as the comparison sees it, or None. One home for
    the normalization: 76 of the depot's .expected files open with one 0x01
    the console capture wrote, and a subset of exactly those use CRLF --
    every CRLF file is 0x01-marked, no unmarked file holds a CR, and
    marked/unmarked siblings (vec-array vs vec-pattern) have identical prints
    and openings, so both bytes are the capture path's line discipline, not
    output. The depot's own adjudicator (build/test.ps1 phase 2) strips every
    CR the same way."""
    exp = TESTS / f'{name}.expected'
    if not exp.is_file():
        return None
    want = exp.read_text(errors='replace').replace('\r', '')
    return want[1:] if want.startswith('\x01') else want


def expected_sha(name):
    want = expected_text(name)
    return None if want is None else hashlib.sha256(
        want.strip().encode()).hexdigest()[:16]


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
    # A program's verdict is a pure function of (this file) x (zig toolchain),
    # so the hash is the cache key --changed compares against the bank.
    r['zig_sha'] = hashlib.sha256(zig.encode()).hexdigest()[:16]

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


def load_run_carry(results, prev):
    """Verdicts from an earlier interrupted or batched --run that still hold.

    `prev` maps name -> zig_sha from the transpile.json the earlier run
    actually compiled, captured before this invocation overwrote it. A
    verdict carries iff the program's freshly emitted zig is byte-identical
    to that and the zig toolchain has not moved. run.jsonl lines written
    before the zig field existed carry on the sha alone, once; the baseline
    bank retires them.
    """
    jsonl = WORK / 'run.jsonl'
    if not jsonl.is_file() or prev is None:
        return {}
    lines = []
    raw = jsonl.read_text().splitlines()
    for i, l in enumerate(raw):
        try:
            lines.append(json.loads(l))
        except json.JSONDecodeError:
            if i == len(raw) - 1:
                print(f'  dropping torn final line of {jsonl}')
                continue
            raise SystemExit(f'{jsonl} line {i + 1} is corrupt; inspect it')
    zv = zig_version()
    now = {r['name']: r.get('zig_sha') for r in results}
    carry, dropped = {}, 0
    for e in lines:
        n = e['name']
        if (prev.get(n) and prev[n] == now.get(n)
                and e.get('zig', zv) == zv):
            carry[n] = e
        else:
            dropped += 1
    print(f'\nresume: {len(carry)} verdicts carried from run.jsonl '
          f'(emitted zig byte-identical, toolchain unmoved)'
          + (f'; {dropped} dropped as stale' if dropped else ''))
    return carry


def stage_run(results, out_dir, persist=True, batch=0, prior=None):
    """Build and run what transpiled clean, diff against the depot's .expected."""
    prior = prior or {}
    clean = [r for r in results if r['stage'] == 'clean']
    todo = [r for r in clean if r['name'] not in prior]
    if batch and batch < len(todo):
        print(f'\nbatch: running {batch} of {len(todo)} outstanding; '
              f'{len(todo) - batch} left for the next invocation')
        todo = todo[:batch]
    print(f'\n{len(clean)} clean programs; building and running {len(todo)}')
    tally = collections.Counter()
    detail = []
    verdicts = {}
    # One line per verdict, flushed as it lands: run.json at the end of the
    # loop kept nothing when the 2026-08-19 run died at program 101 of 250.
    # Carried lines are rewritten first, so the file is always exactly the
    # currently-valid verdict set -- stale lines do not linger.
    jsonl = (out_dir / 'run.jsonl').open('w') if persist else None
    zv = zig_version()
    for e in prior.values():
        tally[e['verdict']] += 1
        verdicts[e['name']] = (e['verdict'], e.get('detail', ''))
        if jsonl:
            jsonl.write(json.dumps(e) + '\n')
    if jsonl:
        jsonl.flush()

    def verdict(name, kind, note=''):
        tally[kind] += 1
        verdicts[name] = (kind, note)
        if kind not in ('match', 'no-expected'):
            detail.append((name, kind, note))
        if jsonl:
            jsonl.write(json.dumps({'name': name, 'verdict': kind,
                                    'detail': note, 'zig': zv}) + '\n')
            jsonl.flush()

    for i, r in enumerate(todo, 1):
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
        want = expected_text(name)
        if got.strip() == want.strip():
            verdict(name, 'match')
        else:
            verdict(name, 'differ', f'want {want.strip()[:60]!r} got {got.strip()[:60]!r}')
        if i % 25 == 0:
            print(f'  {i}/{len(todo)}  {dict(tally)}', flush=True)

    if jsonl:
        jsonl.close()
    print('\n' + ', '.join(f'{k} {v}' for k, v in tally.most_common()))
    return tally, detail, verdicts


# The banked census: name -> {stage, zig_sha, markers, verdict}, written only
# by --bank and diffed like a truth file. Day to day the interesting output is
# the DIFF against it -- which programs flipped match->differ (a regression),
# differ->match (a fix landed), refused->match -- not the wholesale tally.
# The design behind it: corpus/README.md.

def load_bank():
    return json.loads(CENSUS.read_text()) if CENSUS.is_file() else None


def write_bank(programs):
    meta = {
        'date': datetime.date.today().isoformat(),
        'zig': zig_version(),
        'tools': {t.name: hashlib.sha256(t.read_bytes()).hexdigest()[:16]
                  for t in (CODEXIR, ZIGEMIT)},
    }
    CENSUS.write_text(json.dumps({'meta': meta, 'programs': programs},
                                 indent=1, sort_keys=True))


def zig_version():
    return subprocess.run(['zig', 'version'], capture_output=True,
                          text=True).stdout.strip()


def census_key(entry):
    """The one word a program's row answers with: its run verdict when it has
    one, its transpile stage when it never ran."""
    return entry.get('verdict') or entry['stage']


def assemble_census(results, carried, verdicts):
    programs = {}
    for r in results:
        e = {'stage': r['stage']}
        if r.get('zig_sha'):
            e['zig_sha'] = r['zig_sha']
        marks = sorted(set(r.get('markers') or ()))
        if marks:
            e['markers'] = marks
        n = r['name']
        esha = expected_sha(n)
        if esha:
            e['expected_sha'] = esha
        if n in carried:
            e['verdict'] = carried[n]['verdict']
        elif n in verdicts:
            e['verdict'] = verdicts[n][0]
        programs[n] = e
    return programs


def print_bank_diff(bank, programs):
    old = bank['programs']
    flips = []
    for n, e in programs.items():
        o = old.get(n)
        if o is None:
            flips.append((n, '(new)', census_key(e)))
        elif census_key(o) != census_key(e):
            flips.append((n, census_key(o), census_key(e)))
    if flips:
        print(f'\nverdict diff vs bank {bank["meta"]["date"]} ({len(flips)} moved):')
        for n, was, now in sorted(flips):
            print(f'  {n:36s} {was} -> {now}')
    else:
        print(f'\nno verdict moved vs bank {bank["meta"]["date"]}')
    gone = [n for n in old if n not in programs]
    if gone:
        print(f'  ({len(gone)} banked programs no longer in the corpus)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--transpile', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--changed', action='store_true',
                    help='re-emit everything, run only programs whose emitted '
                         'zig moved since the bank, report the verdict diff')
    ap.add_argument('--bank', action='store_true',
                    help='after a full --run or --changed: write census.json')
    ap.add_argument('--limit', type=int, default=0, help='first N programs only')
    ap.add_argument('--batch', type=int, default=0,
                    help='with --run: build/run at most N outstanding programs, '
                         'carrying earlier verdicts whose emitted zig is '
                         'byte-identical; rerun to continue where it left off')
    ap.add_argument('--all', action='store_true', help='(kept for the runner scripts; '
                    'cites are resolved now, so every program is in scope)')
    a = ap.parse_args()
    if not (a.transpile or a.run or a.changed):
        a.transpile = True
    if a.limit and (a.changed or a.bank):
        raise SystemExit('--changed and --bank are full-corpus operations; drop --limit')
    if a.batch and not a.run:
        raise SystemExit('--batch only means something with --run')
    if a.bank and not (a.run or a.changed):
        raise SystemExit('--bank wants run verdicts; pair it with --run or --changed')

    need_tools()
    bank = load_bank()
    if a.changed and bank is None:
        raise SystemExit('--changed needs a bank; run --run once, then --bank')
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
    # The shas the last run compiled against, captured before this
    # invocation's transpile overwrites the file: they are the carry key
    # for resuming an interrupted or batched --run.
    prev_shas = None
    if a.run and persist:
        tj = WORK / 'transpile.json'
        if tj.is_file():
            prev_shas = {e['name']: e.get('zig_sha')
                         for e in json.loads(tj.read_text())}
    results, hist = stage_transpile(names, WORK)
    if persist:
        (WORK / 'transpile.json').write_text(json.dumps(results, indent=1))
        (WORK / 'gaps.json').write_text(json.dumps(hist.most_common(), indent=1))
    else:
        print('\n--limit run: census json left untouched')

    carried, verdicts = {}, {}

    if a.changed:
        # A verdict carries only while both halves of its cache key hold: the
        # emitted zig is byte-identical to the banked hash AND the toolchain
        # that produced the banked verdict is the toolchain that would rerun
        # it. Anything else reruns -- a stale verdict served fast is worse
        # than a fresh one served slow.
        same_zig = bank['meta']['zig'] == zig_version()
        if not same_zig:
            print(f'\nzig toolchain moved ({bank["meta"]["zig"]} -> '
                  f'{zig_version()}); no verdict carries, everything reruns')
        to_run = []
        for r in results:
            if r['stage'] != 'clean':
                continue
            old = bank['programs'].get(r['name'])
            # The .expected content is part of the key: an Update that
            # rewrites an oracle file must rerun the program, or the bank
            # serves a match against an answer that no longer exists.
            if (same_zig and old and old.get('verdict')
                    and old.get('zig_sha') == r.get('zig_sha')
                    and old.get('expected_sha') == expected_sha(r['name'])):
                carried[r['name']] = old
            else:
                to_run.append(r)
        # Saying what was NOT run is load-bearing: an unchanged-but-broken
        # assumption must never read as green silence.
        print(f'\n--changed: {len(carried)} clean programs byte-identical to '
              f'bank {bank["meta"]["date"]}, not rerun; {len(to_run)} to run')
        tally, detail, verdicts = stage_run(to_run, WORK, persist=persist)
    elif a.run:
        prior = load_run_carry(results, prev_shas) if persist else {}
        tally, detail, verdicts = stage_run(results, WORK, persist=persist,
                                            batch=a.batch, prior=prior)
        if persist:
            (WORK / 'run.json').write_text(json.dumps(
                {'tally': dict(tally), 'detail': detail}, indent=1))

    if a.run or a.changed:
        print('\nfindings worth reading first:')
        for name, kind, why in detail[:25]:
            print(f'  {kind:8s} {name:32s} {why}')
        programs = assemble_census(results, carried, verdicts)
        if bank:
            print_bank_diff(bank, programs)
        if a.bank:
            unrun = [n for n, e in programs.items()
                     if e['stage'] == 'clean' and 'verdict' not in e]
            if unrun:
                raise SystemExit(f'--bank refused: {len(unrun)} clean programs '
                                 f'have no run verdict yet; finish the batches first')
            write_bank(programs)
            print(f'\nbanked {len(programs)} programs to {CENSUS}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
