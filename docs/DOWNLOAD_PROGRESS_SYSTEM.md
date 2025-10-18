# Download Progress System

## Overview
Real-time visual progress tracking for file downloads with detailed statistics, similar to the upload progress system. Shows chunk-by-chunk download status, speed, ETA, and current stage.

## Visual Appearance

### Download Progress Banner
A green-themed banner that appears at the top of the Library tab when downloading:

```
┌────────────────────────────────────────────────────────────┐
│ 📥  ⬇️ Downloading chunks...                          [X]  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━ 65% ━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Speed: 142.5 MB/s    ETA: 12s    Chunk 13/20 (65.0%)      │
└────────────────────────────────────────────────────────────┘
```

**Colors:**
- Background: Green tint (GREEN_50)
- Border: Green (GREEN_200)
- Progress bar: Green (GREEN_600)
- Icon: Download arrow (GREEN_600)

## Features

### 1. **Real-time Progress Tracking**
- Shows current chunk being downloaded
- Updates progress bar as chunks complete
- Displays percentage complete

### 2. **Download Statistics**
- **Speed:** MB/s download speed (calculated from chunks/second × 95MB)
- **ETA:** Estimated time remaining
- **Chunk Progress:** "Chunk 13/20 (65.0%)"

### 3. **Download Stages**

#### Stage 1: Downloading Chunks
```
⬇️ Downloading chunks...
━━━━━━━━━━━━━━━━ 50% ━━━━━━━━━━━━━━━━
Speed: 190.0 MB/s    ETA: 8s    Chunk 10/20 (50.0%)
```

#### Stage 2: Merging Chunks
```
🔗 Merging chunks...
━━━━━━━━━━━━━━━━ 75% ━━━━━━━━━━━━━━━━
Progress: Merging...    Chunk 15/20    75% merged
```

#### Stage 3: Verifying File
```
✅ Verifying file...
━━━━━━━━━━━━━━━━ 90% ━━━━━━━━━━━━━━━━
Almost done...    Verifying...    Checking integrity...
```

#### Stage 4: Completed
```
✓ Download complete!
━━━━━━━━━━━━━━━━ 100% ━━━━━━━━━━━━━━━━
Done!                All 20 chunks processed
```

### 4. **Cancel Download**
- Red [X] button in top-right corner
- Click to cancel ongoing download
- Shows "Cancelling download..." notification
- Deletes partial file automatically
- Keyboard shortcut: Press ESC during download

## How It Works

### User Flow

1. **Start Download:**
   - Click download button on any file in Library
   - Green progress banner appears at top
   - Shows "📦 Preparing: [filename]"

2. **Downloading Phase:**
   - Banner updates in real-time as chunks download
   - Shows speed, ETA, and chunk progress
   - Progress bar fills from 0% to 100%

3. **Merging Phase:**
   - Status changes to "🔗 Merging chunks..."
   - Shows merge progress
   - Speed info replaced with "Progress: Merging..."

4. **Verification Phase:**
   - Status changes to "✅ Verifying file..."
   - Checks SHA-256 hash of final file
   - Shows "Checking integrity..."

5. **Completion:**
   - Banner disappears
   - Shows success notification with file path
   - File saved to downloads folder

### Technical Flow

```python
# 1. Initialize download
self.download_running = True
self.download_start_time = time.time()
self.download_progress_banner.visible = True

# 2. Start download with callbacks
result = self.downloader.download_file(
    manifest_id,
    output_path,
    progress_callback=self.download_progress_callback,
    chunk_callback=self.download_chunk_callback
)

# 3. Progress callback updates UI
def download_progress_callback(self, stage, current, total):
    # Calculate speed: chunks per second × 95MB
    elapsed = time.time() - self.download_start_time
    speed = current / elapsed if elapsed > 0 else 0
    mb_speed = speed * 95
    
    # Update UI elements
    self.download_status_text.value = f"⬇️ Downloading chunks..."
    self.download_progress_bar.value = current / total
    self.download_speed_text.value = f"Speed: {mb_speed:.1f} MB/s"
    self.download_eta_text.value = f"ETA: {eta}s"
    self.download_chunk_text.value = f"Chunk {current}/{total}"
    self.page.update()

# 4. Cleanup on completion
def download_complete_cleanup(self, success, message):
    self.download_running = False
    self.download_progress_banner.visible = False
    self.show_snackbar(message, ft.Colors.GREEN if success else ft.Colors.RED)
```

