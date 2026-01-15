import unittest
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_manager import TaskManager

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.test_tasks_file = Path(self.test_dir) / "test_tasks.json"
        
        # Initialize TaskManager with test file
        self.task_manager = TaskManager(self.test_tasks_file)

    def tearDown(self):
        # Remove temporary directory after tests
        shutil.rmtree(self.test_dir)

    def test_add_task(self):
        task_data = {
            "name": "Test Task",
            "program_path": "C:\\Windows\\notepad.exe",
            "schedule_time": "2025-01-01T12:00:00",
            "enabled": True
        }
        
        # Test adding task
        new_id = self.task_manager.add_task(task_data)
        
        # Verify return value
        self.assertIsNotNone(new_id)
        self.assertIsInstance(new_id, int)
        self.assertEqual(new_id, 1)
        
        # Verify task in memory
        tasks = self.task_manager.get_all_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['id'], 1)
        self.assertEqual(tasks[0]['name'], "Test Task")
        
        # Verify persistence (check file)
        with open(self.test_tasks_file, 'r') as f:
            saved_data = json.load(f)
            self.assertEqual(len(saved_data), 1)
            self.assertEqual(saved_data[0]['id'], 1)

    def test_add_task_increment_id(self):
        # Add first task
        self.task_manager.add_task({"name": "Task 1"})
        
        # Add second task
        new_id = self.task_manager.add_task({"name": "Task 2"})
        
        self.assertEqual(new_id, 2)
        
        # Verify max ID logic (simulate gap)
        self.task_manager.tasks[1]['id'] = 10
        self.task_manager.save_tasks()
        
        # Add third task
        new_id_2 = self.task_manager.add_task({"name": "Task 3"})
        self.assertEqual(new_id_2, 11)

    def test_delete_task(self):
        # Setup
        task_id = self.task_manager.add_task({"name": "To Delete"})
        self.assertIsNotNone(task_id)
        
        # Execute Delete
        result = self.task_manager.delete_task(task_id)
        self.assertTrue(result)
        
        # Verify
        self.assertEqual(len(self.task_manager.get_all_tasks()), 0)
        
        # Test delete non-existent
        result = self.task_manager.delete_task(999)
        self.assertFalse(result)

    def test_update_task(self):
        # Setup
        task_id = self.task_manager.add_task({
            "name": "Original Name",
            "enabled": True
        })
        
        # Execute Update
        updated_data = {
            "name": "Updated Name",
            "enabled": False
        }
        self.task_manager.update_task(task_id, updated_data)
        
        # Verify
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task['name'], "Updated Name")
        self.assertFalse(task['enabled'])
        self.assertEqual(task['id'], task_id)

    def test_persistence_reload(self):
        # Add task and save
        self.task_manager.add_task({"name": "Persistent Task"})
        
        # Create new manager instance pointing to same file
        new_manager = TaskManager(self.test_tasks_file)
        
        # Verify it loads data
        tasks = new_manager.get_all_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['name'], "Persistent Task")

if __name__ == '__main__':
    unittest.main()
