import tkinter as tk
from tkinter import messagebox
import time
import sys

def main():
    root = tk.Tk()
    root.title("My Normal Application")
    root.geometry("300x200")
    
    label = tk.Label(root, text="Running normally...", font=("Arial", 12))
    label.pack(pady=20)
    
    # Show error dialog after 2 seconds
    def show_error():
        # This creates a native Windows dialog which pywinauto should detect easily
        messagebox.showerror("Error", "An error has occurred: Update Required to continue.")
        
    root.after(2000, show_error)
    
    root.mainloop()

if __name__ == "__main__":
    main()
