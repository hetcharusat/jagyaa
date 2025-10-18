# Multi-Google Drive Split Uploader - Setup Script
# This script helps set up the development environment

Write-Host "=" -NoNewline
Write-Host "=" * 60
Write-Host "Multi-Google Drive Split Uploader - Setup"
Write-Host "=" * 60
Write-Host ""

# Check Python version
Write-Host "[1/6] Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
    
    # Extract version number
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            Write-Host "✗ Python 3.8 or higher is required" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check for rclone
Write-Host "`n[2/6] Checking rclone installation..."
try {
    $rcloneVersion = rclone version 2>&1 | Select-Object -First 1
    Write-Host "✓ Found: $rcloneVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ rclone not found" -ForegroundColor Red
    Write-Host "  Download from: https://rclone.org/downloads/" -ForegroundColor Yellow
    Write-Host "  Or install via: winget install Rclone.Rclone" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Create virtual environment
Write-Host "`n[3/6] Setting up virtual environment..."
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n[4/6] Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host "`n[5/6] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Setup configuration
Write-Host "`n[6/6] Setting up configuration..."
if (Test-Path "config\drives.json") {
    Write-Host "✓ Configuration file already exists" -ForegroundColor Green
} else {
    Copy-Item "config\drives.example.json" "config\drives.json"
    Write-Host "✓ Configuration file created from template" -ForegroundColor Green
    Write-Host "  Please edit config\drives.json to match your setup" -ForegroundColor Yellow
}

# Create required directories
$directories = @("manifests", "chunks", "downloads")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    }
}

Write-Host "`n" + "=" * 60
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Configure rclone remotes:" -ForegroundColor White
Write-Host "   rclone config" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Edit config\drives.json with your remote names" -ForegroundColor White
Write-Host ""
Write-Host "3. Run the application:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "- README.md - Full documentation" -ForegroundColor White
Write-Host "- SETUP.md - Quick setup guide" -ForegroundColor White
Write-Host "- docs\RCLONE_SETUP.md - Rclone configuration help" -ForegroundColor White
Write-Host ""

# Ask if user wants to configure rclone now
$configureNow = Read-Host "Would you like to configure rclone now? (y/n)"
if ($configureNow -eq "y") {
    Write-Host "`nLaunching rclone config..." -ForegroundColor Cyan
    rclone config
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
