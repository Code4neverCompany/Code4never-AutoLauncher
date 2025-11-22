import os
import sys
import shutil
import zipfile
import winshell
from win32com.client import Dispatch
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def create_shortcut(target_path, shortcut_path, description="", icon_path=None):
    """Create a Windows shortcut."""
    try:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.TargetPath = str(target_path)
        shortcut.WorkingDirectory = str(os.path.dirname(target_path))
        shortcut.Description = description
        if icon_path and os.path.exists(icon_path):
            shortcut.IconLocation = str(icon_path)
        shortcut.save()
        return True
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
        return False

def install():
    # Default install location
    local_app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
    default_install_dir = os.path.join(local_app_data, 'Programs', 'Autolauncher')
    
    # Setup UI
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Ask for install directory
    install_dir = filedialog.askdirectory(
        title="Select Installation Directory",
        initialdir=os.path.dirname(default_install_dir),
        mustexist=False
    )
    
    if not install_dir:
        return  # User cancelled
        
    # If user selected a directory, append 'Autolauncher' if not present to avoid cluttering root
    if not install_dir.endswith('Autolauncher'):
        install_dir = os.path.join(install_dir, 'Autolauncher')
        
    # Confirm installation
    if not messagebox.askyesno("Confirm Installation", f"Install Autolauncher to:\n{install_dir}?"):
        return

    try:
        # Create directory
        os.makedirs(install_dir, exist_ok=True)
        
        # Find bundled ZIP
        # We expect the zip to be named 'app_package.zip' when bundled
        zip_path = get_resource_path("app_package.zip")
        
        if not os.path.exists(zip_path):
            messagebox.showerror("Error", "Installation package not found!")
            return

        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
            
        # Create shortcuts
        exe_path = os.path.join(install_dir, "Autolauncher.exe")
        if os.path.exists(exe_path):
            # Desktop Shortcut
            desktop = winshell.desktop()
            create_shortcut(
                exe_path, 
                os.path.join(desktop, "Autolauncher.lnk"),
                "Autolauncher Application"
            )
            
            # Start Menu Shortcut
            start_menu = winshell.start_menu()
            programs_dir = os.path.join(start_menu, "Programs", "Autolauncher")
            os.makedirs(programs_dir, exist_ok=True)
            create_shortcut(
                exe_path,
                os.path.join(programs_dir, "Autolauncher.lnk"),
                "Autolauncher Application"
            )
            
            messagebox.showinfo("Success", "Installation completed successfully!")
            
            # Launch app
            if messagebox.askyesno("Launch", "Do you want to launch Autolauncher now?"):
                os.startfile(exe_path)
                
        else:
            messagebox.showwarning("Warning", "Installation completed but executable was not found.")
            
    except Exception as e:
        messagebox.showerror("Error", f"Installation failed: {str(e)}")

if __name__ == "__main__":
    install()
