#!/usr/bin/env python3
"""Derive Codex's `char-code` table by asking the compiler, not by assuming ASCII.

`char-code` is NOT ASCII and not Unicode. It is a 1-based frequency-ordered
alphabet private to Codex:

    1 newline, 2 space, 3..12 the digits in order,
    13..38 lowercase in FREQUENCY order  -- etaoinshrdlcumwfgypbvkjxqz
    39..64 uppercase, each exactly lowercase + 26
    65..96 punctuation, also by frequency

Two pieces of compiler source read as bugs until you know this and are correct:
`Syntax/Lexer.codex` classifies an uppercase word with `c >= char-code 'E' &
c <= char-code 'Z'`, which is a RANGE TEST -- 'E' is the lowest-coded uppercase
letter (39) and 'Z' the highest (64), so `cc-first-upper` is named for what it
is. And `Semantics/ChapterScoper.codex` lowercases with `c - 26` rather than
the ASCII 32.

**Why a ladder script and not a note.** `char-code` of a literal is
CONSTANT-FOLDED into the IR: `char-code 'A'` emits `(int-lit 41)`. Any front
end that folds it to 65 produces different IR from the golds on every program
that touches a character, and the diff would appear far from its cause. The
table is an input to the Rust front end, so it has to be derived and checked
rather than transcribed.

Reads native/codexir only -- no QEMU, no plug, ~0.05s.
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import LADDER

CODEXIR = LADDER / 'native' / 'codexir'
# The frequency order is the whole claim; asserting it is what makes this a
# check rather than a dump. Taken from the measurement, then re-derived from
# the compiler on every run and compared.
LOWER_BY_CODE = 'etaoinshrdlcumwfgypbvkjxqz'


def probe_source(chars):
    lines = ['Chapter: CharTable', '', 'Section: Values']
    for i, ch in enumerate(chars):
        lit = {"'": r"'\''", '\\': r"'\\'", '\n': r"'\n'"}.get(ch, f"'{ch}'")
        lines.append(f'  ct-{i:03d} : Integer = char-code {lit}')
    return '\n'.join(lines) + '\n'


def measure(chars):
    if not CODEXIR.is_file():
        raise SystemExit(f'{CODEXIR} is not there; build the natives first')
    # codexir writes the IR to STDERR and diagnostics to stdout, which is the
    # ladder's convention everywhere and surprises everyone once.
    r = subprocess.run([str(CODEXIR)], input=probe_source(chars).encode(),
                       capture_output=True, timeout=300)
    if r.returncode != 0 or not r.stderr:
        raise SystemExit(f'codexir failed: rc={r.returncode}\n'
                         f'{r.stdout.decode(errors="replace")[-2000:]}')
    ir = r.stderr.decode()
    out = {}
    for m in re.finditer(r'\(def "ct-(\d+)" "CharTable" \(params\) int-default '
                         r'\(int-lit (-?\d+)\)', ir):
        out[chars[int(m.group(1))]] = int(m.group(2))
    if len(out) != len(chars):
        raise SystemExit(f'probed {len(chars)} characters but the IR named '
                         f'{len(out)}; the def shape moved')
    return out


def check(table):
    """The structure, not just the values. A table that had silently become a
    permutation of itself would still be 96 distinct numbers."""
    problems = []
    if len(set(table.values())) != len(table):
        problems.append('two characters share a code')
    lower = {c: v for c, v in table.items() if 'a' <= c <= 'z'}
    upper = {c: v for c, v in table.items() if 'A' <= c <= 'Z'}
    if len(lower) != 26 or len(upper) != 26:
        problems.append('the alphabet is not 26 and 26')
    else:
        off = [c for c in lower if table[c.upper()] != table[c] + 26]
        if off:
            problems.append(f'uppercase is not lowercase+26 for: {" ".join(sorted(off))}')
        order = ''.join(sorted(lower, key=lambda c: lower[c]))
        if order != LOWER_BY_CODE:
            problems.append(f'lowercase code order is {order}, expected {LOWER_BY_CODE}')
    for d in '0123456789':
        if d in table and table[d] != 3 + int(d):
            problems.append(f'digit {d} is {table[d]}, expected {3 + int(d)}')
    return problems


def as_rust(table):
    """A Rust source table to be COMMITTED by hand, never generated in-repo.

    rust-codex-compiler is clean by construction -- no code generation inside
    it -- so the ladder emits and the repo receives. Re-run this to check the
    committed copy after any seed change.
    """
    rows = [None] * 128
    for ch, v in table.items():
        rows[ord(ch)] = v
    body = ',\n'.join(
        f'    {rows[i] if rows[i] is not None else 0}, // {i:3} '
        + (repr(chr(i)) if rows[i] is not None else '(not in the alphabet)')
        for i in range(128))
    return ('// Codex `char-code`, measured from the compiler by ladder '
            'charcode_probe.py.\n'
            '// NOT ASCII: a frequency-ordered private alphabet, 1..96. 0 means '
            'the byte\n// has no code. See that script for why this cannot be '
            'transcribed by hand.\n'
            'pub const CHAR_CODE: [u8; 128] = [\n' + body + '\n];\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rust', action='store_true',
                    help='emit the Rust table on stdout instead of the report')
    ap.add_argument('--json', action='store_true', help='emit JSON on stdout')
    args = ap.parse_args()

    chars = [chr(c) for c in range(32, 127)] + ['\n']
    table = measure(chars)
    problems = check(table)
    if problems:
        for p in problems:
            print(f'CHAR-CODE TABLE MOVED: {p}', file=sys.stderr)
        return 1

    if args.rust:
        sys.stdout.write(as_rust(table))
    elif args.json:
        json.dump(table, sys.stdout, indent=0, sort_keys=True)
        sys.stdout.write('\n')
    else:
        print(f'char-code: {len(table)} characters, codes '
              f'{min(table.values())}..{max(table.values())}, all distinct')
        print(f'lowercase by code: {LOWER_BY_CODE}')
        print(f"uppercase = lowercase + 26; 'E'={table['E']} is the lowest, "
              f"'Z'={table['Z']} the highest")
        print(' '.join(f'{v}:{ch!r}' for ch, v in
                       sorted(table.items(), key=lambda kv: kv[1])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
