import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler import TaskScheduler

class TestTaskScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = TaskScheduler()
        # Mock the internal APScheduler to avoid actual background threads if possible, 
        # or just test the wrapper logic. Use real scheduler but stop it.
        # self.scheduler.scheduler.shutdown() # We might want it running for some tests? 
        # Actually better to mock the internal scheduler for unit tests of the wrapper.
        # But for integration, real is better. Let's use real but carefully.

    def tearDown(self):
        try:
            self.scheduler.shutdown()
        except:
            pass

    def test_add_job(self):
        task = {
            "id": 1,
            "name": "Test Job",
            "schedule_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "enabled": True
        }
        
        result = self.scheduler.add_job(task)
        self.assertTrue(result)
        
        # Verify job exists in APScheduler
        job = self.scheduler.scheduler.get_job("task_1")
        self.assertIsNotNone(job)

    def test_remove_job(self):
        task = {
            "id": 1,
            "name": "To Remove",
            "schedule_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "enabled": True
        }
        self.scheduler.add_job(task)
        
        result = self.scheduler.remove_job(1)
        self.assertTrue(result)
        
        # Verify gone
        job = self.scheduler.scheduler.get_job("task_1")
        self.assertIsNone(job)

    @patch('subprocess.Popen')
    def test_execute_task(self, mock_popen):
        # Setup mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None # Running
        mock_popen.return_value = mock_process
        
        task = {
            "id": 2,
            "name": "Exec Task",
            "program_path": "C:\\Games\\Game.exe",
            "enabled": True
        }
        
        # Directly call execute logic
        self.scheduler._execute_task(task)
        
        # Verify Popen called with shell=False
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        
        self.assertEqual(args[0], "C:\\Games\\Game.exe")
        self.assertFalse(kwargs.get('shell', True)) # Should be False now

    @patch('psutil.Process')
    def test_stop_task(self, mock_psutil_class):
        # Setup
        task_id = 99
        mock_process = MagicMock()
        mock_process.pid = 5555
        self.scheduler.active_processes[task_id] = mock_process
        
        mock_proc_instance = MagicMock()
        mock_psutil_class.return_value = mock_proc_instance
        mock_proc_instance.children.return_value = [] # No children
        
        # Exec logic
        self.scheduler.stop_task(task_id)
        
        # Verify terminate called on the STORED process, not the psutil handle
        mock_process.terminate.assert_called()
        # Verify psutil was used to look for children
        mock_proc_instance.children.assert_called()
        
        self.assertNotIn(task_id, self.scheduler.active_processes)

if __name__ == '__main__':
    unittest.main()
