#!/usr/bin/env python3
"""Run the depot's well-behaved programs through native/codexzig and check
the answers against the depot's own `.expected` files.

The single-binary transpiler agrees with `codexir | zigemit` on 85 small
programs and reproduces its own bundle byte for byte. Neither of those says
its OUTPUT IS CORRECT -- they say it matches another tool and itself. The
depot's `.expected` files are the oracle that does say it, because they were
written by someone with no knowledge of this plug.

WHICH PROGRAMS. `corpus/census.json` classifies all 593. The set worth
asking about is `stage == clean` (the plug refused no construct) AND
`verdict == match` (the pipeline's zig built, ran, and agreed with
`.expected`). That is 181 of them. The other 144 clean ones are not
well-behaved for this purpose: 112 emit zig that does not build, 30 have no
`.expected` at all, and 2 only produce their expected output on real
hardware.

TWO CHECKS PER PROGRAM, and they answer different questions:

  same-as-pipeline  the emitted zig is byte-identical to codexir | zigemit's.
                    Structural: this program runs the same code in the same
                    order, so a difference here is a defect in the combining.
  correct           the emitted zig BUILDS, RUNS, and its output equals
                    `.expected`. End-to-end: this is the one that can find a
                    defect the pipeline shares, because the oracle is outside
                    both.

**WHAT THE `.expected` HALF DOES AND DOES NOT PROVE.** The sample is
selected as `verdict == match` -- programs the PIPELINE already got right --
and codexzig's bytes are identical to the pipeline's, so on this sample the
`.expected` result is entailed rather than discovered. It catches a defect
codexzig has and the pipeline does not; it cannot catch one they share,
because the sample is defined to exclude those. Zig's cache is
content-addressed, so the second run of the same bytes is a cache hit and
the run is much faster than the builds would suggest. An earlier version of
this docstring called this leg "the one that can find a defect the pipeline
shares"; that was wrong, and a cold read caught it.

It is still worth running: it is the only leg whose oracle was written by
someone outside this project, and it fails loudly if the emitted zig stops
building or the depot's `.expected` moves.

The comparison semantics are corpus_run's, imported rather than re-spelled:
`expected_text` carries the 0x01/CRLF normalisation the depot's own
adjudicator uses, output is read from STDERR because print-text is
std.debug.print, and every run is memory-bounded and timed out.
"""
import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
import compute_lock
import corpus_run
from ladder_root import LADDER

CODEXZIG = LADDER / 'native' / 'codexzig'
OUT = LADDER / 'corpus' / '.codexzig'


def halted(path):
    """The CODEGEN-HALTED line if the compiler refused the subject, else ''.

    The harness prints this instead of zig when the diagnostic bag has
    errors, the way the driver does (opening.codex:1678). Anything reading
    a transpile has to look for it, or a refusal reads as a short program.
    """
    head = path.read_bytes()[:400].decode('utf-8', 'replace')
    for line in head.splitlines():
        if line.startswith('CODEGEN-HALTED:'):
            return line
    return ''


def emit(tool_argv, src_bytes, dest):
    """Every one of these tools writes its answer to STDERR (print-text is
    cx_print is std.debug.print), which is the wart native_build.sh
    documents and the reason nothing here reads stdout."""
    r = subprocess.run(tool_argv, input=src_bytes, capture_output=True, timeout=300)
    dest.write_bytes(r.stderr)
    return r.returncode == 0 and dest.stat().st_size > 0


