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

TYPE_DEFS = """Section: Type Defs

 The one thing the direct hand-off needs, and it was found by the fixed
 point: codexzig transpiling its own bundle emitted `const SortPartitionS =
 struct` whose fields still said `a`, which is zig that does not compile.

 The IR text emitter DERIVES a record's implicit type parameters as it
 serialises. IRTextEmitter.codex:404-406 computes `inferred` with
 ir-collect-rec-field-tparams and ir-emit-tparams-text:386 takes the
 explicit list if there is one and the inferred list otherwise; the plug
 parses them back, so every emitter downstream of the text wire sees them.
 foreword/core/Sort.codex declares `SortPartition = record { list : List a,
 pivot : Integer }` -- no parameter list at all, `a` free in the fields --
 so the front end's own ATypeDef carries tparams = [] and only the wire
 ever knew better.

 So the text round trip is NOT an identity: it ADDS information. This
 applies the same derivation once, on the way in, which is the whole of
 what the wire was doing for us. It is a COPY of a rule that lives in the
 text emitter, and that is worth saying out loud -- the AST does not carry
 what the serialiser knows, so any consumer of the AST that is not the text
 emitter sees an incomplete type.

  czg-names : List Text, Integer, List Name -> List Name
  czg-names (xs) (i) (acc) =
   if i >= list-length xs then acc
   else czg-names xs (i + 1) (list-push acc (make-name (list-at xs i)))

  czg-fix-typedef : ATypeDef -> ATypeDef
  czg-fix-typedef (td) =
   when td
    is ARecordTypeDef (name) (tparams) (fields) (is-mut) (s) ->
     if list-length tparams > 0 then td
     else let inferred = ir-collect-rec-field-tparams fields 0 (list-length fields) []
     in ARecordTypeDef name (czg-names inferred 0 []) fields is-mut s
    is AVariantTypeDef (name) (tparams) (ctors) (s) ->
     if list-length tparams > 0 then td
     else let inferred = ir-collect-var-ctor-tparams ctors 0 (list-length ctors) []
     in AVariantTypeDef name (czg-names inferred 0 []) ctors s
    is otherwise -> td

  czg-fix-typedefs : List ATypeDef, Integer, List ATypeDef -> List ATypeDef
  czg-fix-typedefs (xs) (i) (acc) =
   if i >= list-length xs then acc
   else czg-fix-typedefs xs (i + 1) (list-push acc (czg-fix-typedef (list-at xs i)))
"""

out = f'''Chapter: CodexZigHarness

{TYPE_DEFS}
Section: Roots

 opening.codex:1316, copied because that chapter cannot ride along.

  czg-emit-roots : List Text
  czg-emit-roots = ["opening", "vb-capacity-auto", "vb-read-auto", "vb-write-auto"]

Section: Driver

  opening : [Console, FileSystem] Nothing = act
    src <- read-file-uni "/dev/stdin"
    {frontend_source("src", True, deck_bytes=HOSTED_DECK_BYTES, resolve=False)}
    in print-text (emit-zig-chapter (ir-prune-unreachable-roots ir czg-emit-roots) (czg-fix-typedefs (ch.type-defs) 0 []))
  end
'''

dest = HERE / 'CodexZigHarness.codex'
dest.write_text(out)
print(f'{dest}: {len(out)} bytes')