## Statistics Calculation

### Download Speed
```python
elapsed = time.time() - self.download_start_time
chunks_per_second = current_chunk / elapsed
mb_per_second = chunks_per_second × 95  # Assuming 95MB chunks
```

**Example:**
- Downloaded 10 chunks in 5 seconds
- Speed = 10 / 5 = 2 chunks/second
- MB/s = 2 × 95 = 190 MB/s

### ETA (Estimated Time)
```python
remaining_chunks = total - current
chunks_per_second = current / elapsed
eta_seconds = remaining_chunks / chunks_per_second
```

**Example:**
- Total: 20 chunks
- Current: 10 chunks
- Elapsed: 5 seconds
- Speed: 2 chunks/second
- ETA = (20 - 10) / 2 = 5 seconds

### Progress Percentage
```python
progress_percent = (current / total) × 100
```

## Download Stages Explained

### 1. Downloading Chunks (Primary Stage)
- Downloads chunks concurrently from Google Drive
- Uses ThreadPoolExecutor for parallel downloads
- Each chunk: 95MB (default)
- Shows real-time speed and ETA
- Updates progress bar per chunk

### 2. Merging Chunks
- Combines downloaded chunks into single file
- Reads chunks in order by index
- Writes to final output file
- Verifies each chunk hash during merge
- Shows merge progress (per chunk merged)

### 3. Verifying File
- Calculates SHA-256 hash of final file
- Compares with expected hash from manifest
- Ensures file integrity
- Prevents corrupted downloads

### 4. Completed
- Final stage before banner disappears
- Shows success notification
- Cleans up temporary chunk files
- File ready in downloads folder

## Error Handling

### Download Cancelled
```
⚠️ Download cancelled
- Partial file deleted
- Banner hidden
- Orange notification shown
```

### Download Failed
```
❌ Download failed for [filename]
- Error logged to console
- Banner hidden
- Red notification shown
```

### Network Error
```
❌ Download error: [error message]
- Exception details shown
- Banner hidden
- Red notification shown
```

### Hash Mismatch
```
❌ File verification failed
- Downloaded file deleted
- Prevents corrupted file
- Red notification shown
```

## Integration Points

### Library View
The download progress banner is integrated at the top of the Library view:

```python
self.content_area.content = ft.Column([
    # Download progress banner (only visible when downloading)
    self.download_progress_banner,
    ft.Container(height=10),  # Gap after banner
    # Library content below...
])
```

### Download Button
Each file card in the library has a download button:
- Click triggers `download_file(item)`
- Banner appears immediately
- Progress updates in real-time

## Benefits

1. **User Visibility:** See exactly what's happening during download
2. **Progress Tracking:** Know how much time remaining
3. **Performance Monitoring:** See download speeds in real-time
4. **Stage Awareness:** Understand current download phase
5. **Cancellation Control:** Stop download anytime with visual feedback
6. **Error Clarity:** Clear error messages with appropriate severity

## Comparison with Upload Progress

| Feature | Upload | Download |
|---------|--------|----------|
| Banner Color | Blue | Green |
| Icon | Cloud Upload | Download Arrow |
| Stages | Hashing → Chunking → Creating Manifest → Uploading | Downloading → Merging → Verifying |
| Speed Calculation | Chunks uploaded per second | Chunks downloaded per second |
| Cancellation | Yes (ESC or X button) | Yes (ESC or X button) |
| Location | Upload tab | Library tab |
| Progress Bar | Blue | Green |

## Future Enhancements

Potential improvements:
1. **Download Queue:** Queue multiple downloads sequentially
2. **Parallel Downloads:** Download multiple files simultaneously (with speed limits)
3. **Pause/Resume:** Pause and resume downloads
4. **Bandwidth Limiting:** Set max download speed
5. **Retry Failed Chunks:** Automatically retry failed chunk downloads
6. **Download History:** Track completed downloads with stats
7. **Size Estimate:** Show total MB being downloaded before starting
8. **Network Stats:** Show network usage, total bytes transferred

## Related Documentation
- `UPLOAD_RETRY_SYSTEM.md` - Automatic upload retry system
- `REUPLOAD_BUTTON.md` - Manual re-upload functionality
- `PERFORMANCE_GUIDE.md` - Performance optimization tips
- `RATE_LIMIT_GUIDE.md` - Understanding API rate limits
