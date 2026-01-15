"""
Configuration module for Autolauncher application.
Contains application-wide settings, paths, and debug mode configuration.
"""

import sys
import os
from pathlib import Path

# Application Information
APP_NAME = "c4n-AutoLauncher"
APP_VERSION = "1.6.0"
APP_AUTHOR = "Code4never"

# Localization
DEFAULT_LANGUAGE = "en"

# Directories
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    # PyInstaller 6.x puts resources in _internal folder
    BASE_DIR = Path(sys.executable).parent
    INTERNAL_DIR = BASE_DIR / "_internal"
    
    # Check if _internal exists (PyInstaller 6.x), otherwise use BASE_DIR
    if INTERNAL_DIR.exists():
        ASSETS_DIR = INTERNAL_DIR / "assets"
    else:
        ASSETS_DIR = BASE_DIR / "assets"
    
    LOGS_DIR = BASE_DIR / "logs"
else:
    # Running as Python script
    BASE_DIR = Path(__file__).parent
    LOGS_DIR = BASE_DIR / "logs"
    ASSETS_DIR = BASE_DIR / "assets"

# User data directory - Use AppData for update-proof storage
# This ensures user's tasks and settings survive application updates
APPDATA = os.getenv('APPDATA')
if APPDATA:
    DATA_DIR = Path(APPDATA) / APP_NAME
else:
    # Fallback for non-Windows or missing APPDATA
    DATA_DIR = Path.home() / f".{APP_NAME}"

# Old data directory (for migration)
OLD_DATA_DIR = BASE_DIR / "data"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# Migrate existing data from old location if needed
def _migrate_user_data():
    """Migrate user data from old app directory to AppData."""
    migration_marker = DATA_DIR / ".migrated"
    
    # Skip if already migrated
    if migration_marker.exists():
        return
    
    # Check if old data exists
    if OLD_DATA_DIR.exists():
        import shutil
        for file_name in ["tasks.json", "settings.json"]:
            old_file = OLD_DATA_DIR / file_name
            new_file = DATA_DIR / file_name
            
            # Only migrate if old file exists and new file doesn't
            if old_file.exists() and not new_file.exists():
                try:
                    shutil.copy2(old_file, new_file)
                    print(f"Migrated {file_name} to AppData")
                except Exception as e:
                    print(f"Failed to migrate {file_name}: {e}")
    
    # Mark migration as complete
    migration_marker.touch()

# Run migration
_migrate_user_data()

# File Paths
TASKS_FILE = DATA_DIR / "tasks.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
BLOCKLIST_FILE = DATA_DIR / "blocklist.json"

# Icon Paths
WINDOW_ICON_PATH = ASSETS_DIR / "icon.ico"
TRAY_ICON_PATH = ASSETS_DIR / "icon.png"
LOGO_DARK_PATH = ASSETS_DIR / "logo_dark.png"
LOGO_LIGHT_PATH = ASSETS_DIR / "logo_light.png"

# Logging Configuration
# Debug mode can be enabled via environment variable: set DEBUG=1
DEBUG_MODE = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes", "on")

# Log Levels
if DEBUG_MODE:
    LOG_LEVEL = "DEBUG"
    CONSOLE_LOG_LEVEL = "DEBUG"
    FILE_LOG_LEVEL = "DEBUG"
else:
    LOG_LEVEL = "INFO"
    CONSOLE_LOG_LEVEL = "INFO"
    FILE_LOG_LEVEL = "INFO"

# Log File Settings
LOG_FILE = LOGS_DIR / "autolauncher.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3  # Keep 3 backup log files

# UI Settings
DEFAULT_WINDOW_WIDTH = 1100
DEFAULT_WINDOW_HEIGHT = 650
TIMER_UPDATE_INTERVAL = 1000  # Update countdown every 1 second (in milliseconds)

# Theme Settings
DEFAULT_THEME = "Light"  # Options: "Light", "Dark", "Auto"

# Stuck Detection Settings
# Keywords to look for in window titles that indicate a process is waiting for update/restart
STUCK_DETECTION_KEYWORDS = [
    "Update Available",
    "Check for Updates",
    "Restart Required",
    "Setup",
    "Installer",
    "Patching",
    "Updating",
    "New Version",
    "Release Notes",
    "Notice"
]

# OCR Keywords (Text inside the window)
STUCK_DETECTION_OCR_KEYWORDS = [
    "update available",
    "new version available",
    "restart the application",
    "download and install",
    "critical update",
    "patch required",
    "patching progress",
    "setup wizard",
    "installation complete",
    "update ready",
    "update required",
    "error"
]

# Confirmation Dialog Keywords - Dialogs that can be auto-dismissed by clicking a button
# These dialogs block task progression and need a button click (Confirm, OK, Continue, etc.)
CONFIRMATION_DIALOG_KEYWORDS = [
    "patching complete",
    "update complete",
    "the game is restarting",
    "restart required",
    "installation complete",
    "download complete",
    "ready to play",
    "click to continue",
    "press any key",
    "click ok to continue",
    "notice",
]

# Button labels to look for when auto-dismissing confirmation dialogs
CONFIRMATION_BUTTON_LABELS = [
    "Confirm",
    "OK",
    "Continue",
    "Play",
    "Start",
    "Launch",
    "Restart",
    "Close",
    "Yes",
    "Accept",
]

# Default Blocklist - Programs that will postpone task execution in Auto mode
# Users can customize this list in Settings
DEFAULT_BLOCKLIST_PROCESSES = [
    # Games
    'valorant.exe', 'valorant-win64-shipping.exe',
    'leagueclient.exe', 'league of legends.exe',
    'csgo.exe', 'cs2.exe',
    'fortnite.exe', 'fortniteclient-win64-shipping.exe',
    'rocketleague.exe',
    'gta5.exe', 'gtavlauncher.exe',
    'minecraft.exe', 'javaw.exe',
    'dota2.exe',
    'overwatch.exe',
    'apex_legends.exe', 'r5apex.exe',
    'cod.exe', 'modernwarfare.exe',
    'pubg.exe', 'tslgame.exe',
    'eldenring.exe',
    'cyberpunk2077.exe',
    'hogwartslegacy.exe',
    'plarium play.exe', 'plrhandler.exe',
    'riotclientservices.exe',
    # IDEs (coding detection)
    'code.exe',
    'devenv.exe',
    'pycharm64.exe', 'pycharm.exe',
    'idea64.exe',
    'webstorm64.exe',
    'sublime_text.exe',
    'atom.exe',
]
