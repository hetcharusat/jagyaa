# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-10-18

### Added
- Initial release
- File chunking with configurable chunk size
- Multi-drive distribution using rclone
- SHA-256 integrity verification
- Concurrent upload/download operations
- PySide6 GUI with drag & drop support
- Progress tracking and status updates
- Manifest-based file reconstruction
- JSON configuration system
- Activity logging
- Cancel operation support

### Core Features
- **Uploader**: Splits files and distributes chunks across multiple Google Drives
- **Downloader**: Retrieves and merges chunks with integrity verification
- **Config Manager**: Manages drive configurations and settings
- **Rclone Manager**: Handles rclone operations for cloud storage
- **Manifest Manager**: Tracks chunk metadata and upload status
- **GUI**: User-friendly interface with tabs for upload/download/settings

### Documentation
- Comprehensive README with setup instructions
- Quick setup guide (SETUP.md)
- Rclone configuration guide
- Build and packaging instructions
- Automated setup scripts for Windows

### Technical Details
- Python 3.8+ support
- Windows 10/11 target platform
- Modular architecture for easy maintenance
- Thread-based concurrent operations
- Cross-platform compatible core (Linux/macOS ready)

## [Planned for 1.1.0]

### Features
- AES-256 encryption for chunks
- Compression support (gzip/lzma)
- Resume interrupted uploads/downloads
- CLI mode for automation
- Remote manifest backup

### Improvements
- Better error handling and recovery
- Upload/download queue management
- Bandwidth throttling options
- Duplicate file detection

### Platform Support
- Linux build and packaging
- macOS build and packaging
- Docker container option
