# Download Queue System

## Overview
Queue multiple file downloads and process them sequentially with visual feedback. Similar to the upload queue system, but for downloading files from Google Drive.

## Visual Appearance

### Download Queue Card
A card appears at the top of the Library tab (below the download progress banner) when files are queued:

```
┌─────────────────────────────────────────────────────┐
│ 📋  Download Queue                                   │
├─────────────────────────────────────────────────────┤
│ ▶ ⬇️ Wheeler, Rawson... [Downloading...]        ⭕ │
│   310.16 MB                                          │
├─────────────────────────────────────────────────────┤
│ #1  Bobby Fischer Teaches Chess               [X]   │
│     145.8 MB                                         │
├─────────────────────────────────────────────────────┤
│ #2  Camera Manual_3                            [X]   │
│     89.3 MB                                          │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Current download shown with spinning progress indicator
- Queued downloads numbered (#1, #2, #3...)
- File size displayed
- Remove button [X] for each queued file

## How It Works

### Adding Files to Queue

**Method 1: Click Download Button**
1. Go to Library tab
2. Click download button (green ⬇️) on any file
3. File added to queue
4. Notification: "✅ [filename] added to download queue"

**Method 2: Multiple Files**
- Click download on multiple files
- All added to queue in order clicked
- Queue processes one at a time

### Sequential Processing

The queue system ensures downloads happen one at a time:

1. **First file starts downloading immediately**
   - Progress banner appears
   - Shows in queue as "Downloading..."
   - Real-time stats displayed

2. **Other files wait in queue**
   - Shown with position number (#1, #2, etc.)
   - Can be removed anytime
   - Processed in order added

3. **Auto-advance to next**
   - When download completes, next file starts automatically
   - Notification: "Processing next download... (X remaining)"
   - Progress banner updates for new file

4. **Queue completion**
   - When all done: "✓ All downloads completed!"
   - Queue card disappears
   - Library refreshes

### Queue Management

**View Queue Status:**
- See all pending downloads
- Current download highlighted in green
- Position in queue (#1, #2, #3...)

**Remove from Queue:**
- Click [X] button next to any file
- File removed immediately
- Queue positions updated
- Notification: "Removed [filename] from download queue"

**Cancel Current Download:**
- Click [X] in progress banner
- Current download stops
- Partial file deleted
- Next file in queue starts automatically

## User Flow Examples

### Example 1: Download Multiple Files

```
User clicks download on 3 files:
1. Wheeler, Rawson... (310 MB)
2. Bobby Fischer... (145 MB)
3. Camera Manual (89 MB)

Queue Status:
┌─────────────────────────────────────────┐
│ ▶ Wheeler, Rawson... [Downloading...] │
│ #1 Bobby Fischer...                [X] │
│ #2 Camera Manual                   [X] │
└─────────────────────────────────────────┘

After Wheeler completes:
┌─────────────────────────────────────────┐
│ ▶ Bobby Fischer... [Downloading...]   │
│ #1 Camera Manual                   [X] │
└─────────────────────────────────────────┘

After Bobby Fischer completes:
┌─────────────────────────────────────────┐
│ ▶ Camera Manual [Downloading...]      │
└─────────────────────────────────────────┘

After Camera Manual completes:
✓ All downloads completed!
Queue card disappears
```

### Example 2: Remove from Queue

```
Queue:
│ ▶ File A [Downloading...]             │
│ #1 File B                         [X] │
│ #2 File C                         [X] │
│ #3 File D                         [X] │

User clicks [X] on File C:

Queue:
│ ▶ File A [Downloading...]             │
│ #1 File B                         [X] │
│ #2 File D                         [X] │

Notification: "Removed File C from download queue"
```

### Example 3: Cancel Current, Queue Continues

```
Queue:
│ ▶ File A [Downloading...]             │
│ #1 File B                         [X] │

User clicks [X] on progress banner:

Result:
- File A download cancelled
- Partial File A deleted
- File B starts downloading immediately

Queue:
│ ▶ File B [Downloading...]             │
```

## Technical Implementation

### State Management

```python
# Queue system variables
self.download_queue = []  # List of download items
self.current_download_item = None  # Currently downloading
self.download_running = False  # Download in progress flag
self.download_cancelled = False  # Cancel flag
self.download_queue_ui = None  # Queue UI container
```

### Adding to Queue

```python
def download_file(self, item):
    """Add file to download queue"""
    filename = self._get_download_filename(item)
    
    # Validate before adding
    # (check for failed status, etc.)
    
    # Check if already in queue
    if item in self.download_queue:
        self.show_snackbar(f"⚠️ {filename} already in queue")
        return
    
    # Add to queue
    self.download_queue.append(item)
    self.show_snackbar(f"✅ {filename} added to download queue")
    
    # Update UI
    self.update_download_queue_ui()
    self.show_library()  # Refresh to show queue card
    
    # Start if not running
    if not self.download_running:
        self.process_download_queue()
