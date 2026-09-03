# Bundle the ir_to_x86 subject: lower's chapter set plus the whole x86-64
# back end -- Lir, ResolveTypes, the real Builtins table, EmitAllocator,
# CdxWriter and all fourteen X86_64 pages -- so the harness runs the
# driver's own x86-64-emit-cdx and finalize over each of its programs and
# dumps the CDX it emits. bundle_passes_to_x86.ps1 calls this with extra
# chapters and its own harness; README "The twelve units" says what each
# holds.
param(
    [string]$Harness = 'IrToX86Harness.codex',
    [string]$OutName = 'ir_to_x86-subject.codex',
    [string]$PlugName = 'ir_to_x86-subject',
    # Chapters appended after the list below, and the BootPaint to carry.
    # The whole-compiler rung adds the middle end and swaps the stub for the
    # real painter; everything else about the unit is identical, so it stays
    # one list rather than two that have to be kept in step.
    [string[]]$ExtraChapters = @(),
    # Sections to drop from a named ExtraChapter. A plug chapter carries its
    # own copies of helpers it cannot cite when it is bundled standalone; in a
    # bundle that already has the originals those copies are duplicates, and a
    # duplicate TYPE is CDX3001, a hard error. Same mechanism the BootPaint and
    # AstNodes 'Deck Copies' drop already use.
    [hashtable]$ExtraDrops = @{},
    [string]$BootPaint = 'BootPaintStubs.codex',
    # OPT IN to carrying Chapter: Opening. A subject only wants the driver if
    # its harness CALLS the driver; carrying it otherwise costs a fifth of the
    # subject's lines and every byte of that is compiled by a guest. zigc asks
    # for it, the rungs still standing in for the driver do not.
    [switch]$WithDriver
)
$ErrorActionPreference = 'Stop'
$ladder = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
$repo = (& python3 (Join-Path $ladder 'ladder_root.py') codex).Trim()
$here = $PSScriptRoot

. "$repo/codex/plugs/common/plug-build-lib.ps1"

