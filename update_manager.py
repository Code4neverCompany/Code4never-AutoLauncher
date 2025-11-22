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
GITHUB_REPO = "Code4neverCompany/Code4never-AutoLauncher_AlphaVersion"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"

class UpdateManager:
    """
    Manages application updates and version information.
    Supports automatic executable downloads and installations.
    """
    
    def __init__(self):
        """Initialize the UpdateManager."""
        self.version_info = self._load_version_info()
        self.is_executable = getattr(sys, 'frozen', False)
        logger.info(f"UpdateManager initialized. Current Version: {self.get_current_version()}")
        logger.info(f"Running as: {'Executable' if self.is_executable else 'Python Script'}")

    def _load_version_info(self) -> Dict:
        """Load version info from local JSON file."""
        try:
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, 'r') as f:
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
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Returns:
            1 if version1 > version2
            0 if version1 == version2
            -1 if version1 < version2
        """
        def version_tuple(v):
            # Remove 'v' prefix and split
            v = v.lstrip('v')
            parts = v.split('.')
            # Handle alpha/beta versions (e.g., "0.1.1-alpha")
            if '-' in parts[-1]:
                parts[-1] = parts[-1].split('-')[0]
            return tuple(int(x) for x in parts)
        
        try:
            v1_tuple = version_tuple(version1)
            v2_tuple = version_tuple(version2)
            
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
        Check GitHub for the latest release (including pre-releases).
        
        Returns:
            Tuple containing:
            - Dictionary with release info if update available, None otherwise.
            - Error message string if check failed, None otherwise.
        """
        try:
            logger.info("Checking for updates...")
            # Fetch list of releases (first one is the latest)
            response = requests.get(GITHUB_API_URL, timeout=10)
            
            if response.status_code == 200:
                releases = response.json()
                if not releases:
                    logger.info("No releases found.")
                    return None, None
                    
                # Get the most recent release (index 0)
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
                        "exe_asset": update_asset, # Keeping key name for compatibility, but it's a zip now
                        "can_auto_update": update_asset is not None and self.is_executable
                    }, None
                else:
                    logger.info("Application is up to date.")
                    return None, None
            elif response.status_code == 404:
                msg = "Update source unavailable. The publisher may be working on a new version or release."
                logger.warning(msg)
                return None, msg
            else:
                msg = f"Failed to check updates. Status: {response.status_code}"
                logger.warning(msg)
                return None, msg
                
        except Exception as e:
            msg = f"Error checking for updates: {str(e)}"
            logger.error(msg)
            return None, msg

    def check_for_updates_silent(self) -> tuple[Optional[Dict], Optional[str]]:
        """
        Check for updates silently without logging errors prominently.
        Ideal for background/automatic checks.
        
        Returns:
            Same as check_for_updates() but with reduced logging verbosity
        """
        try:
            response = requests.get(GITHUB_API_URL, timeout=10)
            
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
                        "exe_asset": update_asset,
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
        Download an update asset.
        
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
            
            logger.info(f"Downloading {file_name} ({file_size} bytes)...")
            
            # Create temp directory for download
            temp_dir = tempfile.mkdtemp(prefix="autolauncher_update_")
            download_path = os.path.join(temp_dir, file_name)
            
            # Download with progress tracking
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            downloaded = 0
            chunk_size = 8192
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, file_size)
            
            logger.info(f"Download complete: {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
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
            if not self.is_executable:
                logger.warning("Cannot auto-update when running as Python script")
                return False
            
            current_exe = sys.executable
            install_dir = os.path.dirname(current_exe)
            logger.info(f"Install directory: {install_dir}")
            logger.info(f"Update package: {zip_path}")
            
            # Extract ZIP to a temp folder
            temp_extract_dir = os.path.join(os.path.dirname(zip_path), "extracted")
            os.makedirs(temp_extract_dir, exist_ok=True)
            
            logger.info(f"Extracting update to {temp_extract_dir}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
                
            # The zip contains a folder 'Autolauncher', we need the contents of that folder
            # Or if the zip structure changed, we need to be adaptive.
            # Based on build_exe.py, it has 'Autolauncher' as root.
            
            source_dir = os.path.join(temp_extract_dir, "Autolauncher")
            if not os.path.exists(source_dir):
                # Fallback: maybe it was zipped without root folder?
                source_dir = temp_extract_dir
            
            logger.info(f"Source directory for update: {source_dir}")
            
            # Create a batch script to replace the files and restart
            batch_content = f"""@echo off
echo Updating Autolauncher...
timeout /t 2 /nobreak >nul
echo Copying new files...
xcopy "{source_dir}" "{install_dir}" /E /H /Y /I
if errorlevel 1 (
    echo Update failed!
    pause
    exit /b 1
)
echo Update complete! Restarting...
start "" "{current_exe}"
exit
"""
            
            batch_path = os.path.join(install_dir, "_update.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            logger.info("Starting update process...")
            
            # Start the batch file and exit current application
            subprocess.Popen(
                batch_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                shell=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Update installation failed: {e}")
            return False

    def open_download_page(self, url: str):
        """Open the release page in the default browser."""
        webbrowser.open(url)
