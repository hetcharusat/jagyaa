# Build Windows EXE using PyInstaller (PySide6 desktop app)
# Requires: pip install pyinstaller

$env:PYTHON="C:/Users/hetp2/OneDrive/Desktop/jagyaa/.venv/Scripts/python.exe"
$env:PIP="$env:PYTHON -m pip"

# Ensure pyinstaller is installed
& $env:PYTHON -m pip install --upgrade pip pyinstaller
& $env:PYTHON -m pip install PySide6

# Clean previous builds
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }

# Build
& $env:PYTHON -m PyInstaller `
  --noconfirm `
  --noconsole `
  --name "MultiDriveCloudManager" `
  --icon "assets/app.ico" `
  --add-data "config;config" `
  --add-data "core;core" `
  --add-data "gui;gui" `
  main.py

Write-Host "\nBuild complete. EXE is in dist/MultiDriveCloudManager" -ForegroundColor Green
