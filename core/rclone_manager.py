"""
Rclone Manager Module
Handles interactions with rclone for upload/download operations
"""
import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Optional, Callable, Tuple


class RcloneManager:
    """Manages rclone operations for file uploads and downloads"""
    
    def __init__(self, rclone_path: str = "rclone", config_path: Optional[str] = None, strict: bool = True):
        """
        Initialize RcloneManager
        
        Args:
            rclone_path: Path to rclone executable (default: "rclone" if in PATH)
            config_path: Path to rclone config file (optional)
        """
        self.rclone_path = rclone_path
        self.config_path = config_path
        
        # Only hard-fail when strict is True; otherwise allow UI to load and handle later
        if strict and not self.is_rclone_available():
            raise RuntimeError("rclone not found. Please install rclone or provide path.")
    
    def is_rclone_available(self) -> bool:
        """Check if rclone is available in system"""
        try:
            result = subprocess.run(
                [self.rclone_path, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_rclone_version(self) -> str:
        """Get rclone version string"""
        try:
            result = subprocess.run(
                [self.rclone_path, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.split('\n')[0]
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def list_remotes(self) -> List[str]:
        """
        List configured rclone remotes
        
        Returns:
            List of remote names
        """
        cmd = [self.rclone_path, "listremotes"]
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Remove trailing colons and empty lines
                remotes = [line.strip(':') for line in result.stdout.strip().split('\n') if line]
                return remotes
            return []
        except Exception as e:
            print(f"Error listing remotes: {e}")
            return []
    
    def upload_file(
        self,
        local_path: str,
        remote_name: str,
        remote_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """
        Upload a file to remote drive
        
        Args:
            local_path: Path to local file
            remote_name: Name of rclone remote
            remote_path: Path on remote (directory + filename, e.g., "folder/file.bin")
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, error_message)
        """
        # Extract directory path (rclone copy needs directory, not full file path)
        from pathlib import Path
        remote_file_path = Path(remote_path)
        remote_dir = str(remote_file_path.parent) if remote_file_path.parent != Path('.') else ""
        
        cmd = [
            self.rclone_path,
            "copy",
            local_path,
            f"{remote_name}:{remote_dir}",
            "--progress",
            "--stats", "1s",
            "--no-traverse"  # Don't check existing files (faster)
        ]
        
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            output_lines = []
            for line in process.stdout:
                output_lines.append(line.strip())
                if progress_callback:
                    progress_callback(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                return (True, "")
            else:
                error_output = '\n'.join(output_lines[-10:])  # Last 10 lines
                return (False, f"Upload failed with exit code {process.returncode}\n{error_output}")
                
        except Exception as e:
            return (False, f"Upload error: {str(e)}")
    
    def download_file(
        self,
        remote_name: str,
        remote_path: str,
        local_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """
        Download a file from remote drive
        
        Args:
            remote_name: Name of rclone remote
            remote_path: Path on remote (including filename)
            local_path: Destination path for downloaded file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, error_message)
        """
        # Ensure local directory exists
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            self.rclone_path,
            "copy",
            f"{remote_name}:{remote_path}",
            str(Path(local_path).parent),
            "--progress",
            "--stats", "1s"
        ]
        
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in process.stdout:
                if progress_callback:
                    progress_callback(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                return (True, "")
            else:
                return (False, f"Download failed with exit code {process.returncode}")
                
        except Exception as e:
            return (False, f"Download error: {str(e)}")
    
    def delete_file(self, remote_name: str, remote_path: str) -> Tuple[bool, str]:
        """
        Delete a file from remote drive
        
        Args:
            remote_name: Name of rclone remote
            remote_path: Path on remote (including filename)
            
        Returns:
            Tuple of (success, error_message)
        """
        cmd = [
            self.rclone_path,
            "delete",
            f"{remote_name}:{remote_path}"
        ]
        
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return (True, "")
            else:
                return (False, f"Delete failed: {result.stderr}")
                
        except Exception as e:
            return (False, f"Delete error: {str(e)}")
    
    def check_file_exists(self, remote_name: str, remote_path: str) -> bool:
        """
        Check if a file exists on remote
        
        Args:
            remote_name: Name of rclone remote
            remote_path: Path on remote (including filename)
            
        Returns:
            True if file exists, False otherwise
        """
        cmd = [
            self.rclone_path,
            "lsf",
            f"{remote_name}:{remote_path}"
        ]
        
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and len(result.stdout.strip()) > 0
        except Exception:
            return False
    
    def configure_remote_interactive(self, client_id: str = None, client_secret: str = None) -> bool:
        """
        Run rclone config in interactive mode, optionally with custom Google credentials
        
        Args:
            client_id: Optional custom Google OAuth client ID
            client_secret: Optional custom Google OAuth client secret
        
        Returns:
            True if successful, False otherwise
        """
        cmd = [self.rclone_path, "config"]
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        # Set environment variables for custom Google credentials
        env = os.environ.copy()
        if client_id and client_secret:
            env["RCLONE_DRIVE_CLIENT_ID"] = client_id
            env["RCLONE_DRIVE_CLIENT_SECRET"] = client_secret
        
        try:
            result = subprocess.run(cmd, env=env)
            return result.returncode == 0
        except Exception as e:
            print(f"Error running rclone config: {e}")
            return False
    
    def get_drive_stats(self, remote_name: str) -> Optional[dict]:
        """
        Get storage statistics for a remote drive
        
        Args:
            remote_name: Name of rclone remote
            
        Returns:
            Dictionary with total, used, free space in bytes, or None if failed
        """
        cmd = [self.rclone_path, "about", f"{remote_name}:", "--json"]
        
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                return {
                    "total": data.get("total", 0),
                    "used": data.get("used", 0),
                    "free": data.get("free", 0),
                    "trashed": data.get("trashed", 0)
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error getting drive stats: {e}")
            return None


if __name__ == "__main__":
    # Test the rclone manager
    try:
        rclone = RcloneManager()
        print(f"Rclone version: {rclone.get_rclone_version()}")
        print(f"Configured remotes: {rclone.list_remotes()}")
    except RuntimeError as e:
        print(f"Error: {e}")
