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
    names = sorted(n for n, v in census['programs'].items()
                   if v.get('stage') == 'clean' and v.get('verdict') == 'match')
    OUT.mkdir(parents=True, exist_ok=True)
    print(f'### codexzig against {len(names)} well-behaved corpus programs')
    print(f'    (clean + match in corpus/census.json, banked {census["meta"]["date"]})')

    tally = {'correct': 0, 'differ': 0, 'refused': 0, 'crashed': 0,
             'timeout': 0, 'transpile-failed': 0}
    same, moved, bad = 0, [], []
    started = time.time()
    for i, name in enumerate(names, 1):
        src = (corpus_run.TESTS / f'{name}.codex').read_bytes()
        one = OUT / f'{name}.zig'
        duo_ir, duo = OUT / f'{name}.ir', OUT / f'{name}.duo.zig'

        if not emit([str(CODEXZIG)], src, one):
            tally['transpile-failed'] += 1
            bad.append((name, 'transpile-failed', 'codexzig wrote nothing'))
            continue
        # Structural: same bytes as the two-process pipeline?
        if emit([str(corpus_run.CODEXIR)], src, duo_ir) and \
           emit([str(corpus_run.ZIGEMIT)], duo_ir.read_bytes(), duo):
            if one.read_bytes() == duo.read_bytes():
                same += 1
            else:
                moved.append(name)

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
            kind = 'crashed' if 'panic:' in err else 'refused'
            tally[kind] += 1
            first = next((l for l in err.splitlines()
                          if 'error:' in l or 'panic:' in l), '')
            bad.append((name, kind, first[:150]))
            continue
        got = p.stderr.decode('utf-8', 'replace')
        want = corpus_run.expected_text(name)
        if got.strip() == want.strip():
            tally['correct'] += 1
        else:
            tally['differ'] += 1
            bad.append((name, 'differ',
                        f'want {want.strip()[:60]!r} got {got.strip()[:60]!r}'))
        if i % 25 == 0:
            print(f'  {i}/{len(names)}  {tally}', flush=True)

    print(f'\n### {int(time.time() - started)}s')
    print('    ' + ', '.join(f'{k} {v}' for k, v in tally.items() if v))
    print(f'    byte-identical to codexir | zigemit: {same}/{len(names)}'
          + (f'  MOVED: {" ".join(moved)}' if moved else ''))
    if bad:
        print('\n### programs to read, most interesting first')
        for name, kind, why in sorted(bad, key=lambda b: b[1]):
            print(f'  {kind:<18} {name:<34} {why}')
    return 1 if (bad or moved) else 0


if __name__ == '__main__':
    sys.exit(main())
