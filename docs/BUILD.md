# Build and Package Instructions

## Building Standalone Executable

### Prerequisites
```powershell
pip install pyinstaller
```

### Build Command

**Single File Executable:**
```powershell
pyinstaller --name="MultiDriveSplitUploader" `
            --windowed `
            --onefile `
            --add-data="config;config" `
            --hidden-import=PySide6 `
            --hidden-import=core `
            --hidden-import=gui `
            main.py
```

**Directory Mode (Faster startup):**
```powershell
pyinstaller --name="MultiDriveSplitUploader" `
            --windowed `
            --add-data="config;config" `
            --hidden-import=PySide6 `
            --hidden-import=core `
            --hidden-import=gui `
            main.py
```

### Output
- Executable: `dist/MultiDriveSplitUploader.exe`
- Build files: `build/` (can be deleted)
- Spec file: `MultiDriveSplitUploader.spec`

## Creating Distribution Package

### 1. Download Rclone
- Get rclone.exe from https://rclone.org/downloads/
- Use the Windows 64-bit version

### 2. Create Distribution Folder

```powershell
# Create distribution structure
mkdir dist_package
cd dist_package

# Copy files
copy ..\dist\MultiDriveSplitUploader.exe .
copy rclone.exe .  # Downloaded separately

# Create config folder
mkdir config
copy ..\config\drives.example.json config\

# Create docs folder
mkdir docs
copy ..\README.md docs\
copy ..\SETUP.md docs\
```

### 3. Create README.txt for Users

Create `dist_package/README.txt`:
```
Multi-Google Drive Split Uploader
==================================

QUICK START:
1. Run MultiDriveSplitUploader.exe
2. Click Settings > Configure Rclone Remotes
3. Add your Google Drive accounts
4. Edit config/drives.json to match remote names
5. Start uploading!

For detailed instructions, see docs/SETUP.md

Requirements:
- Windows 10/11
- Internet connection
- Google Drive accounts

FIRST TIME SETUP:
The application will guide you through rclone configuration.
You need to authenticate each Google Drive account.

Support: See docs/README.md for troubleshooting
```

### 4. Package for Distribution

```powershell
# Create zip file
Compress-Archive -Path dist_package\* -DestinationPath MultiDriveSplitUploader_v1.0.zip
```

## Distribution Package Structure

```
MultiDriveSplitUploader_v1.0.zip
├── MultiDriveSplitUploader.exe
├── rclone.exe
├── README.txt
├── config/
│   └── drives.example.json
└── docs/
    ├── README.md
    ├── SETUP.md
    └── RCLONE_SETUP.md
```

## Testing the Package

1. Extract zip to a clean folder
2. Run MultiDriveSplitUploader.exe
3. Configure rclone remotes
4. Test upload and download

## Advanced: Custom Icon

1. Create or download an icon file (`.ico`)
2. Add to build command:
```powershell
pyinstaller --name="MultiDriveSplitUploader" `
            --windowed `
            --onefile `
            --icon=app_icon.ico `
            --add-data="config;config" `
            main.py
```

## Optimization

### Reduce Executable Size

Add to spec file or command:
```powershell
--exclude-module matplotlib
--exclude-module pandas
--exclude-module numpy
```

### UPX Compression (Optional)

Download UPX from https://upx.github.io/ and add to PATH, then:
```powershell
pyinstaller ... --upx-dir="C:\path\to\upx"
```

## Troubleshooting Build Issues

**"Module not found" errors:**
```powershell
pip install --upgrade pip setuptools pyinstaller
pip install -r requirements.txt --force-reinstall
```

**"Hidden import" warnings:**
Add to command:
```powershell
--hidden-import=module_name
```

**DLL errors:**
Ensure Visual C++ Redistributable is installed:
https://aka.ms/vs/17/release/vc_redist.x64.exe

## Version Management

Update version in:
1. `main.py` - `app.setApplicationVersion()`
2. `README.md` - Badge and heading
3. Package filename

## Release Checklist

- [ ] Update version numbers
- [ ] Test all features
- [ ] Build executable
- [ ] Test executable on clean system
- [ ] Create distribution package
- [ ] Test distribution package
- [ ] Create release notes
- [ ] Upload to distribution platform
