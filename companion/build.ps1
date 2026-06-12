param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Spec = Join-Path $PSScriptRoot "xerax-root.spec"
$Dist = Join-Path $ProjectRoot "dist"
$Build = Join-Path $ProjectRoot "build"
$WebDownloads = Join-Path $ProjectRoot "web\downloads"
$ReleaseMetadata = Join-Path $ProjectRoot "web\release.json"

if ($Clean) {
    if (Test-Path -LiteralPath $Dist) {
        Remove-Item -LiteralPath $Dist -Recurse -Force
    }
    if (Test-Path -LiteralPath $Build) {
        Remove-Item -LiteralPath $Build -Recurse -Force
    }
}

python -m unittest discover -s (Join-Path $ProjectRoot "tests") -v
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed."
}

python -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is required. Run: python -m pip install pyinstaller"
}

python -m PyInstaller --noconfirm --distpath $Dist --workpath $Build $Spec
if ($LASTEXITCODE -ne 0) {
    throw "Companion build failed."
}

$Executable = Join-Path $Dist "XeraxRootCompanion.exe"
if (-not (Test-Path -LiteralPath $Executable)) {
    throw "Expected executable was not created: $Executable"
}

$Hash = (Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant()
$Version = (& $Executable --version).Trim()
if (-not $Version) {
    throw "Unable to read the companion version."
}
$Profiles = Get-Content -Raw (Join-Path $ProjectRoot "profiles\device_profiles.json") |
    ConvertFrom-Json

New-Item -ItemType Directory -Path $WebDownloads -Force | Out-Null
Get-ChildItem -LiteralPath $WebDownloads -Filter "XeraxRootCompanion-*-windows-x64.exe" `
    -ErrorAction SilentlyContinue |
    Remove-Item -Force
$DownloadName = "XeraxRootCompanion-$Version-windows-x64.exe"
$DownloadPath = Join-Path $WebDownloads $DownloadName
Copy-Item -LiteralPath $Executable -Destination $DownloadPath -Force

$Release = [ordered]@{
    schemaVersion = 1
    version = $Version
    platform = "windows-x64"
    filename = $DownloadName
    url = "./downloads/$DownloadName"
    sha256 = $Hash
    size = (Get-Item -LiteralPath $DownloadPath).Length
    signed = $false
    profileRevision = $Profiles.revision
    platformTools = [ordered]@{
        bundled = $false
        verifiedVersion = "37.0.0"
        officialUrl = "https://developer.android.com/tools/releases/platform-tools"
    }
}
$ReleaseJson = $Release | ConvertTo-Json -Depth 4
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ReleaseMetadata, $ReleaseJson + [Environment]::NewLine, $Utf8NoBom)

Write-Host ""
Write-Host "Built: $Executable"
Write-Host "SHA-256: $Hash"
Write-Host "Web download: $DownloadPath"
Write-Host "Release metadata: $ReleaseMetadata"
Write-Host "This build is unsigned. Code-sign it before public distribution."
