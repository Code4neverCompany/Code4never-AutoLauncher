"""
Enhanced Update Manager Module
Handles checking for updates from GitHub, downloading executables, and managing updates.

© 2025 4never Company. All rights reserved.
"""

import json
import os
import sys
import requests
import webbrowser
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Callable
from logger import get_logger

logger = get_logger(__name__)

VERSION_FILE = "version_info.json"
LAST_CHECK_FILE = "last_update_check.json"
ETAG_CACHE_FILE = "etag_cache.json"
GITHUB_REPO = "Code4neverCompany/Code4never-AutoLauncher"
# Allow overriding URL for testing
GITHUB_API_URL = os.environ.get("AUTOLAUNCHER_UPDATE_URL", f"https://api.github.com/repos/{GITHUB_REPO}/releases")

class UpdateManager:
    """
    Manages application updates and version information.
    Supports automatic executable downloads and installations.
    """
    
    def __init__(self):
        """Initialize the UpdateManager."""
        self.version_info = self._load_version_info()
        # Allow forcing executable mode for testing
        self.is_executable = getattr(sys, 'frozen', False) or os.environ.get("AUTOLAUNCHER_TEST_MODE") == "1"
        self.etag_cache = self._load_etag_cache()
        logger.info(f"UpdateManager initialized. Current Version: {self.get_current_version()}")
        logger.info(f"Running as: {'Executable' if self.is_executable else 'Python Script'}")

    def _load_version_info(self) -> Dict:
        """Load version info from local JSON file."""
        try:
            # PyInstaller 6.x puts data files in _internal folder
            if getattr(sys, 'frozen', False):
                # Running as executable - check _internal folder
                exe_dir = os.path.dirname(sys.executable)
                version_file = os.path.join(exe_dir, '_internal', VERSION_FILE)
                if not os.path.exists(version_file):
                    # Fallback to root for older builds
                    version_file = os.path.join(exe_dir, VERSION_FILE)
            else:
                # Running as script - use current directory
                version_file = VERSION_FILE
            
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load version info: {e}")
        
        # Fallback default
        return {
            "version": "0.0.0",
            "build_date": "Unknown",
            "changelog": []
        }

    def get_current_version(self) -> str:
        """Get the current application version."""
        return self.version_info.get("version", "0.0.0")

    def get_changelog(self) -> List[Dict]:
        """Get the full changelog."""
        return self.version_info.get("changelog", [])
    
    def _load_etag_cache(self) -> Dict:
        """Load ETag cache from file."""
        try:
            if os.path.exists(ETAG_CACHE_FILE):
                with open(ETAG_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not load ETag cache: {e}")
        return {}
    
    def _save_etag_cache(self):
        """Save ETag cache to file."""
        try:
            with open(ETAG_CACHE_FILE, 'w') as f:
                json.dump(self.etag_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save ETag cache: {e}")
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings (supports 1.0.0 and 1.0.0a).
        
        Returns:
            1 if version1 > version2
            0 if version1 == version2
            -1 if version1 < version2
        """
        import re
        
        def parse_version(v):
            # Remove 'v' prefix
            v = v.lstrip('v')
            # Split into main parts and potential suffix
            # Matches 1.0.3, 1.0.3a, 1.0.3-alpha, etc.
            match = re.match(r"(\d+)\.(\d+)\.(\d+)([a-z]?)", v)
            if match:
                major, minor, patch, suffix = match.groups()
                # Convert suffix to a number for comparison: '' -> 0, 'a' -> 1, 'b' -> 2
                suffix_val = 0
                if suffix:
                    suffix_val = ord(suffix) - 96 # 'a' is 97
                return (int(major), int(minor), int(patch), suffix_val)
            return (0, 0, 0, 0)
        
        try:
            v1_tuple = parse_version(version1)
            v2_tuple = parse_version(version2)
            
            if v1_tuple > v2_tuple:
                return 1
            elif v1_tuple < v2_tuple:
                return -1
            else:
                return 0
        except Exception as e:
            logger.error(f"Version comparison error: {e}")
            # Fallback to string comparison
            if version1 > version2:
                return 1
            elif version1 < version2:
                return -1
            return 0

    def check_for_updates(self) -> tuple[Optional[Dict], Optional[str]]:
        """
        Check GitHub for the latest release using ETag for efficiency.
        
        Returns:
            Tuple containing:
            - Dictionary with release info if update available, None otherwise.
            - Error message string if check failed, None otherwise.
        """
        try:
            logger.info("Checking for updates...")
            
            # Prepare headers with ETag if available
            headers = {
                'User-Agent': 'AutoLauncher-Updater'  # Required by GitHub API
            }
            etag = self.etag_cache.get('releases_etag')
            if etag:
                headers['If-None-Match'] = etag
                logger.debug(f"Using cached ETag: {etag[:20]}...")
            
            # Fetch list of releases
            response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
            
            # Handle 304 Not Modified - no changes since last check
            if response.status_code == 304:
                logger.info("No changes detected (304 Not Modified)")
                # Use cached data if available
                if 'last_releases_data' in self.etag_cache:
                    releases = self.etag_cache['last_releases_data']
                else:
                    return None, None
            elif response.status_code == 200:
                releases = response.json()
                
                # Cache the ETag and response data
                new_etag = response.headers.get('ETag')
                if new_etag:
                    self.etag_cache['releases_etag'] = new_etag
                    self.etag_cache['last_releases_data'] = releases
                    self._save_etag_cache()
                    logger.debug(f"Cached new ETag: {new_etag[:20]}...")
                
                if not releases:
                    logger.info("No releases found.")
                    return None, None
            elif response.status_code == 404:
                msg = "Update source unavailable. The publisher may be working on a new version or release."
                logger.warning(msg)
                return None, msg
            else:
                msg = f"Failed to check updates. Status: {response.status_code}"
                logger.warning(msg)
                return None, msg
            
            # Process releases (same logic as before)
            latest_release = releases[0]
            latest_tag = latest_release.get("tag_name", "").lstrip("v")
            current_version = self.get_current_version()
            
            logger.debug(f"Latest GitHub release: {latest_tag}, Current: {current_version}")
            
            # Use semantic version comparison
            if self._compare_versions(latest_tag, current_version) > 0:
                logger.info(f"New version found: {latest_tag}")
                
                # Find the .zip asset in the release
                assets = latest_release.get("assets", [])
                update_asset = None
                for asset in assets:
                    if asset.get("name", "").endswith(".zip"):
                        update_asset = asset
                        break
                
                return {
                    "version": latest_tag,
                    "url": latest_release.get("html_url"),
                    "body": latest_release.get("body"),
                    "assets": assets,
                    "zip_asset": update_asset,  # Changed from exe_asset to zip_asset
                    "exe_asset": update_asset,  # Keep for backwards compatibility
                    "can_auto_update": update_asset is not None and self.is_executable
                }, None
            else:
                logger.info("Application is up to date.")
                return None, None
                
        except Exception as e:
            msg = f"Error checking for updates: {str(e)}"
            logger.error(msg)
            return None, msg

    def get_all_releases(self, include_prereleases: bool = True) -> List[Dict]:
        """
        Get all available releases from GitHub.
        
        Args:
            include_prereleases: Whether to include pre-release versions
            
        Returns:
            List of release dictionaries with version, date, and notes
        """
        try:
            logger.info("Fetching all releases from GitHub...")
            headers = {'User-Agent': 'AutoLauncher-Updater'}
            response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
            
            if response.status_code == 200:
                releases = response.json()
                
                result = []
                for release in releases:
                    # Skip prereleases if requested
                    if not include_prereleases and release.get("prerelease", False):
                        continue
                    
                    version = release.get("tag_name", "").lstrip("v")
                    
                    # Find ZIP asset for this release
                    assets = release.get("assets", [])
                    zip_asset = None
                    for asset in assets:
                        if asset.get("name", "").endswith(".zip"):
                            zip_asset = asset
                            break
                    
                    result.append({
                        "version": version,
                        "date": release.get("published_at", "Unknown"),
                        "body": release.get("body", ""),
                        "prerelease": release.get("prerelease", False),
                        "url": release.get("html_url", ""),
                        "assets": assets,
                        "zip_asset": zip_asset
                    })
                
                logger.info(f"Found {len(result)} releases")
                return result
            else:
                logger.warning(f"Failed to fetch releases: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching all releases: {e}")
            return []

    def check_for_updates_silent(self) -> tuple[Optional[Dict], Optional[str]]:
        """
        Check for updates silently without logging errors prominently.
        Ideal for background/automatic checks.
        
        Returns:
            Same as check_for_updates() but with reduced logging verbosity
        """
        try:
            headers = {'User-Agent': 'AutoLauncher-Updater'}
            response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
            
            if response.status_code == 200:
                releases = response.json()
                if not releases:
                    return None, None
                    
                latest_release = releases[0]
                latest_tag = latest_release.get("tag_name", "").lstrip("v")
                current_version = self.get_current_version()
                
                if self._compare_versions(latest_tag, current_version) > 0:
                    # Find the .zip asset in the release
                    assets = latest_release.get("assets", [])
                    update_asset = None
                    for asset in assets:
                        if asset.get("name", "").endswith(".zip"):
                            update_asset = asset
                            break
                    
                    return {
                        "version": latest_tag,
                        "url": latest_release.get("html_url"),
                        "body": latest_release.get("body"),
                        "assets": assets,
                        "zip_asset": update_asset,  # Changed from exe_asset to zip_asset
                        "exe_asset": update_asset,  # Keep for backwards compatibility
                        "can_auto_update": update_asset is not None and self.is_executable
                    }, None
                else:
                    return None, None
            else:
                return None, f"Status: {response.status_code}"
                
        except Exception as e:
            return None, str(e)

    def should_check_for_updates(self) -> bool:
        """
        Determine if an update check should be performed based on user settings.
        
        Returns:
            True if check should be performed, False otherwise
        """
        from task_manager import SettingsManager
        settings = SettingsManager()
        
        frequency = settings.get('auto_update_frequency', 'startup')
        
        if frequency == 'disabled':
            return False
        
        if frequency == 'startup':
            # Only check on startup - this will be handled by the app initialization
            return True
        
        last_check = self.get_last_check_time()
        if not last_check:
            return True
        
        time_since_check = datetime.now() - last_check
        
        if frequency == 'daily' and time_since_check >= timedelta(days=1):
            return True
        elif frequency == 'weekly' and time_since_check >= timedelta(weeks=1):
            return True
        
        return False

    def get_last_check_time(self) -> Optional[datetime]:
        """
        Get the timestamp of the last update check.
        
        Returns:
            datetime object of last check, or None if never checked
        """
        try:
            if os.path.exists(LAST_CHECK_FILE):
                with open(LAST_CHECK_FILE, 'r') as f:
                    data = json.load(f)
                    timestamp_str = data.get('last_check_time')
                    if timestamp_str:
                        return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.debug(f"Could not read last check time: {e}")
        return None

    def save_last_check_time(self, result: str = "no_update", version: Optional[str] = None):
        """
        Save the current time as the last update check time.
        
        Args:
            result: Result of the check ("no_update", "update_available", "error")
            version: Version number if update available
        """
        try:
            data = {
                "last_check_time": datetime.now().isoformat(),
                "last_check_result": result,
                "last_available_version": version
            }
            with open(LAST_CHECK_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved last check time: {result}")
        except Exception as e:
            logger.warning(f"Could not save last check time: {e}")

    def get_last_check_info(self) -> Dict:
        """
        Get information about the last update check.
        
        Returns:
            Dictionary with last check info
        """
        try:
            if os.path.exists(LAST_CHECK_FILE):
                with open(LAST_CHECK_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not read last check info: {e}")
        
        return {
            "last_check_time": None,
            "last_check_result": "never",
            "last_available_version": None
        }

    def download_update(self, asset: Dict, progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[str]:
        """
        Download an update asset using Python requests.
        
        Args:
            asset: Asset dictionary from GitHub API
            progress_callback: Optional callback function(downloaded_bytes, total_bytes)
            
        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            download_url = asset.get("browser_download_url")
            file_name = asset.get("name")
            file_size = asset.get("size", 0)
            
            if not download_url:
                logger.error("No download URL found in asset")
                return None
            
            logger.info("=" * 60)
            logger.info("STARTING UPDATE DOWNLOAD (Native)")
            logger.info("=" * 60)
            logger.info(f"Asset Name: {file_name}")
            logger.info(f"Expected Size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
            logger.info(f"Download URL: {download_url}")
            
            # Create temp directory for download
            temp_dir = tempfile.mkdtemp(prefix="autolauncher_update_")
            download_path = os.path.join(temp_dir, file_name)
            
            logger.info(f"Download Destination: {download_path}")
            
            # Use requests for download
            headers = {'User-Agent': 'AutoLauncher-Updater'}
            with requests.get(download_url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0)) or file_size
                
                with open(download_path, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded, total_length)
            
            # Verify download
            if not os.path.exists(download_path):
                logger.error("Download file missing after stream completion.")
                return None
                
            actual_size = os.path.getsize(download_path)
            logger.info("=" * 60)
            logger.info("DOWNLOAD COMPLETED")
            logger.info(f"Downloaded: {actual_size:,} bytes")
            
            if actual_size == 0:
                logger.error("DOWNLOAD FAILED: File is 0 bytes")
                return None
                
            return download_path

        except Exception as e:
            logger.error("=" * 60)
            logger.error("DOWNLOAD FAILED")
            logger.error(f"Error: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            logger.error("=" * 60)
            return None

    def install_update_and_restart(self, zip_path: str) -> bool:
        """
        Install an update by extracting the ZIP and replacing the current directory.
        
        Args:
            zip_path: Path to the downloaded ZIP file
            
        Returns:
            True if installation started successfully
        """
        import zipfile
        
        try:
            logger.info("=" * 60)
            logger.info("STARTING UPDATE INSTALLATION PROCESS")
            logger.info("=" * 60)
            
            if not self.is_executable:
                logger.warning("Cannot auto-update when running as Python script")
                logger.info("Please manually download and run the update from GitHub")
                return False
            
            current_exe = sys.executable
            logger.info(f"Current executable: {current_exe}")
            
            # Test mode support: Redirect installation to temp dir
            if os.environ.get("AUTOLAUNCHER_TEST_MODE") == "1":
                install_dir = os.path.join(tempfile.gettempdir(), "autolauncher_test_install")
                os.makedirs(install_dir, exist_ok=True)
                # Create a dummy exe to simulate the running app
                current_exe = os.path.join(install_dir, "Autolauncher.exe")
                if not os.path.exists(current_exe):
                    with open(current_exe, 'w') as f:
                        f.write("dummy executable content")
                logger.info(f"TEST MODE: Redirected install to {install_dir}")
            else:
                install_dir = os.path.dirname(current_exe)
                
            logger.info(f"Install directory: {install_dir}")
            logger.info(f"Update package: {zip_path}")
            
            # Verify ZIP file exists
            if not os.path.exists(zip_path):
                logger.error(f"Update package not found: {zip_path}")
                logger.error("INSTALLATION ABORTED: ZIP file does not exist")
                return False
            
            logger.info(f"Update package size: {os.path.getsize(zip_path):,} bytes ({os.path.getsize(zip_path) / (1024*1024):.2f} MB)")
            
            # Verify ZIP is valid before extraction
            try:
                with zipfile.ZipFile(zip_path, 'r') as test_zip:
                    zip_info = test_zip.infolist()
                    logger.info(f"ZIP contains {len(zip_info)} files")
                    logger.info(f"First few files: {[f.filename for f in zip_info[:5]]}")
            except Exception as e:
                logger.error(f"ZIP file is corrupted or invalid: {e}")
                logger.error("INSTALLATION ABORTED: Invalid ZIP file")
                return False
            
            # Extract ZIP to a temp folder
            temp_extract_dir = os.path.join(os.path.dirname(zip_path), "extracted")
            os.makedirs(temp_extract_dir, exist_ok=True)
            
            logger.info(f"Extracting update to {temp_extract_dir}...")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_dir)
                logger.info("Extraction complete")
            except Exception as e:
                logger.error(f"Failed to extract ZIP: {e}")
                logger.error("INSTALLATION ABORTED: Extraction failed")
                return False
                
            # The zip contains a folder 'c4n-AutoLauncher' or 'Autolauncher', find it
            extracted_contents = os.listdir(temp_extract_dir)
            logger.info(f"Extracted contents ({len(extracted_contents)} items):")
            for item in extracted_contents:
                item_path = os.path.join(temp_extract_dir, item)
                if os.path.isdir(item_path):
                    logger.info(f"  [DIR]  {item}/")
                else:
                    logger.info(f"  [FILE] {item}")
            
            source_dir = None
            
            for item in extracted_contents:
                item_path = os.path.join(temp_extract_dir, item)
                if os.path.isdir(item_path) and ('autolauncher' in item.lower() or 'c4n' in item.lower()):
                    source_dir = item_path
                    break
            
            if not source_dir:
                # Fallback: use temp dir directly if no subfolder found
                source_dir = temp_extract_dir
                logger.warning("No autolauncher subfolder found, using extraction root")
            
            logger.info(f"Source directory for update: {source_dir}")
            
            # List source directory contents
            source_contents = os.listdir(source_dir)
            logger.info(f"Source directory contents ({len(source_contents)} items):")
            for item in source_contents[:20]:  # Show first 20 items
                logger.info(f"  - {item}")
            if len(source_contents) > 20:
                logger.info(f"  ... and {len(source_contents) - 20} more items")
            
            # Verify source directory has expected files
            exe_name = os.path.basename(current_exe)
            expected_exe = os.path.join(source_dir, exe_name)
            
            if not os.path.exists(expected_exe):
                logger.error(f"Update package does not contain the application executable: {exe_name}")
                logger.error(f"Expected at: {expected_exe}")
                logger.error(f"Source dir contents: {os.listdir(source_dir)}")
                logger.error("INSTALLATION ABORTED: Missing executable in update package")
                return False
            
            logger.info(f"Verified executable exists in update package: {exe_name}")
            
            # Create a robust batch script with better error handling
            logger.info("Creating update installer batch script...")
            batch_content = f"""@echo off
echo ========================================
echo   c4n-AutoLauncher Update Installer
echo ========================================
echo.
echo Waiting for application to close...
timeout /t 5 /nobreak >nul

echo Ensuring old process is terminated...
taskkill /F /IM {os.path.basename(current_exe)} >nul 2>&1
timeout /t 3 /nobreak >nul

echo Backing up current version...
if exist "{install_dir}\\backup" rd /s /q "{install_dir}\\backup"
mkdir "{install_dir}\\backup"
xcopy "{install_dir}\\*.exe" "{install_dir}\\backup\\" /Y >nul 2>&1

echo Installing update...
xcopy "{source_dir}" "{install_dir}" /E /H /Y /I /R

if errorlevel 1 (
    echo.
    echo ERROR: Update installation failed!
    echo Attempting to restore backup...
    xcopy "{install_dir}\\backup\\*.exe" "{install_dir}\\" /Y >nul
    echo.
    echo Please download and install the update manually from GitHub.
    pause
    exit /b 1
)

echo Update installed successfully!
echo.
echo Cleaning up...
rd /s /q "{temp_extract_dir}"
rd /s /q "{install_dir}\\backup"

echo Restarting application...
timeout /t 2 /nobreak >nul
start "" "{current_exe}"

echo Done!
exit
"""
            
            batch_path = os.path.join(install_dir, "_update_installer.bat")
            logger.info(f"Writing batch script to: {batch_path}")
            
            try:
                with open(batch_path, 'w') as f:
                    f.write(batch_content)
            except Exception as e:
                logger.error(f"Failed to create batch script: {e}")
                logger.error(f"Target path: {batch_path}")
                logger.error("INSTALLATION ABORTED: Could not create batch script")
                return False
            
            # Verify batch script was created
            if not os.path.exists(batch_path):
                logger.error(f"Batch script not found after creation: {batch_path}")
                logger.error("INSTALLATION ABORTED: Batch script verification failed")
                return False
                
            logger.info(f"Batch script created successfully ({os.path.getsize(batch_path)} bytes)")
            logger.info("Starting update process...")
            
            # Start the batch file in a new console for visibility
            try:
                logger.info(f"Executing: {batch_path}")
                logger.info(f"Working directory: {install_dir}")
                
                process = subprocess.Popen(
                    batch_path,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    shell=True,
                    cwd=install_dir
                )
                
                logger.info(f"Update installer launched with PID: {process.pid}")
                logger.info("Batch script will close this application in 5 seconds")
                logger.info("Application will restart automatically after update installation")
                logger.info("=" * 60)
                return True
                
            except Exception as e:
                logger.error(f"Failed to launch batch script: {e}")
                import traceback
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                logger.error("INSTALLATION ABORTED: Could not execute batch script")
                return False
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error("UPDATE INSTALLATION FAILED")
            logger.error(f"Error: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            logger.error("=" * 60)
            return False



    def open_download_page(self, url: str):
        """Open the release page in the default browser."""
        webbrowser.open(url)
