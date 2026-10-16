[CmdletBinding()]
param(
    [ValidateSet('setup','download','lookup','rename')][string]$Action = 'setup',
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$ToolArguments
)
$ErrorActionPreference = 'Stop'
$tool = Join-Path (Split-Path -Parent $PSScriptRoot) 'extensions\browser-paper-download'
$python = Join-Path $tool 'venv-3.12\Scripts\python.exe'
$portable = Join-Path (Split-Path -Parent $PSScriptRoot) 'runtime/python/python.exe'
if (Test-Path -LiteralPath $portable) { $python = $portable }
if (-not (Test-Path -LiteralPath $python)) { throw 'Paper downloader environment missing.' }
if ($Action -eq 'lookup') {
    & $python (Join-Path $tool 'scripts\lookup_ids.py') @ToolArguments
} elseif ($Action -eq 'rename') {
    & $python (Join-Path $tool 'scripts\rename_papers.py') @ToolArguments
} else {
    $adapter = Get-ChildItem -LiteralPath (Join-Path $tool 'windows') -Filter 'browser-*-v1.py' | Select-Object -First 1
    & $python $adapter.FullName $Action @ToolArguments
}
exit $LASTEXITCODE
