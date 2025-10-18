# Permanent Delete - Bypass Google Drive Trash

**Date**: October 19, 2025  
**Issue**: Deleted files go to Google Drive Trash/Bin instead of being permanently deleted

## Problem
When deleting files from the library, they were being sent to Google Drive's Trash bin instead of being permanently deleted. This means:
- Files still take up storage space
- User has to manually empty trash
- Not truly "deleted" until trash is emptied

## Solution
Added `--drive-use-trash=false` flag to rclone delete command to **bypass trash** and **permanently delete** files.

## Changes Made

### 1. **Rclone Delete Command**

**Before:**
```python
cmd = [
    "rclone",
    "delete",
    f"{remote_name}:{remote_path}"
]
# Result: Files go to trash, still use storage
```

**After:**
```python
cmd = [
    "rclone",
    "delete",
    f"{remote_name}:{remote_path}",
    "--drive-use-trash=false"  # Permanently delete
]
# Result: Files are GONE forever, storage freed immediately
```

### 2. **Function Signature**
```python
def delete_file(self, remote_name: str, remote_path: str, use_trash: bool = False)
```

**Parameters:**
- `use_trash=False` (default): Permanently delete, bypass trash
- `use_trash=True`: Send to trash (recoverable for 30 days)

### 3. **Updated Warning Dialog**

**New warnings added:**
- "This will **PERMANENTLY** delete:"
- "• All cloud chunks **(bypasses trash)**"
- "⚠️ Files will NOT go to trash - they are GONE forever!"
- "This action cannot be undone!"

## Behavior Comparison

| Action | Before | After |
|--------|--------|-------|
| Delete from Library | → Google Drive Trash | → Permanently deleted |
| Storage freed | ❌ No (still in trash) | ✅ Yes (immediately) |
| Recoverable | ✅ Yes (30 days) | ❌ No (gone forever) |
| Manual trash empty needed | ✅ Yes | ❌ No |

## Rclone Flag Details

**`--drive-use-trash=false`**
- Bypasses Google Drive trash/recycle bin
- Files are **immediately and permanently deleted**
- Cannot be recovered from trash
- Storage space freed instantly
- No 30-day recovery period

**Default behavior without flag:**
- Files go to trash
- Can recover within 30 days
- Still counts toward storage quota
- Must manually empty trash to free space

## User Impact

### ✅ Benefits
1. **Storage freed immediately** - No need to empty trash
2. **Cleaner Drive** - No clutter in trash bin
3. **True deletion** - When you delete, it's gone
4. **No manual cleanup** - Don't have to remember to empty trash

### ⚠️ Risks
1. **No recovery** - Cannot recover deleted files
2. **Accidental deletion** - If you click delete by mistake, it's permanent
3. **No 30-day grace period** - Gone immediately

### 🛡️ Safety Measures
1. **Confirmation dialog** with multiple warnings
2. **Clear messaging** - "PERMANENTLY delete", "NOT go to trash"
3. **Red text warnings** - High visibility
4. **Cancel button** - Easy to abort

## Testing

1. **Upload a test file**
2. **Delete it from Library**
3. **Check confirmation dialog** - Should see new warnings
4. **Confirm deletion**
5. **Check Google Drive Trash** - File should NOT be there
6. **Check storage** - Should free up immediately

## Console Output

```
[DELETE] Attempting to delete chunk: test.part0000.chunk from drive: gfh
[DELETE] Deleting from iyuhg:MultiDriveSplit/test.part0000.chunk
[RCLONE DELETE] Running: rclone delete iyuhg:MultiDriveSplit/test.part0000.chunk --drive-use-trash=false -v
[RCLONE DELETE] Return code: 0
[DELETE] ✓ Deleted test.part0000.chunk
✓ Deleted test.txt completely (1 chunks)
```

## Alternative: Keep Trash Functionality

If you want to keep trash functionality (recoverable deletes), you can:

**Option 1: Change default in code**
```python
def delete_file(self, remote_name: str, remote_path: str, use_trash: bool = True):
    # Now sends to trash by default
```

**Option 2: Add user setting**
```python
# In app settings
permanent_delete = self.config.app_settings.get('permanent_delete', True)
success, error = self.rclone.delete_file(remote_name, remote_path, use_trash=not permanent_delete)
```

**Option 3: Add checkbox in delete dialog**
```python
ft.Checkbox(
    label="Permanently delete (bypass trash)",
    value=True,
    on_change=lambda e: ...
)
```

## Recommendation

**Keep permanent delete as default** because:
1. App is for chunked file management - files are split/encrypted
2. Original files should be kept elsewhere (this is cloud backup)
3. Users expect "delete" to free storage immediately
4. Chunked files in trash are not useful (can't recover partial files easily)

## Notes

- Only applies to Google Drive (--drive-use-trash flag)
- Other cloud providers may have different trash behavior
- Local files (manifests, chunks) are always permanently deleted
- rclone v1.53+ required for --drive-use-trash flag

## Verification

After deletion:
1. ✅ Files NOT in Google Drive main folder
2. ✅ Files NOT in Google Drive trash
3. ✅ Storage quota decreased immediately
4. ✅ Manifests removed from local folder
5. ✅ Local chunks removed from chunks folder
6. ✅ Library updated automatically
