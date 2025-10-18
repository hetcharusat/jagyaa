Project cleanup summary

Active UI and entrypoint
- Entry: main.py
- UI: gui/main_window.py (PySide6)

Removed (unused/experimental)
- Gradio web UI: gradio_app.py
- Desktop webview wrapper: desktop_main.py
- Alternate entrypoint: main_v2.py
- Modern/Fluent UI experiments and helpers in gui/: 
  - modern_main_window.py, modern_main_window_fixed.py, design_system.py, modern_theme.py
  - library.py, library_modern.py, dashboard.py, upload_panel.py
  - drive_manager.py, settings.py, rclone_installer.py
  - fluent_main_window.py, pyside_main_window.py, tempCodeRunnerFile.py

Why
- Simplify to a single, working desktop UI.
- Avoid confusion and reduce package size for EXE build.

What remains essential
- core/: business logic (Uploader, Downloader, RcloneManager, ManifestManager, etc.)
- config/: app settings and user-configurable drives
- manifests/, chunks/: runtime data folders

Next steps
- Use main.py to run the app.
- Build EXE with build_exe.ps1 when ready.