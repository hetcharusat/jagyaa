# 🚀 Multi-Google Drive Split Uploader

A lightweight desktop application that uploads and downloads large files across **multiple Google Drive accounts** using intelligent chunking and distribution.

![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

- 📦 **Intelligent File Chunking** - Automatically split large files into configurable chunks
- ☁️ **Multi-Drive Distribution** - Distribute chunks across multiple Google Drive accounts
- 🔒 **Integrity Verification** - SHA-256 hashing ensures data integrity
- ⚡ **Concurrent Operations** - Parallel upload/download for maximum speed
- 🎯 **Drag & Drop Interface** - Simple and intuitive GUI
- 📊 **Progress Tracking** - Real-time progress bars and status updates
- 🔄 **Pause/Resume** - Cancel operations at any time
- 📝 **Manifest System** - JSON-based metadata for easy file reconstruction

## 🏗️ Architecture

```
┌─────────────────┐
│   PySide6 GUI   │  ← User Interface
├─────────────────┤
│  Uploader/      │  ← Business Logic
│  Downloader     │
├─────────────────┤
│  File Chunker   │  ← Core Operations
│  Manifest Mgr   │
├─────────────────┤
│ Rclone Manager  │  ← Backend Integration
└─────────────────┘
         ↓
   Google Drives
```

## 📋 Prerequisites

### 1. Python 3.8 or Higher
```powershell
python --version
```

### 2. Rclone
Download and install from [rclone.org](https://rclone.org/downloads/)

**Windows Installation:**
```powershell
# Download rclone and add to PATH, or:
winget install Rclone.Rclone
```

Verify installation:
```powershell
rclone version
```

### 3. Google Drive Accounts
You'll need at least 2-3 Google Drive accounts configured in rclone.

## 🚀 Quick Start

### Step 1: Clone or Extract Project
```powershell
cd C:\Users\hetp2\OneDrive\Desktop\jagyaa
```

### Step 2: Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Rclone Remotes

Run rclone configuration:
```powershell
rclone config
```

**Add each Google Drive:**
1. Type `n` for new remote
2. Name it (e.g., `gdrive1`, `gdrive2`, `gdrive3`)
3. Choose `Google Drive` (option 15)
4. Leave Client ID blank (press Enter)
5. Leave Client Secret blank (press Enter)
6. Choose scope `1` (Full access)
7. Leave Root Folder ID blank
8. Leave Service Account File blank
9. Edit advanced config? `n`
10. Auto config? `y` (browser will open)
11. Authenticate with your Google account
12. Configure as Team Drive? `n`
13. Confirm settings

Repeat for each Google Drive account.

**Verify remotes:**
```powershell
rclone listremotes
```

You should see:
```
gdrive1:
gdrive2:
gdrive3:
```

### Step 5: Configure Application

Copy the example configuration:
```powershell
cp config\drives.example.json config\drives.json
```

Edit `config\drives.json`:
```json
{
  "drives": [
    {
      "name": "drive1",
      "remote_name": "gdrive1",
      "enabled": true,
      "description": "Primary Google Drive"
    },
    {
      "name": "drive2",
      "remote_name": "gdrive2",
      "enabled": true,
      "description": "Secondary Google Drive"
    },
    {
      "name": "drive3",
      "remote_name": "gdrive3",
      "enabled": true,
      "description": "Backup Google Drive"
    }
  ],
  "settings": {
    "chunk_size_mb": 100,
    "max_concurrent_uploads": 3,
    "upload_folder": "MultiDriveSplit",
    "manifest_folder": "manifests",
    "temp_folder": "chunks"
  }
}
```

**Important:** Match `remote_name` values with your rclone remote names!

### Step 6: Run Application
```powershell
python main.py
```

## 📖 Usage Guide

### Uploading Files

**Method 1: Drag & Drop**
1. Open the application
2. Go to the **Upload** tab
3. Drag and drop any file onto the drop zone
4. Upload starts automatically

**Method 2: Browse**
1. Click **Browse for File** button
2. Select your file
3. Upload starts automatically

**What happens during upload:**
1. File is hashed (SHA-256)
2. File is split into chunks (default: 100 MB each)
3. Chunks are distributed across drives in round-robin
4. Manifest file is created in `manifests/` folder
5. All chunks uploaded concurrently
6. Temporary chunks are cleaned up

### Downloading Files

1. Go to the **Download** tab
2. Click **Refresh** to see available files
3. Select a file from the list
4. Click **Download Selected**
5. Choose save location
6. File is reconstructed automatically

**What happens during download:**
1. All chunks downloaded concurrently
2. Chunks are verified (SHA-256)
3. Chunks are merged in correct order
4. Final file hash is verified
5. Temporary files are cleaned up

### Settings

The **Settings** tab shows:
- Configured rclone remotes
- Enabled drives
- Current application settings

Click **Configure Rclone Remotes** to add/modify remotes.

## 📁 Project Structure

```
jagyaa/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore
│
├── config/
│   ├── drives.json        # Drive configuration (user-created)
│   ├── drives.example.json # Configuration template
│   └── rclone.conf        # Rclone config (auto-generated)
│
├── core/                  # Core business logic
│   ├── __init__.py
│   ├── chunker.py         # File splitting/merging
│   ├── config_manager.py  # Configuration handling
│   ├── rclone_manager.py  # Rclone operations
│   ├── manifest.py        # Manifest management
│   ├── uploader.py        # Upload orchestration
│   └── downloader.py      # Download orchestration
│
├── gui/                   # User interface
│   ├── __init__.py
│   └── main_window.py     # Main application window
│
├── manifests/             # Upload manifests (auto-created)
│   └── *.json
│
├── chunks/                # Temporary chunk storage (auto-created)
└── downloads/             # Default download location
```

## ⚙️ Configuration Options

Edit `config/drives.json` to customize:

| Setting | Description | Default |
|---------|-------------|---------|
| `chunk_size_mb` | Size of each chunk in MB | 100 |
| `max_concurrent_uploads` | Parallel upload threads | 3 |
| `upload_folder` | Folder name on remote drives | MultiDriveSplit |
| `manifest_folder` | Local manifest storage | manifests |
| `temp_folder` | Temporary chunk storage | chunks |

## 🔧 Advanced Usage

### CLI Mode (Future Enhancement)

The core modules can be used independently:

```python
from core import ConfigManager, RcloneManager, ManifestManager, Uploader

config = ConfigManager()
rclone = RcloneManager(config_path=config.get_rclone_config_path())
manifest = ManifestManager(config.get_manifest_folder())
uploader = Uploader(config, rclone, manifest)

# Upload a file
manifest_id = uploader.upload_file("large_file.zip")
print(f"Uploaded: {manifest_id}")
```

### Manifest File Structure

Each upload creates a JSON manifest in `manifests/`:

```json
{
  "manifest_id": "myfile_20251018_143022",
  "version": "1.0",
  "created_at": "2025-10-18T14:30:22",
  "original_file": {
    "filename": "myfile.zip",
    "path": "/full/path/to/myfile.zip",
    "size": 524288000,
    "size_formatted": "500.00 MB",
    "hash": "abc123..."
  },
  "chunks": [
    {
      "index": 0,
      "filename": "myfile.part0000.zip.chunk",
      "size": 104857600,
      "hash": "def456...",
      "drive": "drive1",
      "remote_path": "MultiDriveSplit/myfile.part0000.zip.chunk",
      "status": "uploaded",
      "uploaded_at": "2025-10-18T14:35:00"
    }
  ],
  "total_chunks": 5,
  "status": "completed"
}
```

## 🛠️ Building Executable

To create a standalone `.exe` (no Python required):

### Install PyInstaller
```powershell
pip install pyinstaller
```

### Build Executable
```powershell
pyinstaller --name="MultiDriveSplitUploader" `
            --windowed `
            --onefile `
            --icon=icon.ico `
            --add-data="config;config" `
            main.py
```

The executable will be in `dist/` folder.

**Note:** Users still need rclone installed separately.

## 📦 Distribution Package

To create a distributable package:

1. Build the executable (see above)
2. Create a folder structure:
```
MultiDriveSplitUploader/
├── MultiDriveSplitUploader.exe
├── rclone.exe (download from rclone.org)
├── config/
│   └── drives.example.json
└── README.txt (setup instructions)
```

3. Zip the folder for distribution

## 🐛 Troubleshooting

### "rclone not found"
- Ensure rclone is installed and in PATH
- Verify: `rclone version`

### "No enabled drives configured"
- Configure rclone remotes: `rclone config`
- Update `config/drives.json` with correct remote names
- Ensure `enabled: true` for at least one drive

### Upload/Download Fails
- Check internet connection
- Verify rclone remotes: `rclone listremotes`
- Check Google Drive quotas
- Review Activity Log in the application

### GUI Doesn't Start
- Ensure PySide6 is installed: `pip install PySide6`
- Check Python version: `python --version` (must be 3.8+)

## 🔮 Future Enhancements

- [ ] **Encryption** - AES-256 encryption for chunks
- [ ] **Compression** - Optional compression before chunking
- [ ] **Resume Support** - Resume interrupted uploads/downloads
- [ ] **Remote Manifest Backup** - Store manifests on cloud
- [ ] **CLI Mode** - Command-line interface for automation
- [ ] **Scheduling** - Automated upload scheduling
- [ ] **Cloud Provider Support** - OneDrive, Dropbox, S3
- [ ] **Multi-Language** - Internationalization support

## 📄 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review the Activity Log in the application
- Check rclone documentation: [rclone.org/docs](https://rclone.org/docs/)

## 🙏 Acknowledgments

- **Rclone** - Amazing cloud storage CLI tool
- **PySide6** - Cross-platform Qt bindings
- **Python Community** - For excellent libraries

---

**Made with ❤️ for efficient cloud storage management**
