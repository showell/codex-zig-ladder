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


# A wrapper that can HIDE AN ARROW has to be transparent or the arity comes out
# 0. Everything else is an ordinary type constructor and ends the spine.
#
# A head in NEITHER set is REFUSED rather than quietly counted as 0, because
# that silence is exactly what went wrong: `ForAllEff` was missing here, so
# `process-spawn :: ForAllEff 0 (FunTy ...)` was read as taking no arguments,
# and the interpreter built a one-argument function for a value. Nothing about
# an arity of 0 says whether it was read or defaulted.
TRANSPARENT = {'ForAllTy', 'ForAllEff', 'EffectfulTy'}
ENDS_THE_SPINE = {'TypeVar', 'ListTy', 'VectorTy', 'ConstructedTy', 'PropEqTy',
                  'VectorMaskTy', 'LinkedListTy', 'TypeApply', 'RecordTy',
                  # `deck-record T` is a record ON THE DECK -- a wrapper, but
                  # around a type and never around an arrow. `s-new :: ForAllTy 0
                  # (deck-record (ConstructedTy schan ...))` takes no arguments,
                  # and upstream's own emitter agrees: `emit-helper-call-0`.
                  'deck-record'}


def _arity(form, name):
    """How many arguments the FunTy spine takes.

    A builtin's arity is not written down anywhere; it is the shape of its
    type. A `FunTy` contributes one and recurses on its RESULT -- so a
    function-typed ARGUMENT (map-list's first) does not inflate the count.
    """
    if not isinstance(form, list) or not form:
        return 0
    head = form[0]
    if head == 'FunTy':
        return 1 + _arity(form[-1], name)
    if head in TRANSPARENT:
        return _arity(form[-1], name)
    if head in ENDS_THE_SPINE:
        return 0
    raise SystemExit(f'{SOURCE}: {name} has type head {head!r}, which this probe '
                     'does not know. Add it to TRANSPARENT if it can wrap an '
                     'arrow, or to ENDS_THE_SPINE if it cannot.')


def arities(text):
    """name -> arity, for every builtin that DECLARES a type.

    A name absent from the result declares `bs-type = None` and has no arity to
    read. **That is not the same as an arity of 0** and the two must not be
    collapsed: 23 entries declare a plain type -- `get-ticks :: Integer`,
    `uefi-read-key-ex :: Integer`, `__deck-enter :: Nothing`, `assume :: Proof`
    -- which is a NULLARY builtin, a value rather than a function. Only 8 of
    the 263 are genuinely undeclared: True, False, Nothing, open-file,
    close-file, read-all, now, random-integer.

    A bare type name is read here as well as a parenthesised one. Requiring a
    `(` sent all 23 of those down the undeclared path, where they picked up an
    arity of 0 by DEFAULT and looked identical to the ones that had earned it.

    Split per ENTRY rather than pairing a name with the next `bs-type` found: a
    name-then-type search reads straight past an undeclared entry into the
    following one's type -- which gave `__narrow` an arity of 0 and would have
    made every call to it wrong.
    """
    out = {}
    for chunk in text.split('BuiltinSpec {')[1:]:
        m = re.match(r'\s*bs-name\s*=\s*"([^"]*)"', chunk)
        if not m:
            continue
        t = re.search(r'bs-type\s*=\s*Just\s*', chunk)
        if not t:
            continue
        if chunk[t.end():t.end() + 1] != '(':
            out[m.group(1)] = 0  # a bare type name: nullary, and DECLARED so.
            continue
        form, _ = _sexp(chunk, t.end())
        out[m.group(1)] = _arity(form, m.group(1))
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
        '    ("{}", {}),'.format(n, f'Some({ar[n]})' if n in ar else 'None')
        for n in found)
    return ('// The compiler\'s built-in names and ARITIES, read from\n'
            '// Types/Builtins.codex by ladder builtins_probe.py. A call to one of\n'
            '// these is not an undefined name, and the arity is the shape of the\n'
            '// declared type -- a FunTy spine, with ForAllTy, ForAllEff and\n'
            '// EffectfulTy transparent -- so a function-typed argument does not\n'
            '// inflate it.\n'
            '//\n'
            '// `Some(0)` IS NOT `None`. `Some(0)` is a builtin whose declared type\n'
            '// is not an arrow -- `get-ticks : Integer` -- so a reference to it is a\n'
            '// VALUE and not a function of one argument. `None` is one of the eight\n'
            '// that declare no type at all. Re-run the probe after a pin change; do\n'
            '// not edit by hand.\n'
            f'pub const BUILTINS: [(&str, Option<usize>); {len(found)}] = [\n'
            + body + '\n];\n')


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
    nullary = [n for n in found if ar.get(n) == 0]
    print(f'  {len(ar)} declare a type; {len(untyped)} do not: ' + ', '.join(untyped))
    print(f'  {len(nullary)} are NULLARY -- a declared type that is not an arrow')
    print('  ' + ', '.join(f'{n}/{ar[n]}' for n in found[:8] if n in ar) + ' ...')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
