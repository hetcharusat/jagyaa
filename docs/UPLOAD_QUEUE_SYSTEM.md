# Upload Queue System & Folder Upload Support

**Date**: October 19, 2025  
**Features Added**: 
1. Visual upload queue UI
2. Recursive folder upload
3. Multiple file selection support
4. Queue management (add/remove files)

## ✨ New Features

### 1. **Upload Queue UI**

Shows all files waiting to be uploaded with:
- ✅ Current file being uploaded (blue background, progress ring)
- ✅ Queued files (grey background, position number)
- ✅ File name and size for each file
- ✅ Remove button for each queued file
- ✅ Real-time updates as uploads complete

**UI Location**: Upload page, below the drop zone

**Empty State**:
```
┌─────────────────────────────────────────────┐
│ No files in queue. Select files or folders │
│ to upload.                                  │
└─────────────────────────────────────────────┘
```

**With Files**:
```
┌─────────────────────────────────────────────┐
│ 🔵 video.mp4                         ⟳     │ ← Uploading
│     Uploading...                            │
├─────────────────────────────────────────────┤
│ 📄 document.pdf     #1 in queue        ❌   │ ← Queued
│     2.5 MB                                  │
├─────────────────────────────────────────────┤
│ 📄 image.jpg        #2 in queue        ❌   │ ← Queued
│     1.2 MB                                  │
└─────────────────────────────────────────────┘
```

### 2. **Folder Upload**

**Before**: Folder button did nothing useful
**After**: Recursively adds ALL files from folder and subfolders

**How it works**:
1. Click "Browse Folder"
2. Select any folder
3. App scans folder recursively using `os.walk()`
4. All files added to queue
5. Shows notification: "📁 Added X files from foldername"

**Example**:
```
Folder structure:
Documents/
├── Report.pdf
├── Images/
│   ├── chart1.png
│   └── chart2.png
└── Data/
    └── spreadsheet.xlsx

Result: Adds 4 files to queue
```

### 3. **Multiple File Selection**

**Before**: Could select multiple but no visual feedback
**After**: Shows all selected files in queue UI

**How to use**:
1. Click "Browse Files"
2. Hold Ctrl/Cmd and click multiple files
3. Click "Open"
4. All files appear in queue
5. Uploads process sequentially

### 4. **Queue Management**

**Remove from Queue**:
- Click ❌ button next to any queued file
- File removed from queue
- Notification: "Removed filename from queue"

**Cancel Current + Queue**:
- Click ❌ on progress banner
- Cancels current upload
- Clears entire queue
- Notification shows count: "Cancelled upload + 5 files in queue"

## Code Implementation

### Folder Scanning
```python
def folder_picked(self, e: ft.FilePickerResultEvent):
    if e.path:
        folder_path = Path(e.path)
        all_files = []
        
        # Recursive scan
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        # Add to queue
        for file_path in all_files:
            self.upload_queue.append(file_path)
        
        self.update_queue_ui()
        self.process_upload_queue()
```

### Queue UI Update
```python
def update_queue_ui(self):
    self.upload_queue_ui.controls.clear()
    
    # Show current upload
    if self.upload_running:
        # Blue card with progress ring
    
    # Show queued files
    for idx, file_path in enumerate(self.upload_queue):
        # Grey card with position number and remove button
```

### Sequential Processing
```python
def upload_complete(self, result, filename):
    self.upload_running = False
    self.update_queue_ui()
    
    if len(self.upload_queue) > 0:
        # Process next file
        self.process_upload_queue()
    else:
        # All done!
        self.show_snackbar("✓ All uploads completed!")
```

## Benefits

### ✅ Better UX
1. **Visual feedback** - See all files in queue
2. **Progress tracking** - Know what's uploading and what's next
3. **Control** - Remove files you didn't mean to add
4. **Transparency** - No mystery about what's happening

### ✅ Folder Support
1. **Bulk uploads** - Upload entire project folders
2. **Recursive** - Includes all subfolders
3. **Fast selection** - Don't manually select 100 files
4. **Preserves structure** - Files uploaded in order

### ✅ Queue Management
1. **Edit before upload** - Remove unwanted files
2. **See file sizes** - Know how long upload will take
3. **Position tracking** - Know order of uploads
4. **Cancel anytime** - Stop uploads if needed

## User Workflow

### Scenario 1: Multiple Files
```
1. Click "Browse Files"
2. Select files: video1.mp4, video2.mp4, video3.mp4
3. Queue shows 3 files
4. First file starts uploading immediately
5. When done, second file starts
6. When done, third file starts
7. Notification: "✓ All uploads completed!"
```

### Scenario 2: Folder Upload
```
1. Click "Browse Folder"
2. Select folder: "My Project"
3. Notification: "📁 Added 25 files from My Project"
4. Queue shows all 25 files
5. Uploads process one by one
6. Can remove files while waiting
```

### Scenario 3: Mixed Sources
```
1. Click "Browse Files" → Add 3 files
2. Click "Browse Folder" → Add 10 files
3. Drag & drop → Add 2 files
4. Queue shows all 15 files
5. Remove 2 unwanted files
6. Queue now has 13 files
7. Uploads process sequentially
```

## Testing

1. **Test multiple files**:
   - Select 5 small files
   - Check queue shows all 5
   - Watch them upload one by one

2. **Test folder upload**:
   - Create folder with 10 files in subfolders
   - Click "Browse Folder"
   - Check all 10 files appear in queue

3. **Test queue management**:
   - Add 5 files
   - Remove 2 from queue
   - Check only 3 upload

4. **Test cancel**:
   - Add 5 files
   - Cancel during first upload
   - Check queue clears

## Limitations (Current)

### ❌ Not Parallel Yet
- Uploads process **sequentially** (one at a time)
- Parallel uploads would require:
  - Separate uploader instances
  - Concurrent chunk management
  - Shared bandwidth management
  - More complex UI (multiple progress bars)

**Why Sequential for Now**:
1. Simpler to implement
2. Avoids rate limits (Google Drive throttles concurrent uploads)
3. Easier to track progress
4. Less memory usage

### Future: Parallel Uploads
To add parallel uploads later:
```python
# Config setting
max_concurrent_uploads = 3

# Thread pool
upload_threads = []
for i in range(max_concurrent_uploads):
    if self.upload_queue:
        file = self.upload_queue.pop(0)
        thread = threading.Thread(target=self.start_upload, args=(file,))
        upload_threads.append(thread)
        thread.start()
```

## Notes

- Queue persists only during app session (not saved to disk)
- Files are validated when added (checks if they exist)
- Large folders may take a moment to scan
- Queue UI updates automatically on every change
- Cancel clears entire queue (by design)
- Sequential uploads avoid Google Drive rate limits

## Error Handling

**Missing File**:
- If file deleted after adding to queue
- Error shown, skips to next file

**Rate Limit**:
- Stops queue processing
- Shows warning to wait 2-5 minutes
- Queue persists (can retry later)

**Access Denied**:
- File in use or locked
- Error shown, skips to next file
- Other files continue

## Summary

| Feature | Status |
|---------|--------|
| Visual queue UI | ✅ Done |
| Folder upload (recursive) | ✅ Done |
| Multiple file selection | ✅ Done |
| Remove from queue | ✅ Done |
| Sequential processing | ✅ Done |
| Auto-continue on complete | ✅ Done |
| Cancel clears queue | ✅ Done |
| Parallel uploads | ❌ Future enhancement |
| Pause/resume queue | ❌ Future enhancement |
| Drag & drop to queue | ❌ Future enhancement |

**Next Steps**: Test with various file counts and folder structures to ensure stability!
