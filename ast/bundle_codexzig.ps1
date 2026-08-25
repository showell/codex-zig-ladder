# The single-program transpiler: Codex source in, zig out, one binary.
#
# codexir's chapter set (via bundle_codexir.ps1, so the list stays in one
# place) plus ONE chapter: the zig emitter. Everything else the emitter needs,
# the hosted compiler already has -- which is the whole reason this works.
#
# NOT IRTextParser. emit-zig-chapter takes the compiler's own IRChapter, so a
# bundle that carries the compiler has nothing to parse; the parser exists to
# rebuild those values when the IR arrives over a serial ring, which is the
# plug's situation and not ours. Leaving it out also drops seven name
# collisions between it and the compiler's own Lexer/Parser -- tokenize,
# parse-expr, parse-type, parse-type-atom, parse-type-args,
# parse-record-fields-loop, scan-string-body -- two independent parsers that
# picked the same obvious names.
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
# One delta remains and it is deliberate: the compiler's strip-fun-args
# carries an `is ForAllEff (id) (body)` arm the plug's copy lacks, so this
# emitter strips one more constructor than native/zigemit does. Inert for any
# program with no effect polymorphism in a stripped position; the two-process
# pipeline is the oracle that says whether it is inert for a given one.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'bundle_codexir.ps1') `
    -Harness 'CodexZigHarness.codex' `
    -OutName 'codexzig-subject.codex' `
    -PlugName 'codexzig-subject' `
    -MoreChapters @('codex/plugs/zig/ZigEmitter.codex')
