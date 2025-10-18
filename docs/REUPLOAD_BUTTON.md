# Re-upload Button Feature

## Overview
Added a "Re-upload" button to **failed files** in library file cards, allowing users to manually re-upload files that failed during upload.

## How It Works

### Visual Appearance
- The re-upload button appears as a purple upload icon (↑) on library file cards
- **Only visible for FAILED manifest files** (files that failed to upload)
- Successfully uploaded files and remote cloud files don't show this button

### Button Location
The re-upload button is integrated into the second row of action buttons:
- Row 1: Preview, Download
- Row 2: Details, Delete, **Re-upload** (purple icon - only appears on failed files)

The button appears in the same row as Details and Delete to prevent layout overflow issues.

### Functionality

When you click the **Re-upload** button:

1. **Validation Checks:**
   - Verifies the manifest exists and is valid
   - Checks if the original file path is stored in the manifest
   - Confirms the original file still exists on your computer
   - Prevents duplicate uploads (file already in queue or currently uploading)

2. **Queue Management:**
   - Adds the file to the upload queue
   - Shows a success notification: "✅ [filename] added to upload queue"
   - Updates the upload queue UI to show the new file

3. **Navigation:**
   - Automatically switches to the Upload tab
   - Shows the upload progress and queue

4. **Processing:**
   - If no upload is currently running, starts processing the queue immediately
   - If an upload is in progress, the file waits in queue

### Error Handling

The re-upload button handles several error cases:

**Original File Not Found:**
```
❌ Cannot re-upload: Original file not found at [path]
```
- Happens when the original file was moved or deleted after upload

**Missing File Path:**
```
❌ Cannot re-upload [filename]: Original file path not found in manifest
```
- Happens with old manifests that don't store the original path

**File Already in Queue:**
```
⚠️ [filename] is already in the upload queue
```
- Prevents duplicate queue entries

**File Currently Uploading:**
```
⚠️ [filename] is currently being uploaded
```
- Prevents re-adding a file that's already being processed

**Invalid Manifest:**
```
❌ Cannot re-upload: Invalid manifest
```
- Happens if the manifest data is corrupted

## Use Cases

### 1. Failed Uploads
If a file failed to upload due to rate limits or network issues:
1. Go to the Library tab
2. Find the failed file (marked with red "Failed" chip)
3. Click the purple re-upload button
4. File is added back to the queue and retried

### 2. Updating Files
If you modified a file and want to upload the new version:
1. Replace the original file with the updated version (keeping the same filename and location)
2. Go to Library and find the file
3. Click re-upload to upload the new version

### 3. Manual Retry After Rate Limit
If automatic retry isn't working or you want to retry immediately:
1. Find the file in Library
2. Click re-upload
3. File is queued for immediate upload

## Integration with Retry System

The re-upload button works alongside the automatic retry system:

- **Automatic Retry:** Handles rate limits and transient errors automatically with exponential backoff
- **Manual Re-upload:** Gives you control to retry specific files at any time

Both systems use the same upload queue, so they work seamlessly together.

## Technical Implementation

### File Card Button (main_flet_new.py, line ~1500)
```python
# Second row - Info, Delete, and Re-upload (only for failed files)
ft.Row([
    ft.IconButton(
        icon=ft.Icons.INFO_OUTLINE,
        icon_size=18,
        tooltip="Details",
        icon_color=ft.Colors.ORANGE_600,
        on_click=lambda e, i=item: self.show_file_details(i),
    ),
    ft.IconButton(
        icon=ft.Icons.DELETE_OUTLINE,
        icon_size=18,
        tooltip="Delete",
        icon_color=ft.Colors.RED_600,
        on_click=lambda e, i=item: self.delete_library_file(i),
    ),
    # Re-upload button - ONLY for failed manifest files
    ft.IconButton(
        icon=ft.Icons.UPLOAD,
        icon_size=18,
        tooltip="Re-upload",
        icon_color=ft.Colors.PURPLE_600,
        on_click=lambda e, i=item: self.reupload_file(i),
        visible=(source == 'manifest' and status == 'failed'),  # Only show for FAILED files
    ),
], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
```

### Re-upload Handler (main_flet_new.py, line ~2255)
```python
def reupload_file(self, item):
    """Re-upload a file from the library (for failed uploads or re-uploading existing files)"""
    # Get the manifest data
    manifest = item.get('manifest') if isinstance(item, dict) and item.get('source') == 'manifest' else item
    
    if not manifest:
        self.show_snackbar("❌ Cannot re-upload: Invalid manifest", ft.Colors.RED)
        return
    
    # Get original file path from manifest structure: manifest -> original_file -> path
    original_file_info = manifest.get('original_file', {})
    original_path = original_file_info.get('path', '')
    file_name = original_file_info.get('filename', item.get('file_name', 'Unknown'))
    
    # ... validation checks ...
    
    # Store the old manifest ID so we can delete it after successful re-upload
    old_manifest_id = manifest.get('manifest_id', '')
    if old_manifest_id:
        self.reupload_old_manifest_id = old_manifest_id
        print(f"[REUPLOAD] Will delete old manifest {old_manifest_id} after successful upload")
    
    # Add to upload queue
    self.upload_queue.append(original_path)
    self.show_snackbar(f"✅ {file_name} added to upload queue", ft.Colors.GREEN)
    
    # ... rest of logic ...
```

### Cleanup on Success (main_flet_new.py, line ~875)
```python
def upload_complete(self, result, filename):
    """Handle upload completion - ENHANCED with re-upload cleanup"""
    self.upload_running = False
    self.current_upload_path = None
    
    # Track if this was a re-upload (before clearing the variable)
    was_reupload = bool(self.reupload_old_manifest_id)
    
    # If this was a re-upload, delete the old failed manifest
    if self.reupload_old_manifest_id:
        try:
            old_manifest_path = Path(self.manifest_manager.manifest_folder) / f"{self.reupload_old_manifest_id}.json"
            if old_manifest_path.exists():
                old_manifest_path.unlink()
                print(f"[REUPLOAD] Deleted old manifest: {self.reupload_old_manifest_id}")
                self.show_snackbar(f"🗑️ Cleaned up old failed upload", ft.Colors.BLUE)
            else:
                print(f"[REUPLOAD] Old manifest not found: {self.reupload_old_manifest_id}")
        except Exception as e:
            print(f"[REUPLOAD] Error deleting old manifest: {e}")
        finally:
            # Clear the tracking variable
            self.reupload_old_manifest_id = None
    
    # ... success notification ...
    
    # If this was a re-upload, force refresh the library cache
    if was_reupload:
        print("[REUPLOAD] Clearing library cache to reflect changes")
        self.library_items = []  # Clear cache so it reloads fresh
    
    # Auto-refresh current view to show updated data
    current_tab = self.nav_rail.selected_index
    if current_tab == 0:
        self.show_dashboard()
    elif current_tab == 2:
        self.show_library()
    elif current_tab == 1 and hasattr(self, 'library_grid'):
        # Silently refresh library data without changing view
        self.refresh_library(load_remote=False)
```

## Benefits

1. **User Control:** Gives users manual control over retry attempts
2. **Immediate Retry:** No need to wait for automatic retry delays
3. **Selective Retry:** Re-upload specific files instead of all failed uploads
4. **File Updates:** Easy way to upload new versions of files
5. **Recovery:** Manually recover from edge cases not handled by automatic retry
6. **Smart Cleanup:** Automatically removes old failed manifests after successful re-upload
7. **Cache Management:** Refreshes library cache to immediately show updated status

## Cleanup and Cache Management

### Automatic Cleanup After Re-upload

When you successfully re-upload a failed file:

1. **Old Manifest Deletion:**
   - The system automatically deletes the old failed manifest
   - Prevents duplicate entries in the library (one failed, one successful)
   - Frees up disk space from obsolete manifest files

2. **Library Cache Refresh:**
   - Clears the library items cache
   - Forces fresh reload of manifests on next library view
   - Ensures you see the latest upload status immediately

3. **Visual Feedback:**
   - Shows "🗑️ Cleaned up old failed upload" notification
   - Confirms the old manifest was successfully removed
   - "✓ Uploaded: [filename]" confirms successful upload

### How It Works

**Before Re-upload:**
```
Library shows:
- Wheeler, Rawson... (Failed) ❌
```

**During Re-upload:**
```
System tracks:
- old_manifest_id = "Wheeler_Rawson_20251019_015922"
- Uploads file with new manifest_id = "Wheeler_Rawson_20251019_023045"
```

**After Successful Re-upload:**
```
System automatically:
1. Deletes manifests/Wheeler_Rawson_20251019_015922.json
2. Clears library_items cache
3. Refreshes library view

Library now shows:
- Wheeler, Rawson... (4x) ✅  [Only the successful upload]
```

### Cache Refresh Behavior

The library refresh happens intelligently based on which tab you're viewing:

- **On Library Tab:** Automatically reloads and displays updated files
- **On Upload Tab:** Silently refreshes data in background (ready for when you switch back)
- **On Dashboard:** Refreshes dashboard stats to reflect new upload
- **On Other Tabs:** Cache cleared, will reload fresh when you visit library

This ensures:
- No stale data showing old failed uploads
- Immediate visual feedback of successful re-upload
- Efficient loading (only refreshes what's needed)

## Future Enhancements

Potential improvements:
1. **Batch Re-upload:** Select multiple files and re-upload all at once
2. **Re-upload All Failed:** One-click button to re-upload all failed files
3. **Progress Tracking:** Show which files are being re-uploaded vs. new uploads
4. **Version History:** Track multiple versions of the same file with timestamps
5. **Smart Re-upload:** Only re-upload files that have been modified since last upload

## Related Documentation
- `UPLOAD_RETRY_SYSTEM.md` - Automatic retry system with exponential backoff
- `UPLOAD_QUEUE_SYSTEM.md` - Upload queue architecture
- `RATE_LIMIT_GUIDE.md` - Understanding Google Drive rate limits
