import os
import time
import sys
from PIL import ImageGrab, Image
import subprocess

def clear_clipboard():
    """Clears the clipboard to ensure we don't pick up an old image."""
    if sys.platform == 'win32':
        # Use ctypes to clear clipboard on Windows
        import ctypes
        from ctypes import wintypes
        
        user32 = ctypes.windll.user32
        user32.OpenClipboard(None)
        user32.EmptyClipboard()
        user32.CloseClipboard()

def trigger_snip():
    """Launches the Windows Snipping Tool in capture mode."""
    print("Launching Snipping Tool...")
    try:
        os.startfile("ms-screenclip:")
    except Exception as e:
        print(f"Failed to launch via os.startfile: {e}")
        # Fallback
        subprocess.run(["explorer", "ms-screenclip:"], check=False)

def wait_for_image(timeout=60):
    """Polls the clipboard for an image."""
    print("Waiting for screenshot...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            return img
        time.sleep(0.5)
    return None

def main():
    try:
        clear_clipboard()
        trigger_snip()
        
        img = wait_for_image()
        
        if img:
            filename = "screenshot.png"
            # Ensure unique filename if needed, but for now overwrite is fine for this tool's purpose
            # or maybe use timestamp: filename = f"screenshot_{int(time.time())}.png"
            
            img.save(filename, "PNG")
            print(f"SUCCESS: Screenshot saved to {os.path.abspath(filename)}")
        else:
            print("TIMEOUT: No screenshot detected.")
            sys.exit(1)
            
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
