# Qt Designer UI Editing Guide

This project now supports editing the UI visually with Qt Designer!

## Files

- **`gui/main_window.ui`** - Qt Designer UI file (XML format)
- **`gui/main_window_designer.py`** - Python code that loads the `.ui` file
- **`gui/main_window.py`** - Original programmatic UI (backup)

## How to Use Qt Designer

### Opening Qt Designer

Qt Designer is included with PySide6. Launch it with:

```powershell
C:/Users/hetp2/OneDrive/Desktop/jagyaa/.venv/Scripts/pyside6-designer.exe
```

Or from your activated venv:

```powershell
pyside6-designer
```

### Editing the UI

1. **Open the UI file**: File → Open → `gui/main_window.ui`

2. **Make your changes**:
   - Drag widgets from the Widget Box on the left
   - Adjust properties in the Property Editor on the right
   - Arrange layouts by right-clicking widgets
   - Add/remove tabs, buttons, labels, etc.

3. **Save**: Ctrl+S or File → Save

4. **Run the app** to see your changes (no code regeneration needed!)

### Widget Names (Important!)

The Python code references widgets by their `objectName` property. Don't rename these unless you update the Python code too:

**Dashboard Tab:**
- `statsLabel` - Overview statistics
- `dashboardDrivesText` - Drive status text
- `refreshDashboardBtn` - Refresh button
- `recentUploadsList` - Recent uploads list

**Upload Tab:**
- `dropZone` - Drag & drop area
- `browseBtn` - Browse button
- `uploadStatusLabel`, `uploadProgressBar`, `uploadChunkLabel` - Progress indicators
- `uploadCancelBtn` - Cancel button

**Library Tab:**
- `downloadsList` - File list
- `refreshLibraryBtn`, `downloadBtn` - Action buttons
- `detailsLabel` - File details
- `previewImage`, `previewNote` - Preview area
- `downloadStatusLabel`, `downloadProgressBar`, `downloadChunkLabel` - Progress
- `downloadCancelBtn` - Cancel button

**Settings Tab:**
- `drivesStatusLabel` - Drive status
- `autoLoginBtn`, `manualLoginBtn`, `refreshDrivesBtn` - Drive buttons
- `credsFileLabel` - Credentials status
- `uploadCredsBtn`, `clearCredsBtn` - Credential buttons
- `settingsLabel` - Settings display

**Log:**
- `logText` - Activity log text area

## Switching Between UIs

### Use Qt Designer UI (Current):

Edit `main.py` to import the designer version:

```python
from gui.main_window_designer import MainWindow
```

### Use Programmatic UI (Original):

Edit `main.py` to import the original:

```python
from gui.main_window import MainWindow
```

## Tips

1. **Preview in Designer**: Form → Preview (Ctrl+R) to see how it looks without running
2. **Layouts are key**: Always use layouts (VBox, HBox, Grid) for responsive design
3. **StyleSheets**: Edit in Property Editor → styleSheet for custom styling
4. **Signals/Slots**: You can connect signals in Designer, but we do it in Python for clarity

## Advantages of Qt Designer

✅ Visual drag-and-drop interface design  
✅ Real-time preview  
✅ Easier to experiment with layouts  
✅ Property editors for all widget settings  
✅ No Python code changes needed for visual tweaks  
✅ Separation of UI from logic  

## Current Status

The Designer UI (`main_window_designer.py`) has **full feature parity** with the original programmatic UI. All functionality works identically.
