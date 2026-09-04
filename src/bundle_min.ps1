# The ad-hoc bundler: not a rung, and not run by any sweep. It takes an
# arbitrary chapter list, which is what makes it the tool for a bisect --
# name the chapters a hypothesis needs and nothing else.
param(
    [string[]]$Chapters,
    [string]$Harness,
    [string]$OutName
)
$ErrorActionPreference = 'Stop'
# Run bare, every one of those is empty and Join-Path hands Add-PlugChapter
# the ast DIRECTORY, which fails as "Access to the path ... is denied" from
# inside ReadAllLines. Say what is actually wrong instead.
if (-not $Chapters -or -not $Harness -or -not $OutName) {
    [Console]::Error.WriteLine("bundle_min.ps1 is the ad-hoc bundler and has no defaults.")
    [Console]::Error.WriteLine("  usage: bundle_min.ps1 -Chapters <paths> -Harness <file> -OutName <file>")
    [Console]::Error.WriteLine("  paths are repo-relative, falling back to this directory")
    exit 2
}
$ladder = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
$repo = (& python3 (Join-Path $ladder 'ladder_root.py') codex).Trim()
$here = $PSScriptRoot
. "$repo/codex/plugs/common/plug-build-lib.ps1"
$lines = [System.Collections.Generic.List[string]]::new()
foreach ($ch in $Chapters) {
    $p = Join-Path $repo $ch
    if (-not (Test-Path $p)) { $p = Join-Path $here $ch }
    Add-PlugChapter -Lines $lines -Path $p -Quire 'Lexmi'
}
Add-PlugChapter -Lines $lines -Path (Join-Path $here $Harness) -Quire 'Lexmi'
$preLines = Resolve-PlugForewords $lines
Bundle-PlugSource -PreLines $preLines -Lines $lines -BundleSrc (Join-Path $here $OutName) -PlugName 'min-subject'
