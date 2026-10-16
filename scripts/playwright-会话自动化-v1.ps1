[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$ToolArguments)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root 'extensions/browser-paper-download/venv-3.12/Scripts/python.exe'
$portable = Join-Path (Split-Path -Parent $PSScriptRoot) 'runtime/python/python.exe'
if (Test-Path -LiteralPath $portable) { $python = $portable }
if (-not (Test-Path -LiteralPath $python)) { throw 'Install the paper downloader Python environment first; see README.' }
Push-Location -LiteralPath $root
try {
    & $python -m services.automation.cli @ToolArguments
    $result = $LASTEXITCODE
} finally { Pop-Location }
exit $result
