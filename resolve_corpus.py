#!/usr/bin/env python3
"""Write every corpus program out as a SELF-CONTAINED unit.

    ./resolve_corpus.py <out-dir>

The Rust front end reads one file and resolves no cites, and neither does
`native/codexir` -- which is why `corpus_run.py` calls `cite_resolve.resolve`
before handing a program over. The IR golds in `$CODEX_GOLDS/ir/` were cut from
those resolved units, so anything comparing against them has to read the same
bytes. A gold IR names sections from `Foreword ListUtils` and constructors from
`Foreword Tuple` that appear nowhere in the program's own file.

The population is `corpus_run.py`'s, so the two cannot drift: every `.codex`
under `codex/test/` except `apps/`, keyed by bare stem, 1,234 of them at u53.

Units land OUTSIDE every repo, the way `bank_golds.py` puts the golds outside
one: they are generated, they are large (the 3.7 KB floor times the corpus),
and nothing should be tempted to commit them.

A PROVENANCE is written beside them, because a directory name is not a pin. On
2026-09-09 the corpus at ~/units-u56 was found to hold U55 sources: 18 of the
19 comparable files that changed between those Updates matched U55 and none
matched U56, and it had been graded against a U57 oracle. Nothing in the
directory could say otherwise. Name the directory for the revision, and read
the receipt rather than the name.
"""

import pathlib
import subprocess
import sys
import time

# Set before the local imports below: this script is run as `./resolve_corpus.py`
# and as `python3 resolve_corpus.py`, and only the first honours a -B shebang.
sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from cite_resolve import resolve
from corpus_run import select_population
from ladder_root import CODEX


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = pathlib.Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)

    names = select_population(CODEX / 'codex' / 'test')
    unresolved = []
    written = 0
    for src in names:
        unit, missing = resolve(src)
        if missing:
            # Reported, never guessed at -- an invented resolution would build a
            # different program than the depot does. cite_resolve says why.
            unresolved.append((src.stem, missing))
            continue
        (out / f'{src.stem}.codex').write_text(unit)
        written += 1

    rev = subprocess.run(['git', '-C', str(CODEX), 'log', '-1', '--format=%h  %s'],
                         capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(['git', '-C', str(CODEX), 'status', '--porcelain'],
                                capture_output=True, text=True).stdout.strip())
    (out / 'PROVENANCE').write_text(
        'The corpus units beside this file, and the checkout they were resolved from.\n'
        'A directory NAME is not a pin; this is.\n\n'
        f'cut        {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}\n'
        f'checkout   {CODEX}\n'
        f'revision   {rev}{"  DIRTY" if dirty else ""}\n'
        f'units      {written}\n'
        f'population every .codex under codex/test/ except apps/, keyed by bare stem\n'
        f'resolver   cite_resolve.resolve -- dependencies first, each once\n')

    print(f'{written} unit(s) written to {out}')
    print(f'PROVENANCE: {rev}')
    if unresolved:
        print(f'{len(unresolved)} program(s) have a cite nothing resolves:')
        for stem, missing in unresolved[:20]:
            for who, quire, name in missing:
                print(f'  {stem}: {who} cites {quire} chapter {name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
