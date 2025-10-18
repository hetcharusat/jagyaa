# 📁 PROJECT STRUCTURE

```
jagyaa/                                 # Multi-Google Drive Split Uploader
│
├── 📄 main.py                          # Application entry point
├── 📄 test_system.py                   # System diagnostic tool
├── 📄 requirements.txt                 # Python dependencies
├── 📄 setup.ps1                        # Automated setup script
├── 📄 run.ps1                          # Quick launcher
│
├── 📚 DOCUMENTATION
│   ├── README.md                       # Complete user guide
│   ├── SETUP.md                        # Quick setup guide
│   ├── CHANGELOG.md                    # Version history
│   ├── LICENSE                         # MIT License
│   └── docs/
│       ├── RCLONE_SETUP.md            # Rclone configuration
│       ├── BUILD.md                    # Build instructions
│       └── QUICK_REFERENCE.md          # Command reference
│
├── 🔧 CONFIGURATION
│   └── config/
│       ├── drives.json                 # User configuration (create from example)
│       ├── drives.example.json         # Configuration template
│       └── rclone.conf                 # Rclone config (auto-generated)
│
├── 💻 CORE ENGINE
│   └── core/
│       ├── __init__.py                 # Module exports
│       ├── chunker.py                  # File splitting/merging + SHA-256
│       ├── config_manager.py           # Settings and drive management
│       ├── rclone_manager.py           # Rclone wrapper
│       ├── manifest.py                 # Metadata tracking
│       ├── uploader.py                 # Upload orchestration
│       └── downloader.py               # Download orchestration
│
├── 🖥️ USER INTERFACE
│   └── gui/
│       ├── __init__.py                 # GUI module
│       └── main_window.py              # PySide6 application
│
├── 📊 DATA STORAGE (Auto-created)
│   ├── manifests/                      # Upload metadata (JSON)
│   │   └── *.json                      # One file per upload
│   │
│   ├── chunks/                         # Temporary chunk storage
│   │   └── *.chunk                     # Deleted after upload
│   │
│   └── downloads/                      # Default download location
│
└── 🏗️ BUILD ARTIFACTS (Generated)
    ├── venv/                           # Python virtual environment
    ├── build/                          # PyInstaller build files
    ├── dist/                           # Compiled executable
    └── __pycache__/                    # Python cache files

```

---

## 🎯 CORE MODULES EXPLAINED

### 1. **chunker.py** - File Operations
- **Purpose**: Split large files into chunks and merge them back
- **Key Features**:
  - Configurable chunk size (default: 100 MB)
  - SHA-256 hashing for integrity
  - Progress callbacks
  - Memory-efficient streaming

### 2. **config_manager.py** - Configuration
- **Purpose**: Manage app settings and drive configurations
- **Key Features**:
  - JSON-based configuration
  - Drive enable/disable
  - Settings persistence
  - Default values

### 3. **rclone_manager.py** - Cloud Operations
- **Purpose**: Interface with rclone for uploads/downloads
- **Key Features**:
  - Remote detection
  - File upload/download
  - Progress tracking
  - Error handling

### 4. **manifest.py** - Metadata Management
- **Purpose**: Track chunk locations and file info
- **Key Features**:
  - JSON manifest files
  - Upload progress tracking
  - Chunk status updates
  - Manifest querying

### 5. **uploader.py** - Upload Engine
- **Purpose**: Orchestrate multi-drive uploads
- **Key Features**:
  - File chunking
  - Round-robin distribution
  - Concurrent uploads
  - Manifest creation

### 6. **downloader.py** - Download Engine
- **Purpose**: Retrieve and reconstruct files
- **Key Features**:
  - Concurrent downloads
  - Chunk verification
  - File merging
  - Integrity checking

### 7. **main_window.py** - GUI
- **Purpose**: User interface
- **Key Features**:
  - Drag & drop support
  - Progress bars
  - Real-time logging
  - Tabbed interface

---

## 🔄 DATA FLOW

### Upload Process
```
┌──────────────┐
│  User File   │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Calculate Hash  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Split to Chunks │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Create Manifest  │
└──────┬───────────┘
       │
       ▼
┌──────────────────────┐
│ Upload to Drives     │
│ (Round-Robin)        │
│  Chunk 0 → Drive 1   │
│  Chunk 1 → Drive 2   │
│  Chunk 2 → Drive 3   │
│  Chunk 3 → Drive 1   │
│  ...                 │
└──────┬───────────────┘
       │
       ▼
┌──────────────────┐
│  Update Manifest │
│  Status: Complete│
└──────────────────┘
```

### Download Process
```
┌──────────────────┐
│  Load Manifest   │
└──────┬───────────┘
       │
       ▼
┌──────────────────────┐
│ Download All Chunks  │
│ (Concurrent)         │
│  Drive 1 → Chunk 0   │
│  Drive 2 → Chunk 1   │
│  Drive 3 → Chunk 2   │
│  ...                 │
└──────┬───────────────┘
       │
       ▼
┌──────────────────┐
│  Verify Hashes   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Merge Chunks    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Verify Final Hash│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Reconstructed    │
│ Original File    │
└──────────────────┘
```

