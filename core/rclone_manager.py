"""
Rclone Manager Module
Handles interactions with rclone for upload/download operations
"""
import subprocess
import os
import sys
import shutil
import json
from pathlib import Path
from typing import List, Optional, Callable, Tuple

# Windows-specific subprocess flags to prevent console window popup
if sys.platform == 'win32':
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
                timeout=5,
                **SUBPROCESS_FLAGS
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
                timeout=5,
                **SUBPROCESS_FLAGS
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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, **SUBPROCESS_FLAGS)
            if result.returncode == 0:
                # Remove trailing colons and empty lines
                remotes = [line.strip(':') for line in result.stdout.strip().split('\n') if line]
                return remotes
            return []
        except Exception as e:
            print(f"Error listing remotes: {e}")
            return []
    
    def warm_up_connection(self, remote_name: str) -> bool:
        """
        Pre-warm the connection to a remote (reduces first upload delay)
        Does a quick ls to initialize OAuth tokens and connection
        
        Args:
            remote_name: Name of rclone remote
            
        Returns:
            True if connection successful, False otherwise
        """
        cmd = [
            self.rclone_path,
            "lsf",  # Fast list (just filenames)
            f"{remote_name}:",
            "--max-depth", "1",  # Only top level
            "--fast-list",
            "--max-age", "1s"  # Don't actually list anything old
        ]
        
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        try:
            # Run in background, don't wait for full completion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,  # Quick timeout
                **SUBPROCESS_FLAGS
            )
            return result.returncode == 0
        except:
            # Ignore errors - this is just a warm-up
            return False
    
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
        # Use copyto for single file upload (faster than copy)
        from pathlib import Path
        
        cmd = [
            self.rclone_path,
            "copyto",  # copyto is faster for single files (no directory scan)
            local_path,
            f"{remote_name}:{remote_path}",  # Full path including filename
            "--progress",
            "--stats", "1s",
            "--no-traverse",  # Don't check existing files (faster)
            "--no-check-dest",  # Don't check if destination exists (FASTEST!)
            "--ignore-checksum",  # Don't verify checksums
            "--no-update-modtime",  # Don't update modification times
            "--use-server-modtime",  # Use server modification time
            "--fast-list",  # Use fast listing (faster for remotes that support it)
            "--transfers", "4",  # Allow 4 parallel transfers per file
            "--checkers", "1",  # Minimize file checks
            "--low-level-retries", "1"  # Reduce retry attempts for speed
        ]
        
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        import time
        rclone_start = time.time()
        print(f"[RCLONE] Starting rclone copyto command...")
        
        try:
            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'text': True,
                'bufsize': 1,
                'universal_newlines': True
            }
            popen_kwargs.update(SUBPROCESS_FLAGS)
            
            process = subprocess.Popen(cmd, **popen_kwargs)
            
            print(f"[RCLONE] Popen created in {time.time() - rclone_start:.2f}s, reading output...")
            
            # Read output line by line
            output_lines = []
            if process.stdout is not None:
                for line in process.stdout:
                    output_lines.append(line.strip())
                    if progress_callback:
                        progress_callback(line.strip())
            
            process.wait()
            
            total_elapsed = time.time() - rclone_start
            print(f"[RCLONE] Command completed in {total_elapsed:.2f}s (returncode: {process.returncode})")
            
            if process.returncode == 0:
                return (True, "")
            else:
                error_output = '\n'.join(output_lines[-10:])  # Last 10 lines
                
                # Check for specific error types
                error_lower = error_output.lower()
                if "ratelimitexceeded" in error_lower or "rate limit" in error_lower:
                    return (False, "⚠️ Google Drive rate limit exceeded. Please wait a few minutes and try again.")
                elif "quota" in error_lower:
                    return (False, "⚠️ Google Drive quota exceeded. Check your storage space or API quota.")
                elif "authentication" in error_lower or "unauthorized" in error_lower:
                    return (False, "⚠️ Authentication failed. Please re-configure your Google Drive connection.")
                else:
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
            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'text': True,
                'bufsize': 1,
                'universal_newlines': True
            }
            popen_kwargs.update(SUBPROCESS_FLAGS)
            
            process = subprocess.Popen(cmd, **popen_kwargs)
            
            # Read output line by line
            if process.stdout is not None:
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
    
    def delete_file(self, remote_name: str, remote_path: str, use_trash: bool = False) -> Tuple[bool, str]:
        """
        Delete a file from remote drive
        
        Args:
            remote_name: Name of rclone remote
            remote_path: Path on remote (including filename)
            use_trash: If False (default), permanently delete. If True, send to trash.
            
        Returns:
            Tuple of (success, error_message)
        """
        cmd = [
            self.rclone_path,
            "delete",
            f"{remote_name}:{remote_path}",
            "-v"  # Verbose output for debugging
        ]
        
        # Permanently delete by default (don't send to trash)
        if not use_trash:
            cmd.append("--drive-use-trash=false")
        
        if self.config_path:
            cmd.extend(["--config", self.config_path])
        
        print(f"[RCLONE DELETE] Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, **SUBPROCESS_FLAGS)
            
            print(f"[RCLONE DELETE] Return code: {result.returncode}")
            print(f"[RCLONE DELETE] Stdout: {result.stdout}")
            print(f"[RCLONE DELETE] Stderr: {result.stderr}")
            
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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, **SUBPROCESS_FLAGS)
            return result.returncode == 0 and len(result.stdout.strip()) > 0
        except Exception:
            return False
    
    def configure_remote_interactive(self, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> bool:
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
            result = subprocess.run(cmd, env=env, **SUBPROCESS_FLAGS)
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
            # Use encoding='utf-8' and errors='replace' to handle Unicode issues
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                encoding='utf-8',
                errors='replace',
                timeout=60,  # Increased timeout to 60 seconds
                **SUBPROCESS_FLAGS
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    
                    return {
                        "total": data.get("total", 0),
                        "used": data.get("used", 0),
                        "free": data.get("free", 0),
                        "trashed": data.get("trashed", 0)
                    }
                except json.JSONDecodeError as e:
                    print(f"Error parsing drive stats JSON for {remote_name}: {e}")
                    return None
            else:
                if result.stderr:
                    print(f"Error getting drive stats for {remote_name}: {result.stderr.strip()}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"Timeout getting drive stats for {remote_name} (exceeded 60s)")
            return None
        except Exception as e:
            print(f"Error getting drive stats for {remote_name}: {e}")
            return None

    def list_remote_files(
        self,
        remote_name: str,
        path: str = "",
        recursive: bool = False,
        max_entries: Optional[int] = 200
    ) -> List[dict]:
        """List files on a remote using rclone lsjson."""
        target = f"{remote_name}:{path}" if path else f"{remote_name}:"

        cmd = [self.rclone_path, "lsjson", target, "--files-only"]

        if recursive:
            cmd.append("--recursive")

        if self.config_path:
            cmd.extend(["--config", self.config_path])

        try:
            # Use encoding='utf-8' and errors='replace' to handle Unicode issues
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                encoding='utf-8',
                errors='replace',
                timeout=60,  # Increased timeout to 60 seconds
                **SUBPROCESS_FLAGS
            )

            if result.returncode != 0:
                if result.stderr:
                    print(f"Error listing remote files ({remote_name}): {result.stderr.strip()}")
                return []

            if not result.stdout:
                return []

            output = result.stdout.strip()
            if not output:
                return []

            try:
                files = json.loads(output)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON from rclone lsjson for {remote_name}: {e}")
                return []

            if not isinstance(files, list):
                return []

            if max_entries is not None:
                return files[:max_entries]
            return files

        except subprocess.TimeoutExpired:
            print(f"Timeout listing remote files for {remote_name} (exceeded 60s)")
            return []
        except Exception as e:
            print(f"Error listing remote files for {remote_name}: {e}")
            return []


if __name__ == "__main__":
    # Test the rclone manager
    try:
        rclone = RcloneManager()
        print(f"Rclone version: {rclone.get_rclone_version()}")
        print(f"Configured remotes: {rclone.list_remotes()}")
    except RuntimeError as e:
        print(f"Error: {e}")
