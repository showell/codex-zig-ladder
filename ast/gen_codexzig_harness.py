#!/usr/bin/env python3
"""Generate CodexZigHarness.codex: one program, Codex source in, zig out.

`native/codexir` and `native/zigemit` are two processes joined by a pipe --
source to IR text, IR text to zig. This is both of them in one program, with
the pipe replaced by a `let`: emit the IR text, parse it back, emit zig. Same
two bodies, same order, no file and no second process.

**The round trip is deliberate, and the first version did not have it.** The
seam looked like it could be a direct hand-off, because the two halves meet at
a type -- `emit-zig-chapter : IRChapter, List ATypeDef -> Text` takes the
COMPILER's own IRChapter, so the front end has the value already. That version
worked on 85 ordinary programs and then failed on the one that matters: given
its own bundle it emitted a monomorphic `SortPartitionS` whose fields still
said `a`, which is zig that does not compile.

The reason is that the text wire is NOT an identity -- it DERIVES what the AST
does not carry. `IRTextEmitter.codex:404-406` computes a record's implicit type
parameters from its field types as it serialises, and the annotations on its
use sites carry type args the in-memory form renders without.
`foreword/core/Sort.codex` declares `SortPartition = record { list : List a,
pivot : Integer }` -- no parameter list at all, `a` free in the fields -- so
only the wire ever knew. Copying one derivation into this harness fixed the
declaration and left the use sites; copying the next would be a second rule
duplicated from the compiler, and then a third.

So the harness stops copying rules and uses the wire, in memory. What that buys
is bigger than correctness on one type: this program now runs the SAME code in
the SAME order as `codexir | zigemit`, so agreeing with the pipeline byte for
byte is structural rather than measured. That is why carrying IRTextParser is
worth the upstream rename it needed -- its unprefixed `tokenize`, `parse-expr`
and `parse-type` collided with the compiler's own lexer and parser, which is
what made the direct hand-off look like the only option in the first place.

resolve=False and the prune both matter and mirror CodexIrHarness, because the
pipeline is the oracle: `./codexzig_build.sh --check <prog.codex>` runs both
ways and byte-compares.

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
    in let meta = IRTextMeta {{
      chapter-title = ch.chapter-title,
      prose = ch.prose,
      section-titles = ch.section-titles,
      ctor-names = rr.ctor-names,
      prose-blocks = ch.prose-blocks,
      annotations = ch.annotations,
      ground-effects = ch.ground-effects
    }}
    in let ir-text = emit-ir-chapter (ir-prune-unreachable-roots ir czg-emit-roots) meta (ch.type-defs)
    in let parsed = parse-ir-chapter ir-text
    in print-text (emit-zig-chapter (parsed.chapter) (parsed.type-defs))
  end
'''

dest = HERE / 'CodexZigHarness.codex'
dest.write_text(out)
print(f'{dest}: {len(out)} bytes')