---

## 🛠️ TECHNOLOGY STACK

### Core
- **Python 3.8+** - Main language
- **Rclone** - Cloud storage backend

### GUI
- **PySide6** - Qt for Python (UI framework)
- **Qt Widgets** - UI components
- **Qt Threading** - Background operations

### Libraries
- **hashlib** - SHA-256 hashing
- **json** - Configuration and manifests
- **pathlib** - Cross-platform file paths
- **subprocess** - Rclone execution
- **concurrent.futures** - Parallel operations

### Build Tools
- **PyInstaller** - Executable creation
- **Virtual Environment** - Dependency isolation

---

## 📊 FILE SPECIFICATIONS

### Manifest File Format (.json)
```json
{
  "manifest_id": "string",
  "version": "1.0",
  "created_at": "ISO-8601",
  "original_file": {
    "filename": "string",
    "path": "string",
    "size": number,
    "size_formatted": "string",
    "hash": "SHA-256"
  },
  "chunks": [
    {
      "index": number,
      "filename": "string",
      "local_path": "string",
      "size": number,
      "size_formatted": "string",
      "hash": "SHA-256",
      "drive": "string",
      "remote_path": "string",
      "status": "uploaded|pending|failed",
      "uploaded_at": "ISO-8601"
    }
  ],
  "total_chunks": number,
  "status": "created|uploading|completed|failed|cancelled"
}
```

### Configuration File (drives.json)
```json
{
  "drives": [
    {
      "name": "string",
      "remote_name": "string",
      "enabled": boolean,
      "description": "string"
    }
  ],
  "settings": {
    "chunk_size_mb": number,
    "max_concurrent_uploads": number,
    "upload_folder": "string",
    "manifest_folder": "string",
    "temp_folder": "string"
  }
}
```

---

## 🚀 EXECUTION PATHS

### Normal Startup
1. User runs `python main.py` or double-clicks `.exe`
2. Main imports GUI module
3. ConfigManager loads settings
4. RcloneManager initializes
5. MainWindow creates UI
6. Application waits for user input

### Upload Execution
1. User drops file or browses
2. UploadThread created
3. Uploader.upload_file() called
4. FileChunker splits file
5. ManifestManager creates manifest
6. ThreadPool uploads chunks
7. Progress signals update GUI
8. Manifest marked complete
9. Temp files cleaned up

### Download Execution
1. User selects manifest
2. DownloadThread created
3. Downloader.download_file() called
4. ThreadPool downloads chunks
5. FileChunker verifies and merges
6. Final hash verified
7. Temp files cleaned up
8. User notified

---

## 🎨 GUI COMPONENTS

### Upload Tab
- Drop zone (drag & drop)
- Browse button
- Progress bar
- Status label
- Chunk counter
- Cancel button

### Download Tab
- Available files list
- Refresh button
- Download button
- Progress bar
- Status label
- Chunk counter
- Cancel button

### Settings Tab
- Drive status display
- Configure rclone button
- Current settings display

### Activity Log (Bottom)
- Real-time operation log
- Timestamped entries
- Scrollable text area

---

## 🔐 SECURITY NOTES

### Current Implementation
- Files transferred in plaintext
- Rclone handles OAuth2 tokens
- Local manifest files unencrypted
- SHA-256 for integrity only (not encryption)

### Future Security Features
- AES-256 chunk encryption
- Encrypted manifest storage
- Password protection
- Token encryption

---

## 💡 EXTENSION POINTS

### Adding Cloud Providers
1. Implement provider adapter in `rclone_manager.py`
2. Add provider-specific config in `config_manager.py`
3. Update GUI to show provider selection

### Adding Compression
1. Add compression step in `chunker.py` after splitting
2. Add decompression step before merging
3. Store compression type in manifest

### Adding CLI Mode
1. Create `cli.py` with argparse
2. Import core modules
3. Implement command handlers
4. Add to build as separate entry point

---

## 📈 PERFORMANCE CHARACTERISTICS

### Upload Speed
- **Bottleneck**: Internet upload speed
- **Optimization**: Increase concurrent uploads
- **Limitation**: Drive API rate limits

### Download Speed
- **Bottleneck**: Internet download speed
- **Optimization**: Increase concurrent downloads
- **Limitation**: Drive API rate limits

### Memory Usage
- **Chunking**: Streaming, low memory
- **Merging**: Streaming, low memory
- **Peak**: ~100-200 MB for typical operation

### Disk Usage
- **Temp chunks**: 2x original file size during upload
- **Downloaded chunks**: 1x file size during download
- **Manifests**: ~1-10 KB per file

---

## 🧪 TESTING STRATEGY

### Unit Testing (Future)
- Test each core module independently
- Mock rclone operations
- Test edge cases (empty files, huge files, etc.)

### Integration Testing
- Use `test_system.py` for system checks
- Test with real rclone remotes
- Verify end-to-end workflows

### Manual Testing
- Upload various file types
- Test with different chunk sizes
- Test cancellation
- Verify integrity

---

**Last Updated**: October 18, 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✓
