# The hosted-compiler subject: the whole rung's chapters, a different driver.
# Identical chapter set to bundle_passes_to_x86.ps1 for the same reason
# that one wraps bundle_ir_to_x86.ps1 -- one list, kept in one place.
# THE DRIVER, not a copy of it. ZigcHarness calls compile-frontend-cdx, so this
# subject carries Chapter: Opening and the chapters that come with it -- the
# middle end among them, which is why no ExtraChapters list is left here. See
# the -WithDriver block in bundle_ir_to_x86.ps1.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'bundle_ir_to_x86.ps1') `
    -Harness 'ZigcHarness.codex' `
    -OutName 'zigc-subject.codex' `
    -PlugName 'zigc-subject' `
    -WithDriver
