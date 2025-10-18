# Delete Function - Access Denied Fix

**Date**: October 19, 2025  
**Error**: `[WinError 5] Access is denied: 'chunks\\'`

## Problem
The delete function was encountering "Access Denied" errors when trying to delete files.

## Root Causes
1. **Empty chunk names** creating invalid paths (e.g., `chunks\\` instead of `chunks\\file.chunk`)
2. **Trying to delete folder** instead of just files
3. **No validation** that path is a file before deletion
4. **No error handling** for individual chunk/manifest deletion failures

## Fixes Applied

### 1. **Validate Chunk Names**
```python
# Before:
local_chunk = os.path.join(chunk_folder, chunk_info.get('cloud_name', ''))
if os.path.exists(local_chunk):
    os.remove(local_chunk)

# After:
chunk_name = chunk_info.get('cloud_name', '')
if chunk_name:  # Skip empty names
    local_chunk = os.path.join(chunk_folder, chunk_name)
    if os.path.isfile(local_chunk):  # Ensure it's a file
        try:
            os.remove(local_chunk)
        except Exception as chunk_ex:
            print(f"Failed to delete local chunk {chunk_name}: {chunk_ex}")
```

### 2. **Validate File Paths**
- Use `os.path.isfile()` instead of `os.path.exists()`
- `exists()` returns True for both files AND folders
- `isfile()` only returns True for files

### 3. **Better Error Handling**
```python
# Individual try-catch for manifest deletion
try:
    os.remove(manifest_path)
except Exception as manifest_ex:
    print(f"Failed to delete manifest: {manifest_ex}")

# Individual try-catch for each chunk
try:
    os.remove(local_chunk)
except Exception as chunk_ex:
    print(f"Failed to delete chunk: {chunk_ex}")
```

### 4. **User-Friendly Error Messages**
```python
if "Access is denied" in error_msg:
    self.show_snackbar("❌ Access denied. Close any apps using the file and try again.", ft.Colors.RED)
```

## What Changed

| Before | After |
|--------|-------|
| ❌ No chunk name validation | ✅ Skips empty chunk names |
| ❌ Used `os.path.exists()` | ✅ Uses `os.path.isfile()` |
| ❌ Single try-catch for all | ✅ Individual error handling |
| ❌ Technical error messages | ✅ User-friendly messages |
| ❌ Could try to delete folders | ✅ Only deletes files |

## Testing

1. Restart app: `python main_flet_new.py`
2. Go to Library
3. Click delete on a file
4. Confirm deletion
5. Should work without "Access Denied" error

## Common Causes of "Access Denied"

1. **File in use**: File open in another program (video player, PDF reader, etc.)
2. **Insufficient permissions**: Need admin rights for some folders
3. **Antivirus**: Antivirus locking the file
4. **Invalid path**: Trying to delete a folder instead of file
5. **Network drive**: Network issues with cloud-synced folders (OneDrive, Dropbox)

## Solution
If you still get "Access Denied":
1. Close all apps that might be using the file
2. Check if file is on OneDrive/Dropbox (may be syncing)
3. Run app as Administrator
4. Check antivirus isn't blocking file operations
5. Manual delete: Go to `manifests/` and `chunks/` folders and delete files manually

## Benefits
- ✅ No more "Access Denied" from empty paths
- ✅ Continues deleting even if one chunk fails
- ✅ Better error reporting
- ✅ User-friendly error messages
- ✅ Safer file operations
