<#
genimg.ps1 — thin wrapper around genimg.py for vault "generated" images.

Why: long Chinese prompts are painful to pass on the command line in PowerShell
(quoting / encoding eats characters). This wrapper reads the prompt from a UTF-8
file, auto-builds the output path under the vault's _attachments/generated/, and
calls genimg.py (which records a <slug>.prompt.json sidecar so the image can be
regenerated later).

Usage:
    genimg.ps1 <slug> <prompt.txt> [size]
      slug       : output basename, e.g. "claude-mem-architecture"
      prompt.txt : UTF-8 text file holding the (Chinese) prompt
      size       : 1024x1024 (default) | 1024x1536 | 1536x1024 | auto

Override output dir with -OutDir, or the vault root with $env:VAULT_DIR.

Example:
    genimg.ps1 my-diagram C:/Users/ke/AppData/Local/Temp/prompt.txt 1536x1024
#>
param(
    [Parameter(Mandatory = $true)][string]$Slug,
    [Parameter(Mandatory = $true)][string]$PromptFile,
    [string]$Size = "1024x1024",
    [string]$OutDir
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $PromptFile)) {
    Write-Error "prompt file not found: $PromptFile"
    exit 1
}

if (-not $OutDir) {
    $vault = if ($env:VAULT_DIR) { $env:VAULT_DIR } else { "C:/Users/ke/Documents/knowledge-vault" }
    $OutDir = Join-Path $vault "_attachments/generated"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$out = Join-Path $OutDir ("{0}.png" -f $Slug)
$py = "C:/Users/ke/.claude/scripts/genimg.py"

Write-Host "[genimg.ps1] slug=$Slug size=$Size -> $out"
# genimg.py prints the final path on stdout; --prompt-file avoids PS quoting hell.
python $py $out --prompt-file $PromptFile $Size
if ($LASTEXITCODE -ne 0) {
    Write-Error "genimg.py failed (exit $LASTEXITCODE)"
    exit $LASTEXITCODE
}
Write-Host "[genimg.ps1] done: $out (+ $($Slug).prompt.json)"
