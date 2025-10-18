# Delete Function - Missing Chunk Name Fix

**Date**: October 19, 2025  
**Error**: `[DELETE] ✗ Missing remote_name or chunk_name`

## Problem
When deleting files, chunks were not being deleted from Google Drive because the delete function was looking for the wrong key in the manifest.

## Root Cause

### Manifest Structure
When files are uploaded, the manifest stores chunk info like this:
```json
{
  "chunks": [
    {
      "index": 0,
      "filename": "file.part0000.chunk",  ← This is the key!
      "drive": "gfh",
      "remote_path": "MultiDriveSplit/file.part0000.chunk",
      "size": 104857600,
      "hash": "abc123...",
      "status": "uploaded"
    }
  ]
}
```

### The Bug
Delete function was looking for:
```python
chunk_name = chunk_info.get('cloud_name')  # ❌ Wrong key!
```

But manifest stores it as:
```python
chunk_name = chunk_info.get('filename')  # ✅ Correct key!
```

## Fix Applied

### Before:
```python
chunk_name = chunk_info.get('cloud_name')
if not chunk_name:
    print("[DELETE] ✗ Missing chunk_name")
```

Result: **Always missing** → No chunks deleted from cloud!

### After:
```python
# Try both keys for backward compatibility
chunk_name = chunk_info.get('filename') or chunk_info.get('cloud_name')
if chunk_name:
    # Delete from cloud
    upload_folder = self.config.app_settings.get('upload_folder', 'MultiDriveSplit')
    remote_path = f"{upload_folder}/{chunk_name}"
    success, error = self.rclone.delete_file(remote_name, remote_path)
```

Result: **Finds chunk name** → Deletes from cloud! ✅

## Why Two Keys?

**Backward Compatibility**: 
- Old manifests might use `cloud_name`
- New manifests use `filename`
- Code checks both: `get('filename') or get('cloud_name')`

This ensures delete works for both old and new uploads!

## Testing

1. **Restart app**: `python main_flet_new.py`
2. **Upload a test file**
3. **Delete the file** from Library
4. **Check console output**:
   ```
   [DELETE] Attempting to delete chunk: file.part0000.chunk from drive: gfh
   [DELETE] Deleting from iyuhg:MultiDriveSplit/file.part0000.chunk
   [RCLONE DELETE] Running: rclone delete iyuhg:MultiDriveSplit/file.part0000.chunk
   [DELETE] ✓ Deleted file.part0000.chunk
   ```
5. **Refresh Google Drive** - file should be gone!

## What Gets Deleted

When you delete a file from Library:

1. ✅ **All cloud chunks** - From Google Drive (rclone delete)
2. ✅ **Local manifest** - From `manifests/` folder
3. ✅ **Local chunks** - From `chunks/` folder (if they exist)

## Console Output

**Success**:
```
[DELETE] Attempting to delete chunk: file.part0000.chunk from drive: gfh
[DELETE] Deleting from iyuhg:MultiDriveSplit/file.part0000.chunk
[RCLONE DELETE] Return code: 0
[DELETE] ✓ Deleted file.part0000.chunk
✓ Deleted filename.ext completely (3 chunks)
```

**Failure**:
```
[DELETE] ✗ Missing remote_name or chunk_name
⚠️ Deleted 0/3 chunks. 3 failed. Check console for details.
```

## Verification

After deleting a file:
1. Check Google Drive - chunks should be **gone**
2. Check `manifests/` folder - manifest JSON should be **gone**
3. Check `chunks/` folder - local chunks should be **gone**
4. Library should **update automatically**

## Notes

- Delete is **permanent** - no undo!
- Uses `rclone delete` command
- Runs in background thread (non-blocking)
- Shows success/failure count in notification
- Detailed logs in console for debugging

## Common Issues

**Issue**: "Deleted but still showing on Drive"
**Cause**: Was looking for wrong key (`cloud_name` instead of `filename`)
**Fixed**: Now checks both keys ✅

**Issue**: "Access denied"
**Cause**: File/folder in use or permissions issue
**Solution**: Close apps, check OneDrive sync, run as admin

**Issue**: "Rate limit exceeded"
**Cause**: Too many delete operations
**Solution**: Wait 2-5 minutes, then try again
