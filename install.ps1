# Shadow Defender Tool Auto-Installer
$Repo       = "musika08/Shadow-Defender-Bypass-Installer"
$ExeName    = "ShadowDefenderTool.exe"
$DownloadUrl = "https://github.com/$Repo/releases/latest/download/$ExeName"
$TempPath   = Join-Path $env:TEMP $ExeName

Write-Host " [~] Fetching Shadow Defender Tool from GitHub..." -ForegroundColor Cyan

try {
    # Force TLS 1.2 for GitHub compatibility
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    
    # Download the executable
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempPath -ErrorAction Stop
}
catch {
    Write-Error " [!] Download Failed. Please ensure you have created a 'Release' on GitHub with '$ExeName' uploaded."
    exit
}

Write-Host " [+] Starting Installer..." -ForegroundColor Green

# Run as Admin (Corrected Command)
Start-Process -FilePath $TempPath -Verb RunAs
