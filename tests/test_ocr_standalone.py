import os
import sys
import time
import ctypes
from ctypes import wintypes
import subprocess
import tempfile
from PIL import ImageGrab

def get_window_handle(partial_title):
    user32 = ctypes.windll.user32
    found_hwnd = None
    
    def enum_windows_callback(hwnd, lParam):
        nonlocal found_hwnd
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                if partial_title.lower() in buff.value.lower():
                    found_hwnd = hwnd
                    return False # Stop enumeration
        return True

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
    return found_hwnd

def test_ocr(hwnd):
    print(f"Testing OCR on HWND: {hwnd}")
    
    try:
        # Get rect
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        
        print(f"Window Rect: {rect.left}, {rect.top}, {rect.right}, {rect.bottom} ({width}x{height})")
        
        # Screenshot Path
        temp_img = os.path.join(tempfile.gettempdir(), f"test_ocr_{hwnd}.png")
        print(f"Capturing screenshot to {temp_img}...")
        
        # Clean up old
        if os.path.exists(temp_img):
            try:
                os.remove(temp_img)
            except: pass
            
        # Save screenshot
        img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
        img.save(temp_img)
        print("Screenshot saved.")

         
        # Analyze
        try:
             stat = img.convert('L').getextrema()
             print(f"Image brightness range: {stat}")
             if stat == (0, 0):
                 print("WARNING: Image is completely BLACK.")
        except:
             pass


        
        # Run OCR EXE
        ocr_exe = os.path.join(os.getcwd(), "ocr.exe")
        if not os.path.exists(ocr_exe):
             print(f"Error: Exe not found at {ocr_exe}")
             return

        print(f"Running OCR exe: {ocr_exe}")
        cmd = [ocr_exe, temp_img]

        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        print("\n--- OCR OUTPUT ---")
        print(result.stdout)
        print("------------------")
        
        if result.stderr:
            print("\n--- STDERR ---")
            print(result.stderr)
            print("--------------")
            
        # Check keywords
        output_lower = result.stdout.lower()
        keywords = [
            "update available", "check for updates", "restart required", 
            "setup", "installer", "patching", "updating", "new version", 
            "release notes", "notice", "download", "error", "confirm"
        ]
        
        found = [kw for kw in keywords if kw in output_lower]
        if found:
            print(f"\n✅ Matches found: {found}")
        else:
            print(f"\n❌ No keywords matched.")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    target = "Wuthering Waves" # Or 'Auth' or whatever
    # Try to find a window
    print(f"Looking for '{target}'...")
    hwnd = get_window_handle(target)
    
    if not hwnd:
        print(f"'{target}' not found. Listing top 5 visible windows:")
        # fallback list
        # ... (omitted for brevity)
        target = "Antigravity" # Fallback to self
        print(f"Fallback to '{target}'...")
        hwnd = get_window_handle(target)

    if hwnd:
        test_ocr(hwnd)
    else:
        print("No windows found to test.")
