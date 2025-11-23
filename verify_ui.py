
import sys
from PyQt5.QtWidgets import QApplication
from about_interface import AboutInterface

def verify_ui():
    try:
        app = QApplication(sys.argv)
        interface = AboutInterface()
        print("AboutInterface initialized successfully.")
        
        # Check if dashboard exists
        if hasattr(interface, 'dashboard'):
            print("UpdateDashboard found.")
        else:
            print("ERROR: UpdateDashboard not found in AboutInterface.")
            return False
            
        return True
    except Exception as e:
        print(f"ERROR: Failed to initialize UI: {e}")
        return False

if __name__ == "__main__":
    if verify_ui():
        print("Verification PASSED")
        sys.exit(0)
    else:
        print("Verification FAILED")
        sys.exit(1)
