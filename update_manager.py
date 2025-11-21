"""
Update Manager Module
Handles checking for updates from GitHub and managing version information.
"""

import json
import os
import requests
import webbrowser
from typing import Dict, Optional, List
from logger import get_logger

logger = get_logger(__name__)

VERSION_FILE = "version_info.json"
GITHUB_REPO = "Code4neverCompany/Code4never-AutoLauncher_AlphaVersion"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"

class UpdateManager:
    """
    Manages application updates and version information.
    """
    
    def __init__(self):
        """Initialize the UpdateManager."""
        self.version_info = self._load_version_info()
        logger.info(f"UpdateManager initialized. Current Version: {self.get_current_version()}")

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
            response = requests.get(GITHUB_API_URL, timeout=5)
            
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
                
                # Simple string comparison for now (can be improved with semver lib)
                if latest_tag != current_version:
                    logger.info(f"New version found: {latest_tag}")
                    return {
                        "version": latest_tag,
                        "url": latest_release.get("html_url"),
                        "body": latest_release.get("body"),
                        "assets": latest_release.get("assets", [])
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

    def open_download_page(self, url: str):
        """Open the release page in the default browser."""
        webbrowser.open(url)
