#!/usr/bin/env python3
"""Print the `(param ...)` cells of every lifted lambda in a probe's IR wire.

The question this answers is "what type did the COMPILER put on the wire for
a lambda parameter", which is the whole of H2. It is deliberately separate
from `corpus_run.py` and from the emitter: no zig is generated and no plug
opinion is involved, so a cell reading `error` here is the compiler's own
answer and not our rendering of it.

WHICH ARM. This reads `native/codexir`, which is the compiler as OUR BACKEND
renders it, not the seed. That is the right instrument for a COMPILER SOURCE
change, because the seed cannot carry one -- the seed is the shipped compiler
and a patch to `Lowering.codex` is not in it. It is the wrong instrument for
"what does the shipped compiler do", which is `run_seed_probe.sh`'s question.
The harness was eliminated as a confound on 2026-08-27: `ast/CodexIrHarness`
reproduces the driver's check-lower boundary, sort and deep-resolve included.

    ./h2_wire.py findings/probe-h2-lambda-types.codex
    ./h2_wire.py <probe> --save wire.txt
"""

import argparse
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from cite_resolve import resolve
from ladder_root import LADDER

CODEXIR = LADDER / 'native' / 'codexir'
# `(def "name" (params (param "n" <type>) ...)` -- the type runs to the close
# paren that balances its own opener, so it is taken by scanning rather than
# by a regex, which cannot count parentheses.
DEF = re.compile(r'\(def "([^"]*)"')
PARAM = re.compile(r'\(param "([^"]*)" ')


def balanced(text, start):
    """The substring beginning at `start` ('(' or an atom) through its close."""
    if text[start] != '(':
        end = start
        while end < len(text) and text[end] not in ' )':
            end += 1
        return text[start:end]
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]


def cells(wire, only_lifted=True):
    out = []
    for m in DEF.finditer(wire):
        name = m.group(1)
        if only_lifted and not name.startswith('__lam'):
            continue
        # the def's own extent, so a nested def cannot leak its params in
        body = balanced(wire, m.start())
        head = body[:body.find('(body')] if '(body' in body else body
        for p in PARAM.finditer(head):
            out.append((name, p.group(1), balanced(head, p.end())))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('probe')
    ap.add_argument('--save', help='write the whole wire here as well')
    ap.add_argument('--all-defs', action='store_true',
                    help='every definition, not only the lifted lambdas')
    a = ap.parse_args()

    if not CODEXIR.exists():
        raise SystemExit(f'no {CODEXIR}; run ./native_build.sh first')
    unit, miss = resolve(pathlib.Path(a.probe))
    if miss:
        raise SystemExit(f'UNRESOLVED cites: {miss}')
    r = subprocess.run([str(CODEXIR)], input=unit.encode(),
                       capture_output=True, timeout=300)
    # The wire goes to stderr; stdout is empty. A silent failure here reads
    # exactly like a program with no lambdas, so it is refused loudly.
    if r.returncode != 0 or not r.stderr:
        raise SystemExit(f'codexir failed: rc {r.returncode}, '
                         f'{len(r.stderr)} bytes of wire')
    wire = r.stderr.decode('utf-8', 'replace')
    # A refused compile exits 0 and writes its diagnostics where the wire
    # would go. Reading that as a wire finds no lifted lambdas and reports
    # `0 of 0 parameter cells say error`, which is a clean bill of health for
    # a program that never compiled.
    halted = next((l for l in wire.splitlines()
                   if l.startswith('CODEGEN-HALTED')), None)
    if halted:
        raise SystemExit(f'the compiler REFUSED this probe, there is no wire to read:\n  {halted}')
    if a.save:
        pathlib.Path(a.save).write_text(wire)
    print(f'{len(wire)} bytes of wire')
    got = cells(wire, only_lifted=not a.all_defs)
    if not got:
        print('no lifted lambdas in this wire')
    width = max((len(n) for n, _, _ in got), default=8)
    for name, param, ty in got:
        flag = '  <-- ERROR' if ty == 'error' else ''
        print(f'  {name:<{width}}  {param:<8} {ty}{flag}')
    print(f'{sum(1 for _, _, t in got if t == "error")} of {len(got)} '
          f'parameter cells say `error`')


if __name__ == '__main__':
    main()
