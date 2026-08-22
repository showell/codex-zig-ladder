# Bundle the fib-milestone subject: the lower milestone's chapter set plus
# the IR Text Emitter (and OffsetTable, which it cites), so the chain ends
# in the compiler's own serialization instead of a structural dump. The
# harness compiles fib end to end and prints one (def ...) line per
# definition -- the same grammar the IR-CCE wire carries.
param(
    [string]$Harness = 'FibHarness.codex',
    [string]$OutName = 'fib-subject.codex'
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
# ListUtils is NOT listed here. Core/Collections.codex cites Foreword
# chapter ListUtils and Resolve-PlugForewords resolves that cite, so this
# bundle already carries Foreword--ListUtils; listing it again put a second
# copy in the Parsmi quire: two chapters
# defining list-map, fold-list, list-take and the rest, which is what every
# CDX3006 in this rung's log was telling us. See bundle_parse.ps1, where the
# explicit listing IS the only copy and stays.
foreach ($ch in @('codex/compiler/Core/BuildSettings.codex',
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
                  'codex/compiler/Core/OffsetTable.codex',
                  'codex/compiler/Emit/IRTextEmitter.codex')) {
    Add-PlugChapter -Lines $lines -Path (Join-Path $repo $ch) -Quire 'Parsmi'
}
# Update 42 gave PhaseAllocator a cite of Codex chapter BootPaint, and a cite
# names a chapter, so the unit has to carry one. See BootPaintStubs.codex for
# why it is a stub and not the real 341-line screen painter.
Add-PlugChapter -Lines $lines -Path (Join-Path $here 'BootPaintStubs.codex') -Quire 'Parsmi'
Add-PlugChapter -Lines $lines -Path (Join-Path $here 'LowerStubs.codex') -Quire 'Parsmi'
Add-PlugChapter -Lines $lines -Path (Join-Path $here $Harness) -Quire 'Parsmi'

$preLines = Resolve-PlugForewords $lines
Bundle-PlugSource -PreLines $preLines -Lines $lines -BundleSrc (Join-Path $here $OutName) -PlugName 'fib-subject'
