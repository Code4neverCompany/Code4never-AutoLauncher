"""
Sentinel Logic Module
Core detection logic for checking window titles, content, and OCR.
Migrated and enhanced from legacy stuck_detector.py.
"""

import ctypes
from ctypes import wintypes
import os
import tempfile
import sys
from typing import List, Tuple, Optional
import subprocess

from logger import get_logger

logger = get_logger(__name__)

# Windows API Constants
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
GetWindowTextW = ctypes.windll.user32.GetWindowTextW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

class SentinelLogic:
    """
    Logic engine for the Sentinel Addon.
    Monitors processes for specific window titles/content indicating a stuck state.
    """

    def __init__(self):
        self._user32 = ctypes.windll.user32
        self._setup_comtypes()

    def _setup_comtypes(self):
        """Configure comtypes cache directory."""
        try:
            import comtypes.client
            temp_dir = os.path.join(tempfile.gettempdir(), "comtypes_cache")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
            comtypes.client.gen_dir = temp_dir
        except Exception as e:
            logger.debug(f"Could not set comtypes cache: {e}")

    # --- Window Enumeration Helpers ---

    def get_window_titles_and_pids(self) -> List[Tuple[str, int, int]]:
        """
        Return a list of (Window Title, PID, HWND) for all visible windows.
        """
        results = []

        def foreach_window(hwnd, lParam):
            if IsWindowVisible(hwnd):
                length = GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    
                    pid = wintypes.DWORD()
                    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    
                    results.append((title, pid.value, hwnd))
            return True

        self._user32.EnumWindows(EnumWindowsProc(foreach_window), 0)
        return results

    def get_all_window_titles(self) -> List[str]:
        """Return just the titles of all visible windows."""
        return [r[0] for r in self.get_window_titles_and_pids()]

    # --- State Detection ---

    def is_process_stuck(self, pids: List[int], keywords: List[str]) -> Optional[str]:
        """
        Check if any window belonging to the PIDs contains a keyword in its title.
        Returns the title if stuck, None otherwise.
        """
        if not pids or not keywords:
            return None
            
        win_info = self.get_window_titles_and_pids()
        
        for title, pid, hwnd in win_info:
            if pid in pids:
                title_lower = title.lower()
                for kw in keywords:
                    if kw.lower() in title_lower:
                        return title
        return None

    def check_window_content(self, pids: List[int], keywords: List[str]) -> bool:
        """
        Check content of windows belonging to PIDs using UI Automation (pywinauto).
        """
        if not pids or not keywords:
            return False
            
        try:
            from pywinauto import Application
            
            win_info = self.get_window_titles_and_pids()
            target_hwnds = [hwnd for t, p, hwnd in win_info if p in pids]
            
            for hwnd in target_hwnds:
                try:
                    app = Application(backend="uia").connect(handle=hwnd, timeout=1)
                    win = app.window(handle=hwnd)
                    # Check first 50 descendants
                    descendants = win.descendants()
                    for i, child in enumerate(descendants):
                        if i > 50: break
                        try:
                            text = child.window_text()
                            if text:
                                text_lower = text.lower()
                                for kw in keywords:
                                    if kw.lower() in text_lower:
                                        logger.info(f"Sentinel: Found keyword '{kw}' in window content: '{text}'")
                                        return True
                        except:
                            continue
                except:
                    continue
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Sentinel UIA Error: {e}")
            
        return False

    def check_global_window_content(self, keywords: List[str]) -> bool:
        """Check all visible windows globally for keywords in content."""
        # This is expensive, so we only check top windows or limited set
        # For safety/performance, implementing this fully might be too heavy.
        # Implemented as a stub or restricted check if needed.
        # Returning False for now to verify "process specific" first.
        return False

    # --- OCR ---

    def check_window_content_ocr(self, hwnd: int) -> str:
        """
        Use Windows Native OCR to read text from a window's screenshot.
        """
        temp_img = os.path.join(tempfile.gettempdir(), f"sentinel_ocr_{hwnd}.png")
        try:
            from PIL import ImageGrab
            
            # Get window rect
            rect = ctypes.wintypes.RECT()
            self._user32.GetWindowRect(hwnd, ctypes.byref(rect))
            
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            if width <= 0 or height <= 0:
                return ""
            
            # Capture
            try:
                img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
                img.save(temp_img)
            except Exception as e:
                logger.debug(f"Screen capture failed: {e}")
                return ""
                
            # Locate OCR helper
            # We assume we are in addons/c4n_al_sentinel_addon
            # Helper is at ../../assets/scripts/ocr_helper.ps1 (relative to base dir)
            
            # Use current logic to find OCR tool from main app assets
            # Assuming we run from main app context usually
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd() # Approximation
            ocr_exe = os.path.join(base_dir, "ocr.exe")
            
            cmd = []
            if os.path.exists(ocr_exe):
                 cmd = [ocr_exe, temp_img]
            else:
                 ps_script = os.path.join(base_dir, "assets", "scripts", "ocr_helper.ps1")
                 if not os.path.exists(ps_script):
                      # Try fallback relative logic if cwd is different
                      ps_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../assets/scripts/ocr_helper.ps1"))
                 
                 if os.path.exists(ps_script):
                     cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script, temp_img]
                 else:
                     logger.warning("Sentinel: OCR helper script not found.")
                     return ""
            
            # Run
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.stdout.strip()

        except ImportError:
            logger.warning("Sentinel: Pillow not installed.")
            return ""
        except Exception as e:
            logger.error(f"Sentinel OCR Error: {e}")
            return ""
        finally:
            if os.path.exists(temp_img):
                try:
                    os.remove(temp_img)
                except:
                    pass

    # --- Interaction ---

    def find_confirmation_dialog(self, pids: List[Optional[int]], keywords: List[str]) -> bool:
        """Check for confirmation dialogs."""
        if not keywords: return False
        
        # Similar logic to original but properly implemented using get_window_titles_and_pids
        try:
             win_info = self.get_window_titles_and_pids()
             candidate_hwnds = []
             tracked_pids = [p for p in pids if p is not None]
             
             for title, pid, hwnd in win_info:
                 if pid in tracked_pids:
                     candidate_hwnds.append(hwnd)
                     continue
                 
                 # Check title against keywords
                 t_lower = title.lower()
                 for kw in keywords:
                     if kw.lower() in t_lower:
                         candidate_hwnds.append(hwnd)
                         break
             
             # Fallback: check top windows if no candidates and None is in pids (global search)
             if None in pids and not candidate_hwnds:
                 candidate_hwnds = [hwnd for t, p, hwnd in win_info[:10]]
                 
             from pywinauto import Application
             
             for hwnd in candidate_hwnds:
                 try:
                     app = Application(backend="uia").connect(handle=hwnd, timeout=1)
                     win = app.window(handle=hwnd)
                     descendants = win.descendants()
                     for i, child in enumerate(descendants):
                         if i > 50: break
                         try:
                             text = child.window_text()
                             if text:
                                 text_lower = text.lower()
                                 for kw in keywords:
                                     if kw.lower() in text_lower:
                                         logger.info(f"Sentinel: Dialog detected ('{kw}' in '{text}')")
                                         return True
                         except: continue
                 except: continue
        except ImportError:
            pass
        return False

    def click_confirmation_button(self, pids: List[Optional[int]], button_labels: List[str]) -> bool:
        """Find and click button."""
        if not button_labels: return False
        
        try:
             win_info = self.get_window_titles_and_pids()
             candidate_hwnds = []
             tracked_pids = [p for p in pids if p is not None]
             
             for title, pid, hwnd in win_info:
                 if pid in tracked_pids:
                     candidate_hwnds.append(hwnd)
                 else:
                     t_lower = title.lower()
                     if any(kw in t_lower for kw in ["notice", "update", "patch", "launcher"]):
                         candidate_hwnds.append(hwnd)
             
             from pywinauto import Application
             
             for hwnd in candidate_hwnds:
                 try:
                     app = Application(backend="uia").connect(handle=hwnd, timeout=1)
                     win = app.window(handle=hwnd)
                     win_title = win.window_text()
                     
                     for label in button_labels:
                         # 1. Exact match Button
                         try:
                             btn = win.child_window(title=label, control_type="Button")
                             if btn.exists(timeout=0.2):
                                 logger.info(f"Sentinel: Clicking '{label}' in '{win_title}'")
                                 btn.click_input()
                                 return True
                         except: pass
                         
                         # 2. Regex
                         try:
                             btn = win.child_window(title_re=f"(?i)^{label}$", control_type="Button")
                             if btn.exists(timeout=0.2):
                                 logger.info(f"Sentinel: Clicking '{label}' (regex) in '{win_title}'")
                                 btn.click_input()
                                 return True
                         except: pass
                 except: continue
            
             # Fallback Enter
             import pyautogui
             pyautogui.press('enter')
             return True
        except:
             return False