def main():
    compute_lock.take()
    census = json.loads((LADDER / 'corpus' / 'census.json').read_text())
    progs = census['programs']
    every = sorted(progs)
    names = sorted(n for n, v in progs.items()
                   if v.get('stage') == 'clean' and v.get('verdict') == 'match')
    OUT.mkdir(parents=True, exist_ok=True)
    print(f'### codexzig against the corpus, banked {census["meta"]["date"]}')
    print(f'    breadth: {len(every)} programs, byte-compared against the pipeline')
    print(f'    correctness: {len(names)} of them (clean + match) run against .expected')

    wanted = set(names)
    tally = {'correct': 0, 'differ': 0, 'refused': 0, 'crashed': 0,
             'timeout': 0, 'transpile-failed': 0, 'unresolved': 0,
             'halted': 0, 'oom-killed': 0, 'no-expected': 0}
    nocompare = []
    have_pipeline = corpus_run.CODEXIR.is_file() and corpus_run.ZIGEMIT.is_file()
    if not have_pipeline:
        print('    NOTE: native/codexir or native/zigemit is absent, so the '
              'byte-comparison half is SKIPPED.\n          The .expected half '
              'below needs only codexzig and still runs.')
    same, moved, bad = 0, [], []
    started = time.time()
    for i, name in enumerate(every, 1):
        # RESOLVE CITES FIRST. codexir resolves nothing, so a test whose
        # driver calls into a cited chapter arrives with that name undefined
        # and the plug's fallback fires -- which, as corpus_run's own comment
        # warns, "looks exactly like an emitter gap and is not one". Feeding
        # the raw file instead of the resolved unit cost an hour here: 77 of
        # these programs came back refused, with types their cited chapters
        # declare reported as undeclared identifiers.
        unit, missing = corpus_run.resolve(corpus_run.TESTS / f'{name}.codex')
        if missing:
            # NOT a failure of this tool. The census already classifies these
            # as `unresolved` (16 of 593 today) because a cite names a quire
            # the registry has no entry for; cite_resolve refuses rather than
            # guessing. Counting them as failures made this runner incapable
            # of exiting 0, which is a gate that cannot fail -- found cold,
            # 2026-08-25.
            tally['unresolved'] += 1
            continue
        src = unit.encode()
        one = OUT / f'{name}.zig'
        duo_ir, duo = OUT / f'{name}.ir', OUT / f'{name}.duo.zig'

        try:
            got_one = emit([str(CODEXZIG)], src, one)
        except subprocess.TimeoutExpired:
            tally['timeout'] += 1
            bad.append((name, 'timeout', 'codexzig did not finish'))
            continue
        if not got_one:
            tally['transpile-failed'] += 1
            bad.append((name, 'transpile-failed', 'codexzig wrote nothing'))
            continue
        halt = halted(one)
        if halt:
            # The compiler refused the subject. That is an ANSWER, not a
            # failure of the transpiler -- but it is only right if the
            # pipeline refuses too, and today only codexzig carries the gate.
            tally['halted'] += 1
            bad.append((name, 'halted', halt[:110]))
            continue
        # Structural: same bytes as the two-process pipeline? Absent natives
        # are a SKIP with a count, not a silent pass -- a fresh sandbox has
        # codexzig and no native/codexir at all.
        if have_pipeline:
            try:
                ok = (emit([str(corpus_run.CODEXIR)], src, duo_ir)
                      and emit([str(corpus_run.ZIGEMIT)], duo_ir.read_bytes(), duo))
            except subprocess.TimeoutExpired:
                ok = False
            if not ok:
                nocompare.append(name)
            elif one.read_bytes() == duo.read_bytes():
                same += 1
            else:
                moved.append(name)

        if name not in wanted:
            # Breadth only. A program with a refusal marker, or no .expected,
            # or one that needs real hardware, still has to TRANSPILE the same
            # -- that is the question this half asks -- but there is nothing
            # to run it against.
            continue
        try:
            p = subprocess.run(corpus_run.BOUNDED +
                               ['timeout', '300', 'zig', 'run', str(one)],
                               capture_output=True, timeout=330)
        except subprocess.TimeoutExpired:
            tally['timeout'] += 1
            bad.append((name, 'timeout', ''))
            continue
        if p.returncode != 0:
            err = p.stderr.decode('utf-8', 'replace')
            if p.returncode in (137, -9) or 'Killed' in err[-200:]:
                # The cgroup bound fired. corpus_run:317-323 gives this its
                # own verdict because nothing about the emitted zig was
                # judged; calling it `refused` would blame the plug.
                tally['oom-killed'] += 1
                bad.append((name, 'oom-killed', 'resident bound fired'))
                continue
            kind = 'crashed' if 'panic:' in err else 'refused'
            tally[kind] += 1
            first = next((l for l in err.splitlines()
                          if 'error:' in l or 'panic:' in l), '')
            bad.append((name, kind, first[:150]))
            continue
        got = p.stderr.decode('utf-8', 'replace')
        want = corpus_run.expected_text(name)
        if want is None:
            # The census said this program had one. It does not any more, so
            # the census is stale and saying so is the answer.
            tally['no-expected'] += 1
            bad.append((name, 'no-expected', 'census says match, .expected is gone'))
            continue
        if got.strip() == want.strip():
            tally['correct'] += 1
        else:
            tally['differ'] += 1
            bad.append((name, 'differ',
                        f'want {want.strip()[:60]!r} got {got.strip()[:60]!r}'))
        if i % 100 == 0:
            print(f'  {i}/{len(every)}  same {same}  {tally}', flush=True)

    print(f'\n### {int(time.time() - started)}s')
    print('    ' + ', '.join(f'{k} {v}' for k, v in tally.items() if v))
    if have_pipeline:
        compared = same + len(moved)
        print(f'    byte-identical to codexir | zigemit: {same}/{compared} compared'
              + (f', {len(nocompare)} not comparable' if nocompare else '')
              + (f'  MOVED: {" ".join(moved)}' if moved else ''))
    else:
        print('    byte-comparison SKIPPED (no native/codexir, native/zigemit)')
    if bad:
        print('\n### programs to read, most interesting first')
        for name, kind, why in sorted(bad, key=lambda b: b[1]):
            print(f'  {kind:<18} {name:<34} {why}')
    return 1 if (bad or moved) else 0


if __name__ == '__main__':
    sys.exit(main())
