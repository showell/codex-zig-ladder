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
"""

import pathlib
import sys

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

    print(f'{written} unit(s) written to {out}')
    if unresolved:
        print(f'{len(unresolved)} program(s) have a cite nothing resolves:')
        for stem, missing in unresolved[:20]:
            for who, quire, name in missing:
                print(f'  {stem}: {who} cites {quire} chapter {name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
