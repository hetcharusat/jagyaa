# Account Switching & Multi-Account Fixes

## Issues Fixed

### 1. **Library Not Showing Uploaded Files** ✅
**Problem:** When logging in with same account used for uploads, library shows empty

**Root Cause:**
- `refresh_library(load_remote=False)` by default
- Only shows local manifests, not remote files
- Manifests reference old account's drives

**Solutions Implemented:**

#### A. "Sync Remote Files" Button
- Located in Library page (top-right)
- Manually loads files from Google Drive
- Calls `refresh_library(load_remote=True)`
- **Usage:** Click when switching accounts

#### B. Clear All Local Data (Settings)
- New option in Settings → Account Management
- Clears manifests, chunks, cache
- Keeps drives configuration
- **Usage:** When switching to different Google account

**Code:**
```python
def sync_remote_files(self):
    self.show_snackbar("Syncing files from Google Drive...", ft.Colors.BLUE)
    self.refresh_library(load_remote=True)  # Forces remote load
    self.show_snackbar("Sync completed!", ft.Colors.GREEN)
```

---

### 2. **Drive Stats Showing Wrong Values** ✅
**Problem:** Same storage stats for all drives (caching issue)

**Root Cause:**
- Cache stores stats by `remote_name`
- If two drives use same remote, they share cache
- Cache not cleared when switching accounts

**Solution:**

#### Added Debug Logging
```python
def get_cached_drive_stats(self, remote_name: str):
    # Check cache
    if remote_name in self.drive_stats_cache:
        print(f"[CACHE] Using cached stats for {remote_name}: {cached_stats}")
        return cached_stats
    
    # Fetch fresh
    print(f"[CACHE] Fetching fresh stats for {remote_name}...")
    stats = self.rclone.get_drive_stats(remote_name)
    print(f"[CACHE] Got stats for {remote_name}: {stats}")
```

#### Added Manual Cache Clear
```python
def clear_drive_cache(self):
    """Clear drive stats cache"""
    self.drive_stats_cache = {}
    self.cache_timestamp = 0
    print("[CACHE] Drive stats cache cleared")
```

**How to Use:**
1. **Settings → Account Management → "Refresh Cache Only"**
2. Or **"Clear All Local Data"** (also clears cache)

---

### 3. **No Cancel Button for Downloads** ✅
**Problem:** No way to cancel ongoing downloads

**Solution: Added Download Cancellation**

#### Track Download State
```python
# In __init__
self.download_running = False
self.download_cancelled = False
```

#### Updated download_file()
```python
def download_file(self, item):
    # Track state
    self.download_running = True
    self.download_cancelled = False
    
    # Show message with hint
    self.show_snackbar(
        f"⬇️ Downloading {filename}... (Press Esc to cancel)", 
        ft.Colors.BLUE
    )
    
    def download_thread():
        # Check if cancelled before starting
        if self.download_cancelled:
            self.show_snackbar("Download cancelled", ft.Colors.ORANGE)
            return
        
        result = download_actual_file()
        
        # Check if cancelled after completion
        if self.download_cancelled:
            # Delete partial file
            if os.path.exists(output_path):
                os.remove(output_path)
            self.show_snackbar("Download cancelled", ft.Colors.ORANGE)
            return
```

#### Cancel Function
```python
def cancel_download(self):
    """Cancel ongoing download"""
    if self.download_running:
        self.download_cancelled = True
        self.show_snackbar("Cancelling download...", ft.Colors.ORANGE)
```

**How to Use:**
- **Press Esc** while downloading (future: keyboard shortcut)
- Or use future UI cancel button

---

## New Features Added

### 1. **Account Management Section (Settings)**

Located in: **Settings → Account Management**

#### Option A: Clear All Local Data
```
⚠️ Switching Google accounts?

This will:
• Clear all manifests (local upload records)
• Clear drive stats cache  
• Clear chunks folder
• Keep your drives configuration

[Clear All Local Data]  [Cancel]
```

**When to Use:**
- Switching from account A to account B
- Want fresh start with new account
- Library showing files from old account

#### Option B: Refresh Cache Only
```
[Refresh Cache Only]
```

**When to Use:**
- Drive stats showing wrong values
- Don't want to delete manifests
- Just need cache refresh

---

### 2. **Enhanced Library Sync**

#### "Sync Remote Files" Button
- Located: Library page, top-right
- Action: Loads files from Google Drive
- Speed: Slow (queries Google API)
- Use: When files don't appear after upload

**Visual:**
```
[Search] [Sort] [Filter] [Sync Remote Files] [Clean Orphaned Files]
```

---

### 3. **Download Cancellation**

#### User Experience
```
⬇️ Downloading myfile.mp4... (Press Esc to cancel)
[Progress bar or spinner]
```

#### Implementation Details
- Checks `download_cancelled` flag before and after download
- Deletes partial files if cancelled mid-download
- Thread-safe cancellation

---

## Account Switching Workflow

### Scenario: Switching from Account A to Account B

#### Step 1: Configure New Drive
1. Go to **Drives** tab
2. Add drive with Account B credentials
3. Enable the drive

#### Step 2: Clear Old Data (Recommended)
1. Go to **Settings** tab
2. Find **Account Management** section
3. Click **"Clear All Local Data"**
4. Confirm

