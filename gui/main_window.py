"""
Main Window GUI
PySide6-based desktop application interface
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QListWidget, QListWidgetItem, QTabWidget,
    QFileDialog, QMessageBox, QGroupBox, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from core import (
    ConfigManager, RcloneManager, ManifestManager,
    Uploader, Downloader
)


class UploadThread(QThread):
    """Thread for handling file uploads"""
    progress = Signal(str, int, int)  # stage, current, total
    chunk_status = Signal(int, int, str)  # index, total, status
    finished = Signal(bool, str)  # success, manifest_id
    log = Signal(str)
    
    def __init__(self, uploader: Uploader, file_path: str):
        super().__init__()
        self.uploader = uploader
        self.file_path = file_path
    
    def run(self):
        """Run upload in background thread"""
        try:
            self.log.emit(f"Starting upload: {Path(self.file_path).name}")
            
            manifest_id = self.uploader.upload_file(
                self.file_path,
                self.progress_callback,
                self.chunk_callback
            )
            
            if manifest_id:
                self.finished.emit(True, manifest_id)
                self.log.emit(f"Upload completed: {manifest_id}")
            else:
                self.finished.emit(False, "")
                self.log.emit("Upload failed or cancelled")
                
        except Exception as e:
            self.log.emit(f"Upload error: {str(e)}")
            self.finished.emit(False, "")
    
    def progress_callback(self, stage: str, current: int, total: int):
        """Handle progress updates"""
        self.progress.emit(stage, current, total)
    
    def chunk_callback(self, chunk_index: int, total_chunks: int, status: str):
        """Handle chunk status updates"""
        self.chunk_status.emit(chunk_index, total_chunks, status)


class DownloadThread(QThread):
    """Thread for handling file downloads"""
    progress = Signal(str, int, int)  # stage, current, total
    chunk_status = Signal(int, int, str)  # index, total, status
    finished = Signal(bool)  # success
    log = Signal(str)
    
    def __init__(self, downloader: Downloader, manifest_id: str, output_path: str):
        super().__init__()
        self.downloader = downloader
        self.manifest_id = manifest_id
        self.output_path = output_path
    
    def run(self):
        """Run download in background thread"""
        try:
            self.log.emit(f"Starting download: {self.manifest_id}")
            
            success = self.downloader.download_file(
                self.manifest_id,
                self.output_path,
                self.progress_callback,
                self.chunk_callback
            )
            
            if success:
                self.finished.emit(True)
                self.log.emit(f"Download completed: {self.output_path}")
            else:
                self.finished.emit(False)
                self.log.emit("Download failed or cancelled")
                
        except Exception as e:
            self.log.emit(f"Download error: {str(e)}")
            self.finished.emit(False)
    
    def progress_callback(self, stage: str, current: int, total: int):
        """Handle progress updates"""
        self.progress.emit(stage, current, total)
    
    def chunk_callback(self, chunk_index: int, total_chunks: int, status: str):
        """Handle chunk status updates"""
        self.chunk_status.emit(chunk_index, total_chunks, status)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Multi-Google Drive Split Uploader")
        self.setMinimumSize(900, 600)
        
        # Initialize core components
        try:
            self.config = ConfigManager()
            self.manifest_manager = ManifestManager(self.config.get_manifest_folder())
            # Use detected rclone path if available and avoid hard-fail
            rclone_path = self.config.get_rclone_path() or "rclone"
            self.rclone = RcloneManager(rclone_path=rclone_path, config_path=self.config.get_rclone_config_path(), strict=False)
            self.uploader = Uploader(self.config, self.rclone, self.manifest_manager)
            self.downloader = Downloader(self.config, self.rclone, self.manifest_manager)
        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize: {str(e)}")
            sys.exit(1)
        
        self.upload_thread = None
        self.download_thread = None
        
        # Setup UI
        self.setup_ui()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Refresh UI
        self.refresh_drives_status()
        self.refresh_downloads_list()
    
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Upload tab
        upload_tab = self.create_upload_tab()
        tabs.addTab(upload_tab, "Upload")
        
        # Download tab
        download_tab = self.create_download_tab()
        tabs.addTab(download_tab, "Download")
        
        # Settings tab
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "Settings")
        
        # Log area at bottom
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        self.log("Application started")
        self.log(f"Rclone version: {self.rclone.get_rclone_version()}")
    
    def create_upload_tab(self) -> QWidget:
        """Create the upload tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Drop zone
        drop_zone = QLabel("Drag & Drop Files Here\n\nor")
        drop_zone.setAlignment(Qt.AlignCenter)
        drop_zone.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 40px;
                background-color: #f0f0f0;
                font-size: 16px;
                color: #666;
            }
        """)
        drop_zone.setMinimumHeight(150)
        layout.addWidget(drop_zone)
        
        # Browse button
        browse_btn = QPushButton("Browse for File")
        browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(browse_btn)
        
        # Progress group
        progress_group = QGroupBox("Upload Progress")
        progress_layout = QVBoxLayout()
        
        self.upload_status_label = QLabel("Ready")
        progress_layout.addWidget(self.upload_status_label)
        
        self.upload_progress_bar = QProgressBar()
        self.upload_progress_bar.setValue(0)
        progress_layout.addWidget(self.upload_progress_bar)
        
        self.upload_chunk_label = QLabel("")
        progress_layout.addWidget(self.upload_chunk_label)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.upload_cancel_btn = QPushButton("Cancel Upload")
        self.upload_cancel_btn.clicked.connect(self.cancel_upload)
        self.upload_cancel_btn.setEnabled(False)
        control_layout.addWidget(self.upload_cancel_btn)
        
        control_layout.addStretch()
        
        progress_layout.addLayout(control_layout)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        layout.addStretch()
        
        return tab
    
    def create_download_tab(self) -> QWidget:
        """Create the download tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Available downloads list
        list_group = QGroupBox("Available Downloads")
        list_layout = QVBoxLayout()
        
        self.downloads_list = QListWidget()
        self.downloads_list.itemDoubleClicked.connect(self.download_selected)
        list_layout.addWidget(self.downloads_list)
        
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_downloads_list)
        btn_layout.addWidget(refresh_btn)
        
        download_btn = QPushButton("Download Selected")
        download_btn.clicked.connect(self.download_selected)
        btn_layout.addWidget(download_btn)
        
        btn_layout.addStretch()
        
        list_layout.addLayout(btn_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Progress group
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        
        self.download_status_label = QLabel("Ready")
        progress_layout.addWidget(self.download_status_label)
        
        self.download_progress_bar = QProgressBar()
        self.download_progress_bar.setValue(0)
        progress_layout.addWidget(self.download_progress_bar)
        
        self.download_chunk_label = QLabel("")
        progress_layout.addWidget(self.download_chunk_label)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.download_cancel_btn = QPushButton("Cancel Download")
        self.download_cancel_btn.clicked.connect(self.cancel_download)
        self.download_cancel_btn.setEnabled(False)
        control_layout.addWidget(self.download_cancel_btn)
        
        control_layout.addStretch()
        
        progress_layout.addLayout(control_layout)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        return tab
    
    def create_settings_tab(self) -> QWidget:
        """Create the settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Drives status
        drives_group = QGroupBox("Configured Drives")
        drives_layout = QVBoxLayout()
        
        self.drives_status_label = QLabel()
        drives_layout.addWidget(self.drives_status_label)

        btn_row = QHBoxLayout()
        configure_btn = QPushButton("Configure Rclone Remotes (Login)")
        refresh_btn = QPushButton("Refresh Drives")
        configure_btn.clicked.connect(self.configure_rclone)
        refresh_btn.clicked.connect(self.refresh_drives_status)
        btn_row.addWidget(configure_btn)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        drives_layout.addLayout(btn_row)
        
        drives_group.setLayout(drives_layout)
        layout.addWidget(drives_group)
        
        # Settings info
        settings_group = QGroupBox("Current Settings")
        settings_layout = QVBoxLayout()
        
        self.settings_label = QLabel()
        self.update_settings_display()
        settings_layout.addWidget(self.settings_label)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        
        return tab
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        
        if files:
            self.start_upload(files[0])
    
    def browse_file(self):
        """Open file browser"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Upload",
            "",
            "All Files (*.*)"
        )
        
        if file_path:
            self.start_upload(file_path)
    
    def start_upload(self, file_path: str):
        """Start file upload"""
        if self.upload_thread and self.upload_thread.isRunning():
            QMessageBox.warning(self, "Upload in Progress", "An upload is already in progress.")
            return
        
        # Check if drives are configured
        enabled_drives = self.config.get_enabled_drives()
        if not enabled_drives:
            QMessageBox.warning(
                self,
                "No Drives Configured",
                "Please configure rclone remotes and enable drives in config/drives.json"
            )
            return
        
        self.log(f"Selected file: {Path(file_path).name}")
        
        self.upload_thread = UploadThread(self.uploader, file_path)
        self.upload_thread.progress.connect(self.update_upload_progress)
        self.upload_thread.chunk_status.connect(self.update_upload_chunk)
        self.upload_thread.finished.connect(self.upload_finished)
        self.upload_thread.log.connect(self.log)
        
        self.upload_cancel_btn.setEnabled(True)
        self.upload_thread.start()
    
    def cancel_upload(self):
        """Cancel ongoing upload"""
        if self.upload_thread and self.upload_thread.isRunning():
            self.uploader.cancel()
            self.log("Cancelling upload...")
    
    def update_upload_progress(self, stage: str, current: int, total: int):
        """Update upload progress"""
        self.upload_status_label.setText(f"{stage}: {current}/{total}")
        
        if total > 0:
            percentage = int((current / total) * 100)
            self.upload_progress_bar.setValue(percentage)
    
    def update_upload_chunk(self, chunk_index: int, total_chunks: int, status: str):
        """Update chunk status"""
        self.upload_chunk_label.setText(f"Chunk {chunk_index + 1}/{total_chunks}: {status}")
    
    def upload_finished(self, success: bool, manifest_id: str):
        """Handle upload completion"""
        self.upload_cancel_btn.setEnabled(False)
        
        if success:
            self.upload_status_label.setText(f"Upload completed!")
            self.upload_progress_bar.setValue(100)
            QMessageBox.information(
                self,
                "Upload Complete",
                f"File uploaded successfully!\nManifest ID: {manifest_id}"
            )
            self.refresh_downloads_list()
        else:
            self.upload_status_label.setText("Upload failed or cancelled")
            self.upload_progress_bar.setValue(0)
    
    def refresh_downloads_list(self):
        """Refresh the list of available downloads"""
        self.downloads_list.clear()
        
        available = self.downloader.get_available_downloads()
        
        for item in available:
            text = f"{item['filename']} ({item['size_formatted']}) - {item['total_chunks']} chunks"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.UserRole, item['manifest_id'])
            self.downloads_list.addItem(list_item)
        
        self.log(f"Found {len(available)} files available for download")
    
    def download_selected(self):
        """Download selected file"""
        current_item = self.downloads_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a file to download.")
            return
        
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "Download in Progress", "A download is already in progress.")
            return
        
        manifest_id = current_item.data(Qt.UserRole)
        
        # Get output path
        manifest = self.manifest_manager.load_manifest(manifest_id)
        if not manifest:
            QMessageBox.warning(self, "Error", "Failed to load manifest.")
            return
        
        default_filename = manifest['original_file']['filename']
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Downloaded File",
            default_filename,
            "All Files (*.*)"
        )
        
        if not output_path:
            return
        
        self.log(f"Starting download: {manifest_id}")
        
        self.download_thread = DownloadThread(self.downloader, manifest_id, output_path)
        self.download_thread.progress.connect(self.update_download_progress)
        self.download_thread.chunk_status.connect(self.update_download_chunk)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.log.connect(self.log)
        
        self.download_cancel_btn.setEnabled(True)
        self.download_thread.start()
    
    def cancel_download(self):
        """Cancel ongoing download"""
        if self.download_thread and self.download_thread.isRunning():
            self.downloader.cancel()
            self.log("Cancelling download...")
    
    def update_download_progress(self, stage: str, current: int, total: int):
        """Update download progress"""
        self.download_status_label.setText(f"{stage}: {current}/{total}")
        
        if total > 0:
            percentage = int((current / total) * 100)
            self.download_progress_bar.setValue(percentage)
    
    def update_download_chunk(self, chunk_index: int, total_chunks: int, status: str):
        """Update chunk status"""
        self.download_chunk_label.setText(f"Chunk {chunk_index + 1}/{total_chunks}: {status}")
    
    def download_finished(self, success: bool):
        """Handle download completion"""
        self.download_cancel_btn.setEnabled(False)
        
        if success:
            self.download_status_label.setText("Download completed!")
            self.download_progress_bar.setValue(100)
            QMessageBox.information(self, "Download Complete", "File downloaded and verified successfully!")
        else:
            self.download_status_label.setText("Download failed or cancelled")
            self.download_progress_bar.setValue(0)
    
    def refresh_drives_status(self):
        """Refresh drives status display"""
        remotes = self.rclone.list_remotes()
        enabled_drives = self.config.get_enabled_drives()
        
        status_text = f"Rclone remotes found: {len(remotes)}\n"
        status_text += f"Enabled drives: {len(enabled_drives)}\n\n"
        
        if remotes:
            status_text += "Remotes:\n"
            for remote in remotes:
                status_text += f"  • {remote}\n"
        else:
            status_text += "No rclone remotes configured.\n"
        
        if enabled_drives:
            status_text += "\nEnabled drives:\n"
            for drive in enabled_drives:
                status_text += f"  • {drive['name']} → {drive['remote_name']}\n"
        
        self.drives_status_label.setText(status_text)
    
    def update_settings_display(self):
        """Update settings display"""
        settings_text = f"Chunk size: {self.config.get_chunk_size_mb()} MB\n"
        settings_text += f"Max concurrent uploads: {self.config.get_max_concurrent_uploads()}\n"
        settings_text += f"Upload folder: {self.config.get_upload_folder()}\n"
        settings_text += f"Manifest folder: {self.config.get_manifest_folder()}\n"
        settings_text += f"Temp folder: {self.config.get_temp_folder()}\n"
        
        self.settings_label.setText(settings_text)
    
    def configure_rclone(self):
        """Open rclone configuration"""
        self.log("Opening rclone configuration (login)...")
        # Recreate rclone manager with latest path in case it was set after launch
        rclone_path = self.config.get_rclone_path() or "rclone"
        self.rclone = RcloneManager(rclone_path=rclone_path, config_path=self.config.get_rclone_config_path(), strict=False)
        if not self.rclone.is_rclone_available():
            QMessageBox.warning(self, "Rclone", "rclone not found. Please install rclone and set its path in config/app_settings.json, or add it to PATH.")
            return
        success = self.rclone.configure_remote_interactive()
        
        if success:
            self.refresh_drives_status()
            self.log("Rclone configuration completed")
        else:
            self.log("Rclone configuration cancelled or failed")
    
    def log(self, message: str):
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
