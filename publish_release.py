"""
Publish Release Script
Creates installer and publishes both zip and exe to GitHub.
"""

import os
import subprocess
import json

VERSION_FILE = "version_info.json"
RELEASE_DIR = "release"

def load_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    return "0.0.0"

def get_release_package(version):
    """Find the pre-built release package."""
    expected_file = os.path.join(RELEASE_DIR, f"c4n-AutoLauncher_v{version}.zip")
    if os.path.exists(expected_file):
        return expected_file
    
    # Fallback: look for any zip in release folder
    if os.path.exists(RELEASE_DIR):
        for f in os.listdir(RELEASE_DIR):
            if f.endswith('.zip') and version in f:
                return os.path.join(RELEASE_DIR, f)
    
    return None

def get_installer(version):
    """Find the installer exe."""
    expected_file = os.path.join(RELEASE_DIR, f"Autolauncher_Setup_v{version}.exe")
    if os.path.exists(expected_file):
        return expected_file
    return None

def create_installer():
    """Run the installer creation script."""
    print("\n📦 Creating installer...")
    try:
        subprocess.run(["python", "create_installer.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create installer: {e}")
        return False

def create_github_release(version, zip_file, installer_file=None):
    tag = f"v{version}"
    title = f"v{version}"
    
    print(f"\n🚀 Creating GitHub Release {tag}...")
    
    # Build asset list
    assets = [zip_file]
    if installer_file:
        assets.append(installer_file)
    
    # Construct command
    cmd = [
        "gh", "release", "create", tag,
        *assets,
        "--title", title,
        "--notes-file", "latest_release_notes.md"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Release created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create release: {e}")
        return False

def main():
    print("═" * 50)
    print("           PUBLISH RELEASE WORKFLOW")
    print("═" * 50)
    
    # 1. Get Version
    version = load_version()
    print(f"\n📌 Version: {version}")
    
    # 2. Find release package
    zip_file = get_release_package(version)
    if not zip_file:
        print(f"❌ No release package found for v{version}")
        print(f"   Run build_exe.py first to create the package.")
        return
    
    zip_size = os.path.getsize(zip_file) / (1024 * 1024)
    print(f"📁 Package: {zip_file} ({zip_size:.2f} MB)")
    
    # 3. Check/Create installer
    installer_file = get_installer(version)
    if not installer_file:
        print("⚠️  Installer not found, creating...")
        if create_installer():
            installer_file = get_installer(version)
    
    if installer_file:
        installer_size = os.path.getsize(installer_file) / (1024 * 1024)
        print(f"💿 Installer: {installer_file} ({installer_size:.2f} MB)")
    else:
        print("⚠️  No installer available (will publish zip only)")
    
    # 4. Confirm
    print("\n" + "─" * 50)
    confirm = input(f"Ready to publish v{version}? (y/n): ").lower()
    if confirm != 'y':
        print("Aborted.")
        return

    # 5. Publish
    create_github_release(version, zip_file, installer_file)

if __name__ == "__main__":
    main()

