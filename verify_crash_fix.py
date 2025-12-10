import sys
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
from PyQt6.QtCore import Qt

# Create app before imports
app = QApplication(sys.argv)

from autolauncher import AutolauncherApp
from qfluentwidgets import InfoBar

class TestCrashFixes(unittest.TestCase):
    def setUp(self):
        self.app = AutolauncherApp()
        
        # Mock task manager and scheduler
        self.app.task_manager = MagicMock()
        self.app.scheduler = MagicMock()
        self.app.settings_manager = MagicMock()
        
        # Mock InfoBar to prevent actual popup but check calls
        self.info_bar_patch = patch('qfluentwidgets.InfoBar')
        self.mock_info_bar = self.info_bar_patch.start()
        
    def tearDown(self):
        self.info_bar_patch.stop()
        self.app.close()
        
    def test_edit_task_no_selection(self):
        """Test _edit_task with no selection (should show warning, not crash)"""
        print("\nTesting _edit_task (no selection)...")
        self.app.taskTable.clearSelection()
        try:
            self.app._edit_task()
            print("Success: No crash")
        except Exception as e:
            self.fail(f"Crashed: {e}")
            
    def test_toggle_pause_no_selection(self):
        """Test _toggle_task_pause with no selection (should show warning, not crash)"""
        print("\nTesting _toggle_task_pause (no selection)...")
        self.app.taskTable.clearSelection()
        try:
            self.app._toggle_task_pause()
            print("Success: No crash")
        except Exception as e:
            self.fail(f"Crashed: {e}")
            
    def test_add_task_dialog(self):
        """Test _add_task (mocking dialog exec)"""
        print("\nTesting _add_task...")
        with patch('autolauncher.TaskDialog') as MockDialog:
            instance = MockDialog.return_value
            instance.exec.return_value = True
            instance.validate_input.return_value = True
            instance.get_task_data.return_value = {'name': 'Test Task', 'enabled': True}
            
            self.app.task_manager.add_task.return_value = True
            
            try:
                self.app._add_task()
                print("Success: No crash")
            except Exception as e:
                self.fail(f"Crashed: {e}")

if __name__ == '__main__':
    unittest.main()
