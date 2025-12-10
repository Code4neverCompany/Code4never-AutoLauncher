import sys
import time
import argparse
import win32gui
import win32con
import win32process
import win32com.client
from PIL import ImageGrab

def window_enum_handler(hwnd, resultList):
    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) != '':
        resultList.append((hwnd, win32gui.GetWindowText(hwnd)))

def get_window_by_title(title_query):
    top_windows = []
    win32gui.EnumWindows(window_enum_handler, top_windows)
    
    # Case insensitive search
    title_query = title_query.lower()
    
    # Filter for matches
    matches = []
    for hwnd, title in top_windows:
        if title_query in title.lower():
            matches.append((hwnd, title))
            
    if not matches:
        return None
        
    # If multiple matches, prefer exact match or the one with the shortest title (likely the main window)
    return matches[0]

def get_window_by_pid(pid):
    top_windows = []
    win32gui.EnumWindows(window_enum_handler, top_windows)
    
    for hwnd, title in top_windows:
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
        if found_pid == pid:
            return (hwnd, title)
    return None

def bring_to_front(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # This is a bit hacky but often necessary on modern Windows to steal focus
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5) # Wait for animation
    except Exception as e:
        print(f"Warning: Could not bring window to front: {e}")

def capture_window(target, mode="title", output_file="window_capture.png", retries=5):
    match = None
    
    print(f"Searching for window ({mode}='{target}')...")
    
    for i in range(retries):
        if mode == "pid":
            match = get_window_by_pid(int(target))
        else:
            match = get_window_by_title(target)
            
        if match:
            break
        
        if i < retries - 1:
            print(f"Window not found, retrying ({i+1}/{retries})...")
            time.sleep(1)

    if not match:
        print(f"ERROR: No window found matching {mode}='{target}' after {retries} attempts")
        return False
        
    hwnd, title = match
    print(f"Found window: '{title}' (HWND: {hwnd})")
    
    bring_to_front(hwnd)
    
    try:
        # Get window bounds
        rect = win32gui.GetWindowRect(hwnd)
        x1, y1, x2, y2 = rect
        
        # Capture
        print(f"Capturing area: {rect}")
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img.save(output_file)
        print(f"SUCCESS: Saved to {output_file}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to capture: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture a specific window.")
    parser.add_argument("target", help="Window title or PID")
    parser.add_argument("--pid", action="store_true", help="Interpret target as PID")
    
    args = parser.parse_args()
    
    mode = "pid" if args.pid else "title"
    capture_window(args.target, mode=mode)
