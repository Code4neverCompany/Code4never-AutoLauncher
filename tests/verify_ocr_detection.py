
import sys
import time
import os
from pathlib import Path

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

# Mock PyQt6
from unittest.mock import MagicMock
mock_qt = MagicMock()
sys.modules["PyQt6"] = mock_qt
sys.modules["PyQt6.QtCore"] = mock_qt

class MockQObject:
    def __init__(self, *args, **kwargs):
        pass

class MockSignal:
    def __init__(self, *args):
        pass
    def connect(self, func):
        pass
    def emit(self, *args):
        pass

mock_qt.QObject = MockQObject
mock_qt.pyqtSignal = MockSignal

from scheduler import TaskScheduler

def test_ocr_detection():
    print("Initializing Scheduler...")
    scheduler = TaskScheduler()
    
    # Create a dummy task
    task_data = {
        "id": 888,
        "name": "Test OCR App",
        "program_path": "", # Will be set below
        "schedule_time": "2025-01-01T12:00:00",
        "enabled": True,
        "recurrence": "Once"
    }
    
    # Clear log file
    log_file = Path(__file__).parent / "ocr_test_log.txt"
    if log_file.exists():
        log_file.unlink()
        
    print("Executing task...")
    
    # Create bat file wrapper
    bat_path = Path(__file__).parent / "run_ocr_app.bat"
    with open(bat_path, "w") as f:
        f.write(f'python "{str(Path(__file__).parent / "dummy_ocr_app.py")}"')
        
    task_data["program_path"] = str(bat_path)
    
    scheduler.execute_immediately(task_data)
    
    print("Waiting for detection (should take ~35-40 seconds due to 30s interval)...")
    # Monitor check runs every 30s for OCR.
    
    time.sleep(45)
    
    print("Checking log file...")
    if log_file.exists():
        with open(log_file, "r") as f:
            lines = f.readlines()
            print(f"Log entries: {len(lines)}")
            for line in lines:
                print(line.strip())
                
        if len(lines) >= 2:
            print("SUCCESS: Task was restarted via OCR!")
        else:
            print("FAILURE: Task was not restarted.")
    else:
        print("FAILURE: Log file not created.")

    # Cleanup
    scheduler.shutdown()
    try:
        if bat_path.exists():
            bat_path.unlink()
    except:
        pass

if __name__ == "__main__":
    test_ocr_detection()
