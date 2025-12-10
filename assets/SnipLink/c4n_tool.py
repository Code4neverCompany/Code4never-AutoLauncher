import sys
import argparse
import subprocess
import os

# Map commands to scripts
SCRIPTS = {
    "snip": "snip.py",
    "capture": "capture_window.py",
    "inspect": "inspect_window.py",
    "interact": "interact_window.py"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")

def run_script(script_name, args):
    script_path = os.path.join(BASE_DIR, script_name)
    cmd = [VENV_PYTHON, script_path] + args
    
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        sys.exit(e.returncode)

def main():
    parser = argparse.ArgumentParser(description="c4n Desktop Agent Tools")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Snip
    subparsers.add_parser("snip", help="Launch Snipping Tool")
    
    # Capture
    capture_parser = subparsers.add_parser("capture", help="Capture a window")
    capture_parser.add_argument("target", help="Window title or PID")
    capture_parser.add_argument("--pid", action="store_true", help="Interpret target as PID")
    
    # Inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect UI elements")
    inspect_parser.add_argument("pid", help="Process ID")
    inspect_parser.add_argument("--depth", default="2", help="Depth of inspection")
    
    # Interact
    interact_parser = subparsers.add_parser("interact", help="Interact with UI")
    interact_parser.add_argument("pid", help="Process ID")
    interact_parser.add_argument("--action", choices=["type", "click", "menu"], required=True)
    interact_parser.add_argument("--control", help="Control ID")
    interact_parser.add_argument("--text", help="Text to type/select")
    
    # Parse known args to pass the rest to the script if needed, 
    # but here we map explicitly.
    # Actually, simpler approach: just forward arguments based on command.
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
        
    command = sys.argv[1]
    if command not in SCRIPTS:
        print(f"Unknown command: {command}")
        parser.print_help()
        sys.exit(1)
        
    # Forward all remaining args to the specific script
    script_args = sys.argv[2:]
    run_script(SCRIPTS[command], script_args)

if __name__ == "__main__":
    main()
