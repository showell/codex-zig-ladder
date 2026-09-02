#!/usr/bin/env python3
"""Generate IrToX86Harness.codex: the x86-64 back end over two subjects.

This is a UNIT, and it carries two rungs. `ir_to_x86_on_fib` compiles
eighteen lines of fib; `ir_to_x86_on_cce` compiles a real compiler chapter
and lives in gen_ir_to_x86_on_cce_harness.py. They were separate harnesses in separate bundles until
2026-08-18, which meant compiling the same 2.4 MB of compiler twice to ask two
questions of it. The subjects are what differ, so the subjects are what the
unit now carries.

The harness body is emit_harness.py's; the only thing this file owns is the
eighteen lines below and the pairing.

fib is chosen for what it does NOT need. Integers are machine words, so its
arithmetic is a bare `add`; its two self-calls are its only fixup surface;
and it touches no rodata, no runtime helper and no absolute address. That is
what lets f3_run.zig carve it out of the emitted buffer and call it. double
rides along as a five-byte frameless leaf.

LowerStubs is NOT bundled for this milestone -- the real Types/Builtins
rides along because the whole x86-64 code generator does, so bs-emit's
referents finally exist. gen_lower_harness.py is still invoked for its
LowerHarness (the fib rung's sibling), not for the stub."""
import pathlib

import gen_ir_to_x86_on_cce_harness
from emit_harness import harness_source

HERE = pathlib.Path(__file__).parent

FIB = (
    'Chapter: Fib\n'
    '\n'
    'Section: Math\n'
    '  fib : Integer -> Integer\n'
    '  fib (n) =\n'
    '   if n <= 1 then n\n'
    '   else fib (n - 1) + fib (n - 2)\n'
    '\n'
    '  double : Integer -> Integer\n'
    '  double (n) = n + n\n'
    '\n'
    'Section: Main\n'
    '  opening : [Console] Nothing = act\n'
    '   print-line-uni (show (fib 20))\n'
    '  end\n'
)

# The chapter name and walker prefix ('FibxHarness', 'fibx') reach the
# compiled unit as Codex identifiers and are not the rung's name; they stay.
# probe=True is a MEASUREMENT, not a shipping setting: it moves emission
# inside the act block so the deck geometry prints BEFORE the emit is forced.
# Revert once the ir_to_x86 !EXC=06 is understood; no truth may be banked
# while it is on.
out = harness_source('FibxHarness', 'fibx',
                     [('ir_to_x86_on_fib', FIB),
                      ('ir_to_x86_on_cce', gen_ir_to_x86_on_cce_harness.SUBJECT)],
                     probe=True)
dest = HERE / 'IrToX86Harness.codex'
dest.write_text(out)
print(f'{dest}: {len(out)} bytes, subjects ir_to_x86_on_fib + ir_to_x86_on_cce')