$lines = [System.Collections.Generic.List[string]]::new()
# This milestone swaps LexStubs for the real Core/PhaseAllocator.codex,
# and the reason is the cite rather than the functions. Desugarer.codex
# cites 'Codex chapter Phase Allocator', which LexStubs cannot satisfy
# whatever it defines -- a cite names a chapter, not a symbol. Carrying
# both would then define deck-record and deck-short-of twice, so the stub
# steps aside. Nothing else in the unit cites Phase Allocator, which is
# why lex and parse never needed it.
#
# The real deck-short-of reads __deck-pos where the stub did not, and that
# is harmless here: the harness passes a 0 ceiling, for which both answer
# False.
# CCE is NOT listed here, though it was until Update 46 made it fail.
# plug-build-lib carries a foreword chapter automatically once something
# cites it, and this bundle cites it, so listing it as well put CCE in twice
# -- once as Foreword--CCE and once as Parsmi--CCE. Two quires, two copies of
# every definition in it.
#
# That was visible the whole time as CDX3006 warnings and we read past them.
# The value duplicates only warn; CharClass is a TYPE, and Update 46 makes a
# duplicate type definition CDX3001, a hard error. lir lists CCE too and is
# right to: nothing there cites it, so the explicit copy is the only one.
# ListUtils is NOT listed here. Core/Collections.codex cites Foreword
# chapter ListUtils and Resolve-PlugForewords resolves that cite, so this
# bundle already carries Foreword--ListUtils; listing it again put a second
# copy in the Parsmi quire: two chapters
# defining list-map, fold-list, list-take and the rest, which is what every
# CDX3006 in this rung's log was telling us. See bundle_parse.ps1, where the
# explicit listing IS the only copy and stays.
foreach ($ch in @('codex/compiler/Core/OffsetTable.codex',
                  'codex/compiler/Core/VmProfile.codex',
                  'codex/compiler/Types/Builtins.codex',
                  'codex/compiler/IR/Lir.codex',
                  'codex/compiler/Emit/EmitAllocator.codex',
                  'codex/compiler/Emit/CdxWriter.codex',
                  'codex/compiler/Emit/X86_64Boot.codex',
                  'codex/compiler/Emit/X86_64Encoder.codex',
                  'codex/compiler/Emit/X86_64State.codex',
                  'codex/compiler/Emit/X86_64.codex',
                  'codex/compiler/Emit/X86_64Builtins.codex',
                  'codex/compiler/Emit/X86_64Chapter.codex',
                  'codex/compiler/Emit/X86_64Compound.codex',
                  'codex/compiler/Emit/X86_64Helpers.codex',
                  'codex/compiler/Emit/X86_64IO.codex',
                  'codex/compiler/Emit/X86_64IPCHelpers.codex',
                  'codex/compiler/Emit/X86_64InsnCount.codex',
                  'codex/compiler/Emit/X86_64Lir.codex',
                  'codex/compiler/Emit/X86_64ListHelpers.codex',
                  'codex/compiler/Emit/X86_64ProcessHelpers.codex',
                  'codex/compiler/Emit/X86_64TextHelpers.codex',
                  'codex/compiler/Core/BuildSettings.codex',
                  'codex/compiler/Core/Phase.codex',
                  'codex/compiler/Core/PhaseAllocator.codex',
                  'codex/compiler/Core/TextFormat.codex',
                  'codex/compiler/Core/CdxCodes.codex',
                  'codex/compiler/Core/Severity.codex',
                  'codex/compiler/Core/SourceText.codex',
                  'codex/compiler/Core/Name.codex',
                  'codex/compiler/Core/Diagnostic.codex',
                  'codex/compiler/Core/DiagnosticBag.codex',
                  'codex/compiler/Core/Collections.codex',
                  'codex/compiler/Types/CodexType.codex',
                  'codex/compiler/Types/CodexTypeHelpers.codex',
                  'codex/compiler/IR/IRChapter.codex',
                  'codex/compiler/Syntax/Token.codex',
                  'codex/compiler/Syntax/Lexer.codex',
                  'codex/compiler/Syntax/SyntaxNodes.codex',
                  'codex/compiler/Syntax/ParserCore.codex',
                  'codex/compiler/Syntax/ParserExpressions.codex',
                  'codex/compiler/Syntax/Parser.codex',
                  'codex/compiler/Ast/AstNodes.codex',
                  'codex/compiler/Ast/Desugarer.codex',
                  'codex/compiler/Core/SkipListText.codex',
                  'codex/compiler/Semantics/ChapterScoper.codex',
                  'codex/compiler/Semantics/NameResolver.codex',
                  'codex/compiler/Types/CodexTypeTree.codex',
                  'codex/compiler/Types/TypeEnv.codex',
                  'codex/compiler/Types/Unifier.codex',
                  'codex/compiler/Types/TypeChecker.codex',
                  'codex/compiler/Types/TypeCheckerInference.codex',
                  'codex/compiler/IR/LoweringTypes.codex',
                  'codex/compiler/IR/Lowering.codex',
                  # RESOLVE: rewrite-ir-defs. Every harness runs the driver's
                  # resolve phase now, so every subject needs this chapter --
                  # it used to arrive only via the whole rung's extras.
                  'codex/compiler/IR/ResolveTypes.codex',
                  'codex/compiler/Emit/IRTextEmitter.codex')) {
    Add-PlugChapter -Lines $lines -Path (Join-Path $repo $ch) -Quire 'Parsmi'
}
# Update 42 gave PhaseAllocator a cite of Codex chapter BootPaint, and a cite
# names a chapter, so the unit has to carry one. See BootPaintStubs.codex for
# why it is a stub and not the real 341-line screen painter.
foreach ($ch in $ExtraChapters) {
    $drop = if ($ExtraDrops.ContainsKey($ch)) { $ExtraDrops[$ch] } else { @() }
    Add-PlugChapter -Lines $lines -Path (Join-Path $repo $ch) -Quire 'Parsmi' -DropSections $drop
}
# THE DRIVER, carried only when the harness CALLS it.
#
# Update 55 split the entry point out -- opening.codex defines `codex-opening`
# and a fourteen-line EntryPoint.codex holds `opening` -- so Chapter: Opening is
# bundlable by a subject that supplies its own entry point. A harness that
# carries it can call `compile-frontend-cdx` instead of reimplementing it, and a
# moved signature then becomes a compile error at a call we did not write.
#
# The six foreword chapters are carried REAL rather than stubbed. Stubbing was
# tried and abandoned: `gate-import` answers `ImportResult`, a type outside the
# cited list, so the stub surface has a transitive closure and every guessed
# record shape is a type error waiting. These compile and guess nothing, and
# `compile-frontend-cdx` never reaches a disk. BootPaint is the one that must
# stay a stub -- `bp-rtc-seconds` is a wall clock and a rung whose truth changes
# between two identical runs is not an oracle.
#
# The middle end is here because the driver READS it without citing it: B5 gives
# a bundle one flat namespace, so upstream never notices `opening.codex` using
# `run-ir-pipeline` while citing nothing that defines it. A wrapper that also
# names these must stop, because ADD-PLUGCHAPTER DOES NOT DE-DUPLICATE ACROSS
# CALLS -- the result is CDX3004, "spans 2 files, but this page carries no
# Page N of M marker", once per chapter.
if ($WithDriver) {
    @('codex/compiler/IR/Occurrence.codex',
      'codex/compiler/IR/IRCheck.codex',
      'codex/compiler/IR/LambdaLifting.codex',
      'codex/compiler/IR/Simplify.codex',
      'codex/compiler/IR/Passes.codex',
      'codex/compiler/IR/LirTargets.codex',
      'codex/compiler/Emit/CodexEmitter.codex',
      'codex/foreword/core/Maybe.codex',
      'codex/foreword/core/Wrap64.codex',
      'codex/foreword/core/CCE.codex',
      'codex/foreword/core/Fat16.codex',
      'codex/foreword/core/ImportGate.codex',
      'codex/foreword/core/FactDisk.codex',
      'codex/compiler/opening.codex') | ForEach-Object {
        Add-PlugChapter -Lines $lines -Path (Join-Path $repo $_) -Quire 'Parsmi'
    }
}
$bootPaintPath = if ($BootPaint -match '/') { Join-Path $repo $BootPaint } else { Join-Path $here $BootPaint }
Add-PlugChapter -Lines $lines -Path $bootPaintPath -Quire 'Parsmi'
Add-PlugChapter -Lines $lines -Path (Join-Path $here $Harness) -Quire 'Parsmi'

