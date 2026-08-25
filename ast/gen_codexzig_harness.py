#!/usr/bin/env python3
"""Generate CodexZigHarness.codex: one program, Codex source in, zig out.

`native/codexir` and `native/zigemit` are two processes joined by a pipe --
source to IR text, IR text to zig. This is both of them in one program, and
the join is not a pipe or a file but a single expression, because the two
halves already meet at a type rather than at a wire:

    emit-zig-chapter : IRChapter, List ATypeDef -> Text

`IRChapter` is the COMPILER's own type (codex/compiler/IR/IRChapter.codex) and
`ATypeDef` is the compiler's (Ast/AstNodes.codex). The plug's emitter has
always consumed the compiler's IR; IRTextParser exists only to rebuild those
values from text when the IR arrives over a serial ring, which is the plug's
situation and not ours. So this harness carries no parser and does no text
round trip -- it hands the front end's `ir` straight to the emitter.

That is the whole difference from CodexIrHarness, which this is otherwise a
copy of: where that one builds an IRTextMeta and calls emit-ir-chapter, this
calls emit-zig-chapter. The meta record disappears with the text wire, since
every field in it existed to be serialised.

Kept deliberately identical to CodexIrHarness otherwise, because the two-
process pipeline is this program's ORACLE: `codexir p.codex 2>p.ir && zigemit
p.ir 2>p.zig` must produce the same bytes this does. resolve=False and the
prune both matter for that -- they are what the plug is fed today.

ir-prune-unreachable-roots and czg-emit-roots are copied from opening.codex:1316
for the same reason CodexIrHarness copies them: that chapter cannot be bundled
beside a harness that defines `opening`. If the upstream list changes, this copy
is wrong and the IR loses a root.
"""
import pathlib

from emit_harness import frontend_source, HOSTED_DECK_BYTES

HERE = pathlib.Path(__file__).parent

out = f'''Chapter: CodexZigHarness

Section: Roots

 opening.codex:1316, copied because that chapter cannot ride along.

  czg-emit-roots : List Text
  czg-emit-roots = ["opening", "vb-capacity-auto", "vb-read-auto", "vb-write-auto"]

Section: Driver

  opening : [Console, FileSystem] Nothing = act
    src <- read-file-uni "/dev/stdin"
    {frontend_source("src", True, deck_bytes=HOSTED_DECK_BYTES, resolve=False)}
    in print-text (emit-zig-chapter (ir-prune-unreachable-roots ir czg-emit-roots) (ch.type-defs))
  end
'''

dest = HERE / 'CodexZigHarness.codex'
dest.write_text(out)
print(f'{dest}: {len(out)} bytes')
