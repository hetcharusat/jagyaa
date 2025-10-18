"""
File Chunking Module
Handles splitting files into chunks and merging them back
"""
import os
import hashlib
from pathlib import Path
from typing import List, Tuple, Callable, Optional


class FileChunker:
    """Handles file splitting and merging operations"""
    
    def __init__(self, chunk_size_mb: int = 100):
        """
        Initialize FileChunker
        
        Args:
            chunk_size_mb: Size of each chunk in megabytes
        """
        self.chunk_size = chunk_size_mb * 1024 * 1024  # Convert to bytes
    
    def split_file(
        self,
        file_path: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Tuple[str, str, int]]:
        """
        Split a file into chunks
        
        Args:
            file_path: Path to the file to split
            output_dir: Directory to store chunks
            progress_callback: Optional callback(current_chunk, total_chunks)
            
        Returns:
            List of tuples (chunk_path, sha256_hash, chunk_size)
        """
        file_path = Path(file_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_size = file_path.stat().st_size
        total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
        
        chunks_info = []
        
        with open(file_path, 'rb') as f:
            for chunk_index in range(total_chunks):
                # Read chunk
                chunk_data = f.read(self.chunk_size)
                
                # Generate chunk filename
                chunk_filename = f"{file_path.stem}.part{chunk_index:04d}{file_path.suffix}.chunk"
                chunk_path = output_dir / chunk_filename
                
                # Calculate SHA-256 hash
                sha256_hash = hashlib.sha256(chunk_data).hexdigest()
                
                # Write chunk to file
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)
                
                chunk_size = len(chunk_data)
                chunks_info.append((str(chunk_path), sha256_hash, chunk_size))
                
                # Call progress callback
                if progress_callback:
                    progress_callback(chunk_index + 1, total_chunks)
        
        return chunks_info
    
    def merge_chunks(
        self,
        chunk_paths: List[str],
        output_path: str,
        expected_hashes: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Merge chunks back into original file
        
        Args:
            chunk_paths: List of chunk file paths in order
            output_path: Path for the reconstructed file
            expected_hashes: Optional list of expected SHA-256 hashes for verification
            progress_callback: Optional callback(current_chunk, total_chunks)
            
        Returns:
            True if successful, False otherwise
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        total_chunks = len(chunk_paths)
        
        with open(output_path, 'wb') as output_file:
            for idx, chunk_path in enumerate(chunk_paths):
                chunk_path = Path(chunk_path)
                
                if not chunk_path.exists():
                    print(f"Error: Chunk not found: {chunk_path}")
                    return False
                
                # Read chunk
                with open(chunk_path, 'rb') as chunk_file:
                    chunk_data = chunk_file.read()
                
                # Verify hash if provided
                if expected_hashes:
                    actual_hash = hashlib.sha256(chunk_data).hexdigest()
                    if actual_hash != expected_hashes[idx]:
                        print(f"Error: Hash mismatch for chunk {idx}")
                        print(f"Expected: {expected_hashes[idx]}")
                        print(f"Actual: {actual_hash}")
                        return False
                
                # Write to output file
                output_file.write(chunk_data)
                
                # Call progress callback
                if progress_callback:
                    progress_callback(idx + 1, total_chunks)
        
        return True
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """
        Calculate SHA-256 hash of entire file
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA-256 hash string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format byte size to human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted string (e.g., "1.23 GB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


if __name__ == "__main__":
    # Test the chunker
    chunker = FileChunker(chunk_size_mb=10)
    
    def progress(current, total):
        print(f"Progress: {current}/{total}")
    
    # Example usage
    # chunks = chunker.split_file("test_file.bin", "chunks", progress)
    # print(f"Created {len(chunks)} chunks")
    
    # success = chunker.merge_chunks(
    #     [c[0] for c in chunks],
    #     "reconstructed_file.bin",
    #     [c[1] for c in chunks],
    #     progress
    # )
    # print(f"Merge successful: {success}")
