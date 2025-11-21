"""
Apply Rounded Icons - Autolauncher
Replaces current icons with rounded corner versions.

© 2025 4never Company. All rights reserved.
"""

import shutil
from pathlib import Path

def main():
    """Replace current icons with rounded versions."""
    print("=" * 60)
    print("  Applying Rounded Corner Icons")
    print("  © 2025 4never Company. All rights reserved.")
    print("=" * 60)
    print()
    
    assets_dir = Path("assets")
    
    # Mapping of rounded files to their targets
    replacements = [
        ('icon_rounded.png', 'icon.png'),
        ('icon_rounded.ico', 'icon.ico'),
        ('logo_dark_rounded.png', 'logo_dark.png'),
        ('logo_light_rounded.png', 'logo_light.png'),
    ]
    
    success_count = 0
    
    for rounded_name, target_name in replacements:
        rounded_path = assets_dir / rounded_name
        target_path = assets_dir / target_name
        
        if not rounded_path.exists():
            print(f"⚠ Warning: {rounded_path} not found, skipping")
            continue
        
        # Replace the file
        try:
            shutil.copy2(rounded_path, target_path)
            print(f"✓ Replaced {target_name} with rounded version")
            success_count += 1
        except Exception as e:
            print(f"✗ Error replacing {target_name}: {e}")
    
    print()
    print("=" * 60)
    
    if success_count > 0:
        print(f"  Successfully applied {success_count} rounded icons!")
        print("=" * 60)
        print()
        print("Changes applied:")
        print("  • Window icon updated to rounded version")
        print("  • System tray icon updated to rounded version")
        print("  • Logos updated to rounded versions")
        print()
        print("Next steps:")
        print("  1. Restart the application to see the changes")
        print("  2. Rebuild executable: python build_exe.py")
    else:
        print("  No changes applied.")
        print("=" * 60)
        print()
        print("Please run 'python round_corners.py' first to create rounded versions.")
    
    print()

if __name__ == "__main__":
    main()
