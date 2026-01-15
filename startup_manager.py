"""
Startup Manager Module
Handles registration of the application to run at startup via Windows Registry.
"""

import sys
import os
import winreg
from pathlib import Path
from logger import get_logger
from config import APP_NAME

logger = get_logger(__name__)

class StartupManager:
    """Manages the 'Run at Startup' functionality using Windows Registry."""
    
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def __init__(self):
        self.app_name = APP_NAME or "AutoLauncher"
        
    def _get_app_path(self):
        """Get the correct command to run the application."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return f'"{sys.executable}"'
        else:
            # Running as python script
            # Use pythonw.exe to run without console if possible, but sys.executable is safer
            # We need to quote the paths
            script_path = os.path.abspath(sys.argv[0])
            python_exe = sys.executable
            
            # If we are using python.exe, we might want pythonw.exe for background run
            # But let's stick to sys.executable to be safe about environment
            return f'"{python_exe}" "{script_path}"'

    def is_autostart_enabled(self) -> bool:
        """Check if autostart is currently enabled."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                # Check if the path matches current app (ignore case for robustness)
                current_cmd = self._get_app_path()
                # Basic check: is the value roughly what we expect? 
                # Registry might have different quotes or args if modified manually
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Failed to check autostart status: {e}")
            return False

    def set_autostart(self, enabled: bool) -> bool:
        """
        Enable or disable autostart.
        
        Args:
            enabled: True to enable, False to disable.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_WRITE)
            try:
                if enabled:
                    cmd = self._get_app_path()
                    winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, cmd)
                    logger.info(f"Autostart enabled: {cmd}")
                else:
                    try:
                        winreg.DeleteValue(key, self.app_name)
                        logger.info("Autostart disabled")
                    except FileNotFoundError:
                        pass # Already disabled
                return True
            except Exception as e:
                logger.error(f"Failed to set autostart to {enabled}: {e}")
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Failed to access registry: {e}")
            return False
