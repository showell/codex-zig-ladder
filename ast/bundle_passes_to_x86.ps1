# The whole-compiler subject: every chapter under codex/compiler except the
# driver, plus the harness that stands in for it.
#
# opening.codex is the one chapter that cannot come along -- it defines
# `opening`, and so does the harness. Leaving it out is not a subset: IR
# emission prunes to what the opening reaches, so what the unit contains is
# decided by what the harness calls, and the harness calls run-ir-pipeline
# exactly where compile-frontend-passes does. That is what pulls Simplify,
# Occurrence, LambdaLifting, Passes and IRCheck into the IR; bundling them
# without calling them would prune them straight back out.
#
# CodexEmitter and LirTargets ride along for completeness and will be pruned
# if this harness never reaches them.
#
# BootPaint stays the STUB. Swapping in the real 341-line painter looked like
# free completeness and was not: it cites Foreword chapter CCE, which makes
# Resolve-PlugForewords add a Foreword--CCE beside the Parsmi--CCE the list
# already carries, and the seed rejects the unit with eight CDX3001 duplicate
# constructors on CharClass. The painter is unreachable from this harness and
# would be pruned from the IR regardless, so it buys nothing to pay for.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'bundle_ir_to_x86.ps1') `
    -Harness 'PassesToX86Harness.codex' `
    -OutName 'passes_to_x86-subject.codex' `
    -PlugName 'passes_to_x86-subject' `
    -ExtraChapters @(
        # The middle end moved into bundle_ir_to_x86.ps1's own list when the
        # driver joined it -- Chapter: Opening reads these without citing them.
        # Naming them here too includes each chapter TWICE, and Add-PlugChapter
        # does NOT de-duplicate across calls: the result is CDX3004, "spans 2
        # files, but this page carries no Page N of M marker", once per chapter.
        )
