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
# `bs-type = Just (...)` -- the declared type, from which the ARITY comes.
TYPED = re.compile(r'BuiltinSpec\s*\{\s*bs-name\s*=\s*"([^"]*)".*?bs-type\s*=\s*(Just|None)')


def _sexp(text, i):
    """Parse one balanced (...) form starting at i. Returns (form, next-i)."""
    out, tok = [], ''
    assert text[i] == '('
    i += 1
    while i < len(text):
        c = text[i]
        if c == '(':
            if tok:
                out.append(tok)
                tok = ''
            sub, i = _sexp(text, i)
            out.append(sub)
            continue
        if c == ')':
            if tok:
                out.append(tok)
            return out, i + 1
        if c.isspace():
            if tok:
                out.append(tok)
                tok = ''
            i += 1
            continue
        tok += c
        i += 1
    return out, i


def _arity(form):
    """How many arguments the FunTy spine takes.

    A builtin's arity is not written down anywhere; it is the shape of its
    type. `ForAllTy` wrappers are transparent, a `FunTy` contributes one and
    recurses on its RESULT -- so a function-typed ARGUMENT (map-list's first)
    does not inflate the count.
    """
    if not isinstance(form, list) or not form:
        return 0
    head = form[0]
    if head == 'ForAllTy':
        return _arity(form[-1])
    if head == 'FunTy':
        return 1 + _arity(form[-1])
    return 0


def arities(text):
    """name -> arity, for every builtin that declares a type.

    Split per ENTRY rather than pairing a name with the next `bs-type` found:
    31 of the 263 declare `bs-type = None`, and a name-then-type search reads
    straight past those into the following entry's type -- which gave
    `__narrow` an arity of 0 and would have made every call to it wrong.
    """
    out = {}
    for chunk in text.split('BuiltinSpec {')[1:]:
        m = re.match(r'\s*bs-name\s*=\s*"([^"]*)"', chunk)
        if not m:
            continue
        t = re.search(r'bs-type\s*=\s*Just\s*(?=\()', chunk)
        if not t:
            continue
        form, _ = _sexp(chunk, t.end())
        out[m.group(1)] = _arity(form)
    return out


def names():
    text = SOURCE.read_text(errors='replace')
    found = ENTRY.findall(text)
    if not found:
        raise SystemExit(f'{SOURCE}: no BuiltinSpec entries matched; has the record changed?')
    dupes = [n for i, n in enumerate(found) if n in found[:i]]
    if dupes:
        raise SystemExit(f'{SOURCE}: duplicate builtin names {sorted(set(dupes))}')
    return found


def as_rust(found, ar):
    body = '\n'.join(
        ('    ({!r}, {}),'.format(n, ar.get(n, 0))).replace("'", '"') for n in found)
    return ('// The compiler\'s built-in names and ARITIES, read from\n'
            '// Types/Builtins.codex by ladder builtins_probe.py. A call to one of\n'
            '// these is not an undefined name, and the arity is the shape of the\n'
            '// declared type -- a FunTy spine, with ForAllTy transparent -- so a\n'
            '// function-typed argument does not inflate it. An arity of 0 means the\n'
            '// entry declares no type. Re-run the probe after a pin change; do not\n'
            '// edit by hand.\n'
            f'pub const BUILTINS: [(&str, usize); {len(found)}] = [\n' + body + '\n];\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rust', action='store_true', help='emit the Rust table on stdout')
    a = ap.parse_args()
    found = names()
    ar = arities(SOURCE.read_text(errors='replace'))
    if a.rust:
        print(as_rust(found, ar), end='')
        return 0
    print(f'{len(found)} builtin names from {SOURCE}')
    untyped = [n for n in found if n not in ar]
    print(f'  {len(ar)} declare a type; {len(untyped)} do not')
    print('  ' + ', '.join(f'{n}/{ar.get(n, 0)}' for n in found[:8]) + ' ...')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
