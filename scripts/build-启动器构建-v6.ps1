$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$sources = @(Get-ChildItem -LiteralPath (Join-Path $root 'src\launcher') -Recurse -Filter '*.cs' | ForEach-Object { $_.FullName })
& $compiler /nologo /target:winexe /optimize+ /codepage:65001 /reference:System.Windows.Forms.dll /reference:System.Web.Extensions.dll ("/win32icon:" + (Join-Path $root 'assets\icons\sci-browser.ico')) ("/out:" + (Join-Path $root 'sci-browser.exe')) $sources
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }