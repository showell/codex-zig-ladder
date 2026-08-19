#!/usr/bin/env python3
"""Assemble a self-contained unit from a Codex file and everything it cites.

A test in `codex/test/` is usually a driver: five lines that say
`cites Works chapter GopAcpi` and then call `acpi-parse`. The function lives in
the cited chapter. Our native compiler resolves no cites, so without this every
such call arrives as an undefined name and the plug's fallback fires -- which
looks exactly like an emitter gap and is not one. The first corpus histogram was
64 markers of that shape and not one of them was real.

This is the same walk the depot's own bundler does in Resolve-PlugForewords: a
cite names a quire and a chapter, `build/quire-map.ps1` maps the quire to a
directory, and the chapter is a file in it. Dependencies are emitted before the
thing that cites them, transitively, each one once.

Two things it deliberately does NOT do:

  * invent a resolution when the registry has no entry for a quire. The depot
    treats a cite as satisfied when the chapter is already PRESENT in the unit,
    and `Codex` is not a registered quire for exactly that reason. Here an
    unresolvable cite is reported, not guessed at, because a guess would produce
    a unit that compiles into a different program than the depot builds.
  * rewrite chapter headers. The bundler renames to `<Quire>--<Name>` to keep
    quires apart; a single test unit has no such collision to avoid, and
    renaming would change the names the emitted program prints.
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import CODEX

CITE = re.compile(r'^\s*cites\s+([A-Za-z_][A-Za-z0-9_]*)\s+chapter\s+'
                  r'([A-Za-z_][A-Za-z0-9_ -]*?)\s*(?:\(.*)?$', re.M)
QUIRE_LINE = re.compile(r"'([A-Za-z][A-Za-z0-9]*)'\s*=\s*'([^']+)'")


def quire_dirs():
    """The registry, read from the depot rather than copied.

    A copy can be compared and a derivation quietly answers a different
    question -- the same argument plug-build-lib.ps1 makes at the top of itself
    after a derived table silently dropped three whole quires.
    """
    text = (CODEX / 'build' / 'quire-map.ps1').read_text(errors='replace')
    body = text.split('$QuireDirs = @{', 1)[1].split('}', 1)[0]
    return {q: d.replace('\\', '/') for q, d in QUIRE_LINE.findall(body)}


def resolve(path, dirs=None, seen=None, missing=None):
    """Return (unit_text, missing_cites). Dependencies first, each once."""
    dirs = quire_dirs() if dirs is None else dirs
    seen = set() if seen is None else seen
    missing = [] if missing is None else missing
    path = pathlib.Path(path)
    if path in seen:
        return '', missing
    seen.add(path)

    text = path.read_text(errors='replace')
    parts = []
    for quire, name in CITE.findall(text):
        d = dirs.get(quire)
        dep = CODEX / d / f'{name}.codex' if d else None
        if dep is None or not dep.is_file():
            missing.append((path.name, quire, name))
            continue
        sub, _ = resolve(dep, dirs, seen, missing)
        if sub:
            parts.append(sub)
    parts.append(text.rstrip('\n') + '\n')
    return '\n'.join(parts), missing


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: cite_resolve.py <file.codex> [...]  (unit to stdout)')
    for arg in sys.argv[1:]:
        unit, missing = resolve(arg)
        sys.stdout.write(unit)
        for who, quire, name in missing:
            print(f'UNRESOLVED: {who} cites {quire} chapter {name}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
