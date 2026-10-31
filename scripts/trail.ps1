# Project-local Trail Code (formerly Graft), separate from website dependencies.
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$TrailArguments)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDirectory = Join-Path $projectRoot '.tools/node-v24.22.0-win-x64'
$nodeExecutable = Join-Path $runtimeDirectory 'node.exe'
$toolDirectory = Join-Path $projectRoot '.tools/trail-code'
$entryPoint = Join-Path $toolDirectory 'node_modules/@trailhq/trail-code/dist/bin/trail.js'
if (-not (Test-Path -LiteralPath $nodeExecutable)) {
    throw 'Prepare the portable Node runtime first: ./scripts/frontend.ps1 build'
}
$previousPath = $env:PATH
$previousTracking = $env:DO_NOT_TRACK
try {
    $env:PATH = $runtimeDirectory + ';' + $env:PATH
    $env:DO_NOT_TRACK = '1'
    if (-not (Test-Path -LiteralPath $entryPoint)) {
        & (Join-Path $runtimeDirectory 'npm.cmd') install --prefix $toolDirectory --save-exact --ignore-scripts --no-audit --no-fund '@trailhq/trail-code@0.23.0'
        if ($LASTEXITCODE -ne 0) { throw 'Trail Code installation failed.' }
    }
    Push-Location $projectRoot
    try {
        & $nodeExecutable $entryPoint @TrailArguments
        $toolExitCode = $LASTEXITCODE
    } finally { Pop-Location }
} finally {
    $env:PATH = $previousPath
    $env:DO_NOT_TRACK = $previousTracking
}
exit $toolExitCode
