import sys
import argparse
import time
from pywinauto import Application

def interact_window(pid, action, control_id=None, text=None):
    print(f"Connecting to PID: {pid}...")
    try:
        app = Application(backend="uia").connect(process=int(pid))
        dlg = app.top_window()
        
        # Bring to front first
        if dlg.exists():
            dlg.set_focus()
            time.sleep(0.5)
        
        if action == "type":
            if not text:
                print("ERROR: --text required for type action")
                return
            print(f"Typing '{text}'...")
            # If control_id is provided, type into that control, otherwise just send keys to window
            if control_id:
                dlg[control_id].type_keys(text, with_spaces=True)
            else:
                dlg.type_keys(text, with_spaces=True)
                
        elif action == "click":
            if not control_id:
                print("ERROR: --control required for click action")
                return
            print(f"Clicking '{control_id}'...")
            dlg[control_id].click()
            
        elif action == "menu":
            if not text:
                print("ERROR: --text required for menu action (e.g., 'File->Exit')")
                return
            print(f"Selecting menu '{text}'...")
            dlg.menu_select(text)
            
        print("SUCCESS: Action completed.")
        
    except Exception as e:
        print(f"ERROR: Failed to interact: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with UI elements.")
    parser.add_argument("pid", type=int, help="Process ID of the target application")
    parser.add_argument("--action", choices=["type", "click", "menu"], required=True, help="Action to perform")
    parser.add_argument("--control", help="Control identifier (name, auto_id, etc.)")
    parser.add_argument("--text", help="Text to type or menu path")
    
    args = parser.parse_args()
    interact_window(args.pid, args.action, args.control, args.text)