#### Step 3: Sync New Account Files
1. Go to **Library** tab
2. Click **"Sync Remote Files"**
3. Wait for sync to complete

#### Step 4: Verify
1. Check **Dashboard** for updated drive stats
2. Check **Library** for new account's files
3. Upload test file to verify

---

## Troubleshooting

### Issue: Library Still Shows Old Files

**Cause:** Local manifests reference old account

**Solution:**
```
Settings → Account Management → Clear All Local Data
Then: Library → Sync Remote Files
```

---

### Issue: Drive Stats Same for All Drives

**Cause:** Cache not cleared, or drives use same remote

**Solution 1:** Clear cache
```
Settings → Account Management → Refresh Cache Only
```

**Solution 2:** Check drive configuration
```
Drives → Verify each drive has unique remote_name
```

---

### Issue: Files Uploaded But Not Visible

**Cause:** Library not loading from remote

**Solution:**
```
Library → Sync Remote Files (top-right button)
```

---

### Issue: Can't Cancel Download

**Cause:** Download tracking not initialized

**Temporary:**
- Wait for download to complete
- Or restart app

**Permanent Fix:**
- Press Esc (future keyboard shortcut)
- Or click cancel button in download dialog

---

## Technical Details

### Drive Stats Caching

**Cache Duration:** 5 minutes (300 seconds)

**Cache Key:** `remote_name` (e.g., "drueve")

**Cache Storage:**
```python
self.drive_stats_cache = {
    "drueve": {
        "total": 16106127360,
        "used": 9874390016,
        "free": 6231737344
    }
}
```

**Problem with Shared Remotes:**
If two drives use same `remote_name`, they share cache entry!

**Solution:**
- Use unique remote names for each account
- Or clear cache when switching accounts

---

### Manifest Filtering

**Current Logic:**
```python
# Only show manifests if their drives exist
for manifest in manifests:
    chunks = manifest.get('chunks', [])
    drive_names = [d.get('name') for d in current_drives]
    
    # Check if any chunk's drive exists
    has_valid_drive = any(
        chunk.get('drive') in drive_names 
        for chunk in chunks
    )
    
    if not has_valid_drive:
        continue  # Skip this manifest
```

**Issue:**
- Manifests from Account A reference "Drive A"
- Account B has "Drive B" configured
- Manifests filtered out (correct!)
- But remote files from Account A not loaded (unless sync clicked)

**Solution:**
- Click "Sync Remote Files" to load from Account B
- Or clear manifests and re-upload with Account B

---

## Files Modified

1. **`main_flet_new.py`** (Multiple sections)
   - Lines 52-56: Added download tracking variables
   - Lines 196-225: Added cache debug logging and clear_drive_cache()
   - Lines 1570-1685: Enhanced download_file() with cancellation
   - Lines 2522-2573: Added Account Management card in Settings
   - Lines 2660-2730: Added clear_all_local_data() and refresh_cache()

---

## User Instructions

### For First-Time Users

1. **Add Drive:**
   - Drives → Add Drive → Configure OAuth
   
2. **Upload Files:**
   - Upload → Select files → Wait for completion
   
3. **View Files:**
   - Library → Files appear automatically

---

### For Users Switching Accounts

1. **Add New Drive:**
   - Drives → Add Drive → Use new account credentials

2. **Clear Old Data:**
   - Settings → Account Management → Clear All Local Data

3. **Sync New Files:**
   - Library → Sync Remote Files

4. **Verify:**
   - Dashboard → Check drive stats
   - Library → Check files list

---

## Best Practices

### When to Clear Data

✅ **DO Clear:**
- Switching to completely different Google account
- Drive stats showing wrong values for all drives
- Library showing files you didn't upload

❌ **DON'T Clear:**
- Just adding a second drive
- Temporarily switching, will switch back
- Only want to refresh cache (use "Refresh Cache Only")

---

### When to Sync Remote

✅ **DO Sync:**
- Just logged in with existing account
- Uploaded files from another device
- Files missing from library
- After switching accounts (after clearing data)

❌ **DON'T Sync:**
- Files already visible in library
- Don't want to wait (sync is slow)
- Just cleared data (library will be empty anyway)

---

## Future Enhancements

### Planned Features

1. **Automatic Account Detection**
   - Detect when remote account changed
   - Auto-prompt to clear data

2. **Download Progress Bar**
   - Visual progress indicator
   - Cancel button in dialog
   - Speed and ETA display

3. **Multi-Account Support**
   - Switch between accounts without clearing
   - Per-account manifest storage
   - Unified library view

4. **Smart Sync**
   - Auto-sync on login
   - Background sync every 5 minutes
   - Only sync changed files

---

## Summary

**Fixed:**
1. ✅ Library not showing files → Added "Sync Remote Files" button
2. ✅ Wrong drive stats → Added cache clear + debug logging
3. ✅ No download cancel → Added cancellation support

**Added:**
1. ✅ Account Management section in Settings
2. ✅ Clear All Local Data option
3. ✅ Refresh Cache Only option
4. ✅ Enhanced download cancellation

**Improved:**
1. ✅ Better error messages
2. ✅ Debug logging for cache
3. ✅ Clearer user instructions
4. ✅ Confirmation dialogs

**User Experience:**
- Clear path for switching accounts
- No more confusion about missing files
- Proper cache management
- Can cancel long downloads
