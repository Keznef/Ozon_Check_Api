# Build Windows EXE for LicenseClient
# Usage: run in PowerShell from license-server folder
# Requires: Python venv activated and pyinstaller installed

param(
    [string]$Name = "LicenseClient",
    [string]$Entry = "client.py"
)

Write-Host "Installing dependencies..."
pip install -r requirements.txt | Out-Null
pip install pyinstaller | Out-Null

Write-Host "Building $Name from $Entry..."
pyinstaller --onefile --name $Name $Entry

Write-Host "Copy config.json next to the exe if needed"
if (Test-Path -Path "config.json") {
    Copy-Item -Path "config.json" -Destination "dist\$Name" -Force -ErrorAction SilentlyContinue
}

Write-Host "Build complete: dist\$Name.exe"
