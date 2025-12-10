"""
Stuck Detector Module for Autolauncher.
Detects if a process is stuck in an 'Update' or 'Setup' state by inspecting window titles.
"""

import ctypes
import threading
from typing import List, Optional
from logger import get_logger

logger = get_logger(__name__)

# Windows API Constants and Types
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

class StuckDetector:
    """
    Monitors processes for specific window titles that indicate a stuck state
    (e.g., 'Update Available', 'Setup', 'Restart Required').
    """
    
    def __init__(self):
        self._user32 = ctypes.windll.user32
    
    def get_window_titles(self, pid: int) -> List[str]:
        """
        Get all visible window titles belonging to a specific Process ID.
        
        Args:
            pid: Process ID to check
            
        Returns:
            List of window title strings
        """
        titles = []
        
        def enum_windows_callback(hwnd, lParam):
            try:
                # Get Process ID for this window
                window_pid = ctypes.c_ulong()
                self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                
                if window_pid.value == pid:
                    # Get Window Title
                    length = self._user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        self._user32.GetWindowTextW(hwnd, buff, length + 1)
                        if buff.value:
                            titles.append(buff.value)
                return True
            except Exception:
                return True # Continue enumeration even if one fails

        try:
            self._user32.EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
        except Exception as e:
            logger.error(f"Error enumerating windows for PID {pid}: {e}")
            
        return titles

    def is_process_stuck(self, pids: List[int], keywords: List[str]) -> Optional[str]:
        """
        Check if any of the processes has a window title matching the keywords.
        
        Args:
            pids: List of Process IDs to check
            keywords: List of strings to look for (case-insensitive)
            
        Returns:
            The matching title if found, None otherwise
        """
        if not keywords or not pids:
            return None
            
        try:
            # Check each PID
            for pid in pids:
                titles = self.get_window_titles(pid)
                
                for title in titles:
                    title_lower = title.lower()
                    for keyword in keywords:
                        if keyword.lower() in title_lower:
                            return title
                        
            return None
            
        except Exception as e:
            logger.error(f"Error checking stuck state: {e}")
            return None

    def check_window_content(self, pids: List[int], keywords: List[str]) -> bool:
        """
        Check if any of the processes has a window containing the keywords (using UI Automation).
        
        Args:
            pids: List of Process IDs to check
            keywords: List of strings to look for (case-insensitive)
            
        Returns:
            True if keywords found, False otherwise
        """
        if not keywords or not pids:
            return False
            
        try:
            from pywinauto import Desktop
            
            for pid in pids:
                try:
                    # Use Desktop object to find all windows for the process
                    # This is more reliable for finding dialogs
                    windows = Desktop(backend="uia").windows(process=pid)
                    
                    for win in windows:
                        try:
                            # Get all descendants (controls)
                            descendants = win.descendants()
                            
                            for child in descendants:
                                try:
                                    text = child.window_text()
                                    if text:
                                        text_lower = text.lower()
                                        for keyword in keywords:
                                            if keyword.lower() in text_lower:
                                                logger.warning(f"UI MATCH: Found '{keyword}' in control '{text}' (PID {pid})")
                                                return True
                                except:
                                    continue
                        except Exception as e:
                            logger.debug(f"Error inspecting window for PID {pid}: {e}")
                            continue
                            
                except Exception as e:
                    # Process might not have windows or access denied
                    logger.debug(f"Could not connect to PID {pid}: {e}")
                    continue
                    
            return False
            
        except ImportError:
            logger.error("pywinauto not installed. Visual detection disabled.")
            return False
        except Exception as e:
            logger.error(f"Error in visual detection: {e}")
            return False
