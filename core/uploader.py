"""
Uploader Module
Handles concurrent upload of file chunks to multiple drives
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .chunker import FileChunker
from .rclone_manager import RcloneManager
from .manifest import ManifestManager
from .config_manager import ConfigManager


class Uploader:
    """Handles file upload with chunking and distribution across drives"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        rclone_manager: RcloneManager,
        manifest_manager: ManifestManager
    ):
        """
        Initialize Uploader
        
        Args:
            config_manager: Configuration manager instance
            rclone_manager: Rclone manager instance
            manifest_manager: Manifest manager instance
        """
        self.config = config_manager
        self.rclone = rclone_manager
        self.manifest = manifest_manager
        
        self.chunker = FileChunker(chunk_size_mb=self.config.get_chunk_size_mb())
        self.is_cancelled = False
    
    def upload_file(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        chunk_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Optional[str]:
        """
        Upload a file with chunking and distribution
        
        Args:
            file_path: Path to the file to upload
            progress_callback: Optional callback(stage, current, total)
            chunk_callback: Optional callback(chunk_index, total_chunks, status)
            
        Returns:
            Manifest ID if successful, None otherwise
        """
        self.is_cancelled = False
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            print(f"Error: File not found: {file_path}")
            return None
        
        # Get enabled drives
        drives = self.config.get_enabled_drives()
        if not drives:
            print("Error: No enabled drives configured")
            return None
        
        print(f"Starting upload of: {file_path_obj.name}")
        
        # Stage 1: Calculate file hash
        if progress_callback:
            progress_callback("Hashing file", 0, 1)
        
        file_hash = self.chunker.calculate_file_hash(file_path)
        print(f"File hash: {file_hash}")
        
        # Stage 2: Split file into chunks
        if progress_callback:
            progress_callback("Splitting file", 0, 1)
        
        temp_folder = Path(self.config.get_temp_folder())
        temp_folder.mkdir(parents=True, exist_ok=True)
        
        def split_progress(current, total):
            if progress_callback:
                progress_callback("Splitting file", current, total)
        
        chunks_info = self.chunker.split_file(
            file_path,
            str(temp_folder),
            split_progress
        )
        
        print(f"Created {len(chunks_info)} chunks")
        
        # Stage 3: Create manifest
        if progress_callback:
            progress_callback("Creating manifest", 0, 1)
        
        upload_folder = self.config.get_upload_folder()
        chunks_data = []
        
        for idx, (chunk_path, chunk_hash, chunk_size) in enumerate(chunks_info):
            # Distribute chunks across drives in round-robin fashion
            drive = drives[idx % len(drives)]
            remote_path = f"{upload_folder}/{Path(chunk_path).name}"
            
            chunk_info = self.manifest.create_chunk_info(
                index=idx,
                filename=Path(chunk_path).name,
                local_path=chunk_path,
                size=chunk_size,
                hash_value=chunk_hash,
                drive_name=drive["name"],
                remote_path=remote_path
            )
            chunks_data.append(chunk_info)
        
        manifest_id = self.manifest.create_manifest(
            original_filename=file_path_obj.name,
            original_path=str(file_path_obj.absolute()),
            total_size=file_path_obj.stat().st_size,
            file_hash=file_hash,
            chunks=chunks_data
        )
        
        print(f"Created manifest: {manifest_id}")
        
        # Stage 4: Upload chunks
        if progress_callback:
            progress_callback("Uploading chunks", 0, len(chunks_info))
        
        self.manifest.update_manifest(manifest_id, {"status": "uploading"})
        
        success = self._upload_chunks_concurrent(
            manifest_id,
            chunks_data,
            progress_callback,
            chunk_callback
        )
        
        # Update manifest status
        if self.is_cancelled:
            self.manifest.update_manifest(manifest_id, {"status": "cancelled"})
            print("Upload cancelled by user")
        elif success:
            self.manifest.update_manifest(manifest_id, {
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            })
            print("Upload completed successfully")
        else:
            self.manifest.update_manifest(manifest_id, {"status": "failed"})
            print("Upload failed")
        
        # Cleanup temporary chunks
        self._cleanup_chunks(chunks_data)
        
        return manifest_id if (success and not self.is_cancelled) else None
    
    def _upload_chunks_concurrent(
        self,
        manifest_id: str,
        chunks_data: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, int, int], None]],
        chunk_callback: Optional[Callable[[int, int, str], None]]
    ) -> bool:
        """
        Upload chunks concurrently using thread pool
        
        Args:
            manifest_id: ID of the manifest
            chunks_data: List of chunk information dictionaries
            progress_callback: Optional progress callback
            chunk_callback: Optional chunk status callback
            
        Returns:
            True if all chunks uploaded successfully, False otherwise
        """
        max_workers = self.config.get_max_concurrent_uploads()
        total_chunks = len(chunks_data)
        uploaded_count = 0
        failed_chunks = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all upload tasks
            future_to_chunk = {
                executor.submit(
                    self._upload_single_chunk,
                    manifest_id,
                    chunk_data
                ): chunk_data
                for chunk_data in chunks_data
            }
            
            # Process completed uploads
            for future in as_completed(future_to_chunk):
                if self.is_cancelled:
                    # Cancel remaining tasks
                    for f in future_to_chunk:
                        f.cancel()
                    return False
                
                chunk_data = future_to_chunk[future]
                chunk_index = chunk_data["index"]
                
                try:
                    success = future.result()
                    
                    if success:
                        uploaded_count += 1
                        if chunk_callback:
                            chunk_callback(chunk_index, total_chunks, "uploaded")
                    else:
                        failed_chunks.append(chunk_index)
                        if chunk_callback:
                            chunk_callback(chunk_index, total_chunks, "failed")
                    
                    if progress_callback:
                        progress_callback("Uploading chunks", uploaded_count, total_chunks)
                        
                except Exception as e:
                    print(f"Error uploading chunk {chunk_index}: {e}")
                    failed_chunks.append(chunk_index)
                    if chunk_callback:
                        chunk_callback(chunk_index, total_chunks, "error")
        
        if failed_chunks:
            print(f"Failed to upload chunks: {failed_chunks}")
            return False
        
        return True
    
    def _upload_single_chunk(
        self,
        manifest_id: str,
        chunk_data: Dict[str, Any]
    ) -> bool:
        """
        Upload a single chunk to remote drive
        
        Args:
            manifest_id: ID of the manifest
            chunk_data: Chunk information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if self.is_cancelled:
            return False
        
        chunk_index = chunk_data["index"]
        local_path = chunk_data["local_path"]
        drive_name = chunk_data["drive"]
        remote_path = chunk_data["remote_path"]
        
        # Get remote name from drive configuration
        drives = self.config.get_all_drives()
        remote_name = None
        
        for drive in drives:
            if drive["name"] == drive_name:
                remote_name = drive["remote_name"]
                break
        
        if not remote_name:
            print(f"Error: Drive '{drive_name}' not found in configuration")
            return False
        
        # Update chunk status to uploading
        self.manifest.update_chunk_status(manifest_id, chunk_index, "uploading")
        
        # Upload the chunk
        success, error_msg = self.rclone.upload_file(
            local_path,
            remote_name,
            remote_path
        )
        
        if success:
            # Update chunk status to uploaded
            self.manifest.update_chunk_status(
                manifest_id,
                chunk_index,
                "uploaded",
                uploaded_at=datetime.now().isoformat()
            )
            print(f"Uploaded chunk {chunk_index}: {Path(local_path).name}")
            return True
        else:
            # Update chunk status to failed
            self.manifest.update_chunk_status(
                manifest_id,
                chunk_index,
                "failed",
                error=error_msg
            )
            print(f"Failed to upload chunk {chunk_index}: {error_msg}")
            return False
    
    def _cleanup_chunks(self, chunks_data: List[Dict[str, Any]]) -> None:
        """
        Clean up temporary chunk files
        
        Args:
            chunks_data: List of chunk information dictionaries
        """
        for chunk_data in chunks_data:
            chunk_path = Path(chunk_data["local_path"])
            if chunk_path.exists():
                try:
                    chunk_path.unlink()
                except Exception as e:
                    print(f"Warning: Failed to delete chunk {chunk_path}: {e}")
    
    def cancel(self) -> None:
        """Cancel ongoing upload"""
        self.is_cancelled = True
        print("Upload cancellation requested")


if __name__ == "__main__":
    # Test uploader
    config = ConfigManager()
    rclone = RcloneManager(config_path=config.get_rclone_config_path())
    manifest = ManifestManager(config.get_manifest_folder())
    
    uploader = Uploader(config, rclone, manifest)
    
    # Example usage:
    # manifest_id = uploader.upload_file("test_file.bin")
    # print(f"Upload completed: {manifest_id}")
