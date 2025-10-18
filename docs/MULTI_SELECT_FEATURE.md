# Multi-Select Feature for Library

## Overview
Added multi-select functionality to the library, allowing users to select multiple files and perform batch operations (download, delete, re-upload).

## Implementation Details

### State Management (Lines 67-71)
```python
# Multi-select system for library
self.selected_files = []  # List of selected item IDs
self.selection_mode = False  # Toggle selection mode
```

### User Interface

#### 1. Selection Mode Toggle Button (Lines 1320-1324)
- Located in library controls row
- Button text: "Select Multiple"
- Icon: `CHECK_BOX_OUTLINE_BLANK`
- Background: Purple highlight when active
- Click: Toggles selection mode on/off

#### 2. File Card Checkboxes (Lines 1845-1851)
- Checkboxes appear at top-right of cards when `selection_mode = True`
- Visual feedback: Selected cards have:
  - Purple border (2px)
  - Purple background tint (`PURPLE_50`)
- Checkbox automatically reflects selection state

#### 3. Batch Action Bar (Lines 1391-1435)
Appears below controls when files are selected:
- **Selection count:** Shows number of selected files
- **Select All:** Select all visible files in current view
- **Clear:** Deselect all files
- **Download All:** Add all selected to download queue
- **Delete All:** Delete all selected files (with confirmation)
- **Re-upload (N):** Re-upload failed files (only shows if failed files selected)

### Core Methods

#### `toggle_selection_mode()` (Lines 1408-1413)
- Toggles `self.selection_mode` flag
- Clears selections when exiting selection mode
- Refreshes library to show/hide checkboxes

#### `toggle_file_selection(item)` (Lines 1415-1423)
- Adds/removes item from `selected_files` list
- Uses unique item ID for tracking
- Refreshes library to update visual state

#### `select_all_files()` (Lines 1425-1431)
- Selects all files in `library_items` (respects current filters)
- Clears existing selections first
- Refreshes library

#### `clear_selection()` (Lines 1433-1436)
- Clears `selected_files` list
- Does NOT exit selection mode
- Refreshes library

#### `_get_item_id(item)` (Lines 1438-1445)
Generates unique ID for each library item:
- **Manifest files:** `manifest_{manifest_id}`
- **Remote files:** `remote_{remote_path}_{drive_name}`

#### `_get_item_by_id(item_id)` (Lines 1447-1452)
- Finds library item by its unique ID
- Returns `None` if not found

### Batch Operations

#### `batch_download()` (Lines 1454-1479)
- Validates selection (not empty)
- Skips failed files (can't download)
- Adds valid files to download queue
- Shows success message with count
- Clears selection and exits selection mode
- Auto-starts download queue if not running

#### `batch_delete()` (Lines 1481-1522)
- Validates selection (not empty)
- Shows confirmation dialog with count
- Performs deletion for each selected file
- Handles both manifest and remote files
- Shows success message with count
- Clears selection and exits selection mode

#### `batch_reupload()` (Lines 1524-1549)
- Validates selection (not empty)
- Only processes failed manifest files
- Checks if original file still exists
- Adds valid files to upload queue
- Shows success message with count
- Clears selection and exits selection mode
- Auto-starts upload queue if not running

#### `_perform_delete(item)` (Lines 1551-1604)
Helper method for batch delete (no UI dialogs):
- **Manifest files:**
  - Deletes all chunks from cloud
  - Deletes local manifest file
  - Deletes local chunk files
- **Remote files:**
  - Deletes from Google Drive using rclone

## User Workflow

### Basic Selection
1. Click "Select Multiple" button in library controls
2. Checkboxes appear on all file cards
3. Click checkboxes to select/deselect files
4. Selected cards highlighted with purple border

### Batch Download
1. Enter selection mode
2. Select multiple files (excluding failed files)
3. Click "Download All" in action bar
4. All files added to download queue
5. Downloads start automatically

### Batch Delete
1. Enter selection mode
2. Select multiple files
3. Click "Delete All" in action bar
4. Confirm deletion in dialog
5. All selected files deleted (manifest + chunks)

### Batch Re-upload
1. Enter selection mode
2. Select multiple failed files
3. Click "Re-upload (N)" button (N = failed count)
4. All valid failed files added to upload queue
5. Uploads start automatically

### Select All/Clear
- **Select All:** Selects all visible files (respects current filters)
- **Clear:** Deselects all without exiting selection mode

### Exit Selection Mode
- Click "Select Multiple" button again
- Checkboxes disappear
- All selections cleared automatically

## Technical Notes

### Selection Persistence
- Selections cleared when:
  - Exiting selection mode
  - Completing batch operation
  - Refreshing library (manually triggered)
- Selections preserved when:
  - Changing filters/sort
  - Scrolling

### Item Identification
- Uses stable IDs based on manifest ID or remote path
- Safe across library refreshes
- Handles both manifest and remote files

### Performance
- Checkbox state checked during card creation
- Minimal overhead for non-selected cards
- Batch operations processed sequentially

### Limitations
- Cannot download failed files (skipped automatically)
- Cannot re-upload non-manifest files
- Cannot re-upload if original file deleted
- Selection cleared after batch operations

## Visual Design
- **Selection button:** Purple highlight when active
- **Selected cards:** Purple border + light purple background
- **Action bar:** Purple theme matching selection UI
- **Batch buttons:** Icon + text for clarity
- **Re-upload button:** Only visible when failed files selected

## Future Enhancements (Optional)
- [ ] Persist selection across library refreshes
- [ ] Add keyboard shortcuts (Ctrl+A, Escape)
- [ ] Add "Select by type" filter
- [ ] Add progress for batch operations
- [ ] Add undo for batch delete
- [ ] Add drag-to-select in grid view
