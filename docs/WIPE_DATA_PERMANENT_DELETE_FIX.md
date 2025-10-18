# Wipe Data Fixes - Permanent Delete & Manifest Cleanup

**Date**: October 19, 2025  
**Issues Fixed**:
1. Wipe deleted entire folder (went to trash)
2. Library still showing files after wipe

## ✅ Fixes Applied

### Fix 1: Keep Folder, Delete Contents Only

**Before:**
```python
rclone purge remote:MultiDriveSplit
```
- **Problem**: `purge` deletes the folder itself
- **Result**: Folder gone, had to recreate manually
- **Trash**: Folder ended up in Google Drive trash

**After:**
```python
rclone delete remote:MultiDriveSplit --drive-use-trash=false
```
- **Solution**: `delete` removes contents only
- **Result**: Folder remains, only files deleted
- **Trash**: Files bypass trash (permanent delete)

### Fix 2: Clear Local Manifests After Wipe

**Before:**
```python
# After wipe
✓ Wiped folder
# But manifests still exist locally!
# Library shows files that don't exist anymore
```

**After:**
```python
# After wipe
1. Delete files from Drive
2. Find all manifests for this drive
3. Delete matching manifests
4. Refresh library
✓ Wiped folder and cleared 15 local manifests
```

## How It Works Now

### Wipe Process (Step by Step)

1. **User clicks "Wipe Data"**
2. **Confirmation dialog** shows what will be deleted
3. **User confirms**
4. **Wipe thread starts:**
   ```
   [WIPE] Deleting all files from iyuhg:MultiDriveSplit
   → rclone delete iyuhg:MultiDriveSplit --drive-use-trash=false
   → Files deleted permanently (bypass trash)
   → Folder remains empty
   ```
5. **Clean local manifests:**
   ```
   [WIPE] Finding manifests for drive "gfh"
   → Found 15 manifests
   → Deleting manifest files...
   [WIPE] Deleted 15 local manifests
   ```
6. **Refresh UI:**
   ```
   → Clear drive cache
   → Refresh library
   → Library now shows 0 files
   ```

### Commands Comparison

| Command | What It Does | Folder | Files | Trash |
|---------|--------------|--------|-------|-------|
| `rclone purge remote:folder` | Delete folder + contents | ❌ Deleted | ❌ Deleted | ✅ Yes (old) |
| `rclone delete remote:folder` | Delete contents only | ✅ Kept | ❌ Deleted | ✅ Yes (default) |
| `rclone delete remote:folder --drive-use-trash=false` | Delete contents permanently | ✅ Kept | ❌ Deleted | ❌ No (new) |

## What Gets Deleted

### On Google Drive:
```
MultiDriveSplit/
├── file1.part0000.chunk  ← DELETED PERMANENTLY
├── file1.part0001.chunk  ← DELETED PERMANENTLY
├── file2.part0000.chunk  ← DELETED PERMANENTLY
└── ...                    ← ALL FILES DELETED

Folder: MultiDriveSplit/   ← KEPT (empty)
```

### Locally:
```
manifests/
├── file1_manifest.json    ← DELETED
├── file2_manifest.json    ← DELETED
└── ...                    ← ALL MATCHING MANIFESTS DELETED

chunks/ folder             ← NOT touched (cleaned separately)
```

## User Experience

### Before Fixes:

**Issue 1: Folder deleted**
```
1. Click "Wipe Data"
2. Folder MultiDriveSplit deleted
3. Folder in trash bin
4. Have to manually recreate folder
5. Next upload might fail
```

**Issue 2: Library still shows files**
```
1. Wipe Drive
2. Files deleted from Google Drive
3. Open Library
4. Still shows 15 files! 😱
5. Click download → fails (files don't exist)
6. Have to manually delete manifests
```

### After Fixes:

**Fixed!**
```
1. Click "Wipe Data"
2. Confirmation dialog
3. Confirm
4. ✓ Wiped folder and cleared 15 local manifests
5. Folder exists (empty)
6. Library refreshes → Shows 0 files
7. Ready for new uploads
```

## Testing

### Test 1: Wipe and Check Folder
```
1. Upload 3 files
2. Check Drive: MultiDriveSplit folder exists with chunks
3. Click "Wipe Data" → Confirm
4. Check Drive:
   ✅ MultiDriveSplit folder still exists
   ✅ Folder is empty
   ✅ Files NOT in trash
```

### Test 2: Library Sync
```
1. Upload 5 files
2. Library shows 5 files
3. Click "Wipe Data" → Confirm
4. Notification: "Wiped folder and cleared 5 local manifests"
5. Library shows 0 files ✅
```

### Test 3: Upload After Wipe
```
1. Wipe data
2. Immediately upload new file
3. Upload succeeds ✅
4. Folder already exists (wasn't deleted)
```

## Console Output

**Successful Wipe:**
```
[WIPE] Deleting all files from iyuhg:MultiDriveSplit
[RCLONE] Running: rclone delete iyuhg:MultiDriveSplit --drive-use-trash=false -v
[RCLONE] Output: Deleted 15 files
[WIPE] Finding manifests for drive "gfh"
[WIPE] Deleted 15 local manifests
✓ Wiped MultiDriveSplit folder and cleared 15 local manifests
```

**If Folder Empty:**
```
[WIPE] Deleting all files from iyuhg:MultiDriveSplit
[RCLONE] Output: 0 files deleted
[WIPE] Deleted 0 local manifests
✓ Wiped MultiDriveSplit folder and cleared 0 local manifests
```

## Edge Cases Handled

### 1. **Multiple Drives**
- Only wipes selected drive
- Only deletes manifests for that drive
- Other drives unaffected

### 2. **Mixed Manifests**
- Some files on DriveA
- Some files on DriveB
- Wipe DriveA → Only DriveA manifests deleted
- DriveB files still visible in library ✅

### 3. **Folder Doesn't Exist**
- rclone handles gracefully
- No error thrown
- Manifests still cleaned

### 4. **Permission Denied**
- Error message shown
- Manifests NOT deleted (files might still exist)
- User can retry

## Benefits

### ✅ Cleaner Experience
- Folder stays → No need to recreate
- Library syncs → No ghost files
- Ready to use → Upload works immediately

### ✅ Safer
- Bypass trash → True permanent delete
- Consistent behavior → What you see is what you get
- No confusion → Library matches Drive

### ✅ Faster
- Folder exists → No folder creation on next upload
- Manifests cleared → No orphaned data
- Cache refreshed → Stats up to date

## Recovery

**Q: Can I recover wiped files?**
**A:** No. `--drive-use-trash=false` means files are permanently deleted, not in trash.

**Q: What if I wipe by accident?**
**A:** Confirmation dialog with warnings. Read carefully before confirming!

**Q: Can I restore the folder?**
**A:** Folder is NOT deleted! Only contents. Folder remains empty and ready to use.

## Comparison

| Aspect | Before | After |
|--------|--------|-------|
| Folder deleted | ✅ Yes (bad) | ❌ No (good) |
| Goes to trash | ✅ Yes | ❌ No (permanent) |
| Library syncs | ❌ No (manual) | ✅ Yes (auto) |
| Manifests cleaned | ❌ No | ✅ Yes |
| Ready for upload | ❌ No | ✅ Yes |

## Summary

**Before:**
- `rclone purge` → Deleted folder + files → Trash
- Manifests NOT cleaned → Library shows ghosts
- Had to manually fix

**After:**
- `rclone delete --drive-use-trash=false` → Keep folder, delete files permanently
- Auto-clean matching manifests → Library accurate
- Ready to use immediately

**Result:** Cleaner, safer, better UX! 🎉
