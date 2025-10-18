# Multi-Drive Cloud Manager v3.0.3 - Build Script
# Simple and reliable build process

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host " Multi-Drive Cloud Manager v3.0.3 - BUILD SYSTEM" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean
Write-Host "[1/5] Cleaning previous builds..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\MultiDriveCloudManager") { Remove-Item -Recurse -Force "dist\MultiDriveCloudManager" }
if (Test-Path "dist\MultiDriveCloudManager.exe") { Remove-Item -Force "dist\MultiDriveCloudManager.exe" }
Write-Host "Done!" -ForegroundColor Green
Write-Host ""

# Step 2: Verify files
Write-Host "[2/5] Verifying source files..." -ForegroundColor Cyan
if (-not (Test-Path "app_flet_restored.py")) {
    Write-Host "ERROR: app_flet_restored.py not found!" -ForegroundColor Red
    exit 1
}
Write-Host "Source file OK" -ForegroundColor Green
Write-Host ""

# Step 3: Build EXE
Write-Host "[3/5] Building EXE (this takes 2-3 minutes)..." -ForegroundColor Cyan
& .\.venv\Scripts\pyinstaller.exe --clean --noconfirm MultiDriveCloudManager.spec
if (-not (Test-Path "dist\MultiDriveCloudManager.exe")) {
    Write-Host "ERROR: EXE build failed!" -ForegroundColor Red
    exit 1
}
$exeSize = (Get-Item "dist\MultiDriveCloudManager.exe").Length / 1MB
Write-Host "EXE created: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Green
Write-Host ""

# Step 4: Test EXE
Write-Host "[4/5] Testing EXE..." -ForegroundColor Cyan
$testProcess = Start-Process -FilePath "dist\MultiDriveCloudManager.exe" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3
if (-not $testProcess.HasExited) {
    Stop-Process -Id $testProcess.Id -Force
    Write-Host "EXE test passed!" -ForegroundColor Green
} else {
    Write-Host "ERROR: EXE crashed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 5: Create installer
Write-Host "[5/5] Creating installer..." -ForegroundColor Cyan
$isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $isccPath)) {
    Write-Host "WARNING: Inno Setup not found!" -ForegroundColor Yellow
    Write-Host "EXE is ready at: dist\MultiDriveCloudManager.exe" -ForegroundColor Green
    exit 0
}

& $isccPath "installer\MultiDriveCloudManager.iss"
$installerPath = "dist\MultiDriveCloudManager_Setup_3.0.3.exe"
if (Test-Path $installerPath) {
    $installerSize = (Get-Item $installerPath).Length / 1MB
    Write-Host "Installer created: $([math]::Round($installerSize, 2)) MB" -ForegroundColor Green
} else {
    Write-Host "ERROR: Installer build failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Summary
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host " BUILD COMPLETE!" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Output files:" -ForegroundColor Cyan
Write-Host "  EXE:       dist\MultiDriveCloudManager.exe" -ForegroundColor White
Write-Host "  Installer: dist\MultiDriveCloudManager_Setup_3.0.3.exe" -ForegroundColor White
Write-Host ""
Write-Host "Version 3.0.3 fixes:" -ForegroundColor Cyan
Write-Host "  - No terminal window" -ForegroundColor White
Write-Host "  - No admin required" -ForegroundColor White
Write-Host "  - No old data" -ForegroundColor White
Write-Host "  - Complete code restored" -ForegroundColor White
Write-Host ""
Write-Host "Run: dist\MultiDriveCloudManager_Setup_3.0.3.exe" -ForegroundColor Yellow
Write-Host ""
