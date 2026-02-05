
import logging
import cv2
import numpy as np
import mss
import win32gui
import win32con
import win32api
import win32con
import win32api
import ctypes
import time

logger = logging.getLogger(__name__)

class VisualDetector:
    def __init__(self):
        self.sct = mss.mss()
        logger.info("VisualDetector initialized (OpenCV + MSS)")

    def _get_window_rect(self, hwnd):
        """Get window RECT."""
        try:
            rect = win32gui.GetWindowRect(hwnd)
            return rect # (left, top, right, bottom)
        except Exception:
            return None

    def capture_window(self, hwnd) -> np.ndarray:
        """Capture the specific window area using MSS."""
        rect = self._get_window_rect(hwnd)
        if not rect:
            return None
        
        # MSS monitor spec: {'top': t, 'left': l, 'width': w, 'height': h}
        monitor = {
            "left": rect[0],
            "top": rect[1],
            "width": rect[2] - rect[0],
            "height": rect[3] - rect[1]
        }
        
        # Grab screen data
        sct_img = self.sct.grab(monitor)
        # Convert to numpy array (BGRA)
        img = np.array(sct_img)
        # Convert to BGR (OpenCV standard) - drop Alpha
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img_bgr

    def scan_for_template(self, hwnd, template_path: str, confidence=0.8):
        """
        Scan window for template.
        Returns: (center_x, center_y) in SCREEN coordinates if found, else None.
        """
        # 1. Capture
        screen_img = self.capture_window(hwnd)
        if screen_img is None:
            return None

        # 2. Load Template
        template = cv2.imread(template_path)
        if template is None:
            logger.error(f"Failed to load template image: {template_path}")
            return None

        # 3. Match
        result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            logger.info(f"Target found! Confidence: {max_val:.2f}")
            
            # 4. Calculate Center
            # max_loc is top-left in the *captured image* (relative to window)
            t_h, t_w = template.shape[:2]
            
            rel_x = max_loc[0] + t_w // 2
            rel_y = max_loc[1] + t_h // 2
            
            # Convert to Global Screen Coordinates
            rect = self._get_window_rect(hwnd)
            screen_x = rect[0] + rel_x
            screen_y = rect[1] + rel_y
            
            return (screen_x, screen_y)
        
        return None

    def click_at(self, x, y):
        """
        Perform a click at screen coordinates using SendInput.
        Returns True if successful, False if aborted (e.g. user moved mouse).
        """
        try:
            # --- Safety Check: Is User using the mouse? ---
            # We measure cursor position delta over 100ms
            
            # Helper to get pos
            def get_pos():
                pt = win32api.GetCursorPos() # Returns (x, y)
                return pt
            
            start_pos = get_pos()
            time.sleep(0.1)
            end_pos = get_pos()
            
            dist = ((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2) ** 0.5
            if dist > 10: # Threshold: 10 pixels
                logger.warning("Sentinel: Visual interaction ABORTED - User is moving the mouse!")
                return False
                
            # --- Proceed with Click ---
            ix, iy = int(x), int(y)
            logger.info(f"Setting cursor to ({ix}, {iy})")
            
            # 1. Move Cursor
            ctypes.windll.user32.SetCursorPos(ix, iy)
            time.sleep(0.1)

            # 2. Prepare Input Structures via ctypes
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [("dx", ctypes.c_long),
                            ("dy", ctypes.c_long),
                            ("mouseData", ctypes.c_ulong),
                            ("dwFlags", ctypes.c_ulong),
                            ("time", ctypes.c_ulong),
                            ("dwExtraInfo", ctypes.c_void_p)]

            class INPUT(ctypes.Structure):
                _fields_ = [("type", ctypes.c_ulong),
                            ("mi", MOUSEINPUT)]

            # Constants
            INPUT_MOUSE = 0
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            
            # Create Inputs
            inp_down = INPUT()
            inp_down.type = INPUT_MOUSE
            inp_down.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
            
            inp_up = INPUT()
            inp_up.type = INPUT_MOUSE
            inp_up.mi.dwFlags = MOUSEEVENTF_LEFTUP
            
            # Send Down
            ctypes.windll.user32.SendInput(1, ctypes.pointer(inp_down), ctypes.sizeof(inp_down))
            time.sleep(0.15) # Robust delay for games
            
            # Send Up
            ctypes.windll.user32.SendInput(1, ctypes.pointer(inp_up), ctypes.sizeof(inp_up))
            
            logger.info(f"Clicked successfully at ({ix}, {iy}) via SendInput")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click at ({x}, {y}): {e}")
            raise

