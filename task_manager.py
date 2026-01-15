"""
Task Manager Module for Autolauncher.
Handles data persistence using JSON for storing and retrieving scheduled tasks.
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from logger import get_logger
from config import TASKS_FILE, SETTINGS_FILE, DEFAULT_THEME

logger = get_logger(__name__)


class TaskManager:
    """
    Manages task data persistence using JSON files.
    Handles CRUD operations for scheduled tasks.
    """
    
    def __init__(self, tasks_file: Path = TASKS_FILE):
        """
        Initialize the TaskManager.
        
        Args:
            tasks_file: Path to the JSON file for storing tasks
        """
        self.tasks_file = tasks_file
        self.tasks: List[Dict] = []
        self.load_tasks()
        logger.info(f"TaskManager initialized with {len(self.tasks)} tasks")
    
    def load_tasks(self) -> List[Dict]:
        """
        Load tasks from the JSON file.
        
        Returns:
            List of task dictionaries
        """
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
                logger.debug(f"Loaded {len(self.tasks)} tasks from {self.tasks_file}")
            else:
                self.tasks = []
                logger.debug(f"No existing tasks file found at {self.tasks_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tasks file: {e}")
            self.tasks = []
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            self.tasks = []
        
        return self.tasks
    
    def save_tasks(self) -> bool:
        """
        Save tasks to the JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Atomic write: Write to temp file first, then rename
            temp_file = self.tasks_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replacement
            os.replace(temp_file, self.tasks_file)
            
            logger.debug(f"Saved {len(self.tasks)} tasks to {self.tasks_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            # Try to clean up temp file if it exists
            try:
                if 'temp_file' in locals() and temp_file.exists():
                    os.unlink(temp_file)
            except:
                pass
            return False
    
    def add_task(self, task: Dict) -> Optional[int]:
        """
        Add a new task.
        
        Args:
            task: Dictionary containing task data
                  
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            # Add timestamp for task creation
            task['created_at'] = datetime.now().isoformat()
            # Simple ID generation strategy: MAX(id) + 1 or len + 1
            # Using len + 1 is risky if we delete tasks, but for simple app it's "okay" mostly.
            # Ideally we should find max ID. 
            # Let's switch to max ID + 1 for safety.
            max_id = 0
            if self.tasks:
                max_id = max(t.get('id', 0) for t in self.tasks)
            task['id'] = max_id + 1
            
            self.tasks.append(task)
            success = self.save_tasks()
            
            if success:
                logger.info(f"Added new task: {task['name']} (ID: {task['id']})")
                return task['id']
            return None
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return None
    
    def update_task(self, task_id: int, updated_task: Dict) -> bool:
        """
        Update an existing task.
        
        Args:
            task_id: ID of the task to update
            updated_task: Dictionary with updated task data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for i, task in enumerate(self.tasks):
                if task.get('id') == task_id:
                    # Preserve original creation time and ID
                    updated_task['id'] = task_id
                    updated_task['created_at'] = task.get('created_at', datetime.now().isoformat())
                    updated_task['updated_at'] = datetime.now().isoformat()
                    
                    self.tasks[i] = updated_task
                    success = self.save_tasks()
                    
                    if success:
                        logger.info(f"Updated task ID {task_id}: {updated_task['name']}")
                    return success
            
            logger.warning(f"Task ID {task_id} not found for update")
            return False
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task by ID.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            original_count = len(self.tasks)
            self.tasks = [task for task in self.tasks if task.get('id') != task_id]
            
            if len(self.tasks) < original_count:
                success = self.save_tasks()
                if success:
                    logger.info(f"Deleted task ID {task_id}")
                return success
            else:
                logger.warning(f"Task ID {task_id} not found for deletion")
                return False
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """
        Get a task by ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Task dictionary if found, None otherwise
        """
        for task in self.tasks:
            if task.get('id') == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[Dict]:
        """
        Get all tasks.
        
        Returns:
            List of all task dictionaries
        """
        return self.tasks
    
    def get_enabled_tasks(self) -> List[Dict]:
        """
        Get only enabled tasks.
        
        Returns:
            List of enabled task dictionaries
        """
        return [task for task in self.tasks if task.get('enabled', True)]
    
    def set_postponed_until(self, task_id: int, postponed_until: str) -> bool:
        """
        Set a task's postponed time. This persists the postpone state across app restarts.
        
        Args:
            task_id: ID of the task to update
            postponed_until: ISO format datetime string of when to retry
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for task in self.tasks:
                if task.get('id') == task_id:
                    task['postponed_until'] = postponed_until
                    success = self.save_tasks()
                    if success:
                        logger.info(f"Set postponed_until for task ID {task_id}: {postponed_until}")
                    return success
            
            logger.warning(f"Task ID {task_id} not found for postpone update")
            return False
        except Exception as e:
            logger.error(f"Error setting postponed_until: {e}")
            return False
    
    def clear_postponed(self, task_id: int) -> bool:
        """
        Clear a task's postponed state (after successful execution).
        
        Args:
            task_id: ID of the task to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for task in self.tasks:
                if task.get('id') == task_id:
                    if 'postponed_until' in task:
                        del task['postponed_until']
                        success = self.save_tasks()
                        if success:
                            logger.info(f"Cleared postponed state for task ID {task_id}")
                        return success
                    return True  # Already clear
            
            logger.warning(f"Task ID {task_id} not found for clear_postponed")
            return False
        except Exception as e:
            logger.error(f"Error clearing postponed state: {e}")
            return False


class SettingsManager:
    """
    Manages application settings persistence.
    """
    
    def __init__(self, settings_file: Path = SETTINGS_FILE):
        """
        Initialize the SettingsManager.
        
        Args:
            settings_file: Path to the JSON file for storing settings
        """
        self.settings_file = settings_file
        self.settings: Dict = {}
        self.load_settings()
    
    def load_settings(self) -> Dict:
        """
        Load settings from JSON file.
        
        Returns:
            Dictionary of settings
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                logger.debug(f"Loaded settings from {self.settings_file}")
            else:
                # Create default settings
                self.settings = {
                    'theme': DEFAULT_THEME,
                    'window_width': 900,
                    'window_height': 600
                }
                self.save_settings()
                logger.debug("Created default settings")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.settings = {'theme': DEFAULT_THEME}
        
        return self.settings
    
    def save_settings(self) -> bool:
        """
        Save settings to JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Atomic write: Write to temp file first, then rename
            temp_file = self.settings_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replacement
            os.replace(temp_file, self.settings_file)
            
            logger.debug(f"Saved settings to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            try:
                if 'temp_file' in locals() and temp_file.exists():
                    os.unlink(temp_file)
            except:
                pass
            return False
    
    def get(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value) -> bool:
        """Set a setting value and save."""
        self.settings[key] = value
        return self.save_settings()
