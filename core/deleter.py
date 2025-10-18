"""
File Deletion Module
Handles deletion of uploaded files and their chunks from multiple drives
"""
from pathlib import Path
from typing import Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .rclone_manager import RcloneManager
from .manifest import ManifestManager
from .config_manager import ConfigManager


class FileDeleter:
    """Handles deletion of uploaded files from cloud drives"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        rclone_manager: RcloneManager,
        manifest_manager: ManifestManager
    ):
        """
        Initialize FileDeleter
        
        Args:
            config_manager: Configuration manager instance
            rclone_manager: Rclone manager instance
            manifest_manager: Manifest manager instance
        """
        self.config = config_manager
        self.rclone = rclone_manager
        self.manifest = manifest_manager
        self.is_cancelled = False
    
    def delete_file(
        self,
        manifest_id: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """
        Delete all chunks of an uploaded file
        
        Args:
            manifest_id: ID of the manifest
            progress_callback: Optional callback(current, total)
            
        Returns:
            Tuple of (success, message)
        """
        self.is_cancelled = False
        
        # Load manifest
        manifest = self.manifest.load_manifest(manifest_id)
        if not manifest:
            return (False, "Manifest not found")
        
        chunks = manifest.get("chunks", [])
        if not chunks:
            return (False, "No chunks to delete")
        
        filename = manifest["original_file"]["filename"]
        total_chunks = len(chunks)
        
        print(f"Deleting file: {filename} ({total_chunks} chunks)")
        
        # Delete chunks concurrently
        success = self._delete_chunks_concurrent(chunks, progress_callback)
        
        if self.is_cancelled:
            return (False, "Deletion cancelled")
        
        if not success:
            return (False, "Some chunks failed to delete")
        
        # Delete manifest
        self.manifest.delete_manifest(manifest_id)
        
        return (True, f"Successfully deleted {filename}")
    
    def _delete_chunks_concurrent(
        self,
        chunks: list,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> bool:
        """
        Delete chunks concurrently
        
        Args:
            chunks: List of chunk dictionaries
            progress_callback: Optional progress callback
            
        Returns:
            True if all chunks deleted successfully
        """
        total_chunks = len(chunks)
        deleted_count = 0
        failed_chunks = []
        
        max_workers = self.config.get_max_concurrent_uploads()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {
                executor.submit(self._delete_single_chunk, chunk): chunk
                for chunk in chunks
            }
            
            for future in as_completed(future_to_chunk):
                if self.is_cancelled:
                    for f in future_to_chunk:
                        f.cancel()
                    return False
                
                chunk = future_to_chunk[future]
                
                try:
                    success = future.result()
                    
                    if success:
                        deleted_count += 1
                    else:
                        failed_chunks.append(chunk["index"])
                    
                    if progress_callback:
                        progress_callback(deleted_count, total_chunks)
                        
                except Exception as e:
                    print(f"Error deleting chunk {chunk['index']}: {e}")
                    failed_chunks.append(chunk["index"])
        
        if failed_chunks:
            print(f"Failed to delete chunks: {failed_chunks}")
            return False
        
        return True
    
    def _delete_single_chunk(self, chunk: dict) -> bool:
        """
        Delete a single chunk from remote drive
        
        Args:
            chunk: Chunk dictionary with drive and path info
            
        Returns:
            True if successful
        """
        if self.is_cancelled:
            return False
        
        drive_name = chunk["drive"]
        remote_path = chunk["remote_path"]
        
        # Get remote name from configuration
        drives = self.config.get_all_drives()
        remote_name = None
        
        for drive in drives:
            if drive["name"] == drive_name:
                remote_name = drive["remote_name"]
                break
        
        if not remote_name:
            print(f"Drive '{drive_name}' not found")
            return False
        
        # Delete the chunk
        success, error_msg = self.rclone.delete_file(remote_name, remote_path)
        
        if success:
            print(f"Deleted chunk {chunk['index']}: {chunk['filename']}")
            return True
        else:
            print(f"Failed to delete chunk {chunk['index']}: {error_msg}")
            return False
    
    def cancel(self):
        """Cancel ongoing deletion"""
        self.is_cancelled = True
