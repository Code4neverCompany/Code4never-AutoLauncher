
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
from task_manager import TaskManager

def test_stuck_detection():
    print("Initializing Scheduler...")
    scheduler = TaskScheduler()
    
    # Create a dummy task
    task_data = {
        "id": 999,
        "name": "Test Stuck App",
        "program_path": str(Path(__file__).parent / "dummy_stuck_app.py"),
        "schedule_time": "2025-01-01T12:00:00",
        "enabled": True,
        "recurrence": "Once"
    }
    
    # Clear log file
    log_file = Path(__file__).parent / "stuck_test_log.txt"
    if log_file.exists():
        log_file.unlink()
        
    print("Executing task...")
    # We need to run it as a python script, so we might need to adjust program_path or how it's run
    # Scheduler runs program_path directly. 
    # Let's wrap it in a batch file or just run python directly?
    # Scheduler uses shell=True, so "python path/to/script.py" works if python is in path.
    # But program_path is usually the exe.
    # Let's set program_path to "python" and arguments? 
    # Scheduler doesn't support arguments well in 'program_path' if it expects a file.
    # But shell=True allows command strings.
    
    # Let's create a bat file wrapper
    bat_path = Path(__file__).parent / "run_stuck_app.bat"
    with open(bat_path, "w") as f:
        f.write(f'python "{str(Path(__file__).parent / "dummy_stuck_app.py")}"')
        
    task_data["program_path"] = str(bat_path)
    
    scheduler.execute_immediately(task_data)
    
    print("Waiting for detection (should take ~15-20 seconds)...")
    # Monitor runs every 10s. 
    # Wait enough time for:
    # 1. Launch
    # 2. Monitor check (0-10s)
    # 3. Detection -> Kill -> Wait 5s -> Restart
    # 4. Monitor check again?
    
    time.sleep(30)
    
    print("Checking log file...")
    if log_file.exists():
        with open(log_file, "r") as f:
            lines = f.readlines()
            print(f"Log entries: {len(lines)}")
            for line in lines:
                print(line.strip())
                
        if len(lines) >= 2:
            print("SUCCESS: Task was restarted!")
        else:
            print("FAILURE: Task was not restarted (or only ran once).")
    else:
        print("FAILURE: Log file not created.")

    # Cleanup
    scheduler.shutdown()
    try:
        if bat_path.exists():
            bat_path.unlink()
        # Kill any lingering python processes? (Risky)
    except:
        pass

if __name__ == "__main__":
    test_stuck_detection()
