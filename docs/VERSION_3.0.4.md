# Version 3.0.4 Release Notes

**Release Date:** January 19, 2025  
**Critical Fix:** Terminal Window Popup Suppression

## 🎯 Primary Fix

### Terminal Window Popup Issue (CRITICAL)
- **Problem**: Terminal windows were randomly popping up during file operations (uploads, downloads, drive checks)
- **Root Cause**: `subprocess.run()` and `subprocess.Popen()` calls in Python were not configured with Windows-specific flags to suppress console windows
- **Solution**: Added comprehensive subprocess window suppression across all modules

## 🔧 Technical Changes

### 1. **app_flet_restored.py**
```python
# Added Windows-specific subprocess configuration
if sys.platform == 'win32':
    CREATE_NO_WINDOW = 0x08000000
    SUBPROCESS_FLAGS = {
        'creationflags': CREATE_NO_WINDOW,
        'startupinfo': configured_startupinfo
    }
```

**Fixed subprocess calls:**
- OAuth authentication (line ~3603)
- Drive deletion (line ~3692)
- Wipe data operation (line ~3906)
- Drive health checks (line ~4370)

### 2. **core/rclone_manager.py**
**Added identical Windows subprocess suppression**

**Fixed all subprocess operations:**
- `is_rclone_available()` - rclone version check
- `get_rclone_version()` - version string retrieval
- `list_remotes()` - remote listing
- `warmup_remote()` - drive warmup
- `upload_file()` - file upload with Popen (live progress)
- `download_file()` - file download with Popen (live progress)
- `delete_file()` - file deletion
- `remote_exists()` - existence check
- `configure_remote_interactive()` - OAuth configuration
- `get_drive_stats()` - storage statistics
- `list_remote_files()` - file listing

### 3. **Subprocess Flags Applied**
```python
CREATE_NO_WINDOW = 0x08000000  # Windows flag to prevent console creation
startupinfo.dwFlags |= STARTF_USESHOWWINDOW
startupinfo.wShowWindow = SW_HIDE
```

## ✅ What's Fixed

1. ✅ **No terminal windows during uploads**
2. ✅ **No terminal windows during downloads**
3. ✅ **No terminal windows during OAuth authentication**
4. ✅ **No terminal windows during drive health checks**
5. ✅ **No terminal windows during file deletion**
6. ✅ **No terminal windows during remote operations**

## 📊 Impact

- **User Experience**: Clean, professional interface with no console distractions
- **Performance**: No impact - flags only affect window creation
- **Compatibility**: Windows-specific flags only applied on Windows (cross-platform safe)

## 🔍 Testing Performed

- [x] Upload files - no terminal popup
- [x] Download files - no terminal popup
- [x] Delete files - no terminal popup
- [x] Add new Google Drive - no terminal popup during OAuth
- [x] Check drive health - no terminal popup
- [x] Wipe data operation - no terminal popup

## 📦 Build Information

- **Installer**: `MultiDriveCloudManager_Setup_3.0.4.exe`
- **EXE Size**: ~9.5 MB (no change)
- **Installer Size**: ~51.5 MB
- **Python**: 3.13.7
- **Flet**: 0.28.3
- **PyInstaller**: 6.16.0 with runw.exe (windowed bootloader)

## 🎉 Version History

### v3.0.4 (Current)
- Fixed terminal window popups during all operations

### v3.0.3
- Complete code restoration (4,640 lines)
- Fixed syntax errors from manual paste
- All features working

### v3.0.2
- Attempted fixes but broke app launch

### v3.0.1
- Original release with 3 issues:
  - Terminal window visible ✅ Fixed in v3.0.4
  - Required admin rights ✅ Fixed in v3.0.3
  - Old data showing ✅ Fixed in v3.0.3

## 📝 Notes

This is a **critical hotfix** addressing user-reported terminal window popups. All previous features and fixes from v3.0.3 are retained:

- No admin rights required
- No old user data bundled
- Clean installation to %LOCALAPPDATA%
- All upload/download/OAuth features working
- Multi-select, retry system, drive health monitoring
- Complete 4,640-line codebase

## 🚀 Upgrade Instructions

1. Uninstall v3.0.3 (if installed)
2. Run `MultiDriveCloudManager_Setup_3.0.4.exe`
3. Your configuration will be preserved (in %LOCALAPPDATA%\MultiDriveCloudManager\config)
4. Enjoy silent, popup-free operation!

---

**Version 3.0.4** - The "Silent Operations" Release 🤫
