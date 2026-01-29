
import asyncio
import ctypes
from ctypes import wintypes
import os
import tempfile
from PIL import ImageGrab

# Check winsdk import
try:
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.graphics.imaging import BitmapDecoder
    from winsdk.windows.storage import StorageFile, FileAccessMode
    from winsdk.windows.globalization import Language
except ImportError:
    print("winsdk not installed!")
    exit(1)

async def ocr_window(hwnd):
    # Capture Screenshot
    try:
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        
        print(f"Window Size: {width}x{height}")
        if width <= 0 or height <= 0: return
        
        # Save temp file
        temp_img = os.path.join(tempfile.gettempdir(), f"native_ocr_{hwnd}.png")
        img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
        img.save(temp_img)
        print(f"Captured: {temp_img}")
        
        # Load into WinRT
        # Note: winsdk requires absolute path
        file = await StorageFile.get_file_from_path_async(temp_img)
        stream = await file.open_async(FileAccessMode.READ)
        
        pass1_done = False
        result = None
        
        # Method 1: English Explicit
        try:
             lang = Language("en-US")
             if OcrEngine.is_language_supported(lang):
                 engine = OcrEngine.try_create_from_language(lang)
                 print("Engine: en-US created")
                 
                 decoder = await BitmapDecoder.create_async(stream)
                 software_bitmap = await decoder.get_software_bitmap_async()
                 result = await engine.recognize_async(software_bitmap)
                 pass1_done = True
        except Exception as e:
             print(f"Pass 1 failed: {e}")
             
        # Method 2: User Profile
        if not pass1_done: 
             engine = OcrEngine.try_create_from_user_profile_languages()
             print(f"Engine: User Profile ({engine.recognizer_language.display_name})")
             
             # Re-open stream?
             stream.seek(0)
             decoder = await BitmapDecoder.create_async(stream)
             software_bitmap = await decoder.get_software_bitmap_async()
             result = await engine.recognize_async(software_bitmap)

        if result:
            print(f"Lines found: {len(result.lines)}")
            for line in result.lines:
                print(f"LINE: {line.text}")
        
    except Exception as e:
        print(f"OCR Error: {e}")

def get_hwnd(title_fragment):
    hwnd_found = None
    def callback(hwnd, _):
        nonlocal hwnd_found
        len = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(len+1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, len+1)
        if title_fragment.lower() in buff.value.lower() and ctypes.windll.user32.IsWindowVisible(hwnd):
            hwnd_found = hwnd
            return False
        return True
    
    ctypes.windll.user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(callback), 0)
    return hwnd_found

if __name__ == "__main__":
    target = "Wuthering Waves"
    print(f"Adding for '{target}'...")
    hwnd = get_hwnd(target)
    if not hwnd:
        print("Target not found, trying Fallback...")
        hwnd = get_hwnd("Antigravity") # self
        
    if hwnd:
        asyncio.run(ocr_window(hwnd))
    else:
        print("No window found.")
