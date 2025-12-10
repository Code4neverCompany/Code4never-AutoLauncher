
import sys
import time
import tkinter as tk
from pathlib import Path

def main():
    # Log start time
    log_file = Path("stuck_test_log.txt")
    with open(log_file, "a") as f:
        f.write(f"Started at {time.time()}\n")

    # Create a window with a "stuck" title
    root = tk.Tk()
    root.title("Update Available - Critical Patch")
    root.geometry("200x100")
    
    label = tk.Label(root, text="I am stuck!")
    label.pack()
    
    # Keep running
    root.mainloop()

if __name__ == "__main__":
    main()
