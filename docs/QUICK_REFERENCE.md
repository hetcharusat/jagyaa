# Quick Reference Guide

## Common Commands

### Setup
```powershell
# Initial setup
.\setup.ps1

# Run application
.\run.ps1

# Or manually:
.\venv\Scripts\Activate.ps1
python main.py
```

### Rclone Commands
```powershell
# Configure remotes
rclone config

# List remotes
rclone listremotes

# Test remote
rclone ls gdrive1:

# Check storage
rclone about gdrive1:

# Delete files (cleanup)
rclone delete gdrive1:MultiDriveSplit
```

## Configuration Quick Edit

### Add a Drive
Edit `config/drives.json`:
```json
{
  "name": "drive4",
  "remote_name": "gdrive4",
  "enabled": true,
  "description": "Additional Drive"
}
```

### Change Chunk Size
```json
"chunk_size_mb": 50  // Change from 100 to 50 MB
```

### Adjust Concurrency
```json
"max_concurrent_uploads": 5  // Increase from 3 to 5
```

## File Operations

### Upload File
1. Drag file to application
2. Or click "Browse for File"
3. Watch progress
4. Note the manifest ID

### Download File
1. Go to Download tab
2. Click Refresh
3. Select file
4. Choose save location
5. Wait for completion

### Cancel Operation
Click "Cancel Upload" or "Cancel Download" button anytime

## Manifest Management

### Location
`manifests/*.json`

### Structure
```json
{
  "manifest_id": "filename_timestamp",
  "original_file": {...},
  "chunks": [{...}],
  "status": "completed"
}
```

### Manual Operations
```powershell
# View manifest
cat manifests\filename_20251018_143022.json

# Delete manifest
rm manifests\filename_20251018_143022.json

# Backup manifests
copy manifests\*.json backup\
```

## Troubleshooting Quick Fixes

### "rclone not found"
```powershell
# Check if rclone is in PATH
rclone version

# If not, add to PATH or copy rclone.exe to project folder
```

### "No enabled drives"
```powershell
# Check rclone remotes
rclone listremotes

# Edit config
notepad config\drives.json
```

### Reset Configuration
```powershell
# Backup current config
copy config\drives.json config\drives.backup.json

# Reset to default
copy config\drives.example.json config\drives.json
```

### Clear Temporary Files
```powershell
# Remove temp chunks
rm -r chunks\*

# Clear downloads
rm -r downloads\*
```

## Performance Tuning

### For Faster Uploads (Better Connection)
```json
"chunk_size_mb": 200,
"max_concurrent_uploads": 5
```

### For Slower Connections
```json
"chunk_size_mb": 50,
"max_concurrent_uploads": 2
```

### For Many Small Files
```json
"chunk_size_mb": 25,
"max_concurrent_uploads": 4
```

## Keyboard Shortcuts

In Application:
- **Drag & Drop**: Drag file anywhere in Upload tab
- **Ctrl+O**: Browse for file (when Upload tab active)
- **Alt+Tab**: Switch between tabs
- **Esc**: Cancel current operation

## File Size Limits

### Google Drive Limits
- Free: 15 GB per account
- With 3 drives: 45 GB total
- With 5 drives: 75 GB total

### Application Limits
- No file size limit
- Tested up to 100 GB
- Limited only by available drive space

## Common File Sizes and Chunks

| File Size | Chunks (100MB) | Drives Needed |
|-----------|----------------|---------------|
| 500 MB    | 5 chunks       | 1 drive       |
| 1 GB      | 10 chunks      | 2 drives      |
| 5 GB      | 50 chunks      | 2 drives      |
| 10 GB     | 100 chunks     | 3 drives      |
| 50 GB     | 500 chunks     | 4 drives      |

## Backup and Restore

### Backup Everything
```powershell
# Create backup folder
mkdir backup_$(Get-Date -Format 'yyyyMMdd')

# Copy important files
copy config\drives.json backup_$(Get-Date -Format 'yyyyMMdd')\
copy manifests\*.json backup_$(Get-Date -Format 'yyyyMMdd')\manifests\
```

### Restore
```powershell
copy backup_20251018\drives.json config\
copy backup_20251018\manifests\*.json manifests\
```

## Development

### Run Tests
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Run module tests
python -m core.chunker
python -m core.config_manager
python -m core.rclone_manager
```

### Build Executable
```powershell
pip install pyinstaller
pyinstaller --windowed --onefile main.py
```

## Support Resources

- Full docs: `README.md`
- Setup guide: `SETUP.md`
- Rclone help: `docs\RCLONE_SETUP.md`
- Build guide: `docs\BUILD.md`
- Changelog: `CHANGELOG.md`

## Emergency Procedures

### Application Crashes
1. Check `chunks\` folder for leftover files
2. Check Activity Log before crash
3. Verify rclone still works: `rclone version`
4. Try running manually: `python main.py`

### Upload Stuck
1. Click "Cancel Upload"
2. Check internet connection
3. Test rclone: `rclone ls gdrive1:`
4. Restart application

### Download Fails
1. Check manifest exists: `ls manifests\`
2. Verify remotes: `rclone listremotes`
3. Check drive storage: `rclone about gdrive1:`
4. Try manual download: `rclone copy gdrive1:MultiDriveSplit/chunk.file .`

## Pro Tips

1. **Use descriptive names** for manifests (rename files before upload)
2. **Keep manifests safe** - they're needed for downloads
3. **Test with small files** first (< 100 MB)
4. **Monitor storage** - use `rclone about` regularly
5. **Backup manifests** to another location
6. **Use stable internet** for large uploads
7. **Close other cloud apps** during transfers
8. **Enable drives gradually** (test with 2 first)

## Getting Help

1. Check Activity Log in application
2. Review troubleshooting section in README.md
3. Test rclone independently
4. Check Google Drive quotas
5. Verify configuration files