```

### Processing Queue

```python
def process_download_queue(self):
    """Process next file in download queue"""
    if not self.download_queue or self.download_running:
        return
    
    # Get next download
    next_item = self.download_queue.pop(0)
    self.current_download_item = next_item
    
    # Update UI
    self.update_download_queue_ui()
    
    # Start download
    self._start_download_internal(next_item)
```

### Queue UI Update

```python
def update_download_queue_ui(self):
    """Update the download queue display"""
    self.download_queue_ui.controls.clear()
    
    # Show current download
    if self.download_running and self.current_download_item:
        filename = self._get_download_filename(self.current_download_item)
        self.download_queue_ui.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.GREEN_600),
                    ft.Text(filename),
                    ft.ProgressRing(),  # Spinning indicator
                ]),
                bgcolor=ft.Colors.GREEN_50,
            )
        )
    
    # Show queued downloads
    for idx, item in enumerate(self.download_queue):
        filename = self._get_download_filename(item)
        file_size = self._get_download_filesize(item)
        
        self.download_queue_ui.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(f"#{idx + 1}"),
                    ft.Text(filename),
                    ft.Text(file_size),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        on_click=lambda e, i=item: self.remove_from_download_queue(i)
                    ),
                ])
            )
        )
```

### Completion Handler

```python
def download_complete_cleanup(self, success, message):
    """Clean up and process next download"""
    self.download_running = False
    self.current_download_item = None
    self.download_progress_banner.visible = False
    
    # Show result
    self.show_snackbar(message, ft.Colors.GREEN if success else ft.Colors.RED)
    
    # Update queue UI
    self.update_download_queue_ui()
    
    # Process next download
    if len(self.download_queue) > 0:
        self.show_snackbar(f"Processing next download... ({len(self.download_queue)} remaining)")
        self.process_download_queue()
    else:
        self.show_snackbar("✓ All downloads completed!")
        self.show_library()  # Refresh library
```

## Benefits

1. **Multiple Downloads:** Queue many files, download sequentially
2. **No Conflicts:** One download at a time prevents race conditions
3. **Visual Feedback:** See queue status, position, and progress
4. **Control:** Remove items or cancel current download anytime
5. **Automatic:** Queue processes automatically, no manual intervention
6. **Progress Tracking:** Real-time stats for current download
7. **Error Recovery:** Failed download moves to next automatically

## Queue vs. Direct Download

### Without Queue (Old Behavior):
- Click download → starts immediately
- Click another → error or overlap issues
- No visibility into pending downloads
- Hard to manage multiple downloads

### With Queue (New Behavior):
- Click download → adds to queue
- Click multiple → all queued in order
- See all pending downloads
- Remove or reorder easily
- Auto-advance through queue

## Integration with Upload Queue

Both upload and download now have similar queue systems:

| Feature | Upload Queue | Download Queue |
|---------|--------------|----------------|
| **Location** | Upload tab | Library tab |
| **Color Theme** | Blue | Green |
| **Sequential** | Yes | Yes |
| **Remove Items** | Yes | Yes |
| **Cancel Current** | Yes | Yes |
| **Progress Banner** | Yes | Yes |
| **Auto-advance** | Yes | Yes |

## Future Enhancements

Potential improvements:

1. **Parallel Downloads:** Download 2-3 files simultaneously (with speed limits)
2. **Priority Queue:** Drag to reorder, or set high priority
3. **Pause/Resume:** Pause queue, resume later
4. **Smart Scheduling:** Download large files during off-peak hours
5. **Bandwidth Management:** Set max concurrent downloads, speed limits
6. **Download Groups:** Group related files, download as batch
7. **Retry Failed:** Auto-retry failed downloads like upload retry system
8. **Queue Persistence:** Save queue to disk, restore after app restart
9. **Download History:** Track completed downloads with stats
10. **Notifications:** System notifications when queue completes

## Related Documentation
- `DOWNLOAD_PROGRESS_SYSTEM.md` - Real-time download progress tracking
- `UPLOAD_QUEUE_SYSTEM.md` - Upload queue system (similar design)
- `UPLOAD_RETRY_SYSTEM.md` - Automatic retry for failed uploads
- `REUPLOAD_BUTTON.md` - Manual re-upload functionality
