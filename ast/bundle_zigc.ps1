# The hosted-compiler subject: the whole rung's chapters, a different driver.
# Identical chapter set to bundle_passes_to_x86.ps1 for the same reason
# that one wraps bundle_ir_to_x86.ps1 -- one list, kept in one place.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'bundle_ir_to_x86.ps1') `
    -Harness 'ZigcHarness.codex' `
    -OutName 'zigc-subject.codex' `
    -PlugName 'zigc-subject' `
    -ExtraChapters @(
        # The middle end moved into bundle_ir_to_x86.ps1's own list when the
        # driver joined it -- Chapter: Opening reads these without citing them.
        # Naming them here too includes each chapter TWICE, and Add-PlugChapter
        # does NOT de-duplicate across calls: the result is CDX3004, "spans 2
        # files, but this page carries no Page N of M marker", once per chapter.
        )
