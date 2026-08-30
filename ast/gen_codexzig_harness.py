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

from emit_harness import (frontend_source, HOSTED_DECK_BYTES, LIFT_PROSE,
                          halt_gate, halt_formatter, notices_reporter)

HERE = pathlib.Path(__file__).parent

out = f'''Chapter: CodexZigHarness

Section: Halt

 The driver this stands in for does not emit when the bag has errors:
 opening.codex:1676-1678 prints the codegen error header and the notices,
 and then `if bag-has-errors (fe.bag) then print-line-uni "CODEGEN-HALTED:
 errors in bag; no IR emitted"`. This harness skipped that gate until
 2026-08-25, and a cold read found what it costs: a file reading `this is
 not codex at all` produced 36,697 bytes of plausible zig and exit 0, and so
 did a program calling a function that does not exist. For a tool that is
 handed to other people, the first thing they will feed it is a program with
 a mistake in it.

 The bags are the ones the driver merges, reached from what the frontend
 already binds: lex errors from `toks.errors` (opening.codex:449 wraps the
 same list), the parse bag from `doc.parse-bag` (:485), the resolve bag from
 `rr.bag`, and the type checker's from `cr.state.bag` -- which is what
 `check-bag0` at :620 merges. The PRINTERS are not reachable: they live in
 opening.codex, which cannot be bundled beside a harness defining `opening`,
 so this prints the count and the first error rather than the driver's full
 report.

 CODEGEN-HALTED is the marker the rest of the tree already refuses on by
 name (ast/f4_boot.py), which is why the text is that and not a new word.

{halt_formatter('czg', 'zig')}

{notices_reporter('czg')}

Section: Roots

 opening.codex:1316, copied because that chapter cannot ride along.

  czg-emit-roots : List Text
  czg-emit-roots = ["opening", "vb-capacity-auto", "vb-read-auto", "vb-write-auto", "fat16-servicer-read", "fat16-servicer-write"]

Section: Driver

{LIFT_PROSE}

  opening : [Console, FileSystem] Nothing = act
    src <- read-file-uni "/dev/stdin"
    {frontend_source("src", True, deck_bytes=HOSTED_DECK_BYTES, resolve=False, lift=True)}
    {halt_gate('czg', 'zig')}let meta = IRTextMeta {{
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
    in act
      write-binary (czg-report czg-bag)
      print-text (emit-zig-chapter (parsed.chapter) (parsed.type-defs))
    end
  end
'''

dest = HERE / 'CodexZigHarness.codex'
dest.write_text(out)
print(f'{dest}: {len(out)} bytes')
