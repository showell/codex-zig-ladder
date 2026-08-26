# The single-program transpiler: Codex source in, zig out, one binary.
#
# codexir's chapter set (via bundle_codexir.ps1, so the list stays in one
# place) plus ONE chapter: the zig emitter. Everything else the emitter needs,
# the hosted compiler already has -- which is the whole reason this works.
#
# IRTextParser IS carried, and that was the whole argument. The seam looked
# like it could skip the parser -- emit-zig-chapter takes the compiler's own
# IRChapter, so the front end holds the value already -- but the text wire
# DERIVES what the AST does not carry (IRTextEmitter.codex:404-406 infers a
# record's implicit type parameters as it serialises), and a direct hand-off
# emits zig that does not compile for any type declared the way
# foreword/core/Sort.codex declares SortPartition. Going through the wire in
# memory makes this program the same code in the same order as
# codexir | zigemit, so byte-agreement with the pipeline is structural.
#
# Carrying it needed an upstream rename: its unprefixed tokenize, parse-expr,
# parse-type, parse-act-stmts, parse-handle-clauses and four more collided
# with the compiler's own Lexer and Parser -- which is what made the direct
# hand-off look like the only option. IRTextParser now carries the ir- prefix
# its counterpart IRTextEmitter already uses on 99 of its 106 definitions.
#
# NOT PlugTypes either, and that one was measured rather than assumed. It has
# exactly two sections and this bundle needs neither:
#
#   Emitter Helpers -- ApplyChain and collect-apply-chain are in
#     Emit/CodexEmitter.codex, strip-fun-args in Types/CodexTypeHelpers.codex.
#     ApplyChain would FORCE the issue anyway: a duplicate type is CDX3001.
#   Plug Utilities  -- bytes-to-text* are called by ZigPlug.codex, a body this
#     bundle does not carry (ZigEmitter mentions them only in a comment); and
#     deck-record is a second identity copy of Core/PhaseAllocator.codex's.
#
# That deck-record copy is the one worth naming. X86_64Chapter.codex:1155-1157
# sets deck-record-intrinsic from `pa-slug == dr-slug` -- init-phase-allocator
# and deck-record resolving to the SAME chapter. A second deck-record in the
# subject makes which chapter dr-slug names depend on scan order, and the
# answer we want is only the one that happens to come first. That exact
# condition, switched the wrong way, once turned the deck discipline off
# across the whole bundled compiler and stayed invisible for thirteen rungs
# (see bundle_ir_to_x86.ps1). ZigEmitter never CALLS deck-record -- it
# intercepts the name while emitting -- so dropping the copy costs nothing.
#
# One source difference remains and it is INERT, statically, for every
# program -- which is worth stating as a proof rather than a per-program
# hedge, because it read as a live risk until someone grepped. The compiler's
# strip-fun-args (Types/CodexTypeHelpers.codex) carries an
# `is ForAllEff (id) (body)` arm that PlugTypes' copy lacks, and this bundle
# carries the compiler's. But strip-fun-args has NO call site in the emitter:
# in the zigemit bundle it is defined and never called, and the only
# emitter-side caller here is strip-fun-args-emitter, a different function.
# The one real caller is X86_64Chapter.codex, which the zig emitter never
# runs. So the arm cannot reach the emitted bytes and no oracle is needed to
# say so.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'bundle_codexir.ps1') `
    -Harness 'CodexZigHarness.codex' `
    -OutName 'codexzig-subject.codex' `
    -PlugName 'codexzig-subject' `
    -MoreChapters @(
        'codex/plugs/common/IRTextParser.codex',
        'codex/plugs/zig/ZigEmitter.codex')
