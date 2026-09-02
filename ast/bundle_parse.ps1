# Bundle the parse-milestone subject: the lex chapters plus the parser's
# own three files and the CST node definitions, with a harness that dumps
# the parsed Document. Output: parse-subject.codex next to this script.
param(
    [string]$Harness = 'ParseHarness.codex',
    [string]$OutName = 'parse-subject.codex'
)
$ErrorActionPreference = 'Stop'
$ladder = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
$repo = (& python3 (Join-Path $ladder 'ladder_root.py') codex).Trim()
$here = $PSScriptRoot

. "$repo/codex/plugs/common/plug-build-lib.ps1"

$lines = [System.Collections.Generic.List[string]]::new()
# ListUtils is here for a name that appears nowhere in the sources: the
# desugarer turns every `for` expression into a call to map-list
# (Ast/Desugarer.codex, `is ForExpr`), so a chapter using `for` needs
# ListUtils in the unit or codegen reports an undefined name with no
# grep-able reference to explain it.
foreach ($ch in @('codex/foreword/core/ListUtils.codex',
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
                  'codex/compiler/Types/CodexType.codex',
                  'codex/compiler/Types/CodexTypeHelpers.codex',
                  'codex/compiler/IR/IRChapter.codex',
                  'codex/compiler/Syntax/Token.codex',
                  'codex/compiler/Syntax/Lexer.codex',
                  'codex/compiler/Syntax/SyntaxNodes.codex',
                  'codex/compiler/Syntax/ParserCore.codex',
                  'codex/compiler/Syntax/ParserExpressions.codex',
                  'codex/compiler/Syntax/Parser.codex')) {
    Add-PlugChapter -Lines $lines -Path (Join-Path $repo $ch) -Quire 'Parsmi'
}
# PhaseAllocator cites Codex chapter BootPaint, and a cite names a CHAPTER,
# so the unit has to answer for one. BootPaintStubs.codex says why it is a
# stub: the real chapter puts a WALL CLOCK in the truth arm.
Add-PlugChapter -Lines $lines -Path (Join-Path $here 'BootPaintStubs.codex') -Quire 'Parsmi'
# LexStubs is NOT carried here, and after Update 54 it is down to one
# definition: copy-sx-diag. This bundle has Syntax/SyntaxNodes.codex, which
# is where the REAL one lives, and Core/PhaseAllocator.codex for the two the
# stub chapter used to hold. Carrying it anyway defines copy-sx-diag twice --
# CDX3006, which check_diags.py refuses, and correctly: two definitions of a
# name where each chapter sees its own is how a subject silently measures a
# different function than the one it names. lex is the only rung that cannot
# reach SyntaxNodes, so it is the only rung that still needs the stub.
Add-PlugChapter -Lines $lines -Path (Join-Path $here $Harness) -Quire 'Parsmi'

$preLines = Resolve-PlugForewords $lines
Bundle-PlugSource -PreLines $preLines -Lines $lines -BundleSrc (Join-Path $here $OutName) -PlugName 'parse-subject'
