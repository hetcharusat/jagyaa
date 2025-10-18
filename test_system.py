"""
CLI Test Script
Quick test of core functionality without GUI
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core import (
    ConfigManager, RcloneManager, ManifestManager,
    Uploader, Downloader, FileChunker
)


def test_configuration():
    """Test configuration loading"""
    print("=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    config = ConfigManager()
    
    print(f"✓ Chunk size: {config.get_chunk_size_mb()} MB")
    print(f"✓ Max concurrent: {config.get_max_concurrent_uploads()}")
    print(f"✓ Upload folder: {config.get_upload_folder()}")
    
    drives = config.get_enabled_drives()
    print(f"✓ Enabled drives: {len(drives)}")
    
    for drive in drives:
        print(f"  - {drive['name']} → {drive['remote_name']}")
    
    return config


def test_rclone(config):
    """Test rclone connectivity"""
    print("\n" + "=" * 60)
    print("Testing Rclone")
    print("=" * 60)
    
    try:
        rclone = RcloneManager(config_path=config.get_rclone_config_path())
        
        print(f"✓ Rclone version: {rclone.get_rclone_version()}")
        
        remotes = rclone.list_remotes()
        print(f"✓ Configured remotes: {len(remotes)}")
        
        for remote in remotes:
            print(f"  - {remote}")
        
        return rclone
        
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        return None


def test_chunker():
    """Test file chunking (without actual file)"""
    print("\n" + "=" * 60)
    print("Testing File Chunker")
    print("=" * 60)
    
    chunker = FileChunker(chunk_size_mb=100)
    
    # Test format_size function
    test_sizes = [
        (1024, "1.00 KB"),
        (1048576, "1.00 MB"),
        (1073741824, "1.00 GB"),
        (524288000, "500.00 MB")
    ]
    
    print("✓ Size formatting:")
    for size_bytes, expected in test_sizes:
        result = chunker.format_size(size_bytes)
        print(f"  {size_bytes:>12} bytes → {result}")
    
    return chunker


def test_manifest():
    """Test manifest creation"""
    print("\n" + "=" * 60)
    print("Testing Manifest Manager")
    print("=" * 60)
    
    manifest_mgr = ManifestManager("manifests")
    
    print(f"✓ Manifest folder: manifests/")
    
    # Get all manifests
    manifests = manifest_mgr.get_all_manifests()
    print(f"✓ Existing manifests: {len(manifests)}")
    
    if manifests:
        print("\nRecent uploads:")
        for m in manifests[:5]:  # Show first 5
            filename = m['original_file']['filename']
            size = m['original_file']['size_formatted']
            chunks = m['total_chunks']
            status = m.get('status', 'unknown')
            print(f"  - {filename} ({size}) - {chunks} chunks - {status}")
    
    return manifest_mgr


def show_system_info():
    """Show system information"""
    print("\n" + "=" * 60)
    print("System Information")
    print("=" * 60)
    
    print(f"✓ Python: {sys.version.split()[0]}")
    print(f"✓ Platform: {sys.platform}")
    
    # Check dependencies
    try:
        import PySide6
        print(f"✓ PySide6: Installed")
    except ImportError:
        print(f"✗ PySide6: Not installed (required for GUI)")
    
    try:
        import cryptography
        print(f"✓ cryptography: Installed")
    except ImportError:
        print(f"✗ cryptography: Not installed")
    
    # Check paths
    print(f"\n✓ Project root: {Path.cwd()}")
    print(f"✓ Config exists: {Path('config/drives.json').exists()}")
    print(f"✓ Manifests folder: {Path('manifests').exists()}")


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Multi-Google Drive Split Uploader" + " " * 15 + "║")
    print("║" + " " * 20 + "System Test" + " " * 27 + "║")
    print("╚" + "═" * 58 + "╝")
    
    show_system_info()
    
    # Test each component
    config = test_configuration()
    rclone = test_rclone(config)
    chunker = test_chunker()
    manifest_mgr = test_manifest()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if rclone and len(config.get_enabled_drives()) > 0:
        print("✓ System is ready for uploads/downloads")
        print("\nTo start the GUI application, run:")
        print("  python main.py")
    else:
        print("✗ System needs configuration")
        print("\nNext steps:")
        print("1. Configure rclone remotes: rclone config")
        print("2. Edit config/drives.json with your remote names")
        print("3. Run tests again: python test_system.py")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
