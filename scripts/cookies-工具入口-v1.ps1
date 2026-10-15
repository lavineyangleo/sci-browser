[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$ToolArguments)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$tool = Join-Path $root 'extensions\web-cookie-skill'
$python = Join-Path $tool 'venv-3.12\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Cookie tool environment missing.' }
if (-not $ToolArguments -or $ToolArguments -contains '--help' -or $ToolArguments -contains '-h') {
    & $python (Join-Path $tool 'scripts\cookie_tool.py') @ToolArguments --help
    exit $LASTEXITCODE
}
$arguments = @($ToolArguments)
if ($arguments -notcontains '--executable-path') {
    $arguments += @('--executable-path', (Join-Path $root 'runtime\Chrome-bin-v4\chrome.exe'))
}
if ($arguments -notcontains '--user-data-dir') {
    $arguments += @('--user-data-dir', (Join-Path $tool '.cookie-profile'))
}
& $python (Join-Path $tool 'scripts\cookie_tool.py') @arguments
exit $LASTEXITCODE
