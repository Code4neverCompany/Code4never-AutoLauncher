import sys
import argparse
from pywinauto import Application, Desktop

def inspect_window(pid, depth=2):
    print(f"Connecting to PID: {pid}...")
    try:
        app = Application(backend="uia").connect(process=int(pid))
        # Get the main window (top_window might not be enough if there are multiple, but good start)
        dlg = app.top_window()
        
        print(f"Connected to: {dlg.window_text()}")
        print("-" * 40)
        
        # Print control identifiers
        # This prints a tree of controls which is exactly what we need to "see" the UI structure
        dlg.print_control_identifiers(depth=depth)
        
    except Exception as e:
        print(f"ERROR: Failed to inspect window: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect UI elements of a window.")
    parser.add_argument("pid", type=int, help="Process ID of the target application")
    parser.add_argument("--depth", type=int, default=2, help="Depth of the UI tree to print")
    
    args = parser.parse_args()
    inspect_window(args.pid, args.depth)
