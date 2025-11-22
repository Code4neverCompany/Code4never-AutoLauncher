"""
Scheduler Module for Autolauncher.
Handles task scheduling using APScheduler's BackgroundScheduler.
Executes programs at scheduled times without blocking the Qt event loop.
"""

import subprocess
import ctypes
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

from logger import get_logger
from task_manager import SettingsManager

logger = get_logger(__name__)


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]


class TaskScheduler(QObject):
    """
    Manages task scheduling using APScheduler.
    Runs in the background without interfering with the Qt event loop.
    """
    
    # Signals to communicate with UI
    task_started = pyqtSignal(int, str)  # task_id, task_name
    task_finished = pyqtSignal(int)      # task_id
    ask_user_permission = pyqtSignal(dict) # task_data
    task_postponed = pyqtSignal(int, str) # task_id, new_time_str
    
    def __init__(self):
        """
        Initialize the TaskScheduler with a BackgroundScheduler.
        """
        super().__init__()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        self.settings_manager = SettingsManager()
        self.active_processes: Dict[int, subprocess.Popen] = {}
        
        logger.info("TaskScheduler initialized and started")
    
    def _get_idle_time(self) -> float:
        """
        Get system idle time in seconds.
        """
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
        
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo)):
            millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
            return millis / 1000.0
        else:
            return 0
            
    def add_job(self, task: Dict) -> bool:
        """
        Add a scheduled job from task data.
        """
        try:
            if not task.get('enabled', True):
                logger.debug(f"Task {task['name']} is disabled, skipping")
                return False
            
            # Parse schedule time
            schedule_time = datetime.fromisoformat(task['schedule_time'])
            recurrence = task.get('recurrence', 'Once')
            
            # Create job ID from task ID
            job_id = f"task_{task['id']}"
            
            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Determine trigger based on recurrence
            trigger = None
            
            if recurrence == 'Daily':
                trigger = CronTrigger(
                    hour=schedule_time.hour,
                    minute=schedule_time.minute,
                    second=schedule_time.second
                )
            elif recurrence == 'Weekly':
                trigger = CronTrigger(
                    day_of_week=schedule_time.weekday(),
                    hour=schedule_time.hour,
                    minute=schedule_time.minute,
                    second=schedule_time.second
                )
            elif recurrence == 'Monthly':
                trigger = CronTrigger(
                    day=schedule_time.day,
                    hour=schedule_time.hour,
                    minute=schedule_time.minute,
                    second=schedule_time.second
                )
            else: # Once
                if schedule_time <= datetime.now():
                    logger.warning(f"Task {task['name']} scheduled time is in the past, skipping")
                    return False
                trigger = DateTrigger(run_date=schedule_time)
            
            # Add the job
            self.scheduler.add_job(
                func=self._check_and_execute,
                trigger=trigger,
                args=[task],
                id=job_id,
                name=task['name'],
                replace_existing=True
            )
            
            logger.info(f"Scheduled task '{task['name']}' ({recurrence}) for {schedule_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding job for task {task.get('name')}: {e}")
            return False
    
    def remove_job(self, task_id: int) -> bool:
        """Remove a scheduled job."""
        try:
            job_id = f"task_{task_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing job for task ID {task_id}: {e}")
            return False
    
    def update_job(self, task: Dict) -> bool:
        """Update a scheduled job."""
        self.remove_job(task['id'])
        return self.add_job(task)
        
    def get_next_run_time(self, task_id: int) -> Optional[datetime]:
        """Get the next scheduled run time for a task."""
        job_id = f"task_{task_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None
    
    def execute_immediately(self, task: Dict) -> bool:
        """Execute a task immediately (bypassing checks)."""
        try:
            logger.info(f"Manual execution requested for task '{task['name']}'")
            self._execute_task(task)
            return True
        except Exception as e:
            logger.error(f"Failed to execute task immediately: {e}")
            return False

    def _check_and_execute(self, task: Dict):
        """
        Check conditions (Execution Mode, Idle) before executing.
        """
        # Get Execution Mode: 'auto', 'ask', 'run'
        # Default to 'ask' for safety if not set
        mode = self.settings_manager.get('execution_mode', 'ask')
        
        # Fallback for legacy 'automode' bool if 'execution_mode' is missing
        if self.settings_manager.get('execution_mode') is None:
            if self.settings_manager.get('automode', False):
                mode = 'auto'
        
        idle_time = self._get_idle_time()
        
        logger.debug(f"Check execute: Mode={mode}, Idle={idle_time}s")
        
        # If user is idle (> 60s) or mode is 'run' (Aggressive), execute immediately
        if idle_time >= 60 or mode == 'run':
            self._execute_task(task)
            return

        # User is Active (idle < 60s)
        if mode == 'auto':
            # Automatic: Postpone
            logger.info(f"User is active (idle {idle_time}s). Postponing task '{task['name']}'")
            self._postpone_task(task)
        elif mode == 'ask':
            # Interactive: Ask User
            logger.info(f"User is active. Asking permission for task '{task['name']}'")
            self.ask_user_permission.emit(task)
        else:
            # Fallback (shouldn't happen if logic is correct, but treat as 'ask')
            logger.warning(f"Unknown execution mode '{mode}'. Asking permission.")
            self.ask_user_permission.emit(task)

    def _postpone_task(self, task: Dict, minutes: int = 10):
        """Postpone a task by X minutes."""
        new_time = datetime.now() + timedelta(minutes=minutes)
        
        # Schedule a one-time run
        self.scheduler.add_job(
            func=self._check_and_execute,
            trigger=DateTrigger(run_date=new_time),
            args=[task],
            name=f"postponed_{task['name']}"
        )
        
        self.task_postponed.emit(task['id'], new_time.strftime("%H:%M"))
        logger.info(f"Postponed task '{task['name']}' to {new_time}")

    def handle_user_response(self, task: Dict, response: str):
        """Handle user response from UI dialog."""
        if response == 'Run':
            self._execute_task(task)
        elif response == 'Postpone':
            self._postpone_task(task)
        elif response == 'Cancel':
            logger.info(f"Task '{task['name']}' cancelled by user")
        
    def _execute_task(self, task: Dict):
        """
        Execute the task using subprocess.Popen to allow stopping.
        """
        program_path = task['program_path']
        task_id = task['id']
        
        logger.info(f"Executing task '{task['name']}': {program_path}")
        
        try:
            # Resolve .lnk if needed (basic resolution)
            # Note: Proper .lnk resolution requires pywin32 or similar, 
            # but we'll try to run it directly first. 
            # subprocess.Popen works with .lnk on recent Windows if shell=True
            
            process = subprocess.Popen(
                program_path, 
                shell=True,
                cwd=str(Path(program_path).parent)
            )
            
            self.active_processes[task_id] = process
            self.task_started.emit(task_id, task['name'])
            
            # Monitor process in a separate thread to avoid blocking
            # But for shell=True, Popen returns immediately and might not track the actual app if it spawns children.
            # This is a limitation of shell=True. 
            # However, for "Stop", we can try to kill the process object we have.
            
        except Exception as e:
            logger.error(f"Failed to execute task '{task['name']}': {e}")

    def stop_task(self, task_id: int) -> bool:
        """Stop a running task (terminate process)."""
        if task_id in self.active_processes:
            process = self.active_processes[task_id]
            try:
                process.terminate()
                del self.active_processes[task_id]
                self.task_finished.emit(task_id)
                logger.info(f"Stopped task ID {task_id}")
                return True
            except Exception as e:
                logger.error(f"Error stopping task ID {task_id}: {e}")
                return False
        return False

    def pause_job(self, task_id: int) -> bool:
        """Pause a scheduled job."""
        try:
            job_id = f"task_{task_id}"
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error pausing job {task_id}: {e}")
            return False

    def resume_job(self, task_id: int) -> bool:
        """Resume a scheduled job."""
        try:
            job_id = f"task_{task_id}"
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error resuming job {task_id}: {e}")
            return False

    def is_job_paused(self, task_id: int) -> bool:
        """Check if a job is paused."""
        job_id = f"task_{task_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            # In APScheduler, a paused job has next_run_time = None
            return job.next_run_time is None
        return False

    def shutdown(self):
        """Shutdown the scheduler."""
        try:
            self.scheduler.shutdown(wait=False)
            # Terminate all active processes? Maybe not, user might want them open.
            logger.info("TaskScheduler shut down")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")
    
    def has_running_tasks(self) -> bool:
        """
        Check if any tasks are currently running.
        
        Returns:
            True if any tasks are executing, False otherwise
        """
        return len(self.active_processes) > 0
