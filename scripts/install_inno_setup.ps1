# PowerShell script to automatically find or install Inno Setup 6 on Windows.
# Returns the absolute path to ISCC.exe.

$ErrorActionPreference = "Stop"

# Standard installation paths for Inno Setup 6 (including user-level AppData)
$standardPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)

# 1. Check if ISCC is already in Path or standard locations
$isccPath = Get-Command iscc.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if ($isccPath) {
    Write-Host "Found ISCC.exe in PATH: $isccPath"
    exit 0
}

foreach ($path in $standardPaths) {
    if (Test-Path $path) {
        Write-Host "Found ISCC.exe at: $path"
        exit 0
    }
}

Write-Host "Inno Setup not found. Attempting automatic installation..."

# 2. Try installing via Winget (Windows Package Manager)
if (Get-Command winget -ErrorAction SilentlyContinue) {
    try {
        Write-Host "Installing JRSoftware.InnoSetup via winget..."
        Start-Process -FilePath "winget" -ArgumentList "install", "--id", "JRSoftware.InnoSetup", "--silent", "--accept-source-agreements", "--accept-package-agreements" -Wait -NoNewWindow
        
        # Verify after winget
        foreach ($path in $standardPaths) {
            if (Test-Path $path) {
                Write-Host "Successfully installed Inno Setup via winget: $path"
                exit 0
            }
        }
    } catch {
        Write-Warning "Winget installation failed, falling back to direct download."
    }
}

# 3. Fallback to direct download and silent installation
$downloadUrl = "https://github.com/jrsoftware/issrc/releases/download/is-6_2_2/innosetup-6.2.2.exe"
$tempPath = [System.IO.Path]::GetTempFileName() + ".exe"

try {
    Write-Host "Downloading Inno Setup from: $downloadUrl ..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempPath -UseBasicParsing
    
    Write-Host "Running silent installation..."
    $installProcess = Start-Process -FilePath $tempPath -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-" -Wait -PassThru
    
    if ($installProcess.ExitCode -ne 0) {
        throw "Installer exited with non-zero exit code: $($installProcess.ExitCode)"
    }
} finally {
    if (Test-Path $tempPath) {
        Remove-Item -Path $tempPath -Force -ErrorAction SilentlyContinue
    }
}

# 4. Final verification
foreach ($path in $standardPaths) {
    if (Test-Path $path) {
        Write-Host "Successfully downloaded and installed Inno Setup: $path"
        exit 0
    }
}

Write-Error "Inno Setup installation succeeded but ISCC.exe could not be found in standard locations."
exit 1
