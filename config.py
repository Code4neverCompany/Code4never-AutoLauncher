"""
Configuration module for Autolauncher application.
Contains application-wide settings, paths, and debug mode configuration.
"""

import sys
import os
from pathlib import Path

# Application Information
APP_NAME = "Autolauncher"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Code4never"

# Directories
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as Python script
    BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# File Paths
TASKS_FILE = DATA_DIR / "tasks.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

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
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 600
TIMER_UPDATE_INTERVAL = 1000  # Update countdown every 1 second (in milliseconds)

# Theme Settings
DEFAULT_THEME = "Light"  # Options: "Light", "Dark", "Auto"
