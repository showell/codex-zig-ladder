# The hosted-compiler subject: the whole rung's chapters, a different driver.
# Identical chapter set to bundle_passes_to_x86.ps1 for the same reason
# that one wraps bundle_ir_to_x86.ps1 -- one list, kept in one place.
#
# bundle_codexzig.ps1 calls this with MoreChapters for the same reason again:
# it wants this list plus the plug's emitter, and a second copy of seven
# chapter paths is a second thing to keep in step.
param(
    [string]$Harness = 'CodexIrHarness.codex',
    [string]$OutName = 'codexir-subject.codex',
    [string]$PlugName = 'codexir-subject',
    [string[]]$MoreChapters = @(),
    [hashtable]$ExtraDrops = @{}
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'bundle_ir_to_x86.ps1') `
    -Harness $Harness `
    -OutName $OutName `
    -PlugName $PlugName `
    -ExtraDrops $ExtraDrops `
    -ExtraChapters (@(
        'codex/compiler/IR/Occurrence.codex',
        'codex/compiler/IR/IRCheck.codex',
        'codex/compiler/IR/LambdaLifting.codex',
        'codex/compiler/IR/Simplify.codex',
        'codex/compiler/IR/Passes.codex',
        'codex/compiler/IR/LirTargets.codex',
        'codex/compiler/Emit/CodexEmitter.codex') + $MoreChapters)
