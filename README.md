# 🌐 Multi-Drive Cloud Manager# 🚀 Multi-Google Drive Split Uploader



[![Version](https://img.shields.io/badge/version-3.0.4-blue.svg)](https://github.com/hetcharusat/jagyaa/releases)A lightweight desktop application that uploads and downloads large files across **multiple Google Drive accounts** using intelligent chunking and distribution.
## Multi-Drive Cloud Manager

Fast, clean desktop app to manage multiple Google Drives. No admin required. Windows only.

<div align="center">

<a href="https://github.com/hetcharusat/jagyaa/releases/latest">
  <img src="https://img.shields.io/badge/Download-Windows%20Installer-blue?style=for-the-badge&logo=windows&logoColor=white" alt="Download for Windows" />
  
</a>




</div>

### How To Setup

https://github.com/user-attachments/assets/3013c6ac-761f-4d84-8393-9b9058c0e071


### Features
- Multiple Google Drive accounts
- Upload/Download queues with progress
- OAuth login (supports custom Client ID/Secret)
- Clean modern UI (Flet)
- No console popups (v3.0.4)

### Install
1) Download the installer (button above)  
2) Run and follow the wizard  
3) Launch from Start Menu

Requirements: Windows 10/11, internet, and [rclone](https://rclone.org/) in PATH.

### Run from source (optional)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app_flet_restored.py
```

License: MIT. See [LICENSE](LICENSE).

**Important:** Match `remote_name` values with your rclone remote names!

- [📖 Complete Setup Guide](docs/SETUP.md)

- [🏗️ Build Instructions](docs/BUILD.md)### Step 6: Run Application

- [📝 Changelog](docs/CHANGELOG.md)```powershell

- [🔧 Rclone Configuration](docs/RCLONE_SETUP.md)python main.py

- [⚡ Performance Optimization](docs/PERFORMANCE_GUIDE.md)```

- [🎯 Quick Reference](docs/QUICK_REFERENCE.md)

## 📖 Usage Guide

**Version-Specific Notes:**

- [Version 3.0.4 Release Notes](VERSION_3.0.4.md) - Terminal popup fix### Uploading Files

- [Version 3.0.3 Release Notes](docs/VERSION_3.0.3.md) - Code restoration

- [Version 2 Features](docs/V2_FEATURES.md)**Method 1: Drag & Drop**

1. Open the application

---2. Go to the **Upload** tab

3. Drag and drop any file onto the drop zone

## 🛠️ Technology Stack4. Upload starts automatically



| Component | Technology |**Method 2: Browse**

|-----------|------------|1. Click **Browse for File** button

| **UI Framework** | [Flet 0.28.3](https://flet.dev/) (Flutter-based) |2. Select your file

| **Language** | Python 3.13 |3. Upload starts automatically

| **Cloud Backend** | [Rclone](https://rclone.org/) |

| **Packaging** | PyInstaller 6.16.0 |**What happens during upload:**

| **Installer** | Inno Setup 6.5.4 |1. File is hashed (SHA-256)

2. File is split into chunks (default: 100 MB each)

---3. Chunks are distributed across drives in round-robin

4. Manifest file is created in `manifests/` folder

## 🐛 Known Issues & Limitations5. All chunks uploaded concurrently

6. Temporary chunks are cleaned up

### Current Known Issues

- ⚠️ Rclone must be installed separately and in PATH### Downloading Files

- ⚠️ Google Drive OAuth requires browser access

- ⚠️ Large file uploads may take time depending on internet speed1. Go to the **Download** tab

2. Click **Refresh** to see available files

### Planned Improvements3. Select a file from the list

- [ ] Bundled Rclone executable4. Click **Download Selected**

- [ ] Support for OneDrive, Dropbox5. Choose save location

- [ ] File synchronization features6. File is reconstructed automatically

- [ ] Scheduled uploads/backups

**What happens during download:**

---1. All chunks downloaded concurrently

2. Chunks are verified (SHA-256)

## 🤝 Contributing3. Chunks are merged in correct order

4. Final file hash is verified

We welcome contributions! Here's how you can help:5. Temporary files are cleaned up



1. **Fork** the repository### Settings

2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)

3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)The **Settings** tab shows:

4. **Push** to the branch (`git push origin feature/AmazingFeature`)- Configured rclone remotes

5. **Open** a Pull Request- Enabled drives

- Current application settings

### Development Setup

Click **Configure Rclone Remotes** to add/modify remotes.

```bash

# Clone your fork## 📁 Project Structure

git clone https://github.com/YOUR_USERNAME/jagyaa.git

cd jagyaa```

jagyaa/

# Install development dependencies├── main.py                 # Application entry point

pip install -r requirements.txt├── requirements.txt        # Python dependencies

├── README.md              # This file

# Run from source├── .gitignore

python app_flet_restored.py│

├── config/

# Build executable│   ├── drives.json        # Drive configuration (user-created)

pyinstaller MultiDriveCloudManager.spec│   ├── drives.example.json # Configuration template

│   └── rclone.conf        # Rclone config (auto-generated)

# Create installer│

# (Requires Inno Setup installed)├── core/                  # Core business logic

"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\MultiDriveCloudManager.iss│   ├── __init__.py

```│   ├── chunker.py         # File splitting/merging

│   ├── config_manager.py  # Configuration handling

---│   ├── rclone_manager.py  # Rclone operations

│   ├── manifest.py        # Manifest management

## 📄 License│   ├── uploader.py        # Upload orchestration

│   └── downloader.py      # Download orchestration

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.│

├── gui/                   # User interface

```│   ├── __init__.py

MIT License│   └── main_window.py     # Main application window

│

Copyright (c) 2025 Het Charusat├── manifests/             # Upload manifests (auto-created)

│   └── *.json

Permission is hereby granted, free of charge, to any person obtaining a copy│

of this software and associated documentation files (the "Software"), to deal├── chunks/                # Temporary chunk storage (auto-created)

in the Software without restriction, including without limitation the rights└── downloads/             # Default download location

to use, copy, modify, merge, publish, distribute, sublicense, and/or sell```

copies of the Software...

```## ⚙️ Configuration Options



---Edit `config/drives.json` to customize:



## 🙏 Acknowledgments| Setting | Description | Default |

|---------|-------------|---------|

- **[Rclone](https://rclone.org/)** - The backbone of cloud operations| `chunk_size_mb` | Size of each chunk in MB | 100 |

- **[Flet](https://flet.dev/)** - Beautiful cross-platform UI framework| `max_concurrent_uploads` | Parallel upload threads | 3 |

- **[PyInstaller](https://pyinstaller.org/)** - Python to executable packaging| `upload_folder` | Folder name on remote drives | MultiDriveSplit |

- **Google Drive API** - Cloud storage integration| `manifest_folder` | Local manifest storage | manifests |

| `temp_folder` | Temporary chunk storage | chunks |

---

## 🔧 Advanced Usage

## 📞 Support & Contact

### CLI Mode (Future Enhancement)

- **Issues**: [GitHub Issues](https://github.com/hetcharusat/jagyaa/issues)

- **Discussions**: [GitHub Discussions](https://github.com/hetcharusat/jagyaa/discussions)The core modules can be used independently:

- **Email**: [Your Email Here]

```python

---from core import ConfigManager, RcloneManager, ManifestManager, Uploader



## 📊 Project Statsconfig = ConfigManager()

rclone = RcloneManager(config_path=config.get_rclone_config_path())

![GitHub stars](https://img.shields.io/github/stars/hetcharusat/jagyaa?style=social)manifest = ManifestManager(config.get_manifest_folder())

![GitHub forks](https://img.shields.io/github/forks/hetcharusat/jagyaa?style=social)uploader = Uploader(config, rclone, manifest)

![GitHub watchers](https://img.shields.io/github/watchers/hetcharusat/jagyaa?style=social)

# Upload a file

---manifest_id = uploader.upload_file("large_file.zip")

print(f"Uploaded: {manifest_id}")

## 🎉 Version History```



### v3.0.4 (2025-01-19) - Current### Manifest File Structure

- 🔧 **Fixed**: Terminal window popups during operations

- ✅ **Added**: Comprehensive subprocess window suppressionEach upload creates a JSON manifest in `manifests/`:

- 🎯 **Improved**: Silent operation on all cloud interactions

```json

### v3.0.3 (2025-01-18){

- 🔄 **Restored**: Complete codebase (4,640 lines)  "manifest_id": "myfile_20251018_143022",

- 🛠️ **Fixed**: Syntax errors and indentation issues  "version": "1.0",

- ✅ **Verified**: All features working correctly  "created_at": "2025-10-18T14:30:22",

  "original_file": {

### v3.0.2 (2025-01-17)    "filename": "myfile.zip",

- ⚠️ **Attempted**: Bug fixes but broke app launch    "path": "/full/path/to/myfile.zip",

- 🚫 **Status**: Deprecated    "size": 524288000,

    "size_formatted": "500.00 MB",

### v3.0.1 (2025-01-16)    "hash": "abc123..."

- 🎉 **Initial**: Public release  },

- 📦 **Features**: Core functionality complete  "chunks": [

    {

---      "index": 0,

      "filename": "myfile.part0000.zip.chunk",

<div align="center">      "size": 104857600,

      "hash": "def456...",

**Made with ❤️ by Het Charusat**      "drive": "drive1",

      "remote_path": "MultiDriveSplit/myfile.part0000.zip.chunk",

⭐ Star this repo if you find it useful!      "status": "uploaded",

      "uploaded_at": "2025-10-18T14:35:00"

[Download Latest Release](https://github.com/hetcharusat/jagyaa/releases) • [Report Bug](https://github.com/hetcharusat/jagyaa/issues) • [Request Feature](https://github.com/hetcharusat/jagyaa/issues)    }

  ],

</div>  "total_chunks": 5,

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
