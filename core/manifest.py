"""
Manifest Manager Module
Handles creation and management of file chunk manifests
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class ManifestManager:
    """Manages manifest files for chunked uploads"""
    
    def __init__(self, manifest_folder: str = "manifests"):
        """
        Initialize ManifestManager
        
        Args:
            manifest_folder: Directory to store manifest files
        """
        self.manifest_folder = Path(manifest_folder)
        self.manifest_folder.mkdir(parents=True, exist_ok=True)
    
    def create_manifest(
        self,
        original_filename: str,
        original_path: str,
        total_size: int,
        file_hash: str,
        chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Create a new manifest file
        
        Args:
            original_filename: Name of the original file
            original_path: Path to the original file
            total_size: Total size of the original file in bytes
            file_hash: SHA-256 hash of the original file
            chunks: List of chunk dictionaries
            
        Returns:
            Manifest ID (filename without extension)
        """
        # Generate manifest ID based on timestamp and filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_id = f"{Path(original_filename).stem}_{timestamp}"
        
        manifest_data = {
            "manifest_id": manifest_id,
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "original_file": {
                "filename": original_filename,
                "path": original_path,
                "size": total_size,
                "size_formatted": self._format_size(total_size),
                "hash": file_hash
            },
            "chunks": chunks,
            "total_chunks": len(chunks),
            "status": "created"
        }
        
        manifest_path = self.manifest_folder / f"{manifest_id}.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        return manifest_id
    
    def load_manifest(self, manifest_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a manifest file
        
        Args:
            manifest_id: ID of the manifest to load
            
        Returns:
            Manifest data dictionary or None if not found
        """
        manifest_path = self.manifest_folder / f"{manifest_id}.json"
        
        if not manifest_path.exists():
            return None
        
        with open(manifest_path, 'r') as f:
            return json.load(f)
    
    def update_manifest(self, manifest_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update manifest data
        
        Args:
            manifest_id: ID of the manifest to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False if manifest not found
        """
        manifest = self.load_manifest(manifest_id)
        
        if not manifest:
            return False
        
        manifest.update(updates)
        manifest["updated_at"] = datetime.now().isoformat()
        
        manifest_path = self.manifest_folder / f"{manifest_id}.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return True
    
    def update_chunk_status(
        self,
        manifest_id: str,
        chunk_index: int,
        status: str,
        **kwargs
    ) -> bool:
        """
        Update the status of a specific chunk
        
        Args:
            manifest_id: ID of the manifest
            chunk_index: Index of the chunk to update
            status: New status (e.g., "uploading", "uploaded", "failed")
            **kwargs: Additional fields to update for the chunk
            
        Returns:
            True if successful, False otherwise
        """
        manifest = self.load_manifest(manifest_id)
        
        if not manifest or chunk_index >= len(manifest["chunks"]):
            return False
        
        manifest["chunks"][chunk_index]["status"] = status
        manifest["chunks"][chunk_index].update(kwargs)
        
        manifest_path = self.manifest_folder / f"{manifest_id}.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return True
    
    def get_all_manifests(self) -> List[Dict[str, Any]]:
        """
        Get list of all manifests
        
        Returns:
            List of manifest data dictionaries
        """
        manifests = []
        
        for manifest_file in self.manifest_folder.glob("*.json"):
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    manifests.append(manifest)
            except Exception as e:
                print(f"Error loading manifest {manifest_file}: {e}")
        
        # Sort by creation date (newest first)
        manifests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return manifests
    
    def delete_manifest(self, manifest_id: str) -> bool:
        """
        Delete a manifest file
        
        Args:
            manifest_id: ID of the manifest to delete
            
        Returns:
            True if deleted, False if not found
        """
        manifest_path = self.manifest_folder / f"{manifest_id}.json"
        
        if manifest_path.exists():
            manifest_path.unlink()
            return True
        return False
    
    def get_upload_progress(self, manifest_id: str) -> Dict[str, Any]:
        """
        Calculate upload progress for a manifest
        
        Args:
            manifest_id: ID of the manifest
            
        Returns:
            Dictionary with progress information
        """
        manifest = self.load_manifest(manifest_id)
        
        if not manifest:
            return {"error": "Manifest not found"}
        
        total_chunks = manifest["total_chunks"]
        uploaded_chunks = sum(
            1 for chunk in manifest["chunks"]
            if chunk.get("status") == "uploaded"
        )
        
        progress_percent = (uploaded_chunks / total_chunks * 100) if total_chunks > 0 else 0
        
        return {
            "total_chunks": total_chunks,
            "uploaded_chunks": uploaded_chunks,
            "remaining_chunks": total_chunks - uploaded_chunks,
            "progress_percent": progress_percent,
            "status": manifest.get("status", "unknown")
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def create_chunk_info(
        self,
        index: int,
        filename: str,
        local_path: str,
        size: int,
        hash_value: str,
        drive_name: str,
        remote_path: str
    ) -> Dict[str, Any]:
        """
        Create a chunk information dictionary
        
        Args:
            index: Chunk index
            filename: Chunk filename
            local_path: Local path to chunk file
            size: Chunk size in bytes
            hash_value: SHA-256 hash of chunk
            drive_name: Name of the drive where chunk will be stored
            remote_path: Remote path where chunk will be uploaded
            
        Returns:
            Chunk info dictionary
        """
        return {
            "index": index,
            "filename": filename,
            "local_path": local_path,
            "size": size,
            "size_formatted": self._format_size(size),
            "hash": hash_value,
            "drive": drive_name,
            "remote_path": remote_path,
            "status": "pending",
            "uploaded_at": None
        }


if __name__ == "__main__":
    # Test the manifest manager
    manager = ManifestManager()
    
    # Example chunk data
    chunks = [
        manager.create_chunk_info(
            index=0,
            filename="test.part0000.chunk",
            local_path="chunks/test.part0000.chunk",
            size=104857600,
            hash_value="abc123...",
            drive_name="drive1",
            remote_path="MultiDriveSplit/test.part0000.chunk"
        )
    ]
    
    # Create manifest
    manifest_id = manager.create_manifest(
        original_filename="test_file.bin",
        original_path="/path/to/test_file.bin",
        total_size=104857600,
        file_hash="xyz789...",
        chunks=chunks
    )
    
    print(f"Created manifest: {manifest_id}")
    
    # Get progress
    progress = manager.get_upload_progress(manifest_id)
    print(f"Progress: {progress}")
