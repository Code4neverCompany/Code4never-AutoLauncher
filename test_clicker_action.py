from addons.c4n_al_sentinel_addon.logic import SentinelLogic
import time
import os
import psutil
from pywinauto import Desktop

def test_clicker():
    detector = SentinelLogic()
    print("Searching for 'Wuthering Waves' simulation window...")
    
    target_pid = None
    target_hwnd = None
    
    # helper to find the window
    ws = Desktop(backend="win32").windows()
    for w in ws:
        if "Wuthering Waves" in w.window_text():
            target_pid = w.process_id()
            target_hwnd = w.handle
            print(f"Found Simulation! PID: {target_pid}, Handle: {target_hwnd}")
            break
            
    if not target_pid:
        print("Error: Could not find simulation window.")
        return

    print("Attempting to click 'Confirm' using PID-directed search...")
    # PASS THE PID! This enables the "Candidate Window" logic for this specific window.
    success = detector.click_confirmation_button([target_pid], ["Confirm"])
    
    if success:
        print("SUCCESS: Clicker reported success!")
    else:
        print("FAILURE: Clicker could not find/click the button.")

if __name__ == "__main__":
    test_clicker()
