"""
Post-Release Cleanup Script
Cleans up build artifacts and old release files after successful GitHub release.
Keeps only the latest version in the release/ folder.

© 2025 4never Company. All rights reserved.
"""

import os
import glob
import json
from pathlib import Path

def load_current_version():
    """Load current version from version_info.json."""
    with open('version_info.json', 'r') as f:
        data = json.load(f)
        return data.get('version', '0.0.0')

def cleanup_old_releases(keep_version):
    """Remove old release artifacts, keeping only the specified version."""
    print(f"Cleaning up old releases (keeping v{keep_version})...\n")
    
    # Patterns to clean from root directory
    patterns = [
        '*.zip',
        '*.exe',
        '*GITHUB_RELEASE*.md',
        '*BUILD_SUMMARY*.md'
    ]
    
    removed_count = 0
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            # Skip if it's the current version
            if keep_version in file_path:
                print(f"  Keeping: {file_path}")
                continue
            
            try:
                os.remove(file_path)
                print(f"  ✓ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ Failed to remove {file_path}: {e}")
    
    # Clean old release artifacts (keep only latest)
    release_dir = Path('release')
    if release_dir.exists():
        for file_path in release_dir.glob('*'):
            if file_path.is_file() and keep_version not in file_path.name:
                try:
                    file_path.unlink()
                    print(f"  ✓ Removed: release/{file_path.name}")
                    removed_count += 1
                except Exception as e:
                    print(f"  ✗ Failed to remove release/{file_path.name}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} old files.")

def cleanup_build_artifacts():
    """Clean up temporary build artifacts."""
    print("\nCleaning build artifacts...")
    
    # Clean __pycache__ recursively
    for pycache_dir in glob.glob('**/__pycache__', recursive=True):
        try:
            import shutil
            shutil.rmtree(pycache_dir)
            print(f"  ✓ Removed: {pycache_dir}")
        except Exception as e:
            print(f"  ✗ Failed to remove {pycache_dir}: {e}")
    
    # Clean other temp files
    temp_files = ['etag_cache.json', 'last_update_check.json']
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"  ✓ Removed: {temp_file}")
            except Exception as e:
                print(f"  ✗ Failed to remove {temp_file}: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Post-Release Cleanup Script")
    print("=" * 60)
    print()
    
    current_version = load_current_version()
    print(f"Current version: {current_version}\n")
    
    cleanup_old_releases(current_version)
    cleanup_build_artifacts()
    
    print("\n" + "=" * 60)
    print("Cleanup Complete!")
    print("=" * 60)
