# Multi-Google Drive Split Uploader - Setup Guide

## Quick Setup Steps

### 1. Install Python 3.8+
Download from: https://www.python.org/downloads/

### 2. Install Rclone
Download from: https://rclone.org/downloads/

For Windows:
- Download the zip file
- Extract rclone.exe
- Add to PATH or place in project folder

### 3. Setup Python Environment

Open PowerShell in project folder:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Google Drives

```powershell
rclone config
```

For each Google Drive:
- Choose: n (new remote)
- Name: gdrive1, gdrive2, gdrive3, etc.
- Storage: Google Drive
- Follow prompts (leave most blank, use defaults)
- Authenticate in browser

### 5. Update Configuration

Copy `config\drives.example.json` to `config\drives.json`

Edit to match your rclone remote names:

```json
{
  "drives": [
    {
      "name": "drive1",
      "remote_name": "gdrive1",  ← Match rclone remote name
      "enabled": true,
      "description": "Primary Google Drive"
    }
  ]
}
```

### 6. Run Application

```powershell
python main.py
```

## Troubleshooting

**Problem: "rclone not found"**
- Add rclone to PATH or place rclone.exe in project folder

**Problem: "No enabled drives configured"**
- Run `rclone listremotes` to see configured remotes
- Update config\drives.json with correct remote names

**Problem: "PySide6 not found"**
- Run: `pip install PySide6`

## Usage

1. Upload Tab: Drag & drop files or browse
2. Download Tab: Select file and download
3. Settings Tab: View configuration

## File Locations

- Manifests: `manifests/` folder
- Temp chunks: `chunks/` folder (auto-cleanup)
- Config: `config/drives.json`
- Rclone config: `config/rclone.conf` (auto-created)

## Support

See README.md for detailed documentation.
