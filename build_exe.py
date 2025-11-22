"""
Build Script for Autolauncher Executable
Automates the process of creating a standalone Windows executable using PyInstaller.

© 2025 4never Company. All rights reserved.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import zipfile
from datetime import datetime

# Colors for console output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.YELLOW}→ {text}{Colors.END}")

def check_dependencies():
    """Check if all required dependencies are installed."""
    print_header("Checking Dependencies")
    
    try:
        import PyInstaller
        print_success(f"PyInstaller is installed (v{PyInstaller.__version__})")
    except ImportError:
        print_error("PyInstaller is not installed!")
        print_info("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=5.13.0"])
        print_success("PyInstaller installed successfully")
    
    # Check if icon file exists
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        print_success(f"Icon file found: {icon_path}")
    else:
        print_error(f"Icon file not found: {icon_path}")
        return False
    
    return True

def clean_build_directories():
    """Remove old build and dist directories."""
    print_header("Cleaning Build Directories")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print_info(f"Removing {dir_name}/")
            shutil.rmtree(dir_path)
            print_success(f"Removed {dir_name}/")
        else:
            print_info(f"{dir_name}/ does not exist, skipping")
    
    print_success("Cleanup complete")

def build_executable():
    """Build the executable using PyInstaller."""
    print_header("Building Executable")
    
    spec_file = "autolauncher.spec"
    
    if not Path(spec_file).exists():
        print_error(f"Spec file not found: {spec_file}")
        return False
    
    print_info(f"Running PyInstaller with {spec_file}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", spec_file, "--clean"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("PyInstaller build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error("PyInstaller build failed!")
        print(e.stderr)
        return False

def verify_executable():
    """Verify the built executable exists."""
    print_header("Verifying Build")
    
    dist_dir = Path("dist/Autolauncher")
    exe_path = dist_dir / "Autolauncher.exe"
    
    if not dist_dir.exists():
        print_error(f"Distribution directory not found at {dist_dir}")
        return False

    if not exe_path.exists():
        print_error(f"Executable not found at {exe_path}")
        return False
    
    # Get directory size
    total_size = 0
    for path in dist_dir.rglob('*'):
        if path.is_file():
            total_size += path.stat().st_size
            
    size_mb = total_size / (1024 * 1024)
    
    print_success(f"Build verified: {dist_dir}")
    print_info(f"Total size: {size_mb:.2f} MB")
    
    return True

def create_release_package():
    """Create a ZIP package for distribution."""
    print_header("Creating Release Package")
    
    dist_dir = Path("dist/Autolauncher")
    
    if not dist_dir.exists():
        print_error("Cannot create package: distribution directory not found")
        return False
    
    # Create release directory
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)
    
    # Generate package name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"Autolauncher_v1.0.0_{timestamp}.zip"
    zip_path = release_dir / zip_name
    
    print_info(f"Creating package: {zip_path}")
    
    shutil.make_archive(str(zip_path.with_suffix('')), 'zip', root_dir='dist', base_dir='Autolauncher')
    
    print_success(f"Release package created: {zip_path}")
    
    # Get package size  
    pkg_size = zip_path.stat().st_size / (1024 * 1024)
    print_info(f"Package size: {pkg_size:.2f} MB")
    
    return True

def main():
    """Main build process."""
    print_header("Autolauncher Executable Build Script")
    print(f"{Colors.BOLD}© 2025 4never Company. All rights reserved.{Colors.END}\n")
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print_error("Dependency check failed. Please install missing dependencies.")
        return 1
    
    # Step 2: Clean old builds
    clean_build_directories()
    
    # Step 3: Build executable
    if not build_executable():
        print_error("Build failed. Check the error messages above.")
        return 1
    
    # Step 4: Verify build
    if not verify_executable():
        print_error("Verification failed. The executable was not created.")
        return 1
    
    # Step 5: Create release package
    create_release_package()
    
    # Success!
    print_header("Build Complete!")
    print_success("Autolauncher executable is ready for distribution")
    print_info("Executable location: dist/Autolauncher.exe")
    print_info("Release package: release/Autolauncher_*.zip\n")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_error("\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
