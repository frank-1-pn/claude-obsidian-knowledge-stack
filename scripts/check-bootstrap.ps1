param([string]$VaultPath = (Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference = 'Stop'
python (Join-Path $PSScriptRoot 'check_bootstrap.py') --vault $VaultPath
exit $LASTEXITCODE
