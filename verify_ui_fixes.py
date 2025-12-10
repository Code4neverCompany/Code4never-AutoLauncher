"""
Verification Script for UI Fixes
Tests instantiation of SettingsInterface and LogDialog.
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget
from qfluentwidgets import FluentWindow

# Ensure QApplication exists
if not QApplication.instance():
    app = QApplication(sys.argv)

from settings_interface import SettingsInterface
from log_dialog import LogDialog

def verify_ui_fixes():
    print("--- Verifying UI Fixes ---")
    try:
        # Test SettingsInterface
        print("Initializing SettingsInterface...")
        settings = SettingsInterface()
        if hasattr(settings, 'executionModeCard') and hasattr(settings, 'dateFormatCard'):
            print("SUCCESS: SettingsInterface initialized with correct cards.")
        else:
            print("FAILURE: SettingsInterface missing cards.")
            return False
            
        # Test LogDialog
        print("Initializing LogDialog...")
        # LogDialog requires a parent to calculate geometry (MaskDialogBase)
        dummy_parent = QWidget()
        dummy_parent.resize(800, 600)
        dialog = LogDialog(dummy_parent)
        if hasattr(dialog, 'logTable') and hasattr(dialog, 'clearButton'):
            print("SUCCESS: LogDialog initialized with table and buttons.")
        else:
            print("FAILURE: LogDialog missing components.")
            return False
            
        print("ALL UI TESTS PASSED")
        return True
    except Exception as e:
        print(f"FAILURE: UI Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_ui_fixes():
        sys.exit(0)
    else:
        sys.exit(1)
