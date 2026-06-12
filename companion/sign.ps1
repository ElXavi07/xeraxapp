param(
    [Parameter(Mandatory = $true)]
    [string]$Thumbprint,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Executable = Join-Path $ProjectRoot "dist\XeraxRootCompanion.exe"
$ReleaseMetadata = Join-Path $ProjectRoot "web\release.json"

if (-not (Test-Path -LiteralPath $Executable)) {
    throw "Build the companion before signing it."
}
if (-not (Test-Path -LiteralPath $ReleaseMetadata)) {
    throw "Release metadata is missing. Run companion\build.ps1 first."
}

$NormalizedThumbprint = ($Thumbprint -replace "\s", "").ToUpperInvariant()
$Certificate = Get-ChildItem Cert:\CurrentUser\My, Cert:\LocalMachine\My |
    Where-Object {
        $_.Thumbprint -eq $NormalizedThumbprint -and
        $_.HasPrivateKey -and
        $_.EnhancedKeyUsageList.ObjectId -contains "1.3.6.1.5.5.7.3.3"
    } |
    Select-Object -First 1
if (-not $Certificate) {
    throw "A code-signing certificate with a private key was not found for that thumbprint."
}
if ($Certificate.NotAfter -le (Get-Date)) {
    throw "The selected code-signing certificate has expired."
}

$SignTool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" `
    -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "\\x64\\signtool\.exe$" } |
    Sort-Object FullName -Descending |
    Select-Object -First 1
if (-not $SignTool) {
    throw "signtool.exe was not found. Install the Windows SDK signing tools."
}

& $SignTool.FullName sign /sha1 $NormalizedThumbprint /fd SHA256 /tr $TimestampUrl `
    /td SHA256 $Executable
if ($LASTEXITCODE -ne 0) {
    throw "Authenticode signing failed."
}
& $SignTool.FullName verify /pa /v $Executable
if ($LASTEXITCODE -ne 0) {
    throw "Authenticode verification failed."
}

$Release = Get-Content -Raw $ReleaseMetadata | ConvertFrom-Json
$DownloadPath = Join-Path $ProjectRoot ("web\downloads\" + $Release.filename)
Copy-Item -LiteralPath $Executable -Destination $DownloadPath -Force
$Release.sha256 = (Get-FileHash -LiteralPath $DownloadPath -Algorithm SHA256).Hash.ToLowerInvariant()
$Release.size = (Get-Item -LiteralPath $DownloadPath).Length
$Release.signed = $true
$ReleaseJson = $Release | ConvertTo-Json -Depth 4
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    $ReleaseMetadata,
    $ReleaseJson + [Environment]::NewLine,
    $Utf8NoBom
)

Write-Host "Signed and verified: $Executable"
Write-Host "Updated release SHA-256: $($Release.sha256)"
Write-Host "Run companion\deploy.ps1 to regenerate the upload bundle."
