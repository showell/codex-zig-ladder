#!/usr/bin/env python3
"""Run every ported Roc snippet through native/codexzig and check its answer
against ROC's expected value.

The oracle here is not bare metal and not our own comparison: it is the
number the Roc project's own test harness expects, written by people who
never heard of Codex. That is the property PRIORITIES item 6 says we cannot
manufacture, and it is the whole reason for porting somebody else's suite
rather than writing more of our own rows.

So the gate is one thing, end to end:

    <name>.codex  ->  codexzig  ->  zig run  ==  <name>.expected

and `<name>.expected` holds Roc's answer, adapted only where Codex spells
the same value differently (Roc's numeric literals default to a decimal
type and print `10.0` where Codex Integer prints `10`; the port's own prose
records every such adaptation).

WHY codexzig AND NOT corpus_run. corpus_run answers a different question --
it drives `codexir | zigemit`, the two-process pipeline, and it selects its
programs from `corpus/census.json`, which these ports are not in. This
drives the single binary, on a named set, with no census involved. The two
tools agree byte for byte on 564 programs, so this is not a second opinion
on the emitter; it is the CROWN JEWEL path being asked a question the
census cannot pose yet.

The ports are `roc-*.codex` in the depot's test directory. A glob rather
than a manifest on purpose: a list beside the files is a second thing to
keep in step, and this queue has filed that failure twice in one day.
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
import compute_lock
import corpus_run
from codexzig_corpus import CODEXZIG, emit, halted

WORK = corpus_run.LADDER / 'corpus'


def run_one(src, out_dir):
    """One port from Codex source to a verdict. Returns (verdict, detail)."""
    # Cite resolution first, for the reason corpus_run gives: a test is a
    # driver and the functions it calls live in cited chapters, and codexzig
    # resolves nothing. Feeding it a raw .codex makes every cited name look
    # like an emitter gap. That mistake cost an hour on 2026-08-26.
    unit, missing = corpus_run.resolve(src)
    if missing:
        return 'unresolved', '; '.join(f'{q} chapter {n}' for _, q, n in missing[:3])

    zig = out_dir / f'{src.stem}.zig'
    if not emit([str(CODEXZIG)], unit.encode(), zig):
        return 'transpile-failed', 'codexzig wrote nothing'
    halt = halted(zig)
    if halt:
        return 'halted', halt[:140]

    want = corpus_run.expected_text(src.stem)
    if want is None:
        return 'no-expected', "Roc's answer has not been recorded"
    try:
        p = subprocess.run(corpus_run.BOUNDED + ['timeout', '300', 'zig', 'run', str(zig)],
                           capture_output=True, timeout=330)
    except subprocess.TimeoutExpired:
        return 'timeout', 'over 300s'
    if p.returncode != 0:
        err = p.stderr.decode('utf-8', 'replace')
        first = next((l for l in err.splitlines() if 'error:' in l or 'panic:' in l), '')
        return ('crashed' if 'panic:' in err else 'refused'), first[:140]
    # stderr, not stdout: print-text is cx_print is std.debug.print, the wart
    # native_build.sh documents.
    got = p.stderr.decode('utf-8', 'replace')
    if got.strip() == want.strip():
        return 'match', ''
    return 'differ', f'roc wants {want.strip()[:70]!r}, codexzig gave {got.strip()[:70]!r}'


def main():
    compute_lock.require_venue()
    names = sys.argv[1:]
    ports = sorted(corpus_run.TESTS.glob('roc-*.codex'))
    if names:
        ports = [p for p in ports if p.stem in names]
        unknown = set(names) - {p.stem for p in ports}
        if unknown:
            raise SystemExit(f'no such port: {", ".join(sorted(unknown))}')
    if not ports:
        raise SystemExit(f'no roc-*.codex in {corpus_run.TESTS}')
    if not CODEXZIG.is_file():
        raise SystemExit(f'{CODEXZIG} missing; run codexzig_build.sh')

    WORK.mkdir(exist_ok=True)
    print(f'### {len(ports)} ported Roc snippets through {CODEXZIG.name}, '
          f"against Roc's own expected values")
    bad = 0
    for src in ports:
        verdict, detail = run_one(src, WORK)
        if verdict != 'match':
            bad += 1
        print(f'  {verdict:<17} {src.stem:<34} {detail}'.rstrip(), flush=True)
    print(f'### {len(ports) - bad} match, {bad} not')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
