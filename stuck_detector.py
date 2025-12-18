"""
Stuck Detector Module for Autolauncher.
Detects if a process is stuck in an 'Update' or 'Setup' state by inspecting window titles.
"""

import ctypes
import threading
import os
import tempfile
import sys
from typing import List, Optional
from logger import get_logger

logger = get_logger(__name__)

# Windows API Constants and Types
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

# Fix for comtypes in bundled environment
try:
    import comtypes.client
    # Set a writable directory for comtypes generated files
    temp_dir = os.path.join(tempfile.gettempdir(), "comtypes_cache")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
    comtypes.client.gen_dir = temp_dir
    logger.debug(f"Comtypes cache set to: {temp_dir}")
except Exception as e:
    logger.debug(f"Could not set comtypes cache: {e}")

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
        """
        titles = []
        
        def enum_windows_callback(hwnd, lParam):
            try:
                window_pid = ctypes.c_ulong()
                self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                
                if window_pid.value == pid:
                    length = self._user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        self._user32.GetWindowTextW(hwnd, buff, length + 1)
                        if buff.value:
                            titles.append(buff.value)
                return True
            except Exception:
                return True

        try:
            self._user32.EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
        except Exception as e:
            logger.error(f"Error enumerating windows for PID {pid}: {e}")
            
        return titles

    def get_window_titles_and_pids(self) -> List[tuple]:
        """
        Get all visible top-level window titles and their PIDs.
        Returns list of (title, pid, hwnd)
        """
        results = []
        
        def enum_windows_callback(hwnd, lParam):
            try:
                if self._user32.IsWindowVisible(hwnd):
                    length = self._user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        self._user32.GetWindowTextW(hwnd, buff, length + 1)
                        if buff.value:
                            window_pid = ctypes.c_ulong()
                            self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                            results.append((buff.value, window_pid.value, hwnd))
                return True
            except Exception:
                return True

        try:
            self._user32.EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
        except Exception as e:
            logger.error(f"Error enumerating all windows: {e}")
            
        return results

    def is_process_stuck(self, pids: List[int], keywords: List[str]) -> Optional[str]:
        """
        Check if any of the processes has a window title matching the keywords.
        """
        if not keywords or not pids:
            return None
            
        try:
            for pid in pids:
                if not pid: continue
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

    def check_window_content(self, pids: List[Optional[int]], keywords: List[str], timeout_per_win: float = 2.0) -> bool:
        """
        Check if specified processes (or all windows if pid is None) contain keywords.
        Advanced multi-pass optimization.
        """
        if not keywords or not pids:
            return False
            
        try:
            from pywinauto import Desktop, Application
            
            # Fast pass: Get all window titles and PIDs using Win32 API
            win_info = self.get_window_titles_and_pids()
            
            # 1. Prioritized Windows (PIDs we are tracking or titles that match keywords)
            candidate_hwnds = []
            
            # Filter for PIDs
            tracked_pids = [p for p in pids if p is not None]
            
            for title, pid, hwnd in win_info:
                # If window belongs to tracked PID, check it
                if pid in tracked_pids:
                    candidate_hwnds.append(hwnd)
                    continue
                
                # If title contains keyword, check it regardless of PID
                title_lower = title.lower()
                for kw in keywords:
                    if kw.lower() in title_lower:
                        candidate_hwnds.append(hwnd)
                        break
            
            # If no pid specified (global search), and no fast-match titles, fallback to all VISIBLE windows
            if None in pids and not candidate_hwnds:
                # Limit to top 30 most recent visible windows to avoid total system lag
                # User says speed is not a huge issue, so we broaden the search
                candidate_hwnds = [hwnd for title, pid, hwnd in win_info[:30]]

            # Deep pass using pywinauto on candidates
            for hwnd in candidate_hwnds:
                try:
                    # Connect via HWND for speed and precision
                    app = Application(backend="uia").connect(handle=hwnd, timeout=1)
                    win = app.window(handle=hwnd)
                    
                    win_title = win.window_text()
                    logger.debug(f"Optimized Deep-Dive: '{win_title}'")
                    
                    # Search descendants (limit to 50 for performance)
                    descendants = win.descendants()
                    count = 0
                    for child in descendants:
                        count += 1
                        if count > 50: break # Safety limit
                        
                        try:
                            text = child.window_text()
                            if text:
                                text_lower = text.lower()
                                for keyword in keywords:
                                    if keyword.lower() in text_lower:
                                        logger.warning(f"UI MATCH: Found '{keyword}' in control '{text}'")
                                        return True
                        except:
                            continue
                except Exception:
                    continue
            return False
        except ImportError:
            logger.error("pywinauto not installed. Visual detection disabled.")
            return False
        except Exception as e:
            logger.error(f"Error in visual detection: {e}")
            return False
    
    def check_global_window_content(self, keywords: List[str]) -> bool:
        """Check all visible windows for keywords in their content."""
        return self.check_window_content([None], keywords)

    def check_window_content_ocr(self, hwnd: int) -> str:
        """
        Use Windows Native OCR to read text from a window's screenshot.
        Requires 'Pillow' library.
        """
        try:
            from PIL import ImageGrab
            import subprocess
            
            # Get window rect
            rect = ctypes.wintypes.RECT()
            self._user32.GetWindowRect(hwnd, ctypes.byref(rect))
            
            # If window is minimized or invalid size, skip
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            if width <= 0 or height <= 0:
                return ""
            
            # Capture screenshot
            # Note: ImageGrab.grab(bbox) expects (left, top, right, bottom)
            # This captures the screen area, so if window is overlapped, it sees what's on top.
            # Best we can do without specialized DWM APIs.
            # Also, we need to ensure we don't capture if off-screen.
            
            temp_img = os.path.join(tempfile.gettempdir(), f"autolauncher_ocr_{hwnd}.png")
            
            try:
                img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
                img.save(temp_img)
            except Exception as e:
                logger.debug(f"Screenshot failed for HWND {hwnd}: {e}")
                return ""
                
            # Call PowerShell OCR Helper
            ps_script = os.path.join(os.path.dirname(__file__), "assets", "scripts", "ocr_helper.ps1")
            if not os.path.exists(ps_script):
                 # Fallback for frozen executable
                 base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
                 ps_script = os.path.join(base_dir, "assets", "scripts", "ocr_helper.ps1")

            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script, temp_img]
            
            # Run with timeout (OCR is slow-ish)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            
            text = result.stdout.strip()
            
            # Cleanup
            try:
                os.remove(temp_img)
            except:
                pass
                
            return text
            
        except ImportError:
            logger.warning("Pillow not installed. OCR disabled.")
            return ""
        except Exception as e:
            logger.error(f"Error in Native OCR: {e}")
            return ""

    def find_confirmation_dialog(self, pids: List[Optional[int]], keywords: List[str]) -> bool:
        """
        Check if specified processes (or all windows if pid is None) have a confirmation dialog.
        Follows optimized multi-pass strategy.
        """
        if not keywords or not pids:
            return False
            
        try:
            from pywinauto import Application
            
            # Fast pass: Get window info
            win_info = self.get_window_titles_and_pids()
            candidate_hwnds = []
            tracked_pids = [p for p in pids if p is not None]
            
            for title, pid, hwnd in win_info:
                if pid in tracked_pids:
                    candidate_hwnds.append(hwnd)
                    continue
                
                title_lower = title.lower()
                for kw in keywords:
                    if kw.lower() in title_lower:
                        candidate_hwnds.append(hwnd)
                        break
            
            if None in pids and not candidate_hwnds:
                candidate_hwnds = [hwnd for title, pid, hwnd in win_info[:15]]

            for hwnd in candidate_hwnds:
                try:
                    app = Application(backend="uia").connect(handle=hwnd, timeout=1)
                    win = app.window(handle=hwnd)
                    
                    descendants = win.descendants()
                    count = 0
                    for child in descendants:
                        count += 1
                        if count > 50: break
                        
                        try:
                            text = child.window_text()
                            if text:
                                text_lower = text.lower()
                                for keyword in keywords:
                                    if keyword.lower() in text_lower:
                                        logger.info(f"CONFIRMATION DIALOG DETECTED: Found '{keyword}' in '{text}'")
                                        return True
                        except:
                            continue
                except:
                    continue
            return False
        except ImportError:
            logger.error("pywinauto not installed. Confirmation detection disabled.")
            return False
        except Exception as e:
            logger.error(f"Error in confirmation detection: {e}")
            return False
    
    def click_confirmation_button(self, pids: List[Optional[int]], button_labels: List[str]) -> bool:
        """
        Find and click a confirmation button in specified windows.
        Follows optimized HWND strategy.
        """
        if not button_labels or not pids:
            return False
            
        try:
            from pywinauto import Application
            
            win_info = self.get_window_titles_and_pids()
            candidate_hwnds = []
            tracked_pids = [p for p in pids if p is not None]
            
            for title, pid, hwnd in win_info:
                if pid in tracked_pids:
                    candidate_hwnds.append(hwnd)
                else:
                    # Broad match for buttons - often found in "Notice" or "Launcher" windows
                    t_lower = title.lower()
                    if any(kw in t_lower for kw in ["notice", "update", "patch", "launcher"]):
                        candidate_hwnds.append(hwnd)
            
            if None in pids and not candidate_hwnds:
                candidate_hwnds = [hwnd for title, pid, hwnd in win_info[:10]]

            for hwnd in candidate_hwnds:
                try:
                    app = Application(backend="uia").connect(handle=hwnd, timeout=1)
                    win = app.window(handle=hwnd)
                    
                    win_title = win.window_text()
                    logger.debug(f"Looking for buttons in prioritized window: '{win_title}'")
                    
                    for label in button_labels:
                        try:
                            button = win.child_window(title=label, control_type="Button")
                            if button.exists(timeout=0.4):
                                logger.info(f"AUTO-CLICK: Found '{label}' button in window '{win_title}', clicking it")
                                button.click_input()
                                return True
                        except:
                            pass
                            
                        try:
                            button = win.child_window(title_re=f"(?i)^{label}$", control_type="Button")
                            if button.exists(timeout=0.4):
                                logger.info(f"AUTO-CLICK: Found '{label}' button (regex) in window '{win_title}', clicking it")
                                button.click_input()
                                return True
                        except:
                            pass
                except Exception:
                    continue
            
            # Fallback: Try pressing Enter key
            try:
                import pyautogui
                logger.info("AUTO-CLICK: No button found, trying Enter key as fallback")
                pyautogui.press('enter')
                return True
            except ImportError:
                logger.warning("pyautogui not installed, Enter key fallback disabled")
            except Exception as e:
                logger.debug(f"Enter key fallback failed: {e}")
            return False
        except ImportError:
            logger.error("pywinauto not installed. Auto-click disabled.")
            return False
        except Exception as e:
            logger.error(f"Error in auto-click: {e}")
            return False
