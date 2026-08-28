#!/usr/bin/env python3
"""Generate CodexIrHarness.codex: the compiler as a program that emits IR.

zigc emits a CDX, which is what the Codex compiler is for. This emits IR-CCE
instead, which is what the PLUG is fed -- and that is the piece that takes the
seed out of the pipeline. With this and ZigEmitHosted, the chain

    prog.codex -> prog.ir -> prog.zig -> ELF

is three native processes and no VM at all.

The driver is emit-ir-cce's own sequence (opening.codex ~1694), minus the deck
and heap accounting and using the whole-text form rather than the streaming
one: a hosted process has no reason to avoid materialising the text, and
ir-print-defs exists to avoid exactly that.

Two things it must not skip, because they decide what the IR CONTAINS:

  ir-prune-unreachable-roots  -- the IR is what is reachable from the roots,
                                 not every def in the unit
  emit-ir-chapter's meta      -- chapter title, prose, section titles, ctor
                                 names, prose blocks, annotations and ground
                                 effects all ride the text wire

And one it MUST skip, for the same reason: the RESOLVE phase belongs to
compile-frontend-cdx, and compile-frontend-ir -- the sequence this stands in
for -- never runs it. Running it here rewrote every let binding whose nullary
ConstructedTy names a record into a RecordTy the seed driver leaves as ctd:
930 lines of the ir_to_x86 IR, and an IR wire the plug was never fed by the
oracle path. frontend_source's resolve flag carries the why.

ir-emit-roots is copied from opening.codex:1316 rather than cited, because
opening.codex cannot be bundled beside a harness that defines `opening`. If
that list changes upstream, this copy is wrong and the IR will be missing a
root -- which is the cost of standing in for the driver.

**And it HAD drifted, found by a cold read 2026-08-25.** Upstream carries six
roots; this copy carried four, missing `fat16-servicer-read` and
`fat16-servicer-write`. Nothing noticed because CodexZigHarness inherited the
same truncation, so both arms pruned the same two roots and agreed with each
other -- an oracle cannot see a mistake both of its arms make. Any subject
reaching either servicer lost it from the IR silently.
"""
import pathlib

from emit_harness import (frontend_source, HOSTED_DECK_BYTES, LIFT_PROSE,
                          halt_gate, halt_formatter)

HERE = pathlib.Path(__file__).parent

out = f'''Chapter: CodexIrHarness

Section: Halt

 The driver does not emit when the bag has errors -- opening.codex:1676-1678
 prints the codegen header and then `if bag-has-errors (fe.bag) then
 print-line-uni "CODEGEN-HALTED: errors in bag; no IR emitted"`. This harness
 did not, until 2026-08-26, and that is not a cosmetic gap.

 What it cost. native/codexir accepted a three-line program the seed refuses
 with CDX2001, and we reported that to Damian's compiler lane first as a
 soundness hole in their type checker and then as a miscompile in our plug.
 It was neither: native/codexzig, the same compiler from the same plug whose
 harness DOES read the bag, refuses it with the same code and the same
 wording. Their lane ran a four-seed sweep with a positive control to tell us
 we were wrong. The checker was never broken; this harness was deaf.

 What it costs quietly. corpus_run.py runs this tool, so a corpus program
 carrying a compiler error emitted IR anyway and we built, ran and scored its
 zig. Expect the clean count to FALL when this lands -- that is the gate
 working, not a regression.

{halt_formatter('irc', 'IR')}

Section: Roots

 opening.codex:1316, copied because that chapter cannot ride along.

  irc-emit-roots : List Text
  irc-emit-roots = ["opening", "vb-capacity-auto", "vb-read-auto", "vb-write-auto", "fat16-servicer-read", "fat16-servicer-write"]

Section: Driver

{LIFT_PROSE}

  opening : [Console, FileSystem] Nothing = act
    src <- read-file-uni "/dev/stdin"
    {frontend_source("src", True, deck_bytes=HOSTED_DECK_BYTES, resolve=False, lift=True)}
    {halt_gate('irc', 'IR')}let meta = IRTextMeta {{
      chapter-title = ch.chapter-title,
      prose = ch.prose,
      section-titles = ch.section-titles,
      ctor-names = rr.ctor-names,
      prose-blocks = ch.prose-blocks,
      annotations = ch.annotations,
      ground-effects = ch.ground-effects
    }}
    in let pruned = ir-prune-unreachable-roots ir irc-emit-roots
    in print-text (emit-ir-chapter pruned meta (ir-prune-unreachable-typedefs pruned (ch.type-defs)))
  end
'''

dest = HERE / 'CodexIrHarness.codex'
dest.write_text(out)
print(f'{dest}: {len(out)} bytes')
