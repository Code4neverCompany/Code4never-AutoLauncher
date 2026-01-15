"""
Verification Script for New Features
Tests ExecutionLogger, TaskScheduler integration, and Date Format settings.
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.getcwd())

from execution_logger import ExecutionLogger
from scheduler import TaskScheduler
from task_manager import SettingsManager
from logger import get_logger

logger = get_logger("verify_features")

def test_execution_logger():
    print("\n--- Testing Execution Logger ---")
    try:
        log_file = "data/test_execution_log.json"
        if os.path.exists(log_file):
            os.remove(log_file)
            
        logger = ExecutionLogger(log_file)
        
        # Test logging
        logger.log_event(1, "Test Task", "STARTED", "Details 1")
        logger.log_event(1, "Test Task", "FINISHED", "Details 2")
        
        # Test reading
        logs = logger.get_logs()
        if len(logs) == 2:
            print("SUCCESS: Logs written and read correctly.")
            print(f"Log 1: {logs[1]['event_type']}") # Sorted by timestamp desc, so index 1 is the first one? No, get_logs sorts reverse=True (newest first)
            # So logs[0] is FINISHED, logs[1] is STARTED
            if logs[0]['event_type'] == "FINISHED" and logs[1]['event_type'] == "STARTED":
                print("SUCCESS: Log order is correct.")
            else:
                print(f"FAILURE: Log order incorrect. 0={logs[0]['event_type']}, 1={logs[1]['event_type']}")
        else:
            print(f"FAILURE: Expected 2 logs, got {len(logs)}")
            
        # Clean up
        if os.path.exists(log_file):
            os.remove(log_file)
        return True
    except Exception as e:
        print(f"FAILURE: Execution Logger test failed: {e}")
        return False

def test_scheduler_integration():
    print("\n--- Testing Scheduler Integration ---")
    try:
        # We need a QApplication for TaskScheduler because it inherits QObject
        from PyQt6.QtWidgets import QApplication
        if not QApplication.instance():
            app = QApplication(sys.argv)
            
        scheduler = TaskScheduler()
        
        # Check if logger is initialized
        if hasattr(scheduler, 'execution_logger'):
            print("SUCCESS: ExecutionLogger initialized in Scheduler.")
        else:
            print("FAILURE: ExecutionLogger NOT found in Scheduler.")
            return False
            
        # Test adding a job (mock)
        task = {
            'id': 999,
            'name': 'Test Task',
            'program_path': 'notepad.exe',
            'schedule_time': (datetime.now() + timedelta(minutes=10)).isoformat(),
            'recurrence': 'Once',
            'enabled': True
        }
        
        if scheduler.add_job(task):
            print("SUCCESS: Job added to scheduler.")
        else:
            print("FAILURE: Failed to add job.")
            return False
            
        scheduler.shutdown()
        return True
    except Exception as e:
        print(f"FAILURE: Scheduler test failed: {e}")
        return False

def test_settings_date_format():
    print("\n--- Testing Settings (Date Format) ---")
    try:
        settings = SettingsManager()
        
        # Test setting value
        settings.set('date_format', 'DD.MM.YYYY')
        val = settings.get('date_format')
        
        if val == 'DD.MM.YYYY':
            print("SUCCESS: Date format setting saved and retrieved.")
        else:
            print(f"FAILURE: Expected 'DD.MM.YYYY', got '{val}'")
            return False
            
        # Reset to default
        settings.set('date_format', 'YYYY-MM-DD')
        return True
    except Exception as e:
        print(f"FAILURE: Settings test failed: {e}")
        return False

from datetime import timedelta

if __name__ == "__main__":
    results = []
    results.append(test_execution_logger())
    results.append(test_settings_date_format())
    results.append(test_scheduler_integration())
    
    if all(results):
        print("\nALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)
