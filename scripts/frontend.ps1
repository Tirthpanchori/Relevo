param(
    [ValidateSet('dev', 'build', 'preview', 'test', 'check', 'browser', 'test:desktop', 'test:responsive')]
    [string]$Task = 'dev',
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$TaskArguments
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$nodeVersion = '24.22.0'
$runtimeDirectory = Join-Path $projectRoot ".tools/node-v$nodeVersion-win-x64"
$nodeExecutable = Join-Path $runtimeDirectory 'node.exe'
if (-not (Test-Path -LiteralPath $nodeExecutable)) {
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'This portable setup requires 64-bit Windows.' }
    $cacheDirectory = Join-Path $projectRoot '.cache'
    New-Item -ItemType Directory -Force -Path $cacheDirectory | Out-Null
    $archiveName = "node-v$nodeVersion-win-x64.zip"
    $archivePath = Join-Path $cacheDirectory $archiveName
    $releaseUrl = "https://nodejs.org/dist/v$nodeVersion"
    Write-Host "Downloading project-local Node.js $nodeVersion..."
    Invoke-WebRequest -UseBasicParsing "$releaseUrl/$archiveName" -OutFile $archivePath
    $checksums = (Invoke-WebRequest -UseBasicParsing "$releaseUrl/SHASUMS256.txt").Content
    $checksumLine = ($checksums -split "`n" | Where-Object { $_.Trim().EndsWith("  $archiveName") })
    if (@($checksumLine).Count -ne 1) { throw 'Could not identify the official Node checksum.' }
    $expectedHash = ($checksumLine.Trim() -split '\s+')[0]
    if ($expectedHash -notmatch '^[a-fA-F0-9]{64}$' -or (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash -ne $expectedHash) { throw 'Node archive checksum verification failed.' }
    Expand-Archive -LiteralPath $archivePath -DestinationPath (Join-Path $projectRoot '.tools') -Force
}
$env:PATH = $runtimeDirectory + ';' + $env:PATH
$env:npm_config_cache = Join-Path $projectRoot '.cache/npm'
$npmExecutable = Join-Path $runtimeDirectory 'npm.cmd'
Push-Location (Join-Path $projectRoot 'frontend')
try {
    if (-not (Test-Path -LiteralPath 'node_modules/.package-lock.json')) {
        & $npmExecutable ci
        if ($LASTEXITCODE -ne 0) { throw 'Frontend dependencies could not be installed.' }
    }
    $tasks = if ($Task -eq 'check') { @('build', 'test', 'test:e2e') } else { @($Task) }
    if ($Task -eq 'check') {
        & $npmExecutable exec -- playwright install chromium
        if ($LASTEXITCODE -ne 0) { throw 'The test browser could not be prepared.' }
    }
    foreach ($step in $tasks) {
        if ($step -eq 'browser') {
            & $npmExecutable run $step -- @TaskArguments
        } else {
            & $npmExecutable run $step
        }
        if ($LASTEXITCODE -ne 0) { throw "Frontend task failed: $step" }
    }
} finally { Pop-Location }
