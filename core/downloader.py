"""
Downloader Module
Handles downloading and reconstructing files from chunks
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


class Downloader:
    """Handles file download and reconstruction from chunks"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        rclone_manager: RcloneManager,
        manifest_manager: ManifestManager
    ):
        """
        Initialize Downloader
        
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
    
    def download_file(
        self,
        manifest_id: str,
        output_path: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        chunk_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> bool:
        """
        Download and reconstruct a file from chunks
        
        Args:
            manifest_id: ID of the manifest
            output_path: Path where the file should be saved
            progress_callback: Optional callback(stage, current, total)
            chunk_callback: Optional callback(chunk_index, total_chunks, status)
            
        Returns:
            True if successful, False otherwise
        """
        self.is_cancelled = False
        
        # Load manifest
        manifest = self.manifest.load_manifest(manifest_id)
        if not manifest:
            print(f"Error: Manifest not found: {manifest_id}")
            return False
        
        chunks_data = manifest["chunks"]
        total_chunks = len(chunks_data)
        
        print(f"Starting download: {manifest['original_file']['filename']}")
        print(f"Total chunks: {total_chunks}")
        
        # Create temporary download folder
        temp_folder = Path(self.config.get_temp_folder()) / f"download_{manifest_id}"
        temp_folder.mkdir(parents=True, exist_ok=True)
        
        # Stage 1: Download all chunks
        if progress_callback:
            progress_callback("Downloading chunks", 0, total_chunks)
        
        success = self._download_chunks_concurrent(
            manifest_id,
            chunks_data,
            temp_folder,
            progress_callback,
            chunk_callback
        )
        
        if not success or self.is_cancelled:
            print("Download failed or cancelled")
            self._cleanup_download_folder(temp_folder)
            return False
        
        # Stage 2: Verify and merge chunks
        if progress_callback:
            progress_callback("Merging chunks", 0, total_chunks)
        
        # Prepare chunk paths and hashes in order
        chunk_paths = []
        expected_hashes = []
        
        for chunk_data in sorted(chunks_data, key=lambda x: x["index"]):
            chunk_filename = chunk_data["filename"]
            chunk_path = temp_folder / chunk_filename
            chunk_paths.append(str(chunk_path))
            expected_hashes.append(chunk_data["hash"])
        
        # Merge chunks
        def merge_progress(current, total):
            if progress_callback:
                progress_callback("Merging chunks", current, total)
        
        merge_success = self.chunker.merge_chunks(
            chunk_paths,
            output_path,
            expected_hashes,
            merge_progress
        )
        
        if not merge_success:
            print("Error: Failed to merge chunks")
            self._cleanup_download_folder(temp_folder)
            return False
        
        # Stage 3: Verify final file hash
        if progress_callback:
            progress_callback("Verifying file", 0, 1)
        
        final_hash = self.chunker.calculate_file_hash(output_path)
        expected_hash = manifest["original_file"]["hash"]
        
        if final_hash != expected_hash:
            print(f"Error: File hash mismatch!")
            print(f"Expected: {expected_hash}")
            print(f"Actual: {final_hash}")
            self._cleanup_download_folder(temp_folder)
            return False
        
        print("Download and verification completed successfully")
        
        # Cleanup temporary files
        self._cleanup_download_folder(temp_folder)
        
        if progress_callback:
            progress_callback("Completed", total_chunks, total_chunks)
        
        return True
    
    def _download_chunks_concurrent(
        self,
        manifest_id: str,
        chunks_data: List[Dict[str, Any]],
        temp_folder: Path,
        progress_callback: Optional[Callable[[str, int, int], None]],
        chunk_callback: Optional[Callable[[int, int, str], None]]
    ) -> bool:
        """
        Download chunks concurrently using thread pool
        
        Args:
            manifest_id: ID of the manifest
            chunks_data: List of chunk information dictionaries
            temp_folder: Temporary folder for downloaded chunks
            progress_callback: Optional progress callback
            chunk_callback: Optional chunk status callback
            
        Returns:
            True if all chunks downloaded successfully, False otherwise
        """
        max_workers = self.config.get_max_concurrent_uploads()
        total_chunks = len(chunks_data)
        downloaded_count = 0
        failed_chunks = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_chunk = {
                executor.submit(
                    self._download_single_chunk,
                    chunk_data,
                    temp_folder
                ): chunk_data
                for chunk_data in chunks_data
            }
            
            # Process completed downloads
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
                        downloaded_count += 1
                        if chunk_callback:
                            chunk_callback(chunk_index, total_chunks, "downloaded")
                    else:
                        failed_chunks.append(chunk_index)
                        if chunk_callback:
                            chunk_callback(chunk_index, total_chunks, "failed")
                    
                    if progress_callback:
                        progress_callback("Downloading chunks", downloaded_count, total_chunks)
                        
                except Exception as e:
                    print(f"Error downloading chunk {chunk_index}: {e}")
                    failed_chunks.append(chunk_index)
                    if chunk_callback:
                        chunk_callback(chunk_index, total_chunks, "error")
        
        if failed_chunks:
            print(f"Failed to download chunks: {failed_chunks}")
            return False
        
        return True
    
    def _download_single_chunk(
        self,
        chunk_data: Dict[str, Any],
        temp_folder: Path
    ) -> bool:
        """
        Download a single chunk from remote drive
        
        Args:
            chunk_data: Chunk information dictionary
            temp_folder: Temporary folder for downloaded chunks
            
        Returns:
            True if successful, False otherwise
        """
        if self.is_cancelled:
            return False
        
        chunk_index = chunk_data["index"]
        chunk_filename = chunk_data["filename"]
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
        
        # Local path for downloaded chunk
        local_path = temp_folder / chunk_filename
        
        # Download the chunk
        success, error_msg = self.rclone.download_file(
            remote_name,
            remote_path,
            str(local_path)
        )
        
        if success:
            print(f"Downloaded chunk {chunk_index}: {chunk_filename}")
            return True
        else:
            print(f"Failed to download chunk {chunk_index}: {error_msg}")
            return False
    
    def _cleanup_download_folder(self, folder: Path) -> None:
        """
        Clean up temporary download folder
        
        Args:
            folder: Path to temporary folder
        """
        if folder.exists():
            try:
                import shutil
                shutil.rmtree(folder)
                print(f"Cleaned up temporary folder: {folder}")
            except Exception as e:
                print(f"Warning: Failed to clean up folder {folder}: {e}")
    
    def cancel(self) -> None:
        """Cancel ongoing download"""
        self.is_cancelled = True
        print("Download cancellation requested")
    
    def get_available_downloads(self) -> List[Dict[str, Any]]:
        """
        Get list of files available for download
        
        Returns:
            List of manifest summaries
        """
        all_manifests = self.manifest.get_all_manifests()
        
        # Filter to only completed uploads
        available = [
            {
                "manifest_id": m["manifest_id"],
                "filename": m["original_file"]["filename"],
                "size": m["original_file"]["size"],
                "size_formatted": m["original_file"]["size_formatted"],
                "created_at": m["created_at"],
                "total_chunks": m["total_chunks"],
                "status": m.get("status", "unknown")
            }
            for m in all_manifests
            if m.get("status") == "completed"
        ]
        
        return available


if __name__ == "__main__":
    # Test downloader
    config = ConfigManager()
    rclone = RcloneManager(config_path=config.get_rclone_config_path())
    manifest = ManifestManager(config.get_manifest_folder())
    
    downloader = Downloader(config, rclone, manifest)
    
    # Example usage:
    # success = downloader.download_file("manifest_id", "output_file.bin")
    # print(f"Download successful: {success}")
    
    # List available downloads
    available = downloader.get_available_downloads()
    print(f"Available downloads: {len(available)}")
