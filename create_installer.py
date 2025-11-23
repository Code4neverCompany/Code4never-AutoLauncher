import os
import sys
import glob
import shutil
import subprocess
from pathlib import Path

def create_installer():
    print("Building Installer...")
    
    # Find latest release zip
    release_dir = Path("release")
    zips = list(release_dir.glob("c4n-AutoLauncher_v*.zip"))
    
    if not zips:
        print("No release ZIP found in release/ directory. Build the app first.")
        return False
        
    # Get latest by modification time
    latest_zip = max(zips, key=os.path.getmtime)
    print(f"Using release package: {latest_zip}")
    
    # Create a temporary spec file or just run pyinstaller command
    # We need to bundle the zip as 'app_package.zip'
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", f"Autolauncher_Setup_{latest_zip.stem.split('_')[-1]}", # Setup_TIMESTAMP
        "--add-data", f"{latest_zip};.", # Add zip to root of bundle
        "--icon", "assets/icon.ico",
        "installer_script.py"
    ]
    
    # We need to rename the zip inside the bundle to a constant name so the script can find it
    # PyInstaller --add-data "source;dest"
    # On Windows it is ; separator
    
    # Actually, to make it easier, let's copy the zip to a temp name 'app_package.zip' first
    temp_zip = Path("app_package.zip")
    shutil.copy2(latest_zip, temp_zip)
    
    try:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--noconsole",
            "--name", f"Autolauncher_Setup",
            "--add-data", f"app_package.zip;.",
            "--icon", "assets/icon.ico",
            "--clean",
            "installer_script.py"
        ]
        
        print("Running PyInstaller for Setup.exe...")
        subprocess.check_call(cmd)
        
        # Move the setup exe to release folder
        dist_setup = Path("dist/Autolauncher_Setup.exe")
        if dist_setup.exists():
            # Extract version from zip name (e.g., c4n-AutoLauncher_v1.0.0.zip -> v1.0.0)
            version_part = latest_zip.stem.replace('c4n-AutoLauncher_', '')
            target_name = f"Autolauncher_Setup_{version_part}.exe"
            target_path = release_dir / target_name
            shutil.move(str(dist_setup), str(target_path))
            print(f"Installer created: {target_path}")
            return True
        else:
            print("Setup executable not found in dist/")
            return False
            
    except Exception as e:
        print(f"Failed to build installer: {e}")
        return False
    finally:
        if temp_zip.exists():
            os.remove(temp_zip)
            
if __name__ == "__main__":
    create_installer()
