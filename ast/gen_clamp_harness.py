#!/usr/bin/env python3
"""The clamp subject: the whole compiler, compiling plug-oracle-arith.

This rung no longer has a harness of its own. It rides in the unit
gen_whole_harness.py builds, as the second subject that unit's driver runs,
so the 2.58 MB of compiler underneath it is compiled once instead of twice.
What this file owns is the SUBJECT, which is the part that attributes the
failure.

This exists to attribute one failure. The hosted compiler (zigc) compiles
codex/test/plug-oracle-arith.codex into a binary that agrees for seventeen
values and then faults with !EXC=06 -- an invalid opcode -- where the
seed-compiled binary prints 100 / -100 / 42. Those three come from `gauge`,
whose record field is `Integer between -100 and 100 clamping`.

Two things could produce that, and they need separating:

  (a) the zig plug mis-transpiled the clamping path of the x86 emitter, so
      the transpiled compiler emits different x86 than bare metal does;
  (b) the transpilation is faithful and the harness is at fault -- it is not
      opening.codex and skips proof pruning and dropped-def handling -- or
      current source differs from the frozen seed here.

This rung is the same harness on both arms. If the arms agree, the
transpilation is faithful and (b) holds; if they differ, (a) does, and the
diff names the instruction.
"""
from roots import CODEX

SOURCE = CODEX / 'codex' / 'test' / 'plug-oracle-arith.codex'
SUBJECT = SOURCE.read_text()

if __name__ == '__main__':
    print(f'clamp is a subject, not a unit: {SOURCE.name}, '
          f'{SUBJECT.count(chr(10))} lines.')
    print('gen_whole_harness.py builds the unit that runs it.')
