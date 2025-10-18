# Run Multi-Google Drive Split Uploader
# Quick launcher script

Write-Host "Starting Multi-Google Drive Split Uploader..." -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Running setup..." -ForegroundColor Yellow
    .\setup.ps1
    exit
}

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Check if configuration exists
if (-not (Test-Path "config\drives.json")) {
    Write-Host "Configuration not found. Please run setup.ps1 first." -ForegroundColor Red
    Write-Host "Or copy config\drives.example.json to config\drives.json" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Run application
python main.py

# Deactivate virtual environment
deactivate
