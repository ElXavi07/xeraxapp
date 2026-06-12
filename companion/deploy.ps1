param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WebRoot = Join-Path $ProjectRoot "web"

if (-not $Destination) {
    $Destination = Join-Path $ProjectRoot "deploy\xerax-root"
}
$Destination = [System.IO.Path]::GetFullPath($Destination)
$ProjectRootResolved = [System.IO.Path]::GetFullPath($ProjectRoot)
$DefaultDeployRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "deploy"))

if ($Destination -eq $ProjectRootResolved) {
    throw "Deployment destination cannot be the project root."
}
if (Test-Path -LiteralPath $Destination) {
    if (-not $Destination.StartsWith($DefaultDeployRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to replace an existing destination outside $DefaultDeployRoot"
    }
    Remove-Item -LiteralPath $Destination -Recurse -Force
}

if (-not (Test-Path -LiteralPath (Join-Path $WebRoot "release.json"))) {
    throw "Run companion\build.ps1 before creating a deployment bundle."
}

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
Copy-Item -Path (Join-Path $WebRoot "*") -Destination $Destination -Recurse -Force

$Required = @(
    "index.html",
    "styles.css",
    "app.js",
    "release.json"
)
foreach ($File in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $Destination $File))) {
        throw "Deployment is missing $File"
    }
}

$Release = Get-Content -Raw (Join-Path $Destination "release.json") | ConvertFrom-Json
$Download = Join-Path $Destination ("downloads\" + $Release.filename)
if (-not (Test-Path -LiteralPath $Download)) {
    throw "Deployment is missing the companion executable."
}
$ActualHash = (Get-FileHash -LiteralPath $Download -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ActualHash -ne $Release.sha256) {
    throw "Deployment executable hash does not match release.json."
}
$UnexpectedDownloads = Get-ChildItem (Join-Path $Destination "downloads") -File |
    Where-Object { $_.Name -ne $Release.filename }
if ($UnexpectedDownloads) {
    throw "Deployment contains unexpected download files: $($UnexpectedDownloads.Name -join ', ')"
}

Write-Host "Deployment bundle: $Destination"
Write-Host "Verified download SHA-256: $ActualHash"