# There used to be a rename of deck-record to subj-deck-record here. It was
# right when it was written: the seed's emitter hijacked any 1-arg call
# literally named deck-record into __deck-enter/__deck-exit, which corrupts
# memory in a subject that lacks the phase-allocator runtime, and renaming
# sidestepped it.
#
# Update 43 fixed that properly, on our report: the intercept now fires only
# when deck-record and init-phase-allocator are defined in the SAME chapter,
# so a bundle without the Phase Allocator gets the plain identity it declared
# and needs no help from us.
#
# Leaving the rename in place then became the bug. The seed doing the
# compiling is upstream's, so the name it looks for is `deck-record`; we had
# renamed ours out from under it, dr-slug came back empty, and the flag was
# False for every bundle here. That switched the deck discipline off across
# the whole bundled compiler, hundreds of call sites, and stayed invisible for
# thirteen rungs because a clean compile never needs a value to outlive
# emit-all-defs's per-function __heap-restore. clamp does: bag-add parks the
# diagnostic bag on the deck, the bag was freed at the bracket instead, and
# the second diagnostic read a dangling spine.
#
# LexStubs declares deck-record unrenamed, so the stub bundles still resolve.

# All 14 pages of the X86-64 Code Generator chapter are present, so the
# 'Page N of 14' trailers stand as written; the rewrite below is inherited
# from the lir bundle and self-adjusts, a no-op here.
$pageCount = ($lines | Where-Object { $_ -match '^Page \d+ of 14$' }).Count
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^Page \d+ of 14$') {
        $lines[$i] = $lines[$i] -replace 'of 14$', "of $pageCount"
    }
}
$preLines = Resolve-PlugForewords $lines
Bundle-PlugSource -PreLines $preLines -Lines $lines -BundleSrc (Join-Path $here $OutName) -PlugName $PlugName
