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
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

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

    def check_for_updates(self) -> Optional[Dict]:
        """
        Check GitHub for the latest release.
        
        Returns:
            Dictionary with release info if update available, None otherwise.
        """
        try:
            logger.info("Checking for updates...")
            response = requests.get(GITHUB_API_URL, timeout=5)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_tag = release_data.get("tag_name", "").lstrip("v")
                current_version = self.get_current_version()
                
                # Simple string comparison for now (can be improved with semver lib)
                if latest_tag != current_version:
                    logger.info(f"New version found: {latest_tag}")
                    return {
                        "version": latest_tag,
                        "url": release_data.get("html_url"),
                        "body": release_data.get("body"),
                        "assets": release_data.get("assets", [])
                    }
                else:
                    logger.info("Application is up to date.")
            else:
                logger.warning(f"Failed to check updates. Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            
        return None

    def open_download_page(self, url: str):
        """Open the release page in the default browser."""
        webbrowser.open(url)
