param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputPdf
)

$ErrorActionPreference = "Stop"
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $inputFull = [System.IO.Path]::GetFullPath($InputPath)
    $outputFull = [System.IO.Path]::GetFullPath($OutputPdf)
    $document = $word.Documents.Open($inputFull, $false, $true)
    $document.ExportAsFixedFormat($outputFull, 17)
    Write-Output $outputFull
}
finally {
    if ($document -ne $null) {
        try { $document.Close($false) } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) } catch { }
    }
    if ($word -ne $null) {
        try { $word.Quit() } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch { }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
