# Bundle the check-milestone subject: everything the scope milestone
# carries, plus the type checker, its inference half, the unifier and the
# type environment. Output: check-subject.codex next to this script.
#
# Capability is NOT named here, and the reason is a fix rather than a taste.
# Resolve-PlugForewords pulls CITED foreword chapters. TypeChecker used
# capability-names with no cite for it, so this bundle named the chapter
# outright or the definition was simply absent -- that was finding 4 on PR
# 64. Update 43 added the cite, so Capability now arrives on its own and
# naming it a second time is CDX3001, a duplicate CapSpec. Same rule as
# Sort, which was always only cited.
#
# CheckStubs replaces ScopeStubs here and the difference matters. The type
# checker reads bs-type off every builtin, which ScopeStubs did not carry --
# it had only bs-name, because the scoper only needed to know which names
# were taken. So this stub keeps bs-type verbatim from the real table and
# drops only bs-emit, which is the field typed over CodegenState and
# EmitResult and the reason the real chapter cannot be bundled.
param(
    [string]$Harness = 'CheckHarness.codex',
    [string]$OutName = 'check-subject.codex'
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
                  'codex/compiler/Types/TypeCheckerInference.codex')) {
    Add-PlugChapter -Lines $lines -Path (Join-Path $repo $ch) -Quire 'Parsmi'
}
# Update 42 gave PhaseAllocator a cite of Codex chapter BootPaint, and a cite
# names a chapter, so the unit has to carry one. See BootPaintStubs.codex for
# why it is a stub and not the real 341-line screen painter.
Add-PlugChapter -Lines $lines -Path (Join-Path $here 'BootPaintStubs.codex') -Quire 'Parsmi'
Add-PlugChapter -Lines $lines -Path (Join-Path $here 'CheckStubs.codex') -Quire 'Parsmi'
Add-PlugChapter -Lines $lines -Path (Join-Path $here $Harness) -Quire 'Parsmi'

$preLines = Resolve-PlugForewords $lines
Bundle-PlugSource -PreLines $preLines -Lines $lines -BundleSrc (Join-Path $here $OutName) -PlugName 'check-subject'
