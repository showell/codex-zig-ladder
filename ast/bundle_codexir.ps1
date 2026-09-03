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
# The middle end moved into bundle_ir_to_x86.ps1's own list when the driver
# joined it -- Chapter: Opening reads those chapters without citing them. Naming
# them here too includes each one TWICE, and Add-PlugChapter does NOT
# de-duplicate across calls: the result is CDX3004, "spans 2 files, but this page
# carries no Page N of M marker", once per chapter.
& (Join-Path $PSScriptRoot 'bundle_ir_to_x86.ps1') `
    -Harness $Harness `
    -OutName $OutName `
    -PlugName $PlugName `
    -ExtraDrops $ExtraDrops `
    -ExtraChapters $MoreChapters
