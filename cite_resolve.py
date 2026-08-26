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
EMBEDDED = re.compile(r'^Chapter:\s*(\w+)--(.+?)\s*$', re.M)

# The two chapters `Resolve-CiteOrder` walks whether or not anything cites
# them (build/quire-map.ps1:277-280). `for x in xs -> ...` desugars to a call
# to `map-list` (Foreword ListUtils) and a tuple literal or pattern to
# `MkTup<N>` (Foreword Tuple), so these are names the DESUGARER writes and no
# author would know to cite. Leaving them out is what made `mini-bootstrap`
# report `CDX3002 Undefined name: map-list` and `board-types`
# `CDX3008 Undefined type name: Tup2` under a unit that the depot builds.
IMPLICIT = (('Foreword', 'ListUtils'), ('Foreword', 'Tuple'))


def quire_dirs():
    """The registry, read from the depot rather than copied.

    A copy can be compared and a derivation quietly answers a different
    question -- the same argument plug-build-lib.ps1 makes at the top of itself
    after a derived table silently dropped three whole quires.
    """
    text = (CODEX / 'build' / 'quire-map.ps1').read_text(errors='replace')
    body = text.split('$QuireDirs = @{', 1)[1].split('}', 1)[0]
    return {q: d.replace('\\', '/') for q, d in QUIRE_LINE.findall(body)}


def resolve(path, dirs=None):
    """Return (unit_text, missing_cites). Dependencies first, each once.

    The implicit chapters lead, then the root's own cites, then the root --
    the order `Resolve-CiteOrder` returns, and therefore the order the depot's
    own diagnostics are numbered against.
    """
    dirs = quire_dirs() if dirs is None else dirs
    path = pathlib.Path(path)
    text = path.read_text(errors='replace')
    seen, missing = {path}, []
    # A source that already bundles a chapter satisfies it by carrying it;
    # `compile.ps1` seeds `Resolve-CiteOrder` from exactly these lines, so a
    # bundle is not handed a second copy of what it embeds.
    embedded = {(q, n) for q, n in EMBEDDED.findall(text)}
    cites = [c for c in IMPLICIT if c not in embedded] + CITE.findall(text)
    parts = _walk(path.name, cites, dirs, seen, missing)
    parts.append(text.rstrip('\n') + '\n')
    return '\n'.join(parts), missing


def _walk(who, cites, dirs, seen, missing):
    """Each cited chapter preceded by everything it cites, each one once."""
    parts = []
    for quire, name in cites:
        d = dirs.get(quire)
        dep = CODEX / d / f'{name}.codex' if d else None
        if dep is None or not dep.is_file():
            missing.append((who, quire, name))
            continue
        if dep in seen:
            continue
        seen.add(dep)
        text = dep.read_text(errors='replace')
        parts.extend(_walk(dep.name, CITE.findall(text), dirs, seen, missing))
        parts.append(text.rstrip('\n') + '\n')
    return parts


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
