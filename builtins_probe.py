#!/usr/bin/env python3
"""The compiler's BUILT-IN NAMES, read out of `Types/Builtins.codex`.

    ./builtins_probe.py            report the count and the first few
    ./builtins_probe.py --rust     emit the Rust table on stdout

`builtin-names` is `bs-name` of every entry in `builtins`, and the name
resolver needs the set: a call to `text-length` is not an undefined name, and
without the list every program in the corpus reports hundreds that are not
there.

WHY A PROBE AND NOT A TRANSCRIPTION. The list is 263 entries long and moves
with the compiler; typing it once would be a copy nobody could check. This
reads the source of truth, and re-running it after a pin change says whether
the committed copy still matches -- the same arrangement `charcode_probe.py`
has, and for the same reason.

rust-codex-compiler is clean by construction -- no code generation inside it --
so the ladder emits and the repo receives a table committed by hand.
"""

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import CODEX

SOURCE = CODEX / 'codex' / 'compiler' / 'Types' / 'Builtins.codex'
# `bs-name = "..."` inside a BuiltinSpec, and nothing else in the file is
# spelled that way.
ENTRY = re.compile(r'BuiltinSpec\s*\{\s*bs-name\s*=\s*"([^"]*)"')


def names():
    text = SOURCE.read_text(errors='replace')
    found = ENTRY.findall(text)
    if not found:
        raise SystemExit(f'{SOURCE}: no BuiltinSpec entries matched; has the record changed?')
    dupes = [n for i, n in enumerate(found) if n in found[:i]]
    if dupes:
        raise SystemExit(f'{SOURCE}: duplicate builtin names {sorted(set(dupes))}')
    return found


def as_rust(found):
    body = '\n'.join(f'    {n!r},'.replace("'", '"') for n in found)
    return ('// The compiler\'s built-in names, read from Types/Builtins.codex by\n'
            '// ladder builtins_probe.py. A call to one of these is not an undefined\n'
            '// name, and without the set every program reports hundreds that are not\n'
            '// there. Re-run the probe after a pin change; do not edit by hand.\n'
            f'pub const BUILTIN_NAMES: [&str; {len(found)}] = [\n' + body + '\n];\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rust', action='store_true', help='emit the Rust table on stdout')
    a = ap.parse_args()
    found = names()
    if a.rust:
        print(as_rust(found), end='')
        return 0
    print(f'{len(found)} builtin names from {SOURCE}')
    print('  ' + ', '.join(found[:8]) + ' ...')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
