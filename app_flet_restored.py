"""
Main Window GUI - Flet Version (Enhanced)
Beautiful Material Design UI with comprehensive features
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import flet as ft
import subprocess

# Suppress console output when running as frozen executable
if getattr(sys, 'frozen', False):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
from concurrent.futures import ThreadPoolExecutor
import threading

# Windows-specific subprocess flags to prevent console window popup
if sys.platform == 'win32':
    import subprocess
    # CREATE_NO_WINDOW flag for Windows
    CREATE_NO_WINDOW = 0x08000000
    SUBPROCESS_FLAGS = {
        'creationflags': CREATE_NO_WINDOW,
        'startupinfo': None
    }
    # Also configure startupinfo to hide window
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    SUBPROCESS_FLAGS['startupinfo'] = startupinfo
else:
    SUBPROCESS_FLAGS = {}

from core import (
    ConfigManager, RcloneManager, ManifestManager,
    Uploader, Downloader
)


class MultiDriveApp:
    """Enhanced Flet application with complete feature set"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Multi-Drive Cloud Manager"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        
        # Initialize core components
        try:
            self.config = ConfigManager()
            self.manifest_manager = ManifestManager(self.config.get_manifest_folder())
            rclone_path = self.config.get_rclone_path() or "rclone"
            self.rclone = RcloneManager(rclone_path=rclone_path, config_path=self.config.get_rclone_config_path(), strict=False)
            self.uploader = Uploader(self.config, self.rclone, self.manifest_manager)
            self.downloader = Downloader(self.config, self.rclone, self.manifest_manager)
        except Exception as e:
            import traceback
            # Initialization error - app will not function
            traceback.print_exc()
            return
        
        # UI state
        self.selected_manifest_id = None
        self.upload_start_time = None
        self.upload_running = False
        self.current_upload_stats = {"chunks": 0, "total": 0, "bytes_uploaded": 0, "total_bytes": 0}
        self.search_query = ""
        self.sort_by = "name"
        self.filter_type = "all"
        
        # Upload queue system
        self.upload_queue = []  # List of file paths to upload
        self.current_upload_path = None
        self.upload_cancelled = False
        self.upload_queue_ui = None  # Will be initialized in show_upload()
        
        # Retry system for failed uploads
        self.failed_uploads = []  # List of (file_path, retry_count, error_msg)
        self.max_retries = 3  # Max retry attempts per file
        self.retry_delay = 60  # Initial retry delay in seconds (increases exponentially)
        
        # Re-upload tracking
        self.reupload_old_manifest_id = None  # Track old manifest ID when re-uploading
        
        # Download queue system
        self.download_queue = []  # List of download items (manifest or remote file info)
        self.current_download_item = None
        self.download_running = False
        self.download_cancelled = False
        self.download_queue_ui = None  # Will be initialized in show_library()
        
        # Multi-select system for library
        self.selected_files = []  # List of selected items in library
        self.selection_mode = False  # Toggle selection mode
        self.rebuilding_library = False  # Flag to prevent checkbox events during rebuild
        
        # Performance: Cache drive stats to avoid slow queries
        self.drive_stats_cache = {}
        self.cache_timestamp = 0
        self.cache_ttl = 300  # Cache for 5 minutes

        # Performance: Cache manifests to avoid reading disk repeatedly
        self.manifests_cache = []
        self.manifests_cache_ts = 0.0
        self.manifests_cache_ttl = 5.0  # seconds
        self._manifests_cache_dirty = False

        # Debounce for search typing
        self.search_debounce_timer = None
        # Control flag for cancelling batch delete
        self._delete_cancel_flag = False
        
        # Temp file management for previews
        self.preview_temp_files = []  # Track temp files for cleanup
        self.cleanup_old_temp_files()  # Cleanup from previous sessions
        
        # Build UI
        self.build_ui()
        
        # Initial data load
        self.show_dashboard()
    
    def cleanup_old_temp_files(self):
        """Cleanup temp files from previous sessions"""
        try:
            import tempfile
            import glob
            temp_dir = tempfile.gettempdir()
            # Clean up old preview folders
            for folder in glob.glob(os.path.join(temp_dir, "preview_*")):
                try:
                    import shutil
                    shutil.rmtree(folder)

                except:
                    pass
        except:
            pass
    
    def build_ui(self):
        """Build the main UI structure with navigation rail"""
        # App bar
        self.page.appbar = ft.AppBar(
            title=ft.Row([
                ft.Icon(ft.Icons.CLOUD_CIRCLE, size=28),
                ft.Text("Multi-Drive Cloud Manager", size=20, weight=ft.FontWeight.BOLD)
            ]),
            bgcolor=ft.Colors.BLUE_700,
            actions=[
                ft.IconButton(ft.Icons.BRIGHTNESS_6, tooltip="Toggle theme", on_click=self.toggle_theme),
                ft.IconButton(ft.Icons.REFRESH, tooltip="Refresh", on_click=lambda _: self.refresh_current())
            ]
        )
        
        # Navigation rail (removed Login tab)
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD, label="Dashboard"),
                ft.NavigationRailDestination(icon=ft.Icons.CLOUD_UPLOAD_OUTLINED, selected_icon=ft.Icons.CLOUD_UPLOAD, label="Upload"),
                ft.NavigationRailDestination(icon=ft.Icons.PHOTO_LIBRARY_OUTLINED, selected_icon=ft.Icons.PHOTO_LIBRARY, label="Library"),
                ft.NavigationRailDestination(icon=ft.Icons.STORAGE_OUTLINED, selected_icon=ft.Icons.STORAGE, label="Drives"),
                ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Settings"),
            ],
            on_change=self.nav_changed,
        )
        
        # Content area
        self.content_area = ft.Container(expand=True, padding=20)
        
        # Create persistent upload progress overlay (visible across all tabs)
        self.create_upload_progress_overlay()
        
        # Create persistent download progress overlay
        self.create_download_progress_overlay()
        # Create persistent delete progress overlay
        self.create_delete_progress_overlay()
        
        # Main layout
        self.page.add(
            ft.Row([
                self.nav_rail,
                ft.VerticalDivider(width=1),
                self.content_area
            ], expand=True)
        )
    
    def create_upload_progress_overlay(self):
        """Create persistent upload progress BANNER at top of content area"""
        self.upload_progress_bar = ft.ProgressBar(value=0, height=4, color=ft.Colors.BLUE_600, bar_height=4)
        self.upload_status_text = ft.Text("Preparing...", size=13, weight=ft.FontWeight.W_500)
        self.upload_speed_text = ft.Text("Speed: --", size=12, color=ft.Colors.GREY_700)
        self.upload_eta_text = ft.Text("ETA: --", size=12, color=ft.Colors.GREY_700)
        self.upload_chunk_text = ft.Text("--", size=12, color=ft.Colors.GREY_700)
        
        # Create a comprehensive banner with all info
        self.upload_progress_banner = ft.Container(
            content=ft.Column([
                # Status row with cancel button
                ft.Row([
                    ft.Icon(ft.Icons.CLOUD_UPLOAD, size=20, color=ft.Colors.BLUE_600),
                    ft.Container(width=8),
                    ft.Container(
                        content=self.upload_status_text,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=20,
                        tooltip="Cancel Upload",
                        on_click=lambda _: self.cancel_upload(),
                        icon_color=ft.Colors.RED_500,
                    ),
                ], spacing=0),
                ft.Container(height=8),
                # Progress bar
                self.upload_progress_bar,
                ft.Container(height=8),
                # Stats row
                ft.Row([
                    self.upload_speed_text,
                    ft.Container(width=20),
                    self.upload_eta_text,
                    ft.Container(width=20),
                    self.upload_chunk_text,
                ], spacing=0),
            ], spacing=0, tight=True),
            padding=15,
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(2, ft.Colors.BLUE_200),
            border_radius=10,
            visible=False,
        )
        
        # Will be added to content area of each tab

    def create_download_progress_overlay(self):
        """Create persistent download progress BANNER at top of content area"""
        self.download_progress_bar = ft.ProgressBar(value=0, height=4, color=ft.Colors.GREEN_600, bar_height=4)
        self.download_status_text = ft.Text("Downloading...", size=13, weight=ft.FontWeight.W_500)
        self.download_speed_text = ft.Text("Speed: --", size=12, color=ft.Colors.GREY_700)
        self.download_eta_text = ft.Text("ETA: --", size=12, color=ft.Colors.GREY_700)
        self.download_chunk_text = ft.Text("--", size=12, color=ft.Colors.GREY_700)
        
        # Track download stats for progress calculation
        self.download_start_time = None
        self.current_download_stats = {
            "chunks": 0,
            "total": 0,
            "stage": "preparing"
        }
        
        # Create a comprehensive banner with all info
        self.download_progress_banner = ft.Container(
            content=ft.Column([
                # Status row with cancel button
                ft.Row([
                    ft.Icon(ft.Icons.DOWNLOAD, size=20, color=ft.Colors.GREEN_600),
                    ft.Container(width=8),
                    ft.Container(
                        content=self.download_status_text,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=20,
                        tooltip="Cancel Download",
                        on_click=lambda _: self.cancel_download(),
                        icon_color=ft.Colors.RED_500,
                    ),
                ], spacing=0),
                ft.Container(height=8),
                # Progress bar
                self.download_progress_bar,
                ft.Container(height=8),
                # Stats row
                ft.Row([
                    self.download_speed_text,
                    ft.Container(width=20),
                    self.download_eta_text,
                    ft.Container(width=20),
                    self.download_chunk_text,
                ], spacing=0),
            ], spacing=0, tight=True),
            padding=15,
            bgcolor=ft.Colors.GREEN_50,
            border=ft.border.all(2, ft.Colors.GREEN_200),
            border_radius=10,
            visible=False,
        )

    def create_delete_progress_overlay(self):
        """Create persistent delete progress BANNER used during batch deletes"""
        self.delete_progress_bar = ft.ProgressBar(value=0, height=4, color=ft.Colors.RED_600, bar_height=4)
        self.delete_status_text = ft.Text("Deleting...", size=13, weight=ft.FontWeight.W_500)

        cancel_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=20,
            tooltip="Cancel Delete",
            on_click=lambda _: setattr(self, "_delete_cancel_flag", True),
            icon_color=ft.Colors.RED_500,
        )

        self.delete_progress_banner = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.DELETE, size=20, color=ft.Colors.RED_600),
                    ft.Container(width=8),
                    ft.Container(content=self.delete_status_text, expand=True),
                    cancel_btn,
                ], spacing=0),
                ft.Container(height=8),
                self.delete_progress_bar,
            ], spacing=0, tight=True),
            padding=15,
            bgcolor=ft.Colors.RED_50,
            border=ft.border.all(2, ft.Colors.RED_200),
            border_radius=10,
            visible=False,
        )

    def nav_changed(self, e):
        """Handle navigation"""
        idx = e.control.selected_index
        [self.show_dashboard, self.show_upload, self.show_library, self.show_drives, self.show_settings][idx]()
        self.page.update()
    
    def get_cached_drive_stats(self, remote_name: str) -> Optional[dict]:
        """Get drive stats with caching to avoid slow repeated queries"""
        current_time = time.time()
        
        # Check if cache is expired
        if current_time - self.cache_timestamp > self.cache_ttl:
            self.drive_stats_cache = {}
            self.cache_timestamp = current_time
        
        # Return cached value if available
        if remote_name in self.drive_stats_cache:
            cached_stats = self.drive_stats_cache[remote_name]

            return cached_stats
        
        # Fetch new stats (may be slow)

        stats = self.rclone.get_drive_stats(remote_name)

        self.drive_stats_cache[remote_name] = stats
        
        return stats
    
    def clear_drive_cache(self):
        """Clear drive stats cache - useful when switching accounts"""
        self.drive_stats_cache = {}
        self.cache_timestamp = 0

    def show_dashboard(self):
        """Dashboard with comprehensive stats - NO activity log"""
        # ALWAYS reload config to get latest drives
        self.config = ConfigManager()
        
        try:
            manifests = self.manifest_manager.get_all_manifests()
        except:
            manifests = []
        
        total_files = len(manifests)
        total_size = sum(m.get('original_file', {}).get('size', 0) for m in manifests) if manifests else 0
        total_chunks = sum(m.get('total_chunks', 0) for m in manifests) if manifests else 0
        
        try:
            drives = self.config.get_enabled_drives()
            # Ensure drives is a list
            if not isinstance(drives, list):
                drives = []
        except:
            drives = []
        
        # Placeholders (fast render); compute in background
        total_storage = 0
        used_storage = 0
        remaining = 0
        usage_percent = 0
        
        # Stat cards row
        stats = ft.Row([
            self._stat_card("Total Files", str(total_files), ft.Icons.FOLDER, ft.Colors.BLUE_400),
            self._stat_card("Total Size", self._format_size(total_size), ft.Icons.STORAGE, ft.Colors.GREEN_400),
            self._stat_card("Total Chunks", str(total_chunks), ft.Icons.GRID_VIEW, ft.Colors.ORANGE_400),
            self._stat_card("Drives", f"{len(drives)}", ft.Icons.CLOUD, ft.Colors.PURPLE_400),
        ], spacing=15)
        
        # Storage usage card
        # Keep references to update later
        self.storage_used_value_text = ft.Text("…", size=18, weight=ft.FontWeight.BOLD)
        self.storage_total_value_text = ft.Text("…", size=18, weight=ft.FontWeight.BOLD)
        self.storage_free_value_text = ft.Text("…", size=18, weight=ft.FontWeight.BOLD)
        self.storage_progress = ft.ProgressBar(value=0, color=ft.Colors.BLUE_600, height=10)
        self.storage_percent_text = ft.Text("Loading…", size=12, color=ft.Colors.GREY_600)

        storage_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PIE_CHART, size=32, color=ft.Colors.BLUE_600),
                        ft.Text("Storage Usage", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=15),
                    ft.Row([
                        ft.Column([
                            ft.Text("Used", size=12, color=ft.Colors.GREY_600),
                            self.storage_used_value_text,
                        ], spacing=5),
                        ft.Container(width=30),
                        ft.Column([
                            ft.Text("Total", size=12, color=ft.Colors.GREY_600),
                            self.storage_total_value_text,
                        ], spacing=5),
                        ft.Container(width=30),
                        ft.Column([
                            ft.Text("Free", size=12, color=ft.Colors.GREY_600),
                            self.storage_free_value_text,
                        ], spacing=5),
                    ]),
                    ft.Container(height=10),
                    self.storage_progress,
                    self.storage_percent_text,
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        # Drive health list
        drive_health_items = []
        for drive in drives[:5]:  # Show first 5
            status_color = ft.Colors.GREEN if drive.get('enabled', False) else ft.Colors.GREY
            drive_health_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CLOUD_CIRCLE, color=status_color),
                    title=ft.Text(drive.get('name', 'Unknown')),
                    subtitle=ft.Text(f"Remote: {drive.get('remote_name', 'N/A')}"),
                    trailing=ft.Chip(
                        label=ft.Text("Online" if drive.get('enabled') else "Offline"),
                        bgcolor=ft.Colors.GREEN_100 if drive.get('enabled') else ft.Colors.GREY_200,
                    )
                )
            )
        
        drive_health_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.HEALTH_AND_SAFETY, size=32, color=ft.Colors.GREEN_600),
                        ft.Text("Drive Health", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=10),
                    ft.Column(drive_health_items, spacing=5) if drive_health_items else ft.Text("No drives configured"),
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        # Recent uploads
        recent_items = []
        for manifest in manifests[-8:]:  # Last 8
            filename = manifest.get('original_file', {}).get('filename', 'Unknown')
            size = manifest.get('original_file', {}).get('size', 0)
            chunks = manifest.get('total_chunks', 0)
            upload_date = manifest.get('created_at', 'Unknown')[:10]
            
            recent_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FILE_PRESENT, color=ft.Colors.BLUE_400),
                    title=ft.Text(filename),
                    subtitle=ft.Text(f"{self._format_size(size)} • {chunks} chunks"),
                    trailing=ft.Text(upload_date, size=11, color=ft.Colors.GREY_600),
                    dense=True,
                )
            )
        
        recent_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.HISTORY, size=32, color=ft.Colors.ORANGE_600),
                        ft.Text("Recent Uploads", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=10),
                    ft.Column(recent_items, spacing=2, scroll=ft.ScrollMode.AUTO, height=300) if recent_items else ft.Text("No uploads yet"),
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        # API Health
        try:
            rclone_version = "1.71.1"  # Placeholder
            config_status = "OK" if os.path.exists(self.config.get_rclone_config_path()) else "Missing"
            manifest_count = len(manifests)
        except:
            rclone_version = "Unknown"
            config_status = "Error"
            manifest_count = 0
        
        api_health_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.ANALYTICS, size=32, color=ft.Colors.BLUE_600),
                        ft.Text("API Health", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=15),
                    ft.Row([
                        ft.Column([
                            ft.Text("Rclone Version", size=12, color=ft.Colors.GREY_600),
                            ft.Text(rclone_version, size=16, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Container(width=40),
                        ft.Column([
                            ft.Text("Config Status", size=12, color=ft.Colors.GREY_600),
                            ft.Text(config_status, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN if config_status == "OK" else ft.Colors.RED),
                        ]),
                        ft.Container(width=40),
                        ft.Column([
                            ft.Text("Manifests Tracked", size=12, color=ft.Colors.GREY_600),
                            ft.Text(str(manifest_count), size=16, weight=ft.FontWeight.BOLD),
                        ]),
                    ]),
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        # Layout dashboard
        self.content_area.content = ft.Column([
            ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            stats,
            ft.Container(height=15),
            ft.Row([
                ft.Container(storage_card, expand=1),
                ft.Container(width=15),
                ft.Container(drive_health_card, expand=1),
            ], expand=False),
            ft.Container(height=15),
            ft.Row([
                ft.Container(recent_card, expand=1),
                ft.Container(width=15),
                ft.Container(api_health_card, expand=1),
            ], expand=False),
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        self.page.update()

        # Fetch drive stats in background and update UI
        def _update_storage():
            try:
                t_total = 0
                t_used = 0
                for d in drives:
                    if d.get('enabled', False):
                        rn = d.get('remote_name', '')
                        if rn:
                            stats = self.get_cached_drive_stats(rn)
                            if stats:
                                t_total += stats.get('total', 0)
                                t_used += stats.get('used', 0)
                if t_total == 0:
                    t_total = 15 * 1024 * 1024 * 1024  # fallback 15GB
                t_remaining = max(t_total - t_used, 0)
                pct = (t_used / t_total * 100) if t_total > 0 else 0

                # Update UI controls
                self.storage_used_value_text.value = self._format_size(t_used)
                self.storage_total_value_text.value = self._format_size(t_total)
                self.storage_free_value_text.value = self._format_size(t_remaining)
                self.storage_progress.value = pct / 100
                self.storage_percent_text.value = f"{pct:.1f}% used"
                self.page.update()
            except Exception as ex:
                pass  # Failed to update storage stats
        
        threading.Thread(target=_update_storage, daemon=True).start()
    
    def _stat_card(self, title, value, icon, color):
        """Create a stat card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=40, color=color),
                    ft.Container(width=15),
                    ft.Column([
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(title, size=12, color=ft.Colors.GREY_600)
                    ], spacing=0)
                ]),
                padding=20,
            ),
            elevation=2,
        )
    
    def _format_size(self, size_bytes):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def show_upload(self):
        """Upload page with improved UX"""
        self.file_picker = ft.FilePicker(on_result=self.file_picked)
        self.folder_picker = ft.FilePicker(on_result=self.folder_picked)
        self.page.overlay.clear()
        self.page.overlay.append(self.file_picker)
        self.page.overlay.append(self.folder_picker)
        
        # Compact drop zone with better proportions
        drop_zone = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CLOUD_UPLOAD, size=60, color=ft.Colors.BLUE_400),
                ft.Container(height=15),
                ft.Text("Drop files or folders here", size=20, weight=ft.FontWeight.W_600),
                ft.Container(height=8),
                ft.Text("or", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=8),
                ft.Row([
                    ft.ElevatedButton(
                        "Browse Files",
                        icon=ft.Icons.INSERT_DRIVE_FILE,
                        on_click=lambda _: self.file_picker.pick_files(allow_multiple=True),
                        style=ft.ButtonStyle(padding=15)
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "Browse Folder",
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=lambda _: self.folder_picker.get_directory_path(),
                        style=ft.ButtonStyle(padding=15)
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Text("💡 Supports multiple files • Max 95MB chunks • Auto-split large files", 
                       size=11, color=ft.Colors.GREY_500, italic=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            padding=40,
            border=ft.border.all(2, ft.Colors.BLUE_300),
            border_radius=12,
            bgcolor=ft.Colors.BLUE_50,
        )
        
        # Drive health status card
        health_status = self.check_all_drives_health()
        health_items = []
        
        for remote_name, health in health_status.items():
            icon = ft.Icons.CHECK_CIRCLE if health['status'] == 'HEALTHY' else ft.Icons.ERROR
            color = ft.Colors.GREEN_600 if health['status'] == 'HEALTHY' else ft.Colors.RED_600
            
            health_items.append(
                ft.Row([
                    ft.Icon(icon, size=20, color=color),
                    ft.Text(remote_name, size=13, weight=ft.FontWeight.W_500),
                    ft.Text(health['message'], size=12, color=ft.Colors.GREY_700),
                ], spacing=8)
            )
        
        def refresh_health_status(e):
            """Refresh drive health status"""
            self.show_snackbar("🔄 Checking drive health...", ft.Colors.BLUE)
            self.show_upload()  # Reload upload page with fresh health check
        
        health_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.HEALTH_AND_SAFETY, size=20, color=ft.Colors.BLUE_600),
                        ft.Text("Drive Status", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),  # Spacer
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            icon_size=18,
                            tooltip="Refresh drive status",
                            on_click=refresh_health_status
                        ),
                    ]),
                    ft.Container(height=5),
                    ft.Column(health_items, spacing=5) if health_items else ft.Text("No drives configured", size=12, color=ft.Colors.GREY_500),
                ], spacing=8, tight=True),
                padding=12,
            ),
            elevation=1,
        ) if health_items else ft.Container()
        
        self.content_area.content = ft.Column([
            # Upload progress banner (only visible when uploading)
            self.upload_progress_banner,
            ft.Container(height=10),  # Small gap after banner
            # Drive health status
            health_card,
            ft.Container(height=10),
            # Main upload area
            ft.Text("Upload Files", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=5),
            ft.Text("Upload files to your connected cloud drives", 
                   size=13, color=ft.Colors.GREY_600),
            ft.Container(height=20),
            drop_zone,
            ft.Container(height=20),
            # Upload Queue Section
            ft.Text("Upload Queue", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Initialize queue UI container
        self.upload_queue_ui = ft.Column([], spacing=8)
        queue_container = ft.Container(
            content=self.upload_queue_ui,
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )
        self.content_area.content.controls.append(queue_container)
        
        # Initialize queue UI
        self.update_queue_ui()
        self.page.update()

    def update_queue_ui(self):
        """Update the upload queue display - WITH RETRY STATUS"""
        if not hasattr(self, 'upload_queue_ui') or self.upload_queue_ui is None:
            return
        
        self.upload_queue_ui.controls.clear()
        
        # Show failed uploads waiting for retry
        if len(self.failed_uploads) > 0:
            self.upload_queue_ui.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.ERROR_OUTLINE, size=18, color=ft.Colors.ORANGE_600),
                            ft.Text(
                                f"{len(self.failed_uploads)} failed upload(s) waiting for auto-retry",
                                size=12,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.ORANGE_700
                            ),
                        ]),
                        ft.Text(
                            "Files will automatically retry after delay (exponential backoff)",
                            size=11,
                            color=ft.Colors.GREY_600,
                            italic=True
                        ),
                    ], spacing=5, tight=True),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=10,
                    border_radius=6,
                    border=ft.border.all(1, ft.Colors.ORANGE_200),
                )
            )
        
        if not self.upload_queue and not self.upload_running:
            # Empty state (only if no failed uploads either)
            if len(self.failed_uploads) == 0:
                self.upload_queue_ui.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "No files in queue. Select files or folders to upload.",
                            size=13,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        padding=20,
                        alignment=ft.alignment.center,
                    )
                )
        else:
            # Show current upload
            if self.upload_running and self.current_upload_path:
                filename = Path(self.current_upload_path).name
                self.upload_queue_ui.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.UPLOAD, size=20, color=ft.Colors.BLUE_600),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(filename, size=13, weight=ft.FontWeight.W_500),
                                ft.Text("Uploading...", size=11, color=ft.Colors.BLUE_600),
                            ], spacing=2),
                            ft.Container(expand=True),
                            ft.ProgressRing(width=20, height=20, stroke_width=2),
                        ]),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=10,
                        border_radius=6,
                    )
                )
            
            # Show queue
            for idx, file_path in enumerate(self.upload_queue):
                filename = Path(file_path).name
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                
                self.upload_queue_ui.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=20, color=ft.Colors.GREY_600),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(filename, size=13),
                                ft.Text(self._format_size(file_size), size=11, color=ft.Colors.GREY_600),
                            ], spacing=2),
                            ft.Container(expand=True),
                            ft.Text(f"#{idx + 1} in queue", size=11, color=ft.Colors.GREY_500),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=16,
                                tooltip="Remove from queue",
                                on_click=lambda e, path=file_path: self.remove_from_queue(path),
                            ),
                        ]),
                        padding=10,
                        border_radius=6,
                        border=ft.border.all(1, ft.Colors.GREY_200),
                    )
                )
        
        if hasattr(self.page, 'update'):
            self.page.update()
    
    def remove_from_queue(self, file_path):
        """Remove a file from upload queue"""
        if file_path in self.upload_queue:
            self.upload_queue.remove(file_path)
            self.update_queue_ui()
            self.show_snackbar(f"Removed {Path(file_path).name} from queue", ft.Colors.ORANGE)

    def file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file selection - Support multiple files"""
        if e.files:
            self.show_snackbar(f"📄 Added {len(e.files)} file(s) to queue")
            # Add all files to queue
            for file in e.files:
                self.upload_queue.append(file.path)
            # Update queue UI
            self.update_queue_ui()
            # Start upload if not already running
            if not self.upload_running:
                self.process_upload_queue()
    
    def folder_picked(self, e: ft.FilePickerResultEvent):
        """Handle folder selection - recursively add all files"""
        if e.path:
            folder_path = Path(e.path)
            # Recursively find all files in folder
            all_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
            
            if all_files:
                self.show_snackbar(f"📁 Added {len(all_files)} files from {folder_path.name}")
                # Add all files to queue
                for file_path in all_files:
                    self.upload_queue.append(file_path)
                # Update queue UI
                self.update_queue_ui()
                # Start upload if not already running
                if not self.upload_running:
                    self.process_upload_queue()
            else:
                self.show_snackbar(f"⚠️ No files found in {folder_path.name}", ft.Colors.ORANGE)
    
    def update_download_queue_ui(self):
        """Update the download queue display"""
        if not hasattr(self, 'download_queue_ui') or self.download_queue_ui is None:
            return
        
        self.download_queue_ui.controls.clear()
        
        if not self.download_queue and not self.download_running:
            # Empty state
            self.download_queue_ui.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No downloads in queue",
                        size=13,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            # Show current download
            if self.download_running and self.current_download_item:
                filename = self._get_download_filename(self.current_download_item)
                self.download_queue_ui.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DOWNLOAD, size=20, color=ft.Colors.GREEN_600),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(filename, size=13, weight=ft.FontWeight.W_500),
                                ft.Text("Downloading...", size=11, color=ft.Colors.GREEN_600),
                            ], spacing=2),
                            ft.Container(expand=True),
                            ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.Colors.GREEN_600),
                        ]),
                        bgcolor=ft.Colors.GREEN_50,
                        padding=10,
                        border_radius=6,
                    )
                )
            
            # Show queue
            for idx, item in enumerate(self.download_queue):
                filename = self._get_download_filename(item)
                file_size = self._get_download_filesize(item)
                
                self.download_queue_ui.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"#{idx + 1}", size=12, color=ft.Colors.GREY_600, width=35),
                            ft.Column([
                                ft.Text(filename, size=13),
                                ft.Text(file_size, size=11, color=ft.Colors.GREY_600),
                            ], spacing=2, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=18,
                                tooltip="Remove from queue",
                                on_click=lambda e, i=item: self.remove_from_download_queue(i),
                            ),
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=6,
                    )
                )
        
        if hasattr(self.page, 'update'):
            self.page.update()
    
    def _get_download_filename(self, item):
        """Extract filename from download item"""
        if isinstance(item, dict):
            if item.get('source') == 'manifest':
                return item.get('manifest', {}).get('original_file', {}).get('filename', 'Unknown')
            elif item.get('source') == 'remote':
                return item.get('file_name', 'Unknown')
        return 'Unknown'
    
    def _get_download_filesize(self, item):
        """Extract file size from download item"""
        if isinstance(item, dict):
            size = item.get('size', 0)
            return self._format_size(size)
        return '0 B'
    
    def remove_from_download_queue(self, item):
        """Remove a file from download queue"""
        if item in self.download_queue:
            self.download_queue.remove(item)
            self.update_download_queue_ui()
            filename = self._get_download_filename(item)
            self.show_snackbar(f"Removed {filename} from download queue", ft.Colors.ORANGE)
    
    def process_download_queue(self):
        """Process next file in download queue"""
        if not self.download_queue or self.download_running:
            return
        
        # Get next download
        next_item = self.download_queue.pop(0)
        self.current_download_item = next_item
        # Update queue UI to show new state
        self.update_download_queue_ui()
        # Start download
        self._start_download_internal(next_item)
    
    def process_upload_queue(self):
        """Process next file in upload queue - WITH HEALTH CHECK"""
        if not self.upload_queue or self.upload_running:
            return
        
        # PRODUCTION: Validate drives before upload
        if not self.validate_drives_before_upload():
            # Clear queue if drives are broken
            self.upload_queue.clear()
            self.update_queue_ui()
            return
        
        # Get next file
        next_file = self.upload_queue.pop(0)
        # Update queue UI to show new state
        self.update_queue_ui()
        self.start_upload(next_file)
    
    def start_upload(self, path: str):
        """Start upload with progress tracking - ENHANCED"""
        self.upload_running = True
        self.upload_cancelled = False
        self.current_upload_path = path
        self.upload_start_time = time.time()
        self.current_upload_stats = {
            "chunks": 0, 
            "total": 0, 
            "bytes_uploaded": 0, 
            "total_bytes": 0,
            "stage": "preparing"
        }
        
        # Show progress banner with all fields initialized
        self.upload_progress_banner.visible = True

        filename = Path(path).name
        self.upload_status_text.value = f"📦 Preparing: {filename}"
        self.upload_progress_bar.value = 0
        self.upload_speed_text.value = "Speed: --"
        self.upload_eta_text.value = "ETA: --"
        self.upload_chunk_text.value = "Starting..."

        self.page.update()

        def upload_thread():
            try:
                result = self.uploader.upload_file(
                    path,
                    progress_callback=self.upload_progress_callback
                )
                if result:
                    self.upload_complete(result, filename)
                else:
                    self.upload_error("Upload returned None - check logs")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                self.upload_error(str(ex))
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def upload_progress_callback(self, stage, current, total):
        """Update upload progress with real-time stats - COMPLETE UI"""
        if self.upload_cancelled:
            return
        
        self.current_upload_stats["stage"] = stage
        self.current_upload_stats["chunks"] = current
        self.current_upload_stats["total"] = total
        
        # Calculate speed and ETA
        elapsed = time.time() - self.upload_start_time if self.upload_start_time else 1
        
        try:
            filename = Path(self.current_upload_path).name if self.current_upload_path else "file"
            
            # Different UI for different stages
            if stage == "Hashing file":
                self.upload_status_text.value = f"🔐 Hashing: {filename}"
                self.upload_progress_bar.value = 0
                self.upload_speed_text.value = "Speed: --"
                self.upload_eta_text.value = "ETA: Calculating..."
                self.upload_chunk_text.value = "Preparing..."
            
            elif stage == "Splitting file" or stage == "Chunking file":
                progress_percent = (current / total * 100) if total > 0 else 0
                self.upload_status_text.value = f"✂️ Chunking: {filename}"
                self.upload_progress_bar.value = current / total if total > 0 else 0
                self.upload_speed_text.value = f"Progress: {progress_percent:.1f}%"
                self.upload_eta_text.value = f"Chunk {current}/{total}"
                self.upload_chunk_text.value = f"{progress_percent:.0f}% complete"
            
            elif stage == "Creating manifest":
                self.upload_status_text.value = f"📝 Creating manifest: {filename}"
                self.upload_progress_bar.value = 0.5
                self.upload_speed_text.value = "Speed: --"
                self.upload_eta_text.value = "ETA: --"
                self.upload_chunk_text.value = f"{total} chunks ready"
            
            elif stage == "Uploading chunks":
                progress_percent = (current / total * 100) if total > 0 else 0
                speed = current / elapsed if elapsed > 0 else 0
                remaining_chunks = total - current
                eta = remaining_chunks / speed if speed > 0 else 0
                
                # Calculate MB/s (assuming 95MB chunks)
                mb_speed = speed * 95
                
                self.upload_status_text.value = f"☁️ Uploading: {filename}"
                self.upload_progress_bar.value = current / total if total > 0 else 0
                self.upload_speed_text.value = f"Speed: {mb_speed:.1f} MB/s" if mb_speed > 0 else "Speed: Calculating..."
                self.upload_eta_text.value = f"ETA: {self._format_time(eta)}"
                self.upload_chunk_text.value = f"Chunk {current}/{total} ({progress_percent:.1f}%)"
            
            # Queue status (append to chunk text)
            if len(self.upload_queue) > 0:
                self.upload_chunk_text.value = f"{self.upload_chunk_text.value} • Queue: {len(self.upload_queue)}"
            
            # Force UI update
            if hasattr(self.page, 'update'):
                self.page.update()
        except Exception as e:
            pass  # Error handled

    
    pass

    
    def _format_time(self, seconds):
        """Format seconds to human readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"
    
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
                    self.show_snackbar(f"🗑️ Cleaned up old failed upload", ft.Colors.BLUE)
            except Exception as e:
                pass  # Error handled
            finally:
                # Clear the tracking variable
                self.reupload_old_manifest_id = None
        
        # Show success message
        self.show_snackbar(f"✓ Uploaded: {filename}", ft.Colors.GREEN)
        
        # Update queue UI
        self.update_queue_ui()
        
        # If this was a re-upload, force refresh the library cache
        if was_reupload:

            self.invalidate_manifests_cache()
            self.library_items = []  # Clear cache so it reloads fresh
        
        # Check if more files in queue
        if len(self.upload_queue) > 0:
            self.show_snackbar(f"Processing next file... ({len(self.upload_queue)} remaining)", ft.Colors.BLUE)
            self.process_upload_queue()
        else:
            # All done - hide progress card
            self.upload_progress_banner.visible = False
            self.show_snackbar("✓ All uploads completed!", ft.Colors.GREEN)
        
        # Auto-refresh current view
        current_tab = self.nav_rail.selected_index
        if current_tab == 0:
            self.show_dashboard()
        elif current_tab == 2:
            self.show_library()
        # If on upload tab and was a re-upload, also refresh library in background
        elif current_tab == 1 and hasattr(self, 'library_grid'):
            # Silently refresh library data without changing view
            self.invalidate_manifests_cache()
            self.refresh_library(load_remote=False)
        
        self.page.update()
    
    def upload_error(self, error_msg):
        """Handle upload error - ENHANCED with automatic retry system"""
        self.upload_running = False
        failed_file = self.current_upload_path
        self.current_upload_path = None
        filename = Path(failed_file).name if failed_file else "file"
        
        # Update queue UI
        self.update_queue_ui()
        
        # Check if it's a rate limit error (needs special handling)
        if "rate limit" in error_msg.lower():
            # Add ALL queued files + current file to failed_uploads for retry
            print(f"[RETRY] Rate limit hit! Adding {filename} and {len(self.upload_queue)} queued files to retry list")
            
            # Add current failed file
            if failed_file:
                retry_count = self._get_retry_count(failed_file)
                if retry_count < self.max_retries:
                    self.failed_uploads.append((failed_file, retry_count + 1, "Rate limit exceeded"))
                    print(f"[RETRY] {filename} will be retried (attempt {retry_count + 1}/{self.max_retries})")
            
            # Add all queued files to failed list (they haven't been attempted yet)
            for queued_file in self.upload_queue:
                self.failed_uploads.append((queued_file, 0, "Queued when rate limit hit"))
            
            # Clear queue
            self.upload_queue.clear()
            
            # Calculate retry delay (exponential backoff: 60s, 120s, 240s)
            retry_delay = self.retry_delay * (2 ** retry_count)
            
            self.show_snackbar(
                f"⚠️ Rate limit exceeded! {len(self.failed_uploads)} files will auto-retry in {retry_delay}s", 
                ft.Colors.ORANGE
            )
            
            # Schedule retry
            self._schedule_retry(retry_delay)
            
            self.upload_progress_banner.visible = False
            
        elif "authentication" in error_msg.lower() or "oauth" in error_msg.lower():
            # OAuth error - don't retry, needs user action

            self.show_snackbar(
                f"❌ Upload failed: {filename} - Authentication required. Please reconnect drive.", 
                ft.Colors.RED
            )
            # Clear queue - OAuth errors need user intervention
            self.upload_queue.clear()
            self.upload_progress_banner.visible = False
            
        else:
            # Other errors - retry with backoff
            retry_count = self._get_retry_count(failed_file) if failed_file else 0
            
            if retry_count < self.max_retries and failed_file:
                # Add to retry list
                self.failed_uploads.append((failed_file, retry_count + 1, error_msg))
                retry_delay = self.retry_delay * (2 ** retry_count)
                
                print(f"[RETRY] {filename} will be retried in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})")
                self.show_snackbar(
                    f"⚠️ Upload failed: {filename} - Will retry in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})", 
                    ft.Colors.ORANGE
                )
                
                # Schedule retry
                self._schedule_retry(retry_delay)
            else:
                # Max retries exceeded or no file to retry

                self.show_snackbar(f"❌ Upload failed after {self.max_retries} attempts: {filename}", ft.Colors.RED)
            
            # Continue with next file in queue
            if len(self.upload_queue) > 0:
                self.show_snackbar(f"Processing next file... ({len(self.upload_queue)} remaining)", ft.Colors.BLUE)
                self.process_upload_queue()
            else:
                self.upload_progress_banner.visible = False
        
        self.page.update()
    
    def _get_retry_count(self, file_path: str) -> int:
        """Get current retry count for a file"""
        for failed_file, retry_count, _ in self.failed_uploads:
            if failed_file == file_path:
                return retry_count
        return 0
    
    def _schedule_retry(self, delay_seconds: int):
        """Schedule retry of failed uploads after delay"""
        import threading
        import time
        
        def retry_after_delay():

            time.sleep(delay_seconds)
            
            if len(self.failed_uploads) > 0:
                print(f"[RETRY] Retrying {len(self.failed_uploads)} failed uploads...")
                
                # Move failed uploads back to queue
                retry_files = []
                for file_path, _, _ in self.failed_uploads:
                    retry_files.append(file_path)
                
                # Clear failed uploads list
                self.failed_uploads.clear()
                
                # Add to front of queue (priority)
                self.upload_queue = retry_files + self.upload_queue
                
                # Show notification
                self.show_snackbar(f"🔄 Retrying {len(retry_files)} failed uploads...", ft.Colors.BLUE)
                
                # Update queue UI
                self.update_queue_ui()
                
                # Start processing queue
                if not self.upload_running:
                    self.process_upload_queue()
        
        # Start retry thread
        threading.Thread(target=retry_after_delay, daemon=True).start()
    
    def cancel_upload(self):
        """Cancel ongoing upload - ENHANCED with cleanup"""
        if not self.upload_running:
            return
        
        self.upload_cancelled = True
        self.upload_running = False
        self.current_upload_path = None
        filename = Path(self.current_upload_path).name if self.current_upload_path else "file"
        
        # Update UI
        self.upload_status_text.value = f"🛑 Cancelling upload..."
        self.page.update()
        
        # Clear queue
        queue_count = len(self.upload_queue)
        self.upload_queue.clear()
        
        # Update queue UI
        self.update_queue_ui()
        
        # TODO: Cleanup chunks that were already uploaded
        # This requires:
        # 1. Track which chunks were uploaded (manifest tracking)
        # 2. Delete those chunks from Google Drive
        # 3. Delete local chunk files
        # 4. Delete manifest file if created
        
        # Hide progress card
        self.upload_progress_banner.visible = False
        self.show_snackbar(
            f"Upload cancelled: {filename}" + (f" | {queue_count} queued files cleared" if queue_count > 0 else ""),
            ft.Colors.ORANGE
        )
        self.page.update()
    
    def show_library(self):
        """Library gallery with search, sort, and filter"""
        # ALWAYS reload config to get latest drives
        self.config = ConfigManager()
        
        # Search, sort, and filter controls
        self.search_field = ft.TextField(
            label="Search files",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search_change,
            width=300,
        )
        
        self.sort_dropdown = ft.Dropdown(
            label="Sort by",
            options=[
                ft.dropdown.Option("name", "Name"),
                ft.dropdown.Option("size", "Size"),
                ft.dropdown.Option("date", "Date"),
                ft.dropdown.Option("chunks", "Chunks"),
            ],
            value="name",
            on_change=lambda e: self.refresh_library(),
            width=150,
        )
        
        self.filter_dropdown = ft.Dropdown(
            label="Filter",
            options=[
                ft.dropdown.Option("all", "All Files"),
                ft.dropdown.Option("images", "Images"),
                ft.dropdown.Option("documents", "Documents"),
                ft.dropdown.Option("videos", "Videos"),
                ft.dropdown.Option("others", "Others"),
            ],
            value="all",
            on_change=lambda e: self.refresh_library(),
            width=150,
        )
        
        controls_row = ft.Row([
            self.search_field,
            ft.Container(width=15),
            self.sort_dropdown,
            ft.Container(width=15),
            self.filter_dropdown,
            ft.Container(width=15),
            # Selection mode toggle
            ft.ElevatedButton(
                "Select Multiple",
                icon=ft.Icons.CHECK_BOX_OUTLINE_BLANK,
                on_click=lambda e: self.toggle_selection_mode(),
                bgcolor=ft.Colors.PURPLE_100 if self.selection_mode else None,
            ),
            ft.Container(width=15),
            ft.ElevatedButton(
                "Sync Remote Files",
                icon=ft.Icons.CLOUD_SYNC,
                tooltip="Load files from Google Drive (may be slow)",
                on_click=lambda e: self.sync_remote_files(),
            ),
            ft.Container(expand=True),  # Push clean button to right
            ft.OutlinedButton(
                "Clean Orphaned Files",
                icon=ft.Icons.CLEANING_SERVICES,
                icon_color=ft.Colors.ORANGE_600,
                tooltip="Delete manifests for files whose drives no longer exist",
                on_click=lambda e: self.clean_orphaned_manifests(),
            ),
        ])
        
        # Grid view for files - OPTIMIZED for smooth scrolling
        self.library_grid = ft.GridView(
            expand=True,
            runs_count=3,  # Reduced from 4 for better performance
            max_extent=280,  # Slightly larger cards, fewer renders
            child_aspect_ratio=0.85,
            spacing=12,
            run_spacing=12,
        )
        
        # Download queue UI
        self.download_queue_ui = ft.Column([], spacing=8)
        
        download_queue_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.QUEUE, size=20, color=ft.Colors.GREEN_600),
                        ft.Text("Download Queue", size=16, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=8),
                    self.download_queue_ui,
                ]),
                padding=15,
            ),
            elevation=2,
        )
        
        # Build content list dynamically
        content_list = [
            # Download progress banner (only visible when downloading)
            self.download_progress_banner,
            # Delete progress banner (visible during batch deletes)
            self.delete_progress_banner,
            ft.Container(height=10),  # Small gap after banners
        ]
        
        # Add download queue card if there are items
        if len(self.download_queue) > 0 or self.download_running:
            content_list.extend([
                ft.Container(download_queue_card),
                ft.Container(height=10),
            ])
        
        # Add library content
        content_list.extend([
            ft.Container(ft.Text("Library", size=28, weight=ft.FontWeight.BOLD)),
            ft.Container(height=20),
            ft.Container(controls_row),
            ft.Container(height=20),
        ])
        
        # Add batch action bar if in selection mode
        if self.selection_mode:
            # Count selected files and failed files for re-upload button
            selected_count = len(self.selected_files)
            failed_count = 0
            for item_id in self.selected_files:
                item = self._get_item_by_id(item_id)
                if item and item.get('source') == 'manifest' and item.get('status') == 'failed':
                    failed_count += 1
            
            # Show selection status
            if selected_count > 0:
                selection_text = f"{selected_count} file(s) selected"
                selection_icon = ft.Icons.CHECK_CIRCLE
                selection_color = ft.Colors.PURPLE_600
            else:
                selection_text = "No files selected - Click checkboxes to select"
                selection_icon = ft.Icons.CHECK_BOX_OUTLINE_BLANK
                selection_color = ft.Colors.GREY_600
            
            batch_action_bar = ft.Container(
                content=ft.Row([
                    ft.Icon(selection_icon, color=selection_color),
                    ft.Text(selection_text, size=16, weight=ft.FontWeight.BOLD, color=selection_color),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Select All",
                        icon=ft.Icons.SELECT_ALL,
                        on_click=lambda e: self.select_all_files(),
                        bgcolor=ft.Colors.PURPLE_100,
                    ),
                    ft.OutlinedButton(
                        "Clear",
                        icon=ft.Icons.CLEAR,
                        on_click=lambda e: self.clear_selection(),
                        disabled=(selected_count == 0),
                    ),
                    ft.ElevatedButton(
                        "Download All",
                        icon=ft.Icons.DOWNLOAD,
                        icon_color=ft.Colors.GREEN_600,
                        on_click=lambda e: self.batch_download(),
                        disabled=(selected_count == 0),
                    ),
                    ft.ElevatedButton(
                        "Delete All",
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.RED_600,
                        on_click=lambda e: self.batch_delete(),
                        disabled=(selected_count == 0),
                    ),
                    # Re-upload button only if there are failed files selected
                    ft.ElevatedButton(
                        f"Re-upload ({failed_count})",
                        icon=ft.Icons.UPLOAD,
                        icon_color=ft.Colors.PURPLE_600,
                        on_click=lambda e: self.batch_reupload(),
                        visible=(failed_count > 0),
                    ),
                ], spacing=10),
                padding=15,
                bgcolor=ft.Colors.PURPLE_50,
                border_radius=10,
                border=ft.border.all(2, ft.Colors.PURPLE_200),
            )
            content_list.extend([
                batch_action_bar,
                ft.Container(height=15),
            ])
        
        content_list.append(ft.Container(self.library_grid, expand=True))
        
        self.content_area.content = ft.Column(content_list, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Update queue UI
        self.update_download_queue_ui()
        
        # FAST: Load only manifests initially, skip slow remote queries
        self.refresh_library(load_remote=False)
        self.page.update()
    
    def sync_remote_files(self):
        """Manually sync files from Google Drive (slow operation)"""
        self.show_snackbar("Syncing files from Google Drive...", ft.Colors.BLUE)
        
        def _sync():
            try:
                self.refresh_library(load_remote=True)
                self.show_snackbar("Sync completed!", ft.Colors.GREEN)
            except Exception as ex:
                self.show_snackbar(f"Sync error: {ex}", ft.Colors.RED)
        
        threading.Thread(target=_sync, daemon=True).start()
    
    def toggle_selection_mode(self):
        """Toggle multi-select mode in library"""
        self.selection_mode = not self.selection_mode
        if not self.selection_mode:
            # Exiting selection mode - clear selections
            self.selected_files.clear()
        self.show_library()  # Refresh to show/hide checkboxes
    
    def toggle_file_selection(self, item):
        """Toggle selection of a file"""
        # Ignore if we're rebuilding the library
        if self.rebuilding_library:

            return
        
        print(f"[SELECTION] Toggle called for item: {item.get('file_name', 'Unknown')}")
            
        # Use unique identifier for item
        item_id = self._get_item_id(item)
        if item_id in self.selected_files:
            self.selected_files.remove(item_id)

        else:
            self.selected_files.append(item_id)

        print(f"[SELECTION] Total selected: {len(self.selected_files)}")
        
        # Refresh library to update visual state and action bar
        self.show_library()
    
    def select_all_files(self):
        """Select all visible files in library"""
        self.selected_files.clear()
        for item in self.library_items:
            item_id = self._get_item_id(item)
            self.selected_files.append(item_id)
        self.show_library()
    
    def clear_selection(self):
        """Clear all selections"""
        self.selected_files.clear()
        self.show_library()
    
    def _get_item_id(self, item):
        """Get unique identifier for a library item"""
        source = item.get('source', 'manifest')
        if source == 'manifest':
            manifest = item.get('manifest', {})
            # Prefer stable manifest_id; fall back to legacy 'id' or a composite of file metadata
            manifest_id = manifest.get('manifest_id') or manifest.get('id')
            if not manifest_id:
                of = manifest.get('original_file', {}) or {}
                # Composite is less ideal but ensures uniqueness across cards
                manifest_id = f"{of.get('filename','')}_{of.get('size','')}_{manifest.get('created_at','')}"
            return f"manifest_{manifest_id}"
        else:
            # Remote items: include remote_name if available for uniqueness across drives
            return f"remote_{item.get('remote_path', '')}_{item.get('drive_name', item.get('remote_name',''))}"
    
    def _get_item_by_id(self, item_id):
        """Get library item by its ID"""
        for item in self.library_items:
            if self._get_item_id(item) == item_id:
                return item
        return None
    
    def batch_download(self):
        """Add all selected files to download queue"""
        if not self.selected_files:
            self.show_snackbar("No files selected", ft.Colors.ORANGE)
            return
        
        count = 0
        for item_id in self.selected_files:
            item = self._get_item_by_id(item_id)
            if item:
                # Check if it's a failed file
                if item.get('source') == 'manifest' and item.get('status') == 'failed':
                    continue  # Skip failed files
                self.download_queue.append(item)
                count += 1
        
        if count > 0:
            self.update_download_queue_ui()
            self.show_snackbar(f"✓ {count} file(s) added to download queue", ft.Colors.GREEN)
            if not self.download_running:
                self.process_download_queue()
        else:
            self.show_snackbar("No valid files to download", ft.Colors.ORANGE)
        
        # Clear selection and exit selection mode
        self.selected_files.clear()
        self.selection_mode = False
        self.show_library()
    
    def batch_delete(self):
        """Delete all selected files"""
        if not self.selected_files:
            self.show_snackbar("No files selected", ft.Colors.ORANGE)
            return
        
        count = len(self.selected_files)
        
        def confirm_delete(e):
            # Close dialog immediately
            self.close_dialog(dialog)

            # Show progress banner
            self.delete_progress_banner.visible = True
            self.delete_status_text.value = f"Deleting {count} file(s)..."
            self.delete_progress_bar.value = 0
            self.page.update()

            ids_to_delete = list(self.selected_files)
            # Initialize cancel flag
            self._delete_cancel_flag = False

            def do_batch_delete():
                deleted = 0
                total = len(ids_to_delete)
                for idx, item_id in enumerate(ids_to_delete, start=1):
                    if getattr(self, "_delete_cancel_flag", False):
                        break
                    item = self._get_item_by_id(item_id)
                    if item:
                        try:
                            self._perform_delete(item)
                            deleted += 1
                        except Exception as ex:
                            pass  # Error handled

                    try:
                        self.delete_status_text.value = f"Deleting ({idx}/{total})..."
                        self.delete_progress_bar.value = idx / total
                        self.page.update()
                    except Exception:
                        pass

                # Hide progress
                self.delete_progress_banner.visible = False
                if getattr(self, "_delete_cancel_flag", False):
                    self.show_snackbar(f"✖ Delete cancelled. Completed {deleted}/{total}", ft.Colors.ORANGE)
                else:
                    self.show_snackbar(f"✓ {deleted}/{total} file(s) deleted", ft.Colors.GREEN)

                # Clear selection and exit selection mode
                self.selected_files.clear()
                self.selection_mode = False
                # Invalidate manifest cache as files changed
                self.invalidate_manifests_cache()
                self.show_library()

            threading.Thread(target=do_batch_delete, daemon=True).start()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Delete Multiple Files"),
            content=ft.Text(f"Are you sure you want to delete {count} file(s)? This will remove them from the library."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton(
                    f"Delete {count} File(s)",
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    on_click=confirm_delete,
                ),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def batch_reupload(self):
        """Re-upload all selected failed files"""
        if not self.selected_files:
            self.show_snackbar("No files selected", ft.Colors.ORANGE)
            return
        
        count = 0
        for item_id in self.selected_files:
            item = self._get_item_by_id(item_id)
            if item and item.get('source') == 'manifest' and item.get('status') == 'failed':
                manifest = item.get('manifest', {})
                file_path = manifest.get('original_file', {}).get('path', '')
                if file_path and os.path.exists(file_path):
                    self.upload_queue.append(file_path)
                    count += 1
        
        if count > 0:
            self.update_queue_ui()
            self.show_snackbar(f"✓ {count} file(s) added to upload queue", ft.Colors.GREEN)
            if not self.upload_running:
                self.process_upload_queue()
        else:
            self.show_snackbar("No valid failed files to re-upload", ft.Colors.ORANGE)
        
        # Clear selection and exit selection mode
        self.selected_files.clear()
        self.selection_mode = False
        self.show_library()
    
    def _perform_delete(self, item):
        """Perform actual deletion of an item (helper for batch delete)"""
        # Use the existing delete_library_file logic
        # We need to extract the deletion logic without the dialog
        source = item.get('source', 'manifest')
        
        if source == 'remote':
            # Delete remote file
            remote_name = item.get('remote_name')
            remote_path = item.get('remote_path')
            if remote_name and remote_path:
                success, error = self.rclone.delete_file(remote_name, remote_path)
                if not success:
                    print(f"[BATCH DELETE] Failed to delete {item.get('file_name')}: {error}")
        else:
            # Delete manifest + chunks
            manifest = item.get('manifest', {})
            if manifest:
                manifest_id = manifest.get('manifest_id', '')
                chunks = manifest.get('chunks', [])
                
                # Delete chunks from cloud
                for chunk_info in chunks:
                    drive_name = chunk_info.get('drive')
                    chunk_name = chunk_info.get('filename') or chunk_info.get('cloud_name')
                    
                    # Find drive config
                    drives = self.config.get_enabled_drives()
                    remote_name = None
                    for d in drives:
                        if d.get('name') == drive_name:
                            remote_name = d.get('remote_name')
                            break
                    
                    if remote_name and chunk_name:
                        upload_folder = self.config.app_settings.get('upload_folder', 'MultiDriveSplit')
                        remote_path = f"{upload_folder}/{chunk_name}"
                        self.rclone.delete_file(remote_name, remote_path)
                
                # Delete local manifest
                manifest_folder = self.config.get_manifest_folder()
                manifest_path = os.path.join(manifest_folder, f"{manifest_id}.json")
                if os.path.isfile(manifest_path):
                    try:
                        os.remove(manifest_path)
                    except Exception as e:
                        pass  # Error handled


                chunk_folder = self.config.app_settings.get('chunks_folder', 'chunks')
                for chunk_info in chunks:
                    chunk_name = chunk_info.get('filename') or chunk_info.get('cloud_name', '')
                    if chunk_name:
                        local_chunk = os.path.join(chunk_folder, chunk_name)
                        if os.path.isfile(local_chunk):
                            try:
                                os.remove(local_chunk)
                            except Exception as e:
                                pass  # Error handled


    def refresh_library(self, load_remote=False):
        """Refresh library with current search/sort/filter
        
        Args:
            load_remote: If True, queries files from Google Drive (SLOW)
                        If False, only shows local manifests (FAST)
        """
        # Reload config to keep drives in sync
        self.config = ConfigManager()

        manifests = self.get_cached_manifests()
        self.library_items = []

        current_drives = self.config.get_enabled_drives()
        drive_names = [d.get('name') for d in current_drives]
        drive_map = {d.get('name'): d for d in current_drives}

        # AUTO-DETECT: If no manifests, automatically load from remote
        if not manifests:

            load_remote = True
            self.show_snackbar("📡 No local files found. Loading from Google Drive...", ft.Colors.BLUE)

        # ALWAYS load manifests (uploaded files tracked locally) - FAST
        for manifest in manifests:
            chunks = manifest.get('chunks', [])
            if chunks:
                has_valid_drive = any(chunk.get('drive') in drive_names for chunk in chunks)
                if not has_valid_drive:
                    continue

            file_name = manifest.get('original_file', {}).get('filename', 'Unknown')
            primary_drive = chunks[0].get('drive') if chunks else ''

            self.library_items.append({
                "source": "manifest",
                "manifest": manifest,
                "file_name": file_name,
                "size": manifest.get('original_file', {}).get('size', 0),
                "chunks": manifest.get('total_chunks', 0),
                "status": manifest.get('status', ''),
                "date": manifest.get('created_at', ''),
                "file_type": self._get_file_type(file_name),
                "drive_name": primary_drive,
                "remote_name": drive_map.get(primary_drive, {}).get('remote_name', ''),
            })

        # OPTIONAL: Load remote files (SLOW - only when requested)
        if load_remote:
            configured_remotes = set(self.rclone.list_remotes())
            upload_folder = self.config.get_upload_folder() or ""
            
            for drive in current_drives:
                remote_name = drive.get('remote_name')
                if not remote_name:
                    continue
                if remote_name not in configured_remotes:
                    continue

                list_base_path = upload_folder
                remote_files = self.rclone.list_remote_files(
                    remote_name,
                    path=upload_folder,
                    recursive=True,
                    max_entries=300
                )

                if not remote_files:
                    list_base_path = ""
                    remote_files = self.rclone.list_remote_files(
                        remote_name,
                        path="",
                        recursive=False,
                        max_entries=200
                    )

                for remote_file in remote_files:
                    if remote_file.get("IsDir"):
                        continue

                    name = remote_file.get("Name", "")
                    if not name or name.endswith(".chunk"):
                        continue

                    relative_path = remote_file.get("Path") or name
                    base_path = list_base_path.rstrip('/') if list_base_path else ""
                    remote_path = f"{base_path}/{relative_path}" if base_path else relative_path
                    remote_path = remote_path.replace('\\', '/').replace('//', '/')

                    self.library_items.append({
                        "source": "remote",
                        "file_name": name,
                        "size": remote_file.get("Size", 0),
                        "chunks": None,
                        "status": "remote",
                        "date": remote_file.get("ModTime", ""),
                        "file_type": self._get_file_type(name),
                        "drive_name": drive.get('name', remote_name),
                        "remote_name": remote_name,
                        "remote_path": remote_path,
                    })

        # Apply search/filter/sort on combined items
        filtered_items = self.library_items

        search_query = self.search_field.value.lower() if hasattr(self, 'search_field') and self.search_field.value else ""
        if search_query:
            filtered_items = [
                item for item in filtered_items
                if search_query in item.get('file_name', '').lower()
                or search_query in (item.get('drive_name') or '').lower()
            ]

        filter_type = self.filter_dropdown.value if hasattr(self, 'filter_dropdown') else "all"
        if filter_type != "all":
            filtered_items = [item for item in filtered_items if item.get('file_type') == filter_type]

        sort_by = self.sort_dropdown.value if hasattr(self, 'sort_dropdown') else "name"
        if sort_by == "name":
            filtered_items.sort(key=lambda item: item.get('file_name', '').lower())
        elif sort_by == "size":
            filtered_items.sort(key=lambda item: item.get('size', 0), reverse=True)
        elif sort_by == "date":
            filtered_items.sort(key=lambda item: item.get('date', ''), reverse=True)
        elif sort_by == "chunks":
            filtered_items.sort(key=lambda item: item.get('chunks', 0) or 0, reverse=True)

        # Render cards - LIMIT for performance
        # Set flag to prevent checkbox on_change events during rebuild

        self.rebuilding_library = True
        
        self.library_grid.controls.clear()
        if not filtered_items:
            self.library_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OFF, size=48, color=ft.Colors.GREY_400),
                        ft.Text("No files found", size=14, color=ft.Colors.GREY_600),
                        ft.Text("Upload files or sync drives to see them here.", size=12, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    alignment=ft.alignment.center,
                    padding=30,
                )
            )
        else:
            # PERFORMANCE: Limit to 50 items for smooth UI
            max_display = 50
            items_to_show = filtered_items[:max_display]
            
            for item in items_to_show:
                self.library_grid.controls.append(self._create_file_card(item))
            
            # Show message if items were truncated
            if len(filtered_items) > max_display:
                remaining = len(filtered_items) - max_display
                self.library_grid.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.MORE_HORIZ, size=40, color=ft.Colors.GREY_400),
                            ft.Text(f"+{remaining} more files", size=12, color=ft.Colors.GREY_600),
                            ft.Text("Use search/filter to narrow results", size=10, color=ft.Colors.GREY_500),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                        alignment=ft.alignment.center,
                        padding=20,
                    )
                )

        # Clear flag after rebuild
        self.rebuilding_library = False

        self.page.update()

    def on_search_change(self, e):
        """Debounce search to avoid rebuilding on every keystroke"""
        try:
            if self.search_debounce_timer:
                self.search_debounce_timer.cancel()
        except Exception:
            pass
        def _go():
            self.refresh_library(load_remote=False)
        self.search_debounce_timer = threading.Timer(0.3, _go)
        self.search_debounce_timer.daemon = True
        self.search_debounce_timer.start()

    def get_cached_manifests(self):
        """Return manifests with a tiny in-memory cache to speed up UI reads"""
        now = time.time()
        if (not self._manifests_cache_dirty) and self.manifests_cache and (now - self.manifests_cache_ts) < self.manifests_cache_ttl:
            return self.manifests_cache
        try:
            manifests = self.manifest_manager.get_all_manifests()
        except Exception:
            manifests = []
        self.manifests_cache = manifests
        self.manifests_cache_ts = now
        self._manifests_cache_dirty = False
        return manifests

    def invalidate_manifests_cache(self):
        """Mark manifests cache dirty to force refresh on next read."""
        self._manifests_cache_dirty = True
    
    def clean_orphaned_manifests(self):
        """Delete manifest files whose drives no longer exist"""
        def confirm_clean(e):
            self.close_dialog(dialog)
            
            try:
                all_manifests = self.manifest_manager.get_all_manifests()
                current_drives = self.config.get_enabled_drives()
                drive_names = [d.get('name') for d in current_drives]
                
                # Find orphaned manifests
                orphaned = []
                for manifest in all_manifests:
                    chunks = manifest.get('chunks', [])
                    if chunks:
                        # Check if ANY chunk's drive still exists
                        has_valid_drive = any(chunk.get('drive') in drive_names for chunk in chunks)
                        if not has_valid_drive:
                            orphaned.append(manifest)
                
                if not orphaned:
                    self.show_snackbar("✓ No orphaned files found", ft.Colors.GREEN)
                    return
                
                # Delete orphaned manifest files
                deleted_count = 0
                manifest_folder = self.config.get_manifest_folder()
                for manifest in orphaned:
                    manifest_id = manifest.get('manifest_id', '')
                    if manifest_id:
                        manifest_path = os.path.join(manifest_folder, f"{manifest_id}.json")
                        try:
                            if os.path.exists(manifest_path):
                                os.remove(manifest_path)
                                deleted_count += 1
                        except Exception as ex:
                            pass  # Error handled


                self.show_snackbar(f"✓ Cleaned {deleted_count} orphaned file(s)", ft.Colors.GREEN)
                
                # Refresh library
                self.refresh_library()
                
            except Exception as ex:
                self.show_snackbar(f"Error cleaning orphaned files: {str(ex)}", ft.Colors.RED)

        all_manifests = self.manifest_manager.get_all_manifests()
        current_drives = self.config.get_enabled_drives()
        drive_names = [d.get('name') for d in current_drives]
        
        orphaned_count = 0
        for manifest in all_manifests:
            chunks = manifest.get('chunks', [])
            if chunks:
                has_valid_drive = any(chunk.get('drive') in drive_names for chunk in chunks)
                if not has_valid_drive:
                    orphaned_count += 1
        
        if orphaned_count == 0:
            self.show_snackbar("✓ No orphaned files to clean", ft.Colors.GREEN)
            return
        
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CLEANING_SERVICES, color=ft.Colors.ORANGE_600, size=32),
                ft.Text("Clean Orphaned Files"),
            ]),
            content=ft.Text(
                f"Found {orphaned_count} file(s) whose drives no longer exist.\n\n"
                "These manifest files will be permanently deleted.\n"
                "The actual files on cloud storage (if any) will NOT be deleted.\n\n"
                "Continue?",
                size=14,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton(
                    f"Clean {orphaned_count} File(s)",
                    bgcolor=ft.Colors.ORANGE_600,
                    color=ft.Colors.WHITE,
                    on_click=confirm_clean,
                ),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _create_file_card(self, item):
        """Create a SIMPLIFIED file card for better performance"""
        source = item.get('source', 'manifest')
        file_name = item.get('file_name', 'Unknown')
        file_size = self._format_size(item.get('size', 0))
        file_type = item.get('file_type', 'others')
        chunks = item.get('chunks', 0) or 0
        status = item.get('status', '')

        # Icon based on type - SIMPLIFIED
        icon_map = {
            "images": (ft.Icons.IMAGE, ft.Colors.BLUE_400),
            "documents": (ft.Icons.DESCRIPTION, ft.Colors.ORANGE_400),
            "videos": (ft.Icons.VIDEO_FILE, ft.Colors.RED_400),
            "others": (ft.Icons.INSERT_DRIVE_FILE, ft.Colors.GREY_500),
        }
        icon, icon_color = icon_map.get(file_type, (ft.Icons.INSERT_DRIVE_FILE, ft.Colors.GREY_500))

        # Truncate name
        display_name = file_name if len(file_name) <= 18 else file_name[:15] + "..."

        # SIMPLIFIED status chip
        if source == 'manifest':
            is_failed = status == 'failed'
            chip_text = "Failed" if is_failed else f"{chunks}x"
            chip_color = ft.Colors.RED_100 if is_failed else ft.Colors.GREEN_100
            download_disabled = is_failed
        else:
            chip_text = "Cloud"
            chip_color = ft.Colors.BLUE_50
            download_disabled = False
            icon_color = ft.Colors.PURPLE_300

        # Check if this file is selected
        item_id = self._get_item_id(item)
        is_selected = item_id in self.selected_files

        # Create card content
        card_content = [
            # File icon
            ft.Container(
                content=ft.Icon(icon, size=48, color=icon_color),
                alignment=ft.alignment.center,
            ),
            # File name with better text alignment
            ft.Container(
                content=ft.Text(
                    display_name, 
                    size=13, 
                    weight=ft.FontWeight.W_500, 
                    text_align=ft.TextAlign.CENTER, 
                    max_lines=2, 
                    overflow=ft.TextOverflow.ELLIPSIS
                ),
                alignment=ft.alignment.center,
                height=40,
            ),
            # File size
            ft.Text(file_size, size=11, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
            # Status chip
            ft.Container(
                content=ft.Chip(
                    label=ft.Text(chip_text, size=10), 
                    bgcolor=chip_color, 
                    height=24
                ),
                alignment=ft.alignment.center,
            ),
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            # Action buttons - 2 rows for better layout
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.VISIBILITY,
                    icon_size=18,
                    tooltip="Preview",
                    icon_color=ft.Colors.BLUE_600,
                    on_click=lambda e, i=item: self.preview_file(i),
                ),
                ft.IconButton(
                    icon=ft.Icons.DOWNLOAD,
                    icon_size=18,
                    tooltip="Download",
                    icon_color=ft.Colors.GREEN_600,
                    on_click=lambda e, i=item: self.download_file(i),
                    disabled=download_disabled,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
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
        ]

        # Add checkbox at the top if in selection mode
        if self.selection_mode:
            checkbox = ft.Checkbox(
                value=is_selected,
                disabled=True,  # Make checkbox read-only, control via GestureDetector
            )
            # Use GestureDetector for better click control
            checkbox_detector = ft.GestureDetector(
                content=checkbox,
                on_tap=lambda e, i=item: self.toggle_file_selection(i),
            )
            checkbox_container = ft.Container(
                content=checkbox_detector,
                alignment=ft.alignment.top_right,
            )
            # Insert checkbox at the beginning
            card_content.insert(0, checkbox_container)

        # IMPROVED card structure with better styling and delete button
        return ft.Card(
            content=ft.Container(
                content=ft.Column(card_content, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                padding=15,
                bgcolor=ft.Colors.PURPLE_50 if is_selected else None,  # Highlight selected cards
                border=ft.border.all(2, ft.Colors.PURPLE_400) if is_selected else None,
            ),
            elevation=2,
        )
    
    def _get_file_type(self, filename):
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return "images"
        elif ext in ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.pptx']:
            return "documents"
        elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
            return "videos"
        return "others"
    
    def preview_file(self, item):
        """Preview a library entry (manifest or remote file) - ENHANCED with chunk support"""
        # Remote files: show metadata + quick actions
        if isinstance(item, dict) and item.get('source') == 'remote':
            filename = item.get('file_name', 'Unknown')
            drive_label = item.get('drive_name') or item.get('remote_name', '')
            size = self._format_size(item.get('size', 0))
            modified = item.get('date', 'Unknown')

            info_content = ft.Column([
                ft.Icon(ft.Icons.CLOUD, size=64, color=ft.Colors.PURPLE_300),
                ft.Text(filename, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text(f"Drive: {drive_label}", size=12, color=ft.Colors.GREY_600),
                ft.Text(f"Path: {item.get('remote_path', '')}", size=11, color=ft.Colors.GREY_600),
                ft.Text(f"Size: {size}", size=12),
                ft.Text(f"Modified: {modified}", size=12),
                ft.Text("Click 'Download & Preview' to view this file.", size=12, color=ft.Colors.BLUE_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

            dialog = ft.AlertDialog(
                title=ft.Text(f"Remote File: {filename[:50]}"),
                content=ft.Container(content=info_content, width=450, padding=20),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self.close_dialog(dialog)),
                    ft.ElevatedButton(
                        "Download & Preview",
                        icon=ft.Icons.VISIBILITY,
                        on_click=lambda e, i=item: (self.close_dialog(dialog), self._download_and_preview_remote(i))
                    ),
                ],
            )

            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            return

        # Manifests - handle chunked files
        manifest = item.get('manifest') if isinstance(item, dict) and item.get('source') == 'manifest' else item
        if not manifest:
            self.show_snackbar("Unable to preview file", ft.Colors.RED)
            return
        
        filename = manifest.get('original_file', {}).get('filename', 'Unknown')
        file_path = manifest.get('original_file', {}).get('path', '')
        file_type = self._get_file_type(filename)
        
        # Check if original file still exists
        if os.path.exists(file_path):
            # Original file exists - preview directly
            self._show_preview_dialog(file_path, filename, file_type, manifest)
        else:
            # Original file doesn't exist - need to download and merge chunks
            self.show_snackbar("Preparing preview (downloading chunks)...", ft.Colors.BLUE)
            self._download_and_preview_chunked(manifest, filename, file_type)
    
    def _download_and_preview_remote(self, remote_item):
        """Download remote file and show preview"""
        self.show_snackbar("Downloading file for preview...", ft.Colors.BLUE)
        
        def download_and_show():
            try:
                import tempfile
                filename = remote_item.get('file_name', 'temp_file')
                remote_name = remote_item.get('remote_name', '')
                remote_path = remote_item.get('remote_path', '')
                
                # Create temp file
                temp_dir = tempfile.mkdtemp(prefix="preview_")
                temp_file = os.path.join(temp_dir, filename)
                
                # Download
                success, error = self.rclone.download_file(
                    remote_name=remote_name,
                    remote_path=remote_path,
                    local_path=temp_file
                )
                
                if success and os.path.exists(temp_file):
                    file_type = self._get_file_type(filename)
                    self._show_preview_dialog(temp_file, filename, file_type, None, temp_dir)
                    self.show_snackbar("Preview ready!", ft.Colors.GREEN)
                else:
                    self.show_snackbar(f"Failed to download file: {error}", ft.Colors.RED)
            except Exception as ex:
                self.show_snackbar(f"Preview error: {ex}", ft.Colors.RED)
        
        # Run in background
        threading.Thread(target=download_and_show, daemon=True).start()
    
    def _download_and_preview_chunked(self, manifest, filename, file_type):
        """Download chunks, merge, and preview"""
        def download_and_show():
            try:
                import tempfile
                # Create temp directory for preview
                temp_dir = tempfile.mkdtemp(prefix="preview_")
                temp_file = os.path.join(temp_dir, filename)
                
                # Download and merge chunks using downloader
                success = self.downloader.download_file(
                    manifest_id=manifest.get('id'),
                    output_path=temp_file,
                    progress_callback=None
                )
                
                if success and os.path.exists(temp_file):
                    self._show_preview_dialog(temp_file, filename, file_type, manifest, temp_dir)
                    self.show_snackbar("Preview ready!", ft.Colors.GREEN)
                else:
                    self.show_snackbar("Failed to download chunks for preview", ft.Colors.RED)
            except Exception as ex:
                self.show_snackbar(f"Preview error: {ex}", ft.Colors.RED)
        
        # Run in background
        threading.Thread(target=download_and_show, daemon=True).start()
    
    def _show_preview_dialog(self, file_path, filename, file_type, manifest=None, temp_dir=None):
        """Show preview dialog for a file"""
        preview_content = None
        
        # Image preview
        if file_type == "images":
            try:
                preview_content = ft.Column([
                    ft.Image(
                        src=file_path,
                        width=700,
                        height=500,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            except Exception as ex:
                preview_content = ft.Text(f"Could not load image: {str(ex)}", color=ft.Colors.RED)
        
        # Video preview - SMART SYSTEM PLAYER
        elif file_type == "videos":
            # Get video info
            file_size = self._format_size(os.path.getsize(file_path))
            file_size_bytes = os.path.getsize(file_path)
            
            # Determine if it's a temp file (for cleanup tracking)
            is_temp = temp_dir is not None
            
            preview_content = ft.Column([
                ft.Icon(ft.Icons.VIDEO_FILE, size=100, color=ft.Colors.BLUE_400),
                ft.Container(height=20),
                ft.Text("Video Preview", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(filename, size=14, text_align=ft.TextAlign.CENTER, max_lines=2),
                ft.Container(height=10),
                ft.Text(f"Size: {file_size}", size=12, color=ft.Colors.GREY_600),
                ft.Container(height=5),
                ft.Text(
                    "✓ Ready to play" if is_temp else "✓ File available locally",
                    size=11,
                    color=ft.Colors.GREEN_600,
                    italic=True
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "▶️ Play Video",
                    icon=ft.Icons.PLAY_CIRCLE_FILLED,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600,
                        padding=15,
                    ),
                    on_click=lambda e: self._open_with_default_app(file_path)
                ),
                ft.Container(height=10),
                ft.Text(
                    "Opens in your system's video player with full controls",
                    size=11,
                    color=ft.Colors.GREY_500,
                    italic=True,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=5),
                ft.Text(
                    "(seek, pause, volume, fullscreen, subtitles)",
                    size=10,
                    color=ft.Colors.GREY_400,
                    italic=True,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Audio preview - SMART SYSTEM PLAYER
        elif file_type == "others" and Path(filename).suffix.lower() in ['.mp3', '.wav', '.ogg', '.m4a', '.aac']:
            file_size = self._format_size(os.path.getsize(file_path))
            is_temp = temp_dir is not None
            
            preview_content = ft.Column([
                ft.Icon(ft.Icons.AUDIO_FILE, size=100, color=ft.Colors.PURPLE_400),
                ft.Container(height=20),
                ft.Text("Audio Preview", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(filename, size=14, text_align=ft.TextAlign.CENTER, max_lines=2),
                ft.Container(height=10),
                ft.Text(f"Size: {file_size}", size=12, color=ft.Colors.GREY_600),
                ft.Container(height=5),
                ft.Text(
                    "✓ Ready to play" if is_temp else "✓ File available locally",
                    size=11,
                    color=ft.Colors.GREEN_600,
                    italic=True
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "🎵 Play Audio",
                    icon=ft.Icons.PLAY_ARROW,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_600,
                        padding=15,
                    ),
                    on_click=lambda e: self._open_with_default_app(file_path)
                ),
                ft.Container(height=10),
                ft.Text(
                    "Opens in your system's audio player",
                    size=11,
                    color=ft.Colors.GREY_500,
                    italic=True,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Document preview
        elif file_type == "documents":
            ext = Path(filename).suffix.lower()
            if ext == '.txt':
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(10000)  # First 10000 chars
                    preview_content = ft.Column([
                        ft.Text(f"Text File: {filename}", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(content, size=12, selectable=True)
                            ], scroll=ft.ScrollMode.AUTO),
                            bgcolor=ft.Colors.GREY_100,
                            padding=15,
                            border_radius=10,
                            height=450,
                        )
                    ])
                except Exception as ex:
                    preview_content = ft.Text(f"Could not read text file: {ex}", color=ft.Colors.RED)
            else:
                file_size = self._format_size(os.path.getsize(file_path))
                preview_content = ft.Column([
                    ft.Icon(ft.Icons.DESCRIPTION, size=100, color=ft.Colors.ORANGE_400),
                    ft.Container(height=20),
                    ft.Text("Document File", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(filename, size=14, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=10),
                    ft.Text(f"Size: {file_size}", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Open with Default App",
                        icon=ft.Icons.OPEN_IN_NEW,
                        on_click=lambda e: self._open_with_default_app(file_path)
                    ),
                    ft.Container(height=10),
                    ft.Text(f"{ext.upper()} preview in app coming soon", size=11, color=ft.Colors.GREY_500, italic=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Other files
        else:
            file_size = self._format_size(os.path.getsize(file_path))
            preview_content = ft.Column([
                ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=100, color=ft.Colors.GREY_400),
                ft.Container(height=20),
                ft.Text("File Preview", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(filename, size=14, text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                ft.Text(f"Size: {file_size}", size=12, color=ft.Colors.GREY_600),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Open with Default App",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=lambda e: self._open_with_default_app(file_path)
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Create dialog
        def on_close(e):
            self.close_dialog(dialog)
            # Clean up temp files if any
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Preview: {filename[:50]}"),
            content=ft.Container(
                content=preview_content,
                width=750,
                height=550,
            ),
            actions=[
                ft.TextButton("Close", on_click=on_close),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _open_with_default_app(self, file_path):
        """Open file with system default application"""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
            
            self.show_snackbar("Opening file...", ft.Colors.GREEN)
        except Exception as ex:
            self.show_snackbar(f"Could not open file: {ex}", ft.Colors.RED)
    
    def show_file_details(self, item):
        """Show details for a library entry"""
        if isinstance(item, dict) and item.get('source') == 'remote':
            filename = item.get('file_name', 'Unknown')
            size = self._format_size(item.get('size', 0))
            drive_label = item.get('drive_name') or item.get('remote_name', '')
            remote_path = item.get('remote_path', '')
            modified = item.get('date', 'Unknown')

            dialog = ft.AlertDialog(
                title=ft.Text("Remote File Details"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Name: {filename}", size=14),
                        ft.Text(f"Drive: {drive_label}", size=14),
                        ft.Text(f"Path: {remote_path}", size=12, selectable=True),
                        ft.Text(f"Size: {size}", size=14),
                        ft.Text(f"Modified: {modified}", size=14),
                    ], tight=True, spacing=6),
                    width=420,
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self.close_dialog(dialog)),
                ],
            )

            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            return

        manifest = item.get('manifest') if isinstance(item, dict) and item.get('source') == 'manifest' else item
        if not manifest:
            self.show_snackbar("Unable to show file details", ft.Colors.RED)
            return

        file_hash = manifest.get('original_file', {}).get('hash', 'N/A')
        filename = manifest.get('original_file', {}).get('filename', 'Unknown')
        size = manifest.get('original_file', {}).get('size', 0)
        chunks = manifest.get('total_chunks', 0)
        created_at = manifest.get('created_at', 'Unknown')
        
        dialog = ft.AlertDialog(
            title=ft.Text("File Details"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Name: {filename}", size=14),
                    ft.Text(f"Size: {self._format_size(size)}", size=14),
                    ft.Text(f"Chunks: {chunks}", size=14),
                    ft.Text(f"Upload Date: {created_at}", size=14),
                    ft.Container(height=10),
                    ft.ExpansionTile(
                        title=ft.Text("File Hash", size=14),
                        controls=[ft.Text(file_hash, size=11, selectable=True)],
                    ),
                ], tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog(dialog)),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def delete_library_file(self, item):
        """Delete a file from library (manifest + cloud chunks)"""
        # Determine file name and type
        if isinstance(item, dict) and item.get('source') == 'remote':
            filename = item.get('file_name', 'Unknown')
            is_remote_only = True
            remote_name_to_delete = item.get('remote_name')
            remote_path_to_delete = item.get('remote_path')
            manifest = None
        else:
            manifest = item.get('manifest') if isinstance(item, dict) and item.get('source') == 'manifest' else item
            if not manifest:
                self.show_snackbar("Unable to delete file", ft.Colors.RED)
                return
            filename = manifest.get('original_file', {}).get('filename', 'Unknown')
            is_remote_only = False
            remote_name_to_delete = None
            remote_path_to_delete = None
        
        def confirm_delete(e):
            self.close_dialog(dialog)
            self.show_snackbar(f"🗑️ Deleting {filename}...", ft.Colors.ORANGE)
            
            def delete_thread():
                try:
                    if is_remote_only and remote_name_to_delete and remote_path_to_delete:
                        # Delete remote file only
                        success, error = self.rclone.delete_file(remote_name_to_delete, remote_path_to_delete)
                        if success:
                            self.show_snackbar(f"✓ Deleted {filename}", ft.Colors.GREEN)
                        else:
                            self.show_snackbar(f"❌ Delete failed: {error}", ft.Colors.RED)
                    elif manifest:
                        # Delete manifest + all cloud chunks
                        manifest_id = manifest.get('manifest_id', '')
                        chunks = manifest.get('chunks', [])
                        
                        # Delete chunks from cloud
                        failed_chunks = []
                        deleted_count = 0
                        for chunk_info in chunks:
                            drive_name = chunk_info.get('drive')
                            # Try both 'filename' (new manifests) and 'cloud_name' (old manifests)
                            chunk_name = chunk_info.get('filename') or chunk_info.get('cloud_name')


                            drives = self.config.get_enabled_drives()
                            remote_name = None
                            for d in drives:
                                if d.get('name') == drive_name:
                                    remote_name = d.get('remote_name')
                                    break
                            
                            if remote_name and chunk_name:
                                upload_folder = self.config.app_settings.get('upload_folder', 'MultiDriveSplit')
                                remote_path = f"{upload_folder}/{chunk_name}"

                                success, error = self.rclone.delete_file(remote_name, remote_path)
                                if success:
                                    deleted_count += 1

                                else:
                                    failed_chunks.append(chunk_name)

                            else:
                                failed_chunks.append(chunk_name or "unknown")

                        manifest_folder = self.config.get_manifest_folder()
                        manifest_path = os.path.join(manifest_folder, f"{manifest_id}.json")
                        if os.path.isfile(manifest_path):
                            try:
                                os.remove(manifest_path)
                            except Exception as manifest_ex:
                                pass  # Error handled


                        chunk_folder = self.config.app_settings.get('chunks_folder', 'chunks')
                        for chunk_info in chunks:
                            # Try both 'filename' and 'cloud_name' for backward compatibility
                            chunk_name = chunk_info.get('filename') or chunk_info.get('cloud_name', '')
                            if chunk_name:  # Only process if chunk_name is not empty
                                local_chunk = os.path.join(chunk_folder, chunk_name)
                                # Ensure we're not trying to delete the folder itself
                                if os.path.isfile(local_chunk):
                                    try:
                                        os.remove(local_chunk)
                                    except Exception as chunk_ex:
                                        pass  # Error handled


                        total_chunks = len(chunks)
                        if failed_chunks:
                            self.show_snackbar(
                                f"⚠️ Deleted {deleted_count}/{total_chunks} chunks. {len(failed_chunks)} failed. Check console for details.", 
                                ft.Colors.ORANGE
                            )
                        else:
                            self.show_snackbar(f"✓ Deleted {filename} completely ({deleted_count} chunks)", ft.Colors.GREEN)
                    
                    # Refresh library display
                    self.refresh_library()
                    self.page.update()
                    
                except Exception as ex:
                    error_msg = str(ex)
                    # Make error more user-friendly
                    if "Access is denied" in error_msg:
                        self.show_snackbar(f"❌ Access denied. Close any apps using the file and try again.", ft.Colors.RED)
                    else:
                        self.show_snackbar(f"❌ Delete error: {error_msg}", ft.Colors.RED)

            threading.Thread(target=delete_thread, daemon=True).start()
        
        # Confirmation dialog
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.DELETE_FOREVER, color=ft.Colors.RED_600, size=32),
                ft.Text("Delete File"),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"Are you sure you want to delete:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(height=5),
                    ft.Text(
                        filename,
                        size=13,
                        color=ft.Colors.BLUE_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "⚠️ This will PERMANENTLY delete:" if not is_remote_only else "This will PERMANENTLY delete the remote file.",
                        size=12,
                        color=ft.Colors.ORANGE_600,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "• All cloud chunks (bypasses trash)\n• Local manifest\n• Local chunks (if any)",
                        size=11,
                        color=ft.Colors.GREY_700,
                    ) if not is_remote_only else ft.Container(height=0),
                    ft.Container(height=5),
                    ft.Text(
                        "⚠️ Files will NOT go to trash - they are GONE forever!",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED,
                    ),
                    ft.Text(
                        "This action cannot be undone!",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED,
                    ),
                ], tight=True),
                width=400,
                padding=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton(
                    "Delete",
                    icon=ft.Icons.DELETE_FOREVER,
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    on_click=confirm_delete,
                ),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def download_file(self, item):
        """Add file to download queue"""
        filename = self._get_download_filename(item)
        
        # Validate before adding to queue
        if isinstance(item, dict) and item.get('source') == 'manifest':
            status = item.get('status', '')
            if status == 'failed':
                self.show_snackbar(f"❌ Cannot download: File upload failed", ft.Colors.RED)
                return
            
            chunks = item.get('manifest', {}).get('chunks', [])
            failed_chunks = [c for c in chunks if c.get('status') == 'failed']
            if failed_chunks:
                self.show_snackbar(
                    f"❌ Cannot download: {len(failed_chunks)} chunk(s) failed to upload",
                    ft.Colors.RED
                )
                return
        
        # Check if already in queue
        if item in self.download_queue:
            self.show_snackbar(f"⚠️ {filename} is already in the download queue", ft.Colors.ORANGE)
            return
        
        # Check if currently downloading
        if self.download_running and self.current_download_item == item:
            self.show_snackbar(f"⚠️ {filename} is currently being downloaded", ft.Colors.ORANGE)
            return
        
        # Add to queue
        self.download_queue.append(item)
        self.show_snackbar(f"✅ {filename} added to download queue", ft.Colors.GREEN)
        
        # Update queue UI
        self.update_download_queue_ui()
        
        # Refresh library view to show updated queue
        self.show_library()
        
        # Start download if not already running
        if not self.download_running:
            self.process_download_queue()
    
    def _start_download_internal(self, item):
        """Internal method to actually start downloading a file"""
        # Remote download path
        if isinstance(item, dict) and item.get('source') == 'remote':
            remote_name = item.get('remote_name')
            remote_path = item.get('remote_path') or item.get('file_name')
            filename = item.get('file_name', 'downloaded-file')

            if not remote_name or not remote_path:
                self.show_snackbar("❌ Cannot download: remote information missing", ft.Colors.RED)
                return

            download_folder = self.config.app_settings.get('downloads_folder', 'downloads')
            abs_download_folder = os.path.abspath(download_folder)
            
            # Track download state
            self.download_running = True
            self.download_cancelled = False
            
            # Show progress banner (simple version for remote files)
            self.download_progress_banner.visible = True
            self.download_status_text.value = f"⬇️ Downloading: {filename}"
            self.download_progress_bar.value = 0
            self.download_speed_text.value = "Downloading from cloud..."
            self.download_eta_text.value = "Please wait..."
            self.download_chunk_text.value = "Remote file"
            self.page.update()

            def remote_download_thread():
                try:
                    os.makedirs(download_folder, exist_ok=True)
                    output_path = os.path.join(download_folder, filename)

                    # Check if cancelled
                    if self.download_cancelled:
                        self.download_complete_cleanup(False, "Download cancelled")
                        return

                    success, error = self.rclone.download_file(remote_name, remote_path, output_path)
                    
                    if self.download_cancelled:
                        # Delete partial file
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        self.download_complete_cleanup(False, "Download cancelled")
                        return
                    
                    if success:
                        self.download_complete_cleanup(True, f"✓ Downloaded to: {abs_download_folder}\n{filename}")
                    else:
                        self.download_complete_cleanup(False, f"❌ Download failed: {error}")
                except Exception as ex:
                    self.download_complete_cleanup(False, f"❌ Download error: {str(ex)}")

            threading.Thread(target=remote_download_thread, daemon=True).start()
            return

        # Manifest-backed download
        manifest = item.get('manifest') if isinstance(item, dict) and item.get('source') == 'manifest' else item
        if not manifest:
            self.show_snackbar("Error: Invalid manifest", ft.Colors.RED)
            return

        filename = manifest.get('original_file', {}).get('filename', 'Unknown')
        manifest_id = manifest.get('manifest_id', '')

        if not manifest_id:
            self.show_snackbar("Error: Invalid manifest", ft.Colors.RED)
            return

        status = manifest.get('status', '')
        if status == 'failed':
            self.show_snackbar(f"❌ Cannot download: File upload failed", ft.Colors.RED)
            return

        chunks = manifest.get('chunks', [])
        failed_chunks = [c for c in chunks if c.get('status') == 'failed']
        if failed_chunks:
            self.show_snackbar(
                f"❌ Cannot download: {len(failed_chunks)} chunk(s) failed to upload",
                ft.Colors.RED
            )
            return

        download_folder = self.config.app_settings.get('downloads_folder', 'downloads')
        abs_download_folder = os.path.abspath(download_folder)

        # Track download state and initialize stats
        self.download_running = True
        self.download_cancelled = False
        self.download_start_time = time.time()
        self.current_download_stats = {
            "stage": "preparing",
            "chunks": 0,
            "total": len(chunks)
        }
        
        # Show progress banner
        self.download_progress_banner.visible = True
        self.download_status_text.value = f"📦 Preparing: {filename}"
        self.download_progress_bar.value = 0
        self.download_speed_text.value = "Speed: --"
        self.download_eta_text.value = "ETA: --"
        self.download_chunk_text.value = "Starting..."
        self.page.update()

        def download_thread():
            try:
                os.makedirs(download_folder, exist_ok=True)
                output_path = os.path.join(download_folder, filename)

                # Check if cancelled before starting
                if self.download_cancelled:
                    self.download_complete_cleanup(False, "Download cancelled")
                    return

                result = self.downloader.download_file(
                    manifest_id, 
                    output_path,
                    progress_callback=self.download_progress_callback,
                    chunk_callback=self.download_chunk_callback
                )
                
                if self.download_cancelled:
                    # Delete partial file
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    self.download_complete_cleanup(False, "Download cancelled")
                    return

                if result:
                    self.download_complete_cleanup(True, f"✓ Downloaded to: {abs_download_folder}\n{filename}")
                else:
                    self.download_complete_cleanup(False, f"❌ Download failed for {filename}")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                self.download_complete_cleanup(False, f"❌ Download error: {str(ex)}")

        threading.Thread(target=download_thread, daemon=True).start()
    
    def cancel_download(self):
        """Cancel ongoing download and optionally clear queue"""
        if not self.download_running:
            return
        
        self.download_cancelled = True
        
        # Cancel the downloader process
        if hasattr(self, 'downloader'):
            self.downloader.is_cancelled = True
        
        # Get filename for notification
        filename = "Unknown"
        if self.current_download_item:
            filename = self._get_download_filename(self.current_download_item)
        
        # Update UI
        self.download_status_text.value = f"🛑 Cancelling download..."
        self.page.update()
        
        # Clear queue
        queue_count = len(self.download_queue)
        self.download_queue.clear()
        
        # Update queue UI
        self.update_download_queue_ui()
        
        # Hide progress banner
        self.download_progress_banner.visible = False
        self.show_snackbar(
            f"Download cancelled: {filename}" + (f" | {queue_count} queued downloads cleared" if queue_count > 0 else ""),
            ft.Colors.ORANGE
        )
        self.page.update()
    
    def download_progress_callback(self, stage, current, total):
        """Update download progress with real-time stats"""
        if self.download_cancelled:
            return
        
        self.current_download_stats["stage"] = stage
        self.current_download_stats["chunks"] = current
        self.current_download_stats["total"] = total
        
        # Calculate speed and ETA
        elapsed = time.time() - self.download_start_time if self.download_start_time else 1
        
        try:
            # Different UI for different stages
            if stage == "Downloading chunks":
                progress_percent = (current / total * 100) if total > 0 else 0
                speed = current / elapsed if elapsed > 0 else 0
                remaining_chunks = total - current
                eta = remaining_chunks / speed if speed > 0 else 0
                
                # Calculate MB/s (assuming 95MB chunks)
                mb_speed = speed * 95
                
                self.download_status_text.value = f"⬇️ Downloading chunks..."
                self.download_progress_bar.value = current / total if total > 0 else 0
                self.download_speed_text.value = f"Speed: {mb_speed:.1f} MB/s" if mb_speed > 0 else "Speed: Calculating..."
                self.download_eta_text.value = f"ETA: {self._format_time(eta)}"
                self.download_chunk_text.value = f"Chunk {current}/{total} ({progress_percent:.1f}%)"
            
            elif stage == "Merging chunks":
                progress_percent = (current / total * 100) if total > 0 else 0
                self.download_status_text.value = f"🔗 Merging chunks..."
                self.download_progress_bar.value = current / total if total > 0 else 0
                self.download_speed_text.value = "Progress: Merging..."
                self.download_eta_text.value = f"Chunk {current}/{total}"
                self.download_chunk_text.value = f"{progress_percent:.0f}% merged"
            
            elif stage == "Verifying file":
                self.download_status_text.value = f"✅ Verifying file..."
                self.download_progress_bar.value = 0.9
                self.download_speed_text.value = "Almost done..."
                self.download_eta_text.value = "Verifying..."
                self.download_chunk_text.value = "Checking integrity..."
            
            elif stage == "Completed":
                self.download_status_text.value = f"✓ Download complete!"
                self.download_progress_bar.value = 1.0
                self.download_speed_text.value = "Done!"
                self.download_eta_text.value = ""
                self.download_chunk_text.value = f"All {total} chunks processed"
            
            # Force UI update
            if hasattr(self.page, 'update'):
                self.page.update()
        except Exception as e:
            pass  # Error handled


    def download_chunk_callback(self, chunk_index, total_chunks, status):
        """Callback for individual chunk download status"""
        # Optional: Could add per-chunk status tracking here
        pass
    
    def download_complete_cleanup(self, success, message):
        """Clean up and show message after download completes - WITH QUEUE PROCESSING"""
        self.download_running = False
        self.current_download_item = None
        self.download_progress_banner.visible = False
        
        if success:
            self.show_snackbar(message, ft.Colors.GREEN)
        else:
            self.show_snackbar(message, ft.Colors.RED if "error" in message.lower() else ft.Colors.ORANGE)
        
        # Update queue UI
        self.update_download_queue_ui()
        
        # Don't process next if download was cancelled (queue already cleared)
        if self.download_cancelled:
            self.download_cancelled = False  # Reset flag
            self.show_library()  # Refresh library view
            self.page.update()
            return
        
        # Check if more downloads in queue (only if not cancelled)
        if len(self.download_queue) > 0:
            self.show_snackbar(f"Processing next download... ({len(self.download_queue)} remaining)", ft.Colors.BLUE)
            self.process_download_queue()
        else:
            # All done
            self.show_snackbar("✓ All downloads completed!", ft.Colors.GREEN)
            # Refresh library view
            self.show_library()
        
        self.page.update()
    
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
        
        if not original_path:
            self.show_snackbar(f"❌ Cannot re-upload {file_name}: Original file path not found in manifest", ft.Colors.RED)
            return
        
        # Check if original file still exists
        if not os.path.exists(original_path):
            self.show_snackbar(f"❌ Cannot re-upload: Original file not found\n{original_path}", ft.Colors.RED)
            return
        
        # Check if file is already in queue
        if original_path in self.upload_queue:
            self.show_snackbar(f"⚠️ {file_name} is already in the upload queue", ft.Colors.ORANGE)
            return
        
        # Check if file is currently uploading
        if self.upload_running and self.current_upload_path == original_path:
            self.show_snackbar(f"⚠️ {file_name} is currently being uploaded", ft.Colors.ORANGE)
            return
        
        # Store the old manifest ID so we can delete it after successful re-upload
        old_manifest_id = manifest.get('manifest_id', '')
        if old_manifest_id:
            self.reupload_old_manifest_id = old_manifest_id

        self.upload_queue.append(original_path)
        self.show_snackbar(f"✅ {file_name} added to upload queue", ft.Colors.GREEN)
        
        # Update queue UI
        self.update_queue_ui()
        
        # Switch to Upload tab by calling show_upload
        self.show_upload()
        
        # Start processing if not already running
        if not self.upload_running:
            self.process_upload_queue()
    
    def close_dialog(self, dialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()
    
    def show_drives(self):
        """Drive manager with CRUD operations and logged accounts - INSTANT LOAD"""
        # ALWAYS reload config to get latest drives
        self.config = ConfigManager()
        
        try:
            drives = self.config.get_enabled_drives()
            # Ensure drives is a list
            if not isinstance(drives, list):
                drives = []
        except Exception as ex:
            pass  # Error handled


            drives = []
        
        # Logged-in accounts section - use cached list from config
        account_items = []
        
        # FAST: Just count drives from config, no subprocess calls
        for drive in drives:
            remote = drive.get('remote_name', '')
            if remote:
                account_items.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.GREEN_400, size=32),
                        title=ft.Text(remote, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text("Google Drive", size=12),
                        trailing=ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            tooltip="Remove Account",
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda e, r=remote: self.remove_rclone_remote(r),
                        ),
                    )
                )
        
        logged_accounts_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PEOPLE, size=28, color=ft.Colors.GREEN_600),
                        ft.Text("Logged-in Accounts", size=20, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Text(f"{len(account_items)} account(s)", size=12, color=ft.Colors.GREY_600),
                    ]),
                    ft.Divider(),
                    ft.Column(account_items, spacing=5, scroll=ft.ScrollMode.AUTO, height=150) if account_items else ft.Column([
                        ft.Text("No accounts logged in", color=ft.Colors.GREY_600),
                        ft.Container(height=10),
                        ft.Text("👇 Click 'Login with OAuth' below to add your first drive", 
                               size=12, color=ft.Colors.BLUE_600, italic=True),
                    ], spacing=5),
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        # Drive cards grid - increased height for all buttons
        drive_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=350,
            child_aspect_ratio=0.85,  # Reduced from 1.2 to give more vertical space
            spacing=15,
            run_spacing=15,
        )
        
        # Add existing drive cards
        for drive in drives:
            drive_card = self._create_drive_card(drive)
            drive_grid.controls.append(drive_card)
        
        # Add "Add Drive with OAuth" card
        add_drive_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=60, color=ft.Colors.BLUE_300),
                    ft.Container(height=15),
                    ft.Text("Add New Drive", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Login with OAuth",
                        icon=ft.Icons.LOGIN,
                        on_click=lambda _: self.add_drive_with_oauth(),
                    ),
                    ft.Container(height=5),
                    ft.TextButton(
                        "Import Existing Remotes",
                        icon=ft.Icons.SYNC,
                        on_click=lambda _: self.import_existing_remotes(),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30,
            ),
            elevation=2,
        )
        drive_grid.controls.append(add_drive_card)
        
        self.content_area.content = ft.Column([
            ft.Text("Drive Manager", size=28, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton(
                    "Refresh Storage Stats",
                    icon=ft.Icons.REFRESH,
                    tooltip="Load storage info from Google Drive",
                    on_click=lambda e: self.refresh_drive_stats_async(),
                ),
            ]),
            ft.Container(height=10),
            logged_accounts_card,
            ft.Container(height=20),
            ft.Container(drive_grid, expand=True),
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        self.page.update()
    
    def refresh_drive_stats_async(self):
        """Refresh drive stats in background without blocking UI"""
        self.show_snackbar("Loading storage stats...", ft.Colors.BLUE)
        
        def refresh_in_background():
            try:
                drives = self.config.get_enabled_drives()
                for drive in drives:
                    remote_name = drive.get('remote_name', '')
                    if remote_name:
                        # Force fresh query (not from cache)
                        stats = self.rclone.get_drive_stats(remote_name)
                        self.drive_stats_cache[remote_name] = stats
                
                # Update cache timestamp
                self.cache_timestamp = time.time()
                
                # Reload the drives view with new stats
                self.show_drives()
                self.show_snackbar("Stats refreshed!", ft.Colors.GREEN)
            except Exception as ex:
                pass  # Error handled


                self.show_snackbar(f"Error: {ex}", ft.Colors.RED)
        
        # Run in thread to avoid blocking
        threading.Thread(target=refresh_in_background, daemon=True).start()
    
    def _create_drive_card(self, drive):
        """Create a drive status card - NO BLOCKING NETWORK CALLS"""
        status = "Online" if drive.get('enabled', False) else "Offline"
        status_color = ft.Colors.GREEN if drive.get('enabled') else ft.Colors.GREY
        
        # Use cached stats ONLY - never block UI with fresh query
        remote_name = drive.get('remote_name', '')
        stats = self.drive_stats_cache.get(remote_name) if remote_name else None
        
        if stats and stats.get('total', 0) > 0:
            used_gb = stats.get('used', 0) / (1024 ** 3)
            total_gb = stats.get('total', 0) / (1024 ** 3)
            usage_percent = (stats.get('used', 0) / stats.get('total', 1)) * 100
        else:
            # Show placeholder if no cache available
            used_gb = 0
            total_gb = 0
            usage_percent = 0
        
        # Display text
        if total_gb > 0:
            storage_text = f"{used_gb:.1f} GB / {total_gb:.1f} GB"
        else:
            storage_text = "Click 'Refresh Stats' to load"
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CLOUD, size=32, color=status_color),
                        ft.Container(expand=True),
                        ft.Chip(label=ft.Text(status), bgcolor=ft.Colors.GREEN_100 if drive.get('enabled') else ft.Colors.GREY_200),
                    ]),
                    ft.Container(height=10),
                    ft.Text(drive.get('name', 'Unknown'), size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Remote: {drive.get('remote_name', 'N/A')}", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=15),
                    ft.Text(storage_text, size=14),
                    ft.ProgressBar(value=usage_percent/100 if total_gb > 0 else 0, color=ft.Colors.BLUE_600),
                    ft.Container(height=15),
                    # Better button layout - properly contained
                    ft.Row([
                        ft.ElevatedButton(
                            "Open",
                            icon=ft.Icons.OPEN_IN_NEW,
                            on_click=lambda e, d=drive: self.open_drive(d),
                            expand=True,
                        ),
                        ft.OutlinedButton(
                            "Remove",
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=lambda e, d=drive: self.remove_drive(d),
                            expand=True,
                        ),
                    ], spacing=10),
                    ft.Container(height=10),
                    # Wipe Data button - contained within card
                    ft.Container(
                        content=ft.OutlinedButton(
                            "Wipe Data",
                            icon=ft.Icons.DELETE_FOREVER,
                            icon_color=ft.Colors.RED,
                            on_click=lambda e, d=drive: self.wipe_drive(d),
                            expand=True,
                        ),
                        expand=True,
                    ),
                ], spacing=5, tight=True),
                padding=20,
            ),
            elevation=2,
        )
    
    def import_existing_remotes(self):
        """Import remotes from system rclone config"""
        import configparser
        import os
        
        # Try common rclone config locations
        possible_configs = [
            os.path.expanduser("~/.config/rclone/rclone.conf"),  # Linux/Mac
            os.path.join(os.environ.get('APPDATA', ''), 'rclone', 'rclone.conf'),  # Windows
        ]
        
        system_config_path = None
        for path in possible_configs:
            if os.path.exists(path):
                system_config_path = path
                break
        
        if not system_config_path:
            self.show_snackbar("No system rclone config found", ft.Colors.ORANGE)
            return
        
        # Parse system config
        try:
            config = configparser.ConfigParser()
            config.read(system_config_path)
            
            # Get list of Google Drive remotes
            gdrive_remotes = [
                section for section in config.sections()
                if config.has_option(section, 'type') and config.get(section, 'type') == 'drive'
            ]
            
            if not gdrive_remotes:
                self.show_snackbar("No Google Drive remotes found in system config", ft.Colors.ORANGE)
                return
            
            # Show selection dialog
            checkboxes = {}
            checkbox_controls = []
            
            for remote in gdrive_remotes:
                checkbox = ft.Checkbox(label=remote, value=False)
                checkboxes[remote] = checkbox
                checkbox_controls.append(checkbox)
            
            def import_selected(e):
                selected = [name for name, cb in checkboxes.items() if cb.value]
                
                if not selected:
                    self.show_snackbar("No remotes selected", ft.Colors.ORANGE)
                    return
                
                self.close_dialog(dialog)
                
                # Import selected remotes
                imported_count = 0
                app_config_path = self.config.get_rclone_config_path()
                
                try:
                    # Read both configs
                    system_cfg = configparser.ConfigParser()
                    system_cfg.read(system_config_path)
                    
                    app_cfg = configparser.ConfigParser()
                    if os.path.exists(app_config_path):
                        app_cfg.read(app_config_path)
                    
                    # Copy selected remotes
                    for remote in selected:
                        if not app_cfg.has_section(remote):
                            app_cfg.add_section(remote)
                        
                        for option in system_cfg.options(remote):
                            value = system_cfg.get(remote, option)
                            app_cfg.set(remote, option, value)
                        
                        # Add to drives.json
                        self.config.add_drive(
                            name=remote.title(),
                            remote_name=remote,
                            enabled=True
                        )
                        imported_count += 1
                    
                    # Write app config
                    with open(app_config_path, 'w') as f:
                        app_cfg.write(f)
                    
                    self.show_snackbar(f"Imported {imported_count} remote(s)", ft.Colors.GREEN)
                    self.show_drives()  # Refresh view
                    
                except Exception as ex:
                    self.show_snackbar(f"Import failed: {str(ex)}", ft.Colors.RED)
            
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Import Existing Remotes"),
                content=ft.Column([
                    ft.Text(f"Found {len(gdrive_remotes)} Google Drive remote(s):"),
                    ft.Container(height=10),
                    *checkbox_controls,
                ], tight=True, scroll=ft.ScrollMode.AUTO, height=300),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.close_dialog(dialog)),
                    ft.ElevatedButton("Import Selected", on_click=import_selected),
                ],
            )
            
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            
        except Exception as ex:
            self.show_snackbar(f"Failed to read config: {str(ex)}", ft.Colors.RED)
    
    def add_drive_with_oauth(self):
        """Add a new drive with direct OAuth (opens in browser)"""
        drive_name_field = ft.TextField(label="Drive Name", hint_text="My Google Drive")
        remote_name_field = ft.TextField(label="Remote Name", hint_text="mydrive")
        
        def start_oauth(e):
            name = drive_name_field.value
            remote = remote_name_field.value
            
            if not name or not remote:
                self.show_snackbar("Please fill all fields", ft.Colors.RED)
                return
            
            self.close_dialog(dialog)
            self.show_snackbar(f"Opening browser for OAuth...", ft.Colors.BLUE)
            
            # Run OAuth in thread (opens browser automatically)
            def oauth_thread():
                try:
                    import subprocess
                    rclone_path = self.config.get_rclone_path() or "rclone"
                    rclone_config = self.config.get_rclone_config_path()
                    rclone_config = self.config.get_rclone_config_path()
                    rclone_config = self.config.get_rclone_config_path()
                    
                    # Check if custom OAuth credentials exist
                    oauth_json_path = os.path.join('config', 'google_oauth.json')
                    
                    # Create rclone config command that opens browser
                    # Using --drive-scope=drive for full access
                    cmd = [
                        rclone_path,
                        "--config", rclone_config,
                        "config", "create", remote, "drive",
                        "--drive-scope=drive",
                        "--auto-confirm"
                    ]
                    
                    # If custom OAuth exists, use it
                    if os.path.exists(oauth_json_path):
                        try:
                            import json
                            with open(oauth_json_path, 'r') as f:
                                oauth_data = json.load(f)
                            
                            if 'installed' in oauth_data:
                                client_id = oauth_data['installed']['client_id']
                                client_secret = oauth_data['installed']['client_secret']
                            else:
                                client_id = oauth_data.get('client_id')
                                client_secret = oauth_data.get('client_secret')
                            
                            cmd.extend([
                                f"--drive-client-id={client_id}",
                                f"--drive-client-secret={client_secret}"
                            ])
                            self.show_snackbar("Using custom OAuth credentials", ft.Colors.PURPLE)
                        except Exception as ex:
                            pass  # Error handled


                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minutes for user to complete OAuth
                        **SUBPROCESS_FLAGS
                    )
                    
                    if result.returncode == 0:
                        # Add to drives.json
                        drives = self.config.get_enabled_drives()
                        new_drive = {
                            "name": name,
                            "remote_name": remote,
                            "enabled": True
                        }
                        drives.append(new_drive)
                        
                        # Save in correct format
                        drives_config_path = os.path.join('config', 'drives.json')
                        import json
                        
                        # Load full config to preserve settings
                        with open(drives_config_path, 'r') as f:
                            full_config = json.load(f)
                        
                        full_config['drives'] = drives
                        
                        with open(drives_config_path, 'w') as f:
                            json.dump(full_config, f, indent=2)
                        
                        self.show_snackbar(f"✓ Successfully added: {name}", ft.Colors.GREEN)
                        
                        # CRITICAL: Reload config to pick up new drive
                        self.config = ConfigManager()
                        
                        # Refresh drives view (where user currently is)
                        self.show_drives()
                    else:
                        self.show_snackbar(f"OAuth failed: {result.stderr}", ft.Colors.RED)
                
                except subprocess.TimeoutExpired:
                    self.show_snackbar("OAuth timed out", ft.Colors.RED)
                except Exception as ex:
                    self.show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
            
            threading.Thread(target=oauth_thread, daemon=True).start()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Add Drive with OAuth"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("This will open your browser for Google authentication", 
                           size=14, color=ft.Colors.GREY_700),
                    ft.Container(height=15),
                    drive_name_field,
                    ft.Container(height=10),
                    remote_name_field,
                    ft.Container(height=10),
                    ft.Text("⚠️ Complete the browser login within 5 minutes", 
                           size=12, color=ft.Colors.ORANGE_600),
                ], tight=True),
                width=450,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton(
                    "Start OAuth Login",
                    icon=ft.Icons.LOGIN,
                    on_click=start_oauth
                ),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def remove_rclone_remote(self, remote_name):
        """Remove an rclone remote (logged-in account)"""
        def confirm_remove(e):
            self.close_dialog(dialog)
            
            def remove_thread():
                try:
                    import subprocess
                    rclone_path = self.config.get_rclone_path() or "rclone"
                    rclone_config = self.config.get_rclone_config_path()

                    # Delete remote from rclone config
                    result = subprocess.run(
                        [rclone_path, "--config", rclone_config, "config", "delete", remote_name],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        **SUBPROCESS_FLAGS
                    )
                    
                    if result.returncode == 0:
                        # Also remove from drives.json if it exists there
                        try:
                            drives_config_path = os.path.join('config', 'drives.json')
                            import json
                            
                            with open(drives_config_path, 'r') as f:
                                full_config = json.load(f)
                            
                            drives = full_config.get('drives', [])
                            drives = [d for d in drives if d.get('remote_name') != remote_name]
                            full_config['drives'] = drives
                            
                            with open(drives_config_path, 'w') as f:
                                json.dump(full_config, f, indent=2)
                            
                            # Reload config
                            self.config = ConfigManager()
                        except Exception as ex:
                            pass  # Error handled


                        self.show_snackbar(f"✓ Removed account: {remote_name}", ft.Colors.ORANGE)
                        
                        # Auto-refresh ALL views
                        self.show_drives()  # Refresh drives
                        if self.nav_rail.selected_index == 0:
                            self.show_dashboard()
                        if self.nav_rail.selected_index == 2:
                            self.show_library()  # Refresh library to hide orphaned files
                    else:
                        self.show_snackbar(f"Failed to remove: {result.stderr}", ft.Colors.RED)
                
                except Exception as ex:
                    self.show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
            
            threading.Thread(target=remove_thread, daemon=True).start()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Remove Account"),
            content=ft.Text(
                f"Remove {remote_name} from rclone?\n\n"
                "This will log out this account and remove its configuration.",
                size=14,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Remove", bgcolor=ft.Colors.RED, on_click=confirm_remove),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def add_drive(self):
        """Add a new drive with dialog"""
        drive_name_field = ft.TextField(label="Drive Name", hint_text="My Drive")
        remote_name_field = ft.TextField(label="Remote Name (from rclone config)", hint_text="mydrive")
        
        def save_drive(e):
            name = drive_name_field.value
            remote = remote_name_field.value
            
            if not name or not remote:
                self.show_snackbar("Please fill all fields", ft.Colors.RED)
                return
            
            # Add drive to config
            try:
                drives = self.config.get_enabled_drives()
                new_drive = {
                    "name": name,
                    "remote_name": remote,
                    "enabled": True
                }
                drives.append(new_drive)
                
                # Save to config file
                drives_config_path = os.path.join('config', 'drives.json')
                import json
                with open(drives_config_path, 'w') as f:
                    json.dump(drives, f, indent=2)
                
                self.show_snackbar(f"Added drive: {name}", ft.Colors.GREEN)
                self.close_dialog(dialog)
                self.show_drives()  # Refresh view
            except Exception as ex:
                self.show_snackbar(f"Error adding drive: {str(ex)}", ft.Colors.RED)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Add New Drive"),
            content=ft.Container(
                content=ft.Column([
                    drive_name_field,
                    ft.Container(height=10),
                    remote_name_field,
                    ft.Container(height=10),
                    ft.Text("Make sure the remote exists in rclone config first!", 
                           size=12, color=ft.Colors.ORANGE_600),
                ], tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Add Drive", on_click=save_drive),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def open_drive(self, drive):
        """Open a drive (e.g., in browser)"""
        remote_name = drive.get('remote_name', '')
        self.show_snackbar(f"Opening {drive.get('name', 'drive')}...", ft.Colors.BLUE)
        
        # Try to open in browser (for Google Drive)
        try:
            # Run rclone to get drive link
            import subprocess
            # For now just show success message
            self.show_snackbar(f"Drive: {remote_name} (open in Google Drive manually)", ft.Colors.GREEN)
        except Exception as ex:
            self.show_snackbar(f"Could not open drive: {str(ex)}", ft.Colors.RED)
    
    def remove_drive(self, drive):
        """Remove a drive from configuration"""
        def confirm_remove(e):
            self.close_dialog(dialog)
            
            try:
                # Read current drives
                drives_config_path = os.path.join('config', 'drives.json')
                import json
                
                with open(drives_config_path, 'r') as f:
                    full_config = json.load(f)
                
                drives = full_config.get('drives', [])
                
                # Remove the drive by comparing both name and remote_name
                original_count = len(drives)
                drives = [d for d in drives if not (
                    d.get('name') == drive.get('name') and 
                    d.get('remote_name') == drive.get('remote_name')
                )]
                
                if len(drives) < original_count:
                    # Save updated drives
                    full_config['drives'] = drives
                    with open(drives_config_path, 'w') as f:
                        json.dump(full_config, f, indent=2)
                    
                    self.show_snackbar(f"✓ Removed {drive.get('name', 'drive')}", ft.Colors.ORANGE)
                    
                    # Reload config and refresh ALL views
                    self.config = ConfigManager()
                    self.show_drives()  # Refresh drives view
                    
                    # Refresh dashboard if visible
                    if self.nav_rail.selected_index == 0:
                        self.show_dashboard()
                    
                    # Refresh library if visible (to hide orphaned files)
                    if self.nav_rail.selected_index == 2:
                        self.show_library()
                else:
                    self.show_snackbar("Drive not found in configuration", ft.Colors.RED)
                    
            except Exception as ex:
                self.show_snackbar(f"Error removing drive: {str(ex)}", ft.Colors.RED)

        dialog = ft.AlertDialog(
            title=ft.Text("Remove Drive"),
            content=ft.Text(
                f"Remove {drive.get('name', 'this drive')} from configuration?\n\n"
                "This will NOT delete any data on the cloud.",
                size=14,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Remove", bgcolor=ft.Colors.ORANGE, on_click=confirm_remove),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def wipe_drive(self, drive):
        """Wipe all data from a drive with confirmation"""
        def confirm_wipe(e):
            self.close_dialog(dialog)
            self.show_snackbar(f"Wiping {drive.get('name', 'drive')}...", ft.Colors.RED)
            
            # Run wipe in thread
            def wipe_thread():
                try:
                    remote_name = drive.get('remote_name', '')
                    upload_folder = self.config.app_settings.get('upload_folder', 'MultiDriveSplit')
                    remote_path = f"{remote_name}:{upload_folder}"

                    import subprocess
                    rclone_path = self.config.get_rclone_path() or "rclone"
                    
                    result = subprocess.run(
                        [
                            rclone_path, 
                            "--config", self.config.get_rclone_config_path(), 
                            "delete",  # Delete contents only (keeps folder)
                            remote_path,
                            "--drive-use-trash=false",  # Permanent delete (bypass trash)
                            "-v"  # Verbose
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,  # Increased timeout for large folders
                        **SUBPROCESS_FLAGS
                    )


                    if result.returncode == 0:
                        # Also clear local manifests for this drive
                        drive_name = drive.get('name', '')
                        if drive_name:
                            manifests = self.manifest_manager.get_all_manifests()
                            manifest_folder = self.config.get_manifest_folder()
                            deleted_count = 0
                            
                            for manifest in manifests:
                                chunks = manifest.get('chunks', [])
                                # Check if this manifest is for the wiped drive
                                if any(chunk.get('drive') == drive_name for chunk in chunks):
                                    manifest_id = manifest.get('manifest_id', '')
                                    if manifest_id:
                                        manifest_path = os.path.join(manifest_folder, f"{manifest_id}.json")
                                        try:
                                            if os.path.exists(manifest_path):
                                                os.remove(manifest_path)
                                                deleted_count += 1
                                        except Exception as ex:
                                            pass  # Error handled


                        pass


                        self.show_snackbar(
                            f"✓ Wiped {upload_folder} folder and cleared {deleted_count} local manifests", 
                            ft.Colors.GREEN
                        )
                        # Refresh drive stats and library
                        self.clear_drive_cache()
                        self.refresh_library()
                    else:
                        self.show_snackbar(f"❌ Wipe failed: {result.stderr}", ft.Colors.RED)
                except Exception as ex:
                    self.show_snackbar(f"❌ Wipe error: {str(ex)}", ft.Colors.RED)

            threading.Thread(target=wipe_thread, daemon=True).start()
        
        # Get upload folder name
        upload_folder = self.config.app_settings.get('upload_folder', 'MultiDriveSplit')
        
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED, size=32),
                ft.Text("⚠️ Wipe Upload Folder"),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"This will PERMANENTLY DELETE all files from:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Text(
                            f"📁 {drive.get('name', 'Drive')} → {upload_folder}/",
                            size=13,
                            color=ft.Colors.BLUE_600,
                        ),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=10,
                        border_radius=6,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "What gets deleted:",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "• All chunk files in upload folder\n"
                        "• All files you uploaded via this app\n"
                        "• Cannot be recovered (bypasses trash)",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "✅ Safe: Other folders and files NOT touched",
                        size=12,
                        color=ft.Colors.GREEN_700,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "⚠️ This action cannot be undone!",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED,
                    ),
                ], tight=True),
                width=450,
                padding=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton(
                    "Wipe Upload Folder",
                    icon=ft.Icons.DELETE_FOREVER,
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                    on_click=confirm_wipe,
                ),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    
    def show_settings(self):
        """Settings page"""
        # OAuth credentials card with file upload
        oauth_json_path = os.path.join('config', 'google_oauth.json')
        oauth_status = "Custom credentials loaded" if os.path.exists(oauth_json_path) else "Using default rclone credentials"
        oauth_color = ft.Colors.GREEN if os.path.exists(oauth_json_path) else ft.Colors.GREY_600
        
        oauth_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.KEY, size=32, color=ft.Colors.BLUE_600),
                        ft.Text("Custom OAuth Credentials", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=15),
                    ft.Text(
                        "Upload your own Google OAuth client_id and client_secret JSON to avoid rate limits.\n"
                        "Get it from: https://console.cloud.google.com/apis/credentials",
                        size=13, color=ft.Colors.GREY_700
                    ),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if os.path.exists(oauth_json_path) else ft.Icons.INFO,
                            color=oauth_color,
                            size=20
                        ),
                        ft.Text(oauth_status, size=13, color=oauth_color, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=15),
                    ft.Row([
                        ft.ElevatedButton(
                            "Upload OAuth JSON",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=lambda _: self.upload_oauth_file(),
                        ),
                        ft.Container(width=10),
                        ft.OutlinedButton(
                            "Clear Custom Creds",
                            icon=ft.Icons.CLEAR,
                            on_click=lambda _: self.clear_oauth_creds(),
                        ),
                    ], spacing=10),
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        # Download folder card
        try:
            current_folder = self.config.app_settings.get('downloads_folder', 'Not set')
        except:
            current_folder = "Not set"
        download_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FOLDER, size=32, color=ft.Colors.ORANGE_600),
                        ft.Text("Download Folder", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=15),
                    ft.Text("Current folder:", size=14, color=ft.Colors.GREY_600),
                    ft.Text(current_folder, size=12, weight=ft.FontWeight.BOLD),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        "Change Folder",
                        icon=ft.Icons.EDIT,
                        on_click=lambda _: self.change_download_folder(),
                    ),
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        # App settings card
        settings = self.config.app_settings
        app_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SETTINGS, size=32, color=ft.Colors.PURPLE_600),
                        ft.Text("App Settings", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=15),
                    ft.Text(f"Chunk Size: {settings.get('chunk_size_mb', 95)} MB", size=14),
                    ft.Text(f"Max Concurrent Uploads: {settings.get('max_concurrent_uploads', 3)}", size=14),
                    ft.Text(f"Chunks Folder: {settings.get('chunks_folder', 'chunks')}", size=14),
                    ft.Text(f"Manifests Folder: {settings.get('manifests_folder', 'manifests')}", size=14),
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        # Account switching helper card
        account_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SWITCH_ACCOUNT, size=32, color=ft.Colors.RED_600),
                        ft.Text("Account Management", size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Container(height=15),
                    ft.Text(
                        "⚠️ Switching Google accounts? Clear local data to avoid seeing files from the old account.",
                        size=13, color=ft.Colors.ORANGE_700
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "This will:\n• Clear all manifests (local upload records)\n• Clear drive stats cache\n• Clear chunks folder\n• Keep your drives configuration",
                        size=12, color=ft.Colors.GREY_600
                    ),
                    ft.Container(height=15),
                    ft.Row([
                        ft.ElevatedButton(
                            "Clear All Local Data",
                            icon=ft.Icons.DELETE_FOREVER,
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.RED_600,
                            on_click=lambda _: self.clear_all_local_data(),
                        ),
                        ft.Container(width=10),
                        ft.OutlinedButton(
                            "Refresh Cache Only",
                            icon=ft.Icons.REFRESH,
                            on_click=lambda _: self.refresh_cache(),
                        ),
                    ]),
                ], spacing=10),
                padding=20,
            ),
            elevation=2,
        )
        
        self.content_area.content = ft.Column([
            ft.Text("Settings", size=28, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            oauth_card,
            ft.Container(height=15),
            download_card,
            ft.Container(height=15),
            app_card,
            ft.Container(height=15),
            account_card,
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        self.page.update()
    
    def upload_oauth_file(self):
        """Upload OAuth JSON file"""
        oauth_file_picker = ft.FilePicker(on_result=self.oauth_file_selected)
        self.page.overlay.append(oauth_file_picker)
        self.page.update()
        oauth_file_picker.pick_files(
            allowed_extensions=["json"],
            dialog_title="Select Google OAuth JSON"
        )
    
    def oauth_file_selected(self, e: ft.FilePickerResultEvent):
        """Handle OAuth JSON file selection"""
        if e.files:
            selected_file = e.files[0]
            
            try:
                import json
                import shutil
                
                # Read and validate JSON
                with open(selected_file.path, 'r') as f:
                    oauth_data = json.load(f)
                
                # Validate it has required fields
                if 'installed' in oauth_data:
                    if 'client_id' not in oauth_data['installed'] or 'client_secret' not in oauth_data['installed']:
                        self.show_snackbar("Invalid OAuth JSON format", ft.Colors.RED)
                        return
                elif 'client_id' not in oauth_data or 'client_secret' not in oauth_data:
                    self.show_snackbar("Invalid OAuth JSON format", ft.Colors.RED)
                    return
                
                # Copy to config folder
                oauth_json_path = os.path.join('config', 'google_oauth.json')
                shutil.copy(selected_file.path, oauth_json_path)
                
                self.show_snackbar("Custom OAuth credentials uploaded successfully!", ft.Colors.GREEN)
                self.show_settings()  # Refresh to show updated status
                
            except json.JSONDecodeError:
                self.show_snackbar("Invalid JSON file", ft.Colors.RED)
            except Exception as ex:
                self.show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
    
    def clear_oauth_creds(self):
        """Clear custom OAuth credentials"""
        oauth_json_path = os.path.join('config', 'google_oauth.json')
        if os.path.exists(oauth_json_path):
            try:
                os.remove(oauth_json_path)
                self.show_snackbar("Custom OAuth credentials removed. Using rclone defaults.", ft.Colors.ORANGE)
                self.show_settings()  # Refresh
            except Exception as ex:
                self.show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        else:
            self.show_snackbar("No custom credentials to remove", ft.Colors.GREY_600)
    
    def change_download_folder(self):
        """Change download folder"""
        folder_picker = ft.FilePicker(on_result=self.download_folder_selected)
        self.page.overlay.append(folder_picker)
        self.page.update()
        folder_picker.get_directory_path(dialog_title="Select Download Folder")
    
    def download_folder_selected(self, e: ft.FilePickerResultEvent):
        """Handle download folder selection"""
        if e.path:
            try:
                # Update config
                self.config.app_settings['downloads_folder'] = e.path
                
                # Save to config file
                config_path = os.path.join('config', 'app_settings.json')
                import json
                with open(config_path, 'w') as f:
                    json.dump(self.config.app_settings, f, indent=2)
                
                self.show_snackbar(f"Download folder set to: {e.path}", ft.Colors.GREEN)
                self.show_settings()  # Refresh to show new path
            except Exception as ex:
                self.show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
    
    def clear_all_local_data(self):
        """Clear all local manifests and cache when switching accounts"""
        try:
            import shutil
            
            # Ask for confirmation
            confirm_dialog = ft.AlertDialog(
                title=ft.Text("⚠️ Clear All Local Data?"),
                content=ft.Text(
                    "This will delete:\n"
                    "• All manifests (upload records)\n"
                    "• All chunks in chunks folder\n"
                    "• Drive stats cache\n\n"
                    "Your drives configuration will be kept.\n\n"
                    "Are you sure?",
                    size=14
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(confirm_dialog)),
                    ft.ElevatedButton(
                        "Yes, Clear All",
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE,
                        on_click=lambda e: self.do_clear_all_data(confirm_dialog)
                    ),
                ],
            )
            self.page.overlay.append(confirm_dialog)
            confirm_dialog.open = True
            self.page.update()
        except Exception as ex:
            self.show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
    
    def do_clear_all_data(self, dialog):
        """Actually perform the data clear"""
        try:
            import shutil
            
            # Close dialog first
            self.close_dialog(dialog)
            
            # Clear manifests folder
            manifests_folder = self.config.app_settings.get('manifests_folder', 'manifests')
            if os.path.exists(manifests_folder):
                shutil.rmtree(manifests_folder)
                os.makedirs(manifests_folder)
            
            # Clear chunks folder
            chunks_folder = self.config.app_settings.get('chunks_folder', 'chunks')
            if os.path.exists(chunks_folder):
                shutil.rmtree(chunks_folder)
                os.makedirs(chunks_folder)
            
            # Clear cache
            self.clear_drive_cache()
            
            self.show_snackbar(
                "✓ All local data cleared! Library and cache have been reset.",
                ft.Colors.GREEN
            )
            
            # Refresh current view
            self.show_dashboard()
            
        except Exception as ex:
            self.show_snackbar(f"Error clearing data: {str(ex)}", ft.Colors.RED)
    
    def refresh_cache(self):
        """Just refresh the drive stats cache"""
        self.clear_drive_cache()
        self.show_snackbar("✓ Cache cleared! Drive stats will be refreshed.", ft.Colors.GREEN)
        self.show_dashboard()
    
    def toggle_theme(self, e):
        self.page.theme_mode = ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        self.page.update()
    
    def refresh_current(self):
        self.show_dashboard()
    
    def show_snackbar(self, message, bgcolor=ft.Colors.BLUE_400):
        """Show a snackbar notification"""
        snackbar = ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor)
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def check_drive_health(self, remote_name: str) -> dict:
        """
        Check if a drive is healthy and can authenticate
        
        Returns:
            dict with keys: 'status' ('HEALTHY', 'OAUTH_ERROR', 'ERROR'), 'message', 'error_details'
        """
        import subprocess
        
        cmd = [
            self.rclone.rclone_path,
            "lsf",
            f"{remote_name}:",
            "--max-depth", "1",
            "--config", self.config.get_rclone_config_path()
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                **SUBPROCESS_FLAGS
            )
            
            error_text = result.stderr.lower()
            
            # Only flag CRITICAL OAuth errors that definitely need user action
            if "unauthorized_client" in error_text or "couldn't fetch token" in error_text:
                return {
                    'status': 'OAUTH_ERROR',
                    'message': '🔒 Authentication required',
                    'error_details': result.stderr
                }
            elif "rate limit" in error_text or "ratelimitexceeded" in error_text:
                return {
                    'status': 'RATE_LIMIT',
                    'message': '⏳ Rate limit exceeded',
                    'error_details': result.stderr
                }
            elif result.returncode == 0:
                return {
                    'status': 'HEALTHY',
                    'message': '✅ Connected',
                    'error_details': ''
                }
            else:
                # For other errors, treat as healthy (might be transient)
                # Only block upload for OAuth/rate limit errors
                return {
                    'status': 'HEALTHY',
                    'message': '✅ Connected',
                    'error_details': ''
                }
        except subprocess.TimeoutExpired:
            return {
                'status': 'TIMEOUT',
                'message': '⏱️ Connection timeout',
                'error_details': 'Request timed out after 10 seconds'
            }
        except Exception as e:
            return {
                'status': 'UNKNOWN',
                'message': f'❓ Unknown error',
                'error_details': str(e)
            }
    
    def check_all_drives_health(self) -> dict:
        """Check health of all enabled drives"""
        drives = self.config.get_enabled_drives()
        health_status = {}
        
        for drive in drives:
            remote_name = drive.get('remote', '')
            health = self.check_drive_health(remote_name)
            health_status[remote_name] = health
        
        return health_status
    
    def show_oauth_error_dialog(self, remote_name: str, error_details: str):
        """Show user-friendly OAuth error dialog with recovery options"""
        
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        def reconnect_drive(e):
            """Guide user to reconnect the drive"""
            close_dialog(e)
            
            import webbrowser
            
            def close_instructions_dialog(e):
                instructions_dialog.open = False
                self.page.update()
            
            # Show instructions
            instructions_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Reconnect {remote_name}", size=18, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("To fix the authentication issue:", weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Text("1. Open PowerShell/Terminal", size=13),
                        ft.Text("2. Run this command:", size=13),
                        ft.Container(
                            content=ft.Text(
                                f"rclone config reconnect {remote_name}: --config config/rclone.conf",
                                size=12,
                                selectable=True
                            ),
                            bgcolor=ft.Colors.GREY_900,
                            padding=10,
                            border_radius=5
                        ),
                        ft.Text("3. Your browser will open - log in to Google", size=13),
                        ft.Text("4. Come back to the app and try upload again", size=13),
                        ft.Container(height=15),
                        ft.Text("Alternative: Delete and recreate the drive:", weight=ft.FontWeight.BOLD, size=12),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    f"rclone config delete {remote_name} --config config/rclone.conf",
                                    size=11,
                                    selectable=True
                                ),
                                ft.Text(
                                    f"rclone config create {remote_name} drive --config config/rclone.conf",
                                    size=11,
                                    selectable=True
                                ),
                            ], spacing=5, tight=True),
                            bgcolor=ft.Colors.GREY_900,
                            padding=10,
                            border_radius=5
                        ),
                    ], tight=True, spacing=8),
                    width=500
                ),
                actions=[
                    ft.TextButton("OK", on_click=close_instructions_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            
            self.page.overlay.append(instructions_dialog)
            instructions_dialog.open = True
            self.page.update()
        
        def view_docs(e):
            """Open OAuth troubleshooting docs"""
            close_dialog(e)
            import webbrowser
            docs_path = os.path.join(os.getcwd(), "docs", "OAUTH_ERROR_HANDLING.md")
            if os.path.exists(docs_path):
                webbrowser.open(f"file://{docs_path}")
            else:
                self.show_snackbar("Documentation not found", ft.Colors.RED)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=32),
                ft.Text("Google Drive Authentication Error", size=18, weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Column([
                ft.Text(
                    f"Drive '{remote_name}' cannot authenticate with Google.",
                    size=14,
                    weight=ft.FontWeight.W_500
                ),
                ft.Container(height=10),
                ft.Text("Common causes:", size=13, weight=ft.FontWeight.BOLD),
                ft.Text("• OAuth token expired", size=12),
                ft.Text("• Google OAuth client not configured", size=12),
                ft.Text("• Drive was deleted/renamed", size=12),
                ft.Container(height=15),
                ft.Container(
                    content=ft.Text(
                        "You need to re-authenticate this drive.",
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ORANGE_700
                    ),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=10,
                    border_radius=5
                ),
            ], tight=True, spacing=5),
            actions=[
                ft.TextButton("📖 View Docs", on_click=view_docs),
                ft.TextButton("🔧 Fix Instructions", on_click=reconnect_drive),
                ft.TextButton("Cancel", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def validate_drives_before_upload(self) -> bool:
        """
        Validate that all enabled drives are healthy before allowing upload
        
        Returns:
            True if all drives are healthy, False otherwise
        """
        drives = self.config.get_enabled_drives()
        
        if not drives:
            self.show_snackbar("❌ No drives enabled. Please enable at least one drive.", ft.Colors.RED)
            return False
        
        # Check health of all drives
        health_status = self.check_all_drives_health()
        
        # Find unhealthy drives
        oauth_errors = []
        other_errors = []
        
        for remote_name, health in health_status.items():
            if health['status'] == 'OAUTH_ERROR':
                oauth_errors.append(remote_name)
            elif health['status'] != 'HEALTHY':
                other_errors.append((remote_name, health['message']))
        
        # Show errors if any
        if oauth_errors:
            # Show OAuth error for first broken drive
            first_error = oauth_errors[0]
            error_details = health_status[first_error]['error_details']
            self.show_oauth_error_dialog(first_error, error_details)
            return False
        
        if other_errors:
            error_list = "\n".join([f"• {name}: {msg}" for name, msg in other_errors])
            
            def close_error_dialog(e):
                error_dialog.open = False
                self.page.update()
            
            error_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Drive Health Issues", size=18, weight=ft.FontWeight.BOLD),
                content=ft.Text(
                    f"The following drives have issues:\n\n{error_list}\n\nPlease fix or disable them before uploading.",
                    size=14
                ),
                actions=[
                    ft.TextButton("OK", on_click=close_error_dialog)
                ]
            )
            
            self.page.overlay.append(error_dialog)
            error_dialog.open = True
            self.page.update()
            return False
        
        return True


def main(page: ft.Page):
    app = MultiDriveApp(page)


if __name__ == "__main__":
    import sys
    # Use desktop mode explicitly when running as executable
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        ft.app(target=main, view=ft.AppView.FLET_APP)
    else:
        # Running in normal Python environment
        ft.app(target=main)
