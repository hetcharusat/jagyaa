"""
Configuration Manager Module
Handles application settings and drive configurations
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any


class ConfigManager:
    """Manages application configuration and drive settings"""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize ConfigManager
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.drives_config_path = self.config_dir / "drives.json"
        self.rclone_config_path = self.config_dir / "rclone.conf"
        self.app_settings_path = self.config_dir / "app_settings.json"
        
        self.drives_config = self._load_drives_config()
        self.app_settings = self._load_app_settings()

        # Auto-detect rclone path if missing and persist
        if not self.get_rclone_path():
            detected = self._detect_rclone_path()
            if detected:
                self.set_rclone_path(detected)
    
    def _load_drives_config(self) -> Dict[str, Any]:
        """Load drives configuration from JSON file"""
        if not self.drives_config_path.exists():
            # Create default config from example
            example_path = self.config_dir / "drives.example.json"
            if example_path.exists():
                with open(example_path, 'r') as f:
                    config = json.load(f)
                self._save_drives_config(config)
                return config
            else:
                # Create minimal default config
                default_config = {
                    "drives": [],
                    "settings": {
                        "chunk_size_mb": 100,
                        "max_concurrent_uploads": 3,
                        "upload_folder": "MultiDriveSplit",
                        "manifest_folder": "manifests",
                        "temp_folder": "chunks"
                    }
                }
                self._save_drives_config(default_config)
                return default_config
        
        with open(self.drives_config_path, 'r') as f:
            return json.load(f)
    
    def _save_drives_config(self, config: Dict[str, Any]) -> None:
        """Save drives configuration to JSON file"""
        with open(self.drives_config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def _load_app_settings(self) -> Dict[str, Any]:
        """Load app-level settings (like rclone_path)"""
        if self.app_settings_path.exists():
            with open(self.app_settings_path, 'r') as f:
                return json.load(f)
        data = {}
        with open(self.app_settings_path, 'w') as f:
            json.dump(data, f, indent=2)
        return data

    def _save_app_settings(self) -> None:
        with open(self.app_settings_path, 'w') as f:
            json.dump(self.app_settings, f, indent=2)
    
    def get_enabled_drives(self) -> List[Dict[str, Any]]:
        """Get list of enabled drives"""
        return [d for d in self.drives_config.get("drives", []) if d.get("enabled", False)]
    
    def get_all_drives(self) -> List[Dict[str, Any]]:
        """Get list of all drives"""
        return self.drives_config.get("drives", [])
    
    def add_drive(self, name: str, remote_name: str, description: str = "", enabled: bool = True) -> None:
        """
        Add a new drive configuration
        
        Args:
            name: Display name for the drive
            remote_name: Rclone remote name
            description: Optional description
            enabled: Whether the drive is enabled
        """
        drive_config = {
            "name": name,
            "remote_name": remote_name,
            "enabled": enabled,
            "description": description
        }
        
        self.drives_config["drives"].append(drive_config)
        self._save_drives_config(self.drives_config)
    
    def remove_drive(self, name: str) -> bool:
        """
        Remove a drive configuration
        
        Args:
            name: Name of the drive to remove
            
        Returns:
            True if removed, False if not found
        """
        drives = self.drives_config.get("drives", [])
        initial_len = len(drives)
        
        self.drives_config["drives"] = [d for d in drives if d.get("name") != name]
        
        if len(self.drives_config["drives"]) < initial_len:
            self._save_drives_config(self.drives_config)
            return True
        return False
    
    def update_drive(self, name: str, **kwargs) -> bool:
        """
        Update drive configuration
        
        Args:
            name: Name of the drive to update
            **kwargs: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        for drive in self.drives_config.get("drives", []):
            if drive.get("name") == name:
                drive.update(kwargs)
                self._save_drives_config(self.drives_config)
                return True
        return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.drives_config.get("settings", {}).get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value"""
        if "settings" not in self.drives_config:
            self.drives_config["settings"] = {}
        
        self.drives_config["settings"][key] = value
        self._save_drives_config(self.drives_config)
    
    def get_chunk_size_mb(self) -> int:
        """Get configured chunk size in MB"""
        return self.get_setting("chunk_size_mb", 100)
    
    def get_max_concurrent_uploads(self) -> int:
        """Get maximum concurrent uploads"""
        return self.get_setting("max_concurrent_uploads", 3)
    
    def get_upload_folder(self) -> str:
        """Get upload folder name on remote drives"""
        return self.get_setting("upload_folder", "MultiDriveSplit")
    
    def get_manifest_folder(self) -> str:
        """Get local manifest storage folder"""
        return self.get_setting("manifest_folder", "manifests")
    
    def get_temp_folder(self) -> str:
        """Get temporary chunks folder"""
        return self.get_setting("temp_folder", "chunks")

    def get_preview_folder(self) -> str:
        """Get preview images folder (for thumbnails)"""
        return str(self.config_dir.parent / "previews")
    
    def rclone_config_exists(self) -> bool:
        """Check if rclone config file exists"""
        return self.rclone_config_path.exists()
    
    def get_rclone_config_path(self) -> str:
        """Get path to rclone config file"""
        return str(self.rclone_config_path)

    def set_rclone_path(self, path: str) -> None:
        """Persist rclone.exe absolute path for later use"""
        self.app_settings["rclone_path"] = path
        self._save_app_settings()

    def get_rclone_path(self) -> str | None:
        return self.app_settings.get("rclone_path")

    def _detect_rclone_path(self) -> str | None:
        """Try to auto-detect rclone.exe on Windows (winget typical location)"""
        # 1) Prefer an rclone.exe bundled next to the app executable (PyInstaller) or repo root
        try:
            exe_dir = Path(getattr(__import__('sys'), 'frozen', False) and __import__('sys')._MEIPASS or Path(__file__).resolve().parents[1])
            # Check sibling of app exe or project root for rclone.exe
            candidates = [
                exe_dir / 'rclone.exe',
                Path(__file__).resolve().parents[2] / 'rclone.exe',  # repo root
                Path.cwd() / 'rclone.exe',
            ]
            for c in candidates:
                if c.exists():
                    return str(c)
        except Exception:
            pass
        # 2) PATH lookup
        try:
            # Preferred: on PATH
            from shutil import which
            path = which("rclone")
            if path:
                return path
        except Exception:
            pass
        # 3) Fallback: search WinGet directory
        base = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        try:
            for p in base.rglob("rclone.exe"):
                return str(p)
        except Exception:
            return None
        return None


if __name__ == "__main__":
    # Test the config manager
    config = ConfigManager()
    
    print(f"Enabled drives: {len(config.get_enabled_drives())}")
    print(f"Chunk size: {config.get_chunk_size_mb()} MB")
    print(f"Max concurrent uploads: {config.get_max_concurrent_uploads()}")
