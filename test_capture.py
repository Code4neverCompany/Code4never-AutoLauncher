
import ctypes
from ctypes import wintypes
import os
import tempfile
from PIL import Image

# User32 and GDI32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def test_printwindow(hwnd, filename):
    try:
        # Get Window Rect
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        
        print(f"Window Size: {width}x{height}")
        
        # Create DC
        hwndDC = user32.GetWindowDC(hwnd)
        mfcDC  = gdi32.CreateCompatibleDC(hwndDC)
        saveBitMap = gdi32.CreateCompatibleBitmap(hwndDC, width, height)
        
        gdi32.SelectObject(mfcDC, saveBitMap)
        
        # PrintWindow
        # PW_RENDERFULLCONTENT = 0x00000002
        result = user32.PrintWindow(hwnd, mfcDC, 2)
        
        if result == 0:
            print("PrintWindow failed, trying default...")
            result = user32.PrintWindow(hwnd, mfcDC, 0)
            
        print(f"PrintWindow Result: {result}")
        
        # Save to file using PIL from buffer?
        # Requires getting bitmap bits.
        # Simplified: Use PIL ImageGrab.grab equivalent logic? 
        # Actually simplest is to write BMP header or use Pillow from buffer.
        
        import win32ui
        import win32gui
        import win32con
        
        # We need pywin32 for easy bitmap saving? properties are messy in ctypes raw.
        # Let's try raw ctypes bitmap save or just check pixels?
        
        # Use simple pixel check?
        pixel = gdi32.GetPixel(mfcDC, width//2, height//2)
        print(f"Center Pixel: {hex(pixel)}")
        
        # Cleanup
        gdi32.DeleteObject(saveBitMap)
        gdi32.DeleteDC(mfcDC)
        user32.ReleaseDC(hwnd, hwndDC)
        
        if pixel != 0 and pixel != 0xFFFFFFFF:
             print("SUCCESS: Non-black/white pixel detected.")
        else:
             print("WARNING: Pixel looks black/empty.")

    except Exception as e:
        print(f"Error: {e}")

def get_hwnd(target):
    found = None
    def cb(hwnd, _):
        nonlocal found
        len = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(len+1)
        user32.GetWindowTextW(hwnd, buff, len+1)
        if target.lower() in buff.value.lower() and user32.IsWindowVisible(hwnd):
            found = hwnd
            return False
        return True
    user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(cb), 0)
    return found

if __name__ == "__main__":
    t = "Wuthering Waves"
    h = get_hwnd(t)
    if h:
        print(f"Testing PrintWindow on {h}")
        test_printwindow(h, "test.bmp")
    else:
        print("Window not found")
