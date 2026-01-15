"""
Stuck Detector Module for Autolauncher.
Detects if a process is stuck in an 'Update' or 'Setup' state by inspecting window titles.
"""

import ctypes
from ctypes import wintypes
import threading
import os
import tempfile
import sys
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
        self._setup_comtypes()

    def _setup_comtypes(self):
        """Configure comtypes cache directory to avoid permission errors."""
        try:
            import comtypes.client
            temp_dir = os.path.join(tempfile.gettempdir(), "comtypes_cache")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
            comtypes.client.gen_dir = temp_dir
            logger.debug(f"Comtypes cache set to: {temp_dir}")
        except Exception as e:
            logger.debug(f"Could not set comtypes cache: {e}")

    def check_window_content_ocr(self, hwnd: int) -> str:
        """
        Use Windows Native OCR to read text from a window's screenshot.
        Requires 'Pillow' library.
        """
        temp_img = os.path.join(tempfile.gettempdir(), f"autolauncher_ocr_{hwnd}.png")
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
            img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
            img.save(temp_img)
            
            # Check for black screen (common in Exclusive Fullscreen games)
            try:
                extrema = img.convert("L").getextrema()
                if extrema == (0, 0):
                    logger.warning(f"OCR: Screenshot for HWND {hwnd} is BLACK. Try Windowed/Borderless.")
                    return ""
            except:
                pass

            # Determine OCR executable path
            ocr_exe = os.path.join(os.path.dirname(__file__), "ocr.exe")
            if not os.path.exists(ocr_exe):
                 base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
                 ocr_exe = os.path.join(base_dir, "ocr.exe")

            cmd = []
            if os.path.exists(ocr_exe):
                 cmd = [ocr_exe, temp_img]
            else:
                 # Fallback to PowerShell script
                 ps_script = os.path.join(os.path.dirname(__file__), "assets", "scripts", "ocr_helper.ps1")
                 if not os.path.exists(ps_script):
                      base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
                      ps_script = os.path.join(base_dir, "assets", "scripts", "ocr_helper.ps1")
                 
                 cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script, temp_img]
            
            # Run OCR
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.stdout.strip()

        except ImportError:
            logger.warning("OCR Disabled: Pillow library not installed.")
            return ""
        except Exception as e:
            logger.error(f"OCR Error for HWND {hwnd}: {e}")
            return ""
        finally:
            # Always clean up temp file
            if os.path.exists(temp_img):
                try:
                    os.remove(temp_img)
                except:
                    pass

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
