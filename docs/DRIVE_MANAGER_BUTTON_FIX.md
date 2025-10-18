# Drive Manager Button Layout Fix

**Date**: October 19, 2025  
**Issue**: Drive card buttons (Open, Remove, Wipe Data) were misaligned and out of CSS

## Problems Fixed

### 1. Button Alignment Issues ✅
**Before**: Buttons were cramped and poorly aligned
**After**: 
- Open and Remove buttons side-by-side with equal width (`expand=True`)
- Wipe Data button full-width below them
- Proper spacing (10px between buttons)

### 2. Button Layout
```python
# Top row: Open + Remove (equal width, side by side)
ft.Row([
    ft.ElevatedButton("Open", icon=..., expand=True),
    ft.OutlinedButton("Remove", icon=..., expand=True),
], spacing=10)

# Bottom: Wipe Data (full width)
ft.OutlinedButton("Wipe Data", icon=..., width=float('inf'))
```

### 3. Visual Hierarchy
- **Open**: ElevatedButton (primary action)
- **Remove**: OutlinedButton (secondary)
- **Wipe Data**: OutlinedButton with RED icon (dangerous action)

## Wipe Data Functionality

The "Wipe Data" button works correctly:

1. **Click "Wipe Data"** → Shows confirmation dialog
2. **Confirmation dialog** warns: "This will PERMANENTLY DELETE all data"
3. **Confirms** → Runs `rclone purge` in background thread
4. **Deletes**: All files from `remote:MultiDriveSplit` folder
5. **Success/Error notification** shown

### Code Flow
```python
wipe_drive(drive) 
  → Show AlertDialog with warning
  → User confirms
  → Run rclone purge in thread
  → Show success/error snackbar
```

## Testing
1. Restart app: `python main_flet_new.py`
2. Go to Drive Manager
3. Verify buttons are properly aligned
4. Test "Wipe Data" (CAREFUL - it's destructive!)

## Notes
- Wipe Data uses `rclone purge` (faster than delete)
- Action is **IRREVERSIBLE**
- Only deletes from `MultiDriveSplit` folder (not entire drive)
- Runs in background thread (non-blocking)
