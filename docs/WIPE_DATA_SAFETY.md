# Wipe Data Button - Safe Folder-Only Deletion

**Date**: October 19, 2025  
**Issue**: Wipe Data button clarity and safety concerns

## ✅ What "Wipe Data" Actually Does

### **SAFE: Only Deletes Upload Folder**

The "Wipe Data" button **ONLY** deletes files from the upload folder (`MultiDriveSplit` by default), **NOT** your entire Google Drive!

**What gets deleted:**
```
Google Drive/
├── MultiDriveSplit/          ← ONLY THIS FOLDER!
│   ├── file1.part0000.chunk
│   ├── file1.part0001.chunk
│   ├── file2.part0000.chunk
│   └── ...
├── Documents/                ← SAFE
├── Photos/                   ← SAFE
├── Videos/                   ← SAFE
└── ...other files...         ← SAFE
```

**What's SAFE:**
- ✅ Your personal documents
- ✅ Your photos, videos
- ✅ Files in other folders
- ✅ Everything outside upload folder

## Updated Dialog - Much Clearer!

### Before (Scary & Unclear):
```
⚠️ Confirm Data Wipe
This will PERMANENTLY DELETE all data from Drive Name.
[Cancel] [Wipe Data]
```

### After (Clear & Safe):
```
⚠️ Wipe Upload Folder

This will PERMANENTLY DELETE all files from:
📁 Drive Name → MultiDriveSplit/

What gets deleted:
• All chunk files in upload folder
• All files you uploaded via this app
• Cannot be recovered (bypasses trash)

✅ Safe: Other folders and files NOT touched

⚠️ This action cannot be undone!

[Cancel] [Wipe Upload Folder]
```

## Implementation

```python
# SAFE: Scoped to upload folder only
upload_folder = self.config.app_settings.get('upload_folder', 'MultiDriveSplit')
remote_path = f"{remote_name}:{upload_folder}"  # Only this folder!

# NOT the entire drive!
# NOT: f"{remote_name}:" ❌
# NOT: f"{remote_name}:/" ❌
```

## Safety Features

1. **Folder Scoped** - Only deletes upload folder
2. **Clear Dialog** - Shows exact folder path
3. **Confirmation Required** - Can't accidental click
4. **Verbose Logging** - See exactly what's deleted
5. **Cache Refresh** - Updates storage stats after

## Testing

**Try this**:
1. Put a test file in your Drive root
2. Upload something via app
3. Click "Wipe Data"
4. Confirm
5. Check Drive: Root file still there! ✅

Your personal files are 100% safe! Only app chunks deleted.
