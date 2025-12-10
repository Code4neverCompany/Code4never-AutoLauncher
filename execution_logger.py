"""
Execution Logger Module
Handles logging of task execution events (start, finish, error, postpone) to a JSON file.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from logger import get_logger

logger = get_logger(__name__)

class ExecutionLogger:
    """
    Manages the execution log file.
    Stores events like: STARTED, FINISHED, FAILED, POSTPONED, SKIPPED.
    """
    
    def __init__(self, log_file: str = "data/execution_log.json"):
        """
        Initialize the execution logger.
        
        Args:
            log_file: Path to the log file
        """
        self.log_file = Path(log_file)
        self._ensure_log_file()
        
    def _ensure_log_file(self):
        """Ensure the log file exists and contains a valid JSON array."""
        if not self.log_file.parent.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            
        if not self.log_file.exists():
            self._write_log([])
        else:
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    json.load(f)
            except (json.JSONDecodeError, ValueError):
                logger.warning("Execution log file corrupted, resetting.")
                self._write_log([])
                
    def _read_log(self) -> List[Dict]:
        """Read the log entries."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read execution log: {e}")
            return []
            
    def _write_log(self, entries: List[Dict]):
        """Write entries to the log file."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write execution log: {e}")
            
    def log_event(self, task_id: int, task_name: str, event_type: str, details: str = "", **kwargs):
        """
        Log a task execution event.
        
        Args:
            task_id: ID of the task
            task_name: Name of the task
            event_type: Type of event:
                - STARTED: Task execution began
                - FINISHED: Task execution completed
                - FAILED: Task execution failed
                - POSTPONED: Task was postponed due to user activity
                - MISSED: Task missed scheduled time (system unavailable)
                - WAKE_SCHEDULED: Wake timer was set for task
                - WAKE_SUCCESS: System woke successfully for task
            details: Optional details about the event
            **kwargs: Additional fields (e.g., scheduled_time for MISSED events)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "task_name": task_name,
            "event_type": event_type,
            "details": details
        }
        
        # Add any additional fields from kwargs
        if 'scheduled_time' in kwargs:
            entry['scheduled_time'] = kwargs['scheduled_time']
        
        entries = self._read_log()
        entries.append(entry)
        
        # Limit log size (keep last 1000 entries)
        if len(entries) > 1000:
            entries = entries[-1000:]
            
        self._write_log(entries)
        logger.debug(f"Logged event: {event_type} for {task_name}")
        
    def get_logs(self, limit: int = 100) -> List[Dict]:
        """
        Get the most recent log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of log entries (most recent first)
        """
        entries = self._read_log()
        return sorted(entries, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def clear_logs(self):
        """Clear all log entries."""
        self._write_log([])
        logger.info("Execution log cleared")
