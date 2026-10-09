param(
    [Parameter(Mandatory=$true)][string]$Pptx,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$deckPath = (Resolve-Path -LiteralPath $Pptx).Path
$renderDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $renderDirectory) { throw 'Render directory exists; choose a fresh directory.' }
New-Item -ItemType Directory -Path $renderDirectory | Out-Null
$alreadyRunning = @(Get-Process POWERPNT -ErrorAction SilentlyContinue).Count -gt 0
$powerpoint = $null
$presentation = $null
try {
    $powerpoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerpoint.Presentations.Open($deckPath, -1, 0, 0)
    $count = $presentation.Slides.Count
    for ($index = 1; $index -le $count; $index++) {
        $pngPath = Join-Path $renderDirectory ('slide-{0:d2}.png' -f $index)
        $presentation.Slides.Item($index).Export($pngPath, 'PNG', 1280, 720)
        if (-not (Test-Path -LiteralPath $pngPath)) { throw "PowerPoint did not render slide $index" }
    }
    $receipt = @{ renderer='Microsoft PowerPoint COM'; slides=$count; input_sha256=(Get-FileHash -LiteralPath $deckPath -Algorithm SHA256).Hash.ToLower(); rendered_at=(Get-Date).ToString('o') }
    $receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $renderDirectory 'render-receipt.json') -Encoding UTF8
    $receipt | ConvertTo-Json
}
finally {
    if ($null -ne $presentation) { $presentation.Close(); [Runtime.InteropServices.Marshal]::ReleaseComObject($presentation) | Out-Null }
    if ($null -ne $powerpoint) {
        if (-not $alreadyRunning -and $powerpoint.Presentations.Count -eq 0) { $powerpoint.Quit() }
        [Runtime.InteropServices.Marshal]::ReleaseComObject($powerpoint) | Out-Null
    }
}
