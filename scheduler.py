"""
Scheduler Module for Autolauncher.
Handles task scheduling using APScheduler's BackgroundScheduler.
Executes programs at scheduled times without blocking the Qt event loop.
"""

import subprocess
import ctypes
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import threading
from power_manager import PowerManager
from stuck_detector import StuckDetector
from config import STUCK_DETECTION_KEYWORDS, STUCK_DETECTION_OCR_KEYWORDS, CONFIRMATION_DIALOG_KEYWORDS, CONFIRMATION_BUTTON_LABELS
from input_monitor import get_input_monitor, start_input_monitor

from PyQt6.QtCore import QObject, pyqtSignal
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_MISSED, EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

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
    update_detector_started = pyqtSignal(int, str)  # task_id, task_name
    update_detector_stopped = pyqtSignal(int)       # task_id
    
    def __init__(self):
        """
        Initialize the TaskScheduler with a BackgroundScheduler.
        """
        super().__init__()
        # Configure APScheduler with misfire handling
        # - misfire_grace_time: Jobs can be up to 5 minutes late and still run
        # - coalesce: If multiple runs were missed, only run once
        self.scheduler = BackgroundScheduler(
            job_defaults={
                'misfire_grace_time': 300,  # 5 minute grace period
                'coalesce': True  # Combine multiple missed runs into one
            }
        )
        self.scheduler.start()
        
        self.settings_manager = SettingsManager()
        self.active_processes: Dict[int, subprocess.Popen] = {}
        
        # Initialize ExecutionLogger
        from execution_logger import ExecutionLogger
        self.execution_logger = ExecutionLogger()
        
        # Initialize Power Manager
        self.power_manager = PowerManager()
        self.stuck_detector = StuckDetector()
        self._keep_awake_counter = 0
        self._keep_awake_lock = threading.Lock()
        
        # Start the input monitor for real input detection
        start_input_monitor()
        self._input_monitor = get_input_monitor()
        
        # Add event listeners for job execution monitoring
        self.scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        
        # Add periodic wake timer refresh to keep timers fresh during extended sleep
        # This ensures the wake timer is refreshed every 4 hours, preventing stale timers
        self.scheduler.add_job(
            func=self._periodic_wake_timer_refresh,
            trigger=IntervalTrigger(hours=4),
            id='periodic_wake_timer_refresh',
            name='Periodic Wake Timer Refresh',
            replace_existing=True
        )

        # Periodic process cleanup (Zombie Collection)
        self.scheduler.add_job(
            func=self._cleanup_finished_processes,
            trigger=IntervalTrigger(seconds=60),
            id='process_cleanup',
            name='Process Cleanup',
            replace_existing=True
        )
        
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
    
    def _is_system_busy(self) -> tuple:
        """
        Check if the system is currently busy based on multiple factors.
        
        Returns:
            tuple: (is_busy: bool, reason: str)
        """
        reasons = []
        
        # Thresholds (configurable in future)
        CPU_THRESHOLD = 50  # percent
        RAM_THRESHOLD = 80  # percent
        GPU_THRESHOLD = 50  # percent
        IDLE_THRESHOLD = 60  # seconds
        
        # Load user-configured blocklist (falls back to defaults)
        # Load user-configured blocklist (falls back to defaults)
        from config import DEFAULT_BLOCKLIST_PROCESSES, BLOCKLIST_FILE
        import json
        
        user_blocklist = []
        
        # 1. Try to load from JSON file (Highest Priority - External Config)
        if BLOCKLIST_FILE.exists():
            try:
                with open(BLOCKLIST_FILE, 'r', encoding='utf-8') as f:
                    user_blocklist = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load blocklist.json: {e}")
        
        # 2. If nothing in JSON, try settings (Legacy)
        if not user_blocklist:
            user_blocklist = self.settings_manager.get('blocklist_processes', None)
            
        # 3. Fallback to hardcoded defaults
        if not user_blocklist:
            user_blocklist = DEFAULT_BLOCKLIST_PROCESSES
        
        
        # Convert to lowercase set for efficient lookup
        BLOCKLIST_PROCESSES = set(p.lower() for p in user_blocklist)
        
        # 1. Check CPU usage
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            if cpu_percent > CPU_THRESHOLD:
                reasons.append(f"CPU at {cpu_percent:.0f}%")
        except Exception as e:
            logger.debug(f"CPU check failed: {e}")
        
        # 2. Check RAM usage
        try:
            ram = psutil.virtual_memory()
            if ram.percent > RAM_THRESHOLD:
                reasons.append(f"RAM at {ram.percent:.0f}%")
        except Exception as e:
            logger.debug(f"RAM check failed: {e}")
        
        # 3. Check GPU usage (optional - requires GPUtil)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_load = max(gpu.load * 100 for gpu in gpus)
                if gpu_load > GPU_THRESHOLD:
                    reasons.append(f"GPU at {gpu_load:.0f}%")
        except ImportError:
            pass  # GPUtil not installed, skip GPU check
        except Exception as e:
            logger.debug(f"GPU check failed: {e}")
        
        # NOTE: We do NOT check idle time for POSTPONE decisions.
        # POSTPONE only triggers on:
        #   1. Blocklist programs running (e.g., games, IDEs)
        #   2. High resource usage (CPU/GPU/RAM above threshold)
        # User idle time is irrelevant - task runs as long as no blocklist programs
        # and resources are available.
        
        # 5. Check for known games/apps running
        try:
            running_blocklist = []
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if proc_name in BLOCKLIST_PROCESSES:
                        running_blocklist.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if running_blocklist:
                # Deduplicate
                unique_apps = list(set(running_blocklist))[:3]  # Show max 3
                reasons.append(f"Running: {', '.join(unique_apps)}")
        except Exception as e:
            logger.debug(f"Process check failed: {e}")
        
        if reasons:
            return (True, "; ".join(reasons))
        else:
            return (False, "System is idle")
    
    def _on_job_missed(self, event):
        """
        Handle APScheduler job missed event.
        Logs when a scheduled job was missed (beyond misfire_grace_time).
        For user tasks, reschedules the task to run in 2 minutes to attempt recovery.
        """
        try:
            job = self.scheduler.get_job(event.job_id)
            if job and job.args and len(job.args) > 0:
                task = job.args[0]
                task_id = task.get('id', 0)
                task_name = task.get('name', 'Unknown')
                
                # Calculate how late we were
                scheduled_time = event.scheduled_run_time
                now = datetime.now(scheduled_time.tzinfo) if scheduled_time.tzinfo else datetime.now()
                delay_seconds = (now - scheduled_time).total_seconds()
                
                reason = f"Wake-up failed or system unavailable. Scheduled: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}, Delay: {int(delay_seconds)}s"
                
                logger.warning(f"MISSED: Task '{task_name}' missed execution. {reason}")
                
                # Log to execution logger with MISSED event type
                self.execution_logger.log_event(
                    task_id, 
                    task_name, 
                    "MISSED", 
                    reason,
                    scheduled_time=scheduled_time.isoformat()
                )
                
                # RECOVERY: Reschedule the missed task to run in 2 minutes
                # This gives the user a chance to have the task executed even if wake failed
                recovery_time = datetime.now() + timedelta(minutes=2)
                
                logger.info(f"RECOVERY: Rescheduling missed task '{task_name}' to run at {recovery_time.strftime('%H:%M:%S')} (in 2 minutes)")
                
                # Log the recovery attempt
                self.execution_logger.log_event(
                    task_id,
                    task_name,
                    "RECOVERY_SCHEDULED",
                    f"Missed task rescheduled to {recovery_time.strftime('%Y-%m-%d %H:%M:%S')} after wake-up failure"
                )
                
                # Schedule recovery job
                self.scheduler.add_job(
                    func=self._check_and_execute,
                    trigger=DateTrigger(run_date=recovery_time),
                    args=[task],
                    name=f"recovery_{task_name}_{recovery_time.strftime('%H%M')}"
                )
                
                self.task_postponed.emit(task_id, recovery_time.strftime("%H:%M"))
            else:
                # System job (like prewake) - just log, don't reschedule
                logger.warning(f"MISSED: System job '{event.job_id}' missed execution")
            
            # Refresh wake timer for next scheduled task
            # This ensures the system can still wake for future tasks after missing one
            self._update_system_wake_timer()
        except Exception as e:
            logger.error(f"Error handling job missed event: {e}")
    
    def _on_job_error(self, event):
        """
        Handle APScheduler job error event.
        Logs when a scheduled job raised an exception.
        """
        try:
            job = self.scheduler.get_job(event.job_id)
            if job and job.args and len(job.args) > 0:
                task = job.args[0]
                task_id = task.get('id', 0)
                task_name = task.get('name', 'Unknown')
                
                error_msg = str(event.exception) if event.exception else "Unknown error"
                logger.error(f"JOB ERROR: Task '{task_name}' failed with: {error_msg}")
                
                # Log to execution logger
                self.execution_logger.log_event(task_id, task_name, "FAILED", f"Scheduler error: {error_msg}")
        except Exception as e:
            logger.error(f"Error handling job error event: {e}")
    
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
                # Check if this task should have already run today but hasn't yet
                now = datetime.now()
                today_time = now.replace(hour=schedule_time.hour, minute=schedule_time.minute, second=schedule_time.second, microsecond=0)
                
                # If scheduled time for today has passed but it was within the last hour, 
                # we might want to trigger it now if the system just woke up.
                # However, APScheduler's CronTrigger with misfire_grace_time usually handles this.
                # The issue is when the system wakes up AT or very close to the time.
                
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
            
            # Schedule Pre-wake job if enabled
            if task.get('wake_enabled', False):
                self._schedule_pre_wake_job(task)
            
            logger.info(f"Scheduled task '{task['name']}' ({recurrence}) for {schedule_time}")
            
            # Update system wake timer
            self._update_system_wake_timer()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding job for task {task.get('name')}: {e}")
            return False

    def resync_all_jobs(self):
        """
        Re-sync all jobs in the scheduler.
        Used after system resume to ensure the scheduler state is consistent 
        and all triggers are correctly calculated for the new current time.
        """
        try:
            logger.info("Re-syncing all scheduled jobs...")
            from task_manager import TaskManager
            tm = TaskManager()
            enabled_tasks = tm.get_enabled_tasks()
            
            for task in enabled_tasks:
                self.add_job(task)
                
            self._update_system_wake_timer()
            logger.info(f"Re-sync complete. {len(enabled_tasks)} tasks updated.")
        except Exception as e:
            logger.error(f"Error during scheduler re-sync: {e}")
    
    def remove_job(self, task_id: int) -> bool:
        """Remove a scheduled job."""
        try:
            job_id = f"task_{task_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                # Also remove pre-wake job if exists
                pre_wake_id = f"prewake_{task_id}"
                if self.scheduler.get_job(pre_wake_id):
                    self.scheduler.remove_job(pre_wake_id)
                    
                self._update_system_wake_timer()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing job for task ID {task_id}: {e}")
            return False
    
    def clear_jobs(self):
        """Remove all scheduled jobs."""
        self.scheduler.remove_all_jobs()

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
        Check conditions (Execution Mode, System Usage) before executing.
        Uses smart detection for auto mode: CPU, RAM, GPU, idle time, running games.
        """
        task_id = task.get('id', 0)
        task_name = task.get('name', 'Unknown')
        
        # Reload settings to get fresh execution_mode (may have been changed via UI)
        self.settings_manager.load_settings()
        
        # Get Execution Mode: 'auto', 'ask', 'run'
        # Default to 'ask' for safety if not set
        mode = self.settings_manager.get('execution_mode', 'ask')
        
        # Fallback for legacy 'automode' bool if 'execution_mode' is missing
        if self.settings_manager.get('execution_mode') is None:
            if self.settings_manager.get('automode', False):
                mode = 'auto'
        
        logger.debug(f"Check execute: Mode={mode}, Task={task_name}")
        
        # Mode: Aggressive (run) - Always execute immediately
        if mode == 'run':
            logger.info(f"Execution mode is 'Aggressive'. Executing task '{task_name}' immediately")
            self._execute_task(task)
            return
        
        # Mode: Automatic - Use smart busy detection
        if mode == 'auto':
            is_busy, reason = self._is_system_busy()
            
            if is_busy:
                # Log postponement with detailed reason
                logger.info(f"System busy ({reason}). Postponing task '{task_name}'")
                self.execution_logger.log_event(
                    task_id, 
                    task_name, 
                    "POSTPONED", 
                    f"System busy: {reason}"
                )
                self._postpone_task(task, minutes=30)  # 30-minute retry interval
            else:
                # Log that conditions were met
                logger.info(f"System idle ({reason}). Executing task '{task_name}'")
                self.execution_logger.log_event(
                    task_id,
                    task_name,
                    "EXECUTED",
                    f"Conditions met: {reason}"
                )
                self._execute_task(task)
            return
        
        # Mode: Interactive (ask) - Check idle time first, then ask
        idle_time = self._get_idle_time()
        if idle_time >= 60:
            logger.info(f"User is idle ({idle_time}s). Executing task '{task_name}'")
            self._execute_task(task)
        else:
            logger.info(f"User is active. Asking permission for task '{task_name}'")
            self.ask_user_permission.emit(task)

    def _postpone_task(self, task: Dict, minutes: int = 30):
        """
        Postpone a task by X minutes.
        Default is 30 minutes for auto mode. Never cancels - always retries.
        Persists the postpone time to tasks.json so it survives app restarts.
        """
        task_id = task.get('id', 0)
        task_name = task.get('name', 'Unknown')
        new_time = datetime.now() + timedelta(minutes=minutes)
        
        # Persist postpone time to tasks.json (survives app restart)
        from task_manager import TaskManager
        tm = TaskManager()
        tm.set_postponed_until(task_id, new_time.isoformat())
        
        # Schedule a one-time run - never give up
        self.scheduler.add_job(
            func=self._check_and_execute,
            trigger=DateTrigger(run_date=new_time),
            args=[task],
            name=f"retry_{task_name}_{new_time.strftime('%H%M')}"
        )
        
        self.task_postponed.emit(task_id, new_time.strftime("%H:%M"))
        logger.info(f"Task '{task_name}' rescheduled for {new_time.strftime('%H:%M')} (retry in {minutes} mins)")

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
        task_name = task['name']
        
        # Clear postpone state since task is now executing
        from task_manager import TaskManager
        tm = TaskManager()
        tm.clear_postponed(task_id)
        
        logger.info(f"Executing task '{task_name}': {program_path}")
        
        # Log STARTED event
        self.execution_logger.log_event(task_id, task_name, "STARTED", f"Program: {program_path}")
        
        launch_time = time.time()
        
        try:
            # Use shell=False for reliable PID tracking
            # If arguments are needed in the future, we should split program_path
            process = subprocess.Popen(
                program_path, 
                shell=False,
                cwd=str(Path(program_path).parent)
            )
            
            self.active_processes[task_id] = process
            self.task_started.emit(task_id, task_name)
            
            # Log FINISHED event (immediately after start for shell=True)
            self.execution_logger.log_event(task_id, task_name, "FINISHED", "Process started successfully")
            
        except Exception as e:
            logger.error(f"Failed to execute task '{task_name}': {e}")
            # Log FAILED event
            self.execution_logger.log_event(task_id, task_name, "FAILED", f"Error: {str(e)}")
            
            # If task failed, we should release the keep-awake lock if we were holding it
            # But wait, we only release it when the process finishes or if we skipped execution.
            # If we are here, we tried to execute.
            # If execution failed (exception), we need to decrement counter if we incremented it in pre-wake.
            # However, pre-wake is a separate job.
            # The keep-awake is started in pre-wake.
            # We need to ensure we stop it eventually.
            # Let's handle it in _handle_task_completion (new method) or just here.
            self._release_keep_awake()

            self._release_keep_awake()

        # Start Stuck Detection Monitor (runs in background)
        if process and process.pid:
            self._start_stuck_monitor(task_id, task_name, process.pid, task)

        # Handle Sleep After Completion
        if task.get('sleep_after', False):
            # Check if system woke up for this task (Smart Sleep)
            woke_for_task = False
            try:
                wake_info = self.power_manager.get_last_wake_info()
                if wake_info and wake_info.get('wake_time'):
                    wake_time = wake_info['wake_time']
                    # Check if wake was recent (within last 15 mins)
                    # If PC woke recently, we assume it might be for this task (or another scheduled one)
                    # If PC has been on for hours, woke_for_task will be False
                    now = datetime.now(wake_time.tzinfo)
                    if (now - wake_time).total_seconds() < 900: # 15 minutes
                        woke_for_task = True
                        logger.info(f"Smart Sleep: Recent wake detected at {wake_time} (Source: {wake_info.get('wake_source')})")
                    else:
                        logger.info(f"Smart Sleep: System was already awake (Last wake: {wake_time})")
            except Exception as e:
                logger.error(f"Error checking wake info: {e}")

            self._handle_sleep_after_task(task_id, task_name, launch_time, woke_for_task)
        
        # Always release keep-awake after task starts
        # If sleep_after is True, we still release the "pre-wake" hold.
        # The sleep logic handles its own power state (forcing sleep later).
        self._release_keep_awake()
        
        # CRITICAL: Refresh wake timer for the NEXT scheduled task
        # This ensures that if the system goes to sleep soon after this task completes,
        # the wake timer for the next task is already set.
        # Without this, there's a gap where the system could sleep before the next timer is set.
        self._update_system_wake_timer()

    def _schedule_pre_wake_job(self, task: Dict):
        """Schedule a job to wake the system before the task."""
        try:
            task_id = task['id']
            job_id = f"prewake_{task_id}"
            
            # Get pre-wake duration
            pre_wake_minutes = self.settings_manager.get('pre_wake_minutes', 5)
            
            # Calculate trigger time based on task schedule
            # This is tricky for recurring tasks.
            # We need to hook into the main job's next run time.
            # APScheduler doesn't easily support "run X mins before another dynamic job".
            # Alternative: The wake timer is set by _update_system_wake_timer.
            # The pre-wake job is needed to START the keep-awake state.
            # We can use the same trigger as the main job but with a jitter? No.
            # We need to calculate the next run time and schedule a one-off pre-wake?
            # Or use a custom trigger?
            
            # Simpler approach:
            # _update_system_wake_timer sets the hardware wake timer.
            # When the system wakes up, we need to ensure it STAYS awake.
            # If we rely on the hardware timer to wake us at T minus 5,
            # we can just schedule a job at T minus 5 to call _start_keep_awake.
            
            # But for recurring tasks, we don't know the absolute T easily without querying the job.
            # Let's rely on _update_system_wake_timer to schedule the pre-wake job dynamically?
            # No, that's polling.
            
            # Better: When adding the main job, we add a pre-wake job with the same recurrence
            # but shifted time? CronTrigger doesn't support "shift".
            
            # Workaround:
            # We only really need the hardware wake timer to wake us.
            # Once awake, if the app is running, we can check if a task is imminent.
            # But if the app is just a background process, we need code to run.
            
            # Let's stick to: _update_system_wake_timer sets the hardware timer.
            # It ALSO schedules a one-off python job to run at that wake time to "hold" the state.
            # This needs to be refreshed whenever a task runs or is updated.
            pass 
        except Exception as e:
            logger.error(f"Error scheduling pre-wake: {e}")

    def _start_pre_wake(self):
        """Start keeping the system awake."""
        with self._keep_awake_lock:
            self._keep_awake_counter += 1
            if self._keep_awake_counter == 1:
                self.power_manager.start_keep_awake()
            logger.info(f"Pre-wake started. Counter: {self._keep_awake_counter}")

    def _periodic_wake_timer_refresh(self):
        """
        Periodically refresh the system wake timer to ensure reliability.
        This fixes the issue where wake timers become stale after 24+ hours of sleep.
        Called automatically every 4 hours by an APScheduler interval job.
        """
        logger.info("Periodic wake timer refresh triggered - ensuring wake timer is fresh")
        self._update_system_wake_timer()

    def _release_keep_awake(self):
        """Release the keep-awake hold."""
        with self._keep_awake_lock:
            if self._keep_awake_counter > 0:
                self._keep_awake_counter -= 1
                if self._keep_awake_counter == 0:
                    self.power_manager.stop_keep_awake()
                logger.info(f"Keep-awake released. Counter: {self._keep_awake_counter}")

    def _handle_sleep_after_task(self, task_id: int, task_name: str, launch_time: float = None, woke_for_task: bool = False):
        """
        Wait for the task to finish and then put the system to sleep.
        Runs in a separate thread to avoid blocking.
        Tracks ALL spawned processes (handles launchers that spawn games).
        """
        def wait_and_sleep():
            from process_tracker import get_spawned_processes, wait_for_processes, resolve_shortcut
            
            def should_enter_sleep():
                """Determine if we should sleep based on REAL (non-simulated) input."""
                # Get Smart Sleep settings
                try:
                    from task_manager import SettingsManager
                    settings = SettingsManager()
                    is_enabled = settings.get('smart_sleep_enabled', False)
                    threshold = settings.get('smart_sleep_threshold', 60) # Default 60 seconds
                except ImportError:
                    is_enabled = False
                    threshold = 60
                
                if not is_enabled:
                    logger.info("Smart Sleep disabled. Proceeding to sleep immediately.")
                    return True

                logger.info(f"Smart Sleep: Monitoring for REAL input for {threshold} seconds...")
                
                # Get the input monitor
                input_monitor = get_input_monitor()
                
                # Monitor for threshold seconds, checking every 1 second for faster response
                monitoring_duration = int(threshold)
                check_interval = 1
                
                # Record the START of monitoring - don't reset global state
                # We'll compare idle time against this to detect new input
                monitoring_start = time.time()
                initial_idle = input_monitor.get_real_idle_time()
                
                for i in range(monitoring_duration // check_interval):
                    time.sleep(check_interval)
                    current_idle = input_monitor.get_real_idle_time()
                    elapsed = time.time() - monitoring_start
                    
                    # If idle time is less than elapsed time, user provided input
                    # (idle resets to 0 when real input is detected)
                    if current_idle < elapsed - 0.5:  # Small buffer for timing
                        logger.info(f"Smart Sleep: Real human input detected (idle {current_idle:.1f}s, elapsed {elapsed:.1f}s). Skipping sleep.")
                        return False
                    
                logger.info(f"Smart Sleep: No real input detected for {monitoring_duration} seconds. Proceeding to sleep.")
                return True

            # Get target process name from task program path
            target_name = None
            try:
                # Need to fetch task data to get program path
                from task_manager import TaskManager
                tm = TaskManager()
                task = tm.get_task(task_id)
                if task and 'program_path' in task:
                    program_path = task['program_path']
                    # Resolve shortcut if it is one
                    if program_path.lower().endswith('.lnk'):
                        resolved_path = resolve_shortcut(program_path)
                        if resolved_path:
                            target_name = Path(resolved_path).name
                    else:
                        target_name = Path(program_path).name
            except Exception as e:
                logger.warning(f"Could not determine target process name: {e}")

            logger.info(f"Monitoring spawned processes for '{task_name}' (Target: {target_name})...")
            
            # Wait a moment for the launch to complete
            time.sleep(1)
            
            # Find all processes that were spawned by the task
            # Use launch_time if available to catch fast-starting processes
            spawned_processes = get_spawned_processes(timeout=8, target_process_name=target_name, search_start_time=launch_time)
            
            if spawned_processes:
                logger.info(f"Waiting for {len(spawned_processes)} spawned process(es) to complete before sleeping...")
                
                # Wait for ALL spawned processes to finish
                wait_for_processes(spawned_processes)
                
                # Clean up active_processes so Running status clears
                if task_id in self.active_processes:
                    del self.active_processes[task_id]
                
                # Emit task finished signal
                self.task_finished.emit(task_id)
                
                logger.info(f"Task '{task_name}' and all spawned processes finished. Initiating sleep mode...")
                time.sleep(2)  # Small buffer to ensure cleanup
                
                # Check sleep conditions
                if should_enter_sleep():
                    self.power_manager.enter_sleep_mode()

            else:
                # Fallback to old behavior if we couldn't find processes
                logger.warning(f"No spawned processes detected for '{task_name}', using fallback method")
                process = self.active_processes.get(task_id)
                if process:
                    process.wait()
                    if task_id in self.active_processes:
                        del self.active_processes[task_id]
                        self.task_finished.emit(task_id)
                    logger.info(f"Task '{task_name}' finished (fallback). Initiating sleep mode...")
                    
                    # Check sleep conditions
                    if should_enter_sleep():
                        self.power_manager.enter_sleep_mode()
        
        thread = threading.Thread(target=wait_and_sleep, daemon=True)
        thread.start()
    
    def _update_system_wake_timer(self):
        """
        Calculate the next wake time and set the system wake timer.
        Also schedules a Python job to hold the system awake from that time.
        Uses per-task pre_wake_minutes if available, falls back to global setting.
        """
        try:
            next_wake_time = None
            next_wake_task = None  # Track which task triggered the wake
            global_pre_wake = self.settings_manager.get('pre_wake_minutes', 5)
            
            # Iterate through all jobs to find the earliest 'wake_enabled' task
            for job in self.scheduler.get_jobs():
                if job.id.startswith("prewake_"):
                    continue
                if job.id == "system_prewake_hold":
                    continue
                
                # Check if this job has a task with wake_enabled
                if job.args and len(job.args) > 0:
                    task = job.args[0]
                    if task.get('wake_enabled', False) and job.next_run_time:
                        run_time = job.next_run_time
                        
                        # Use task-specific pre-wake duration if available
                        task_pre_wake = task.get('pre_wake_minutes', global_pre_wake)
                        
                        # Wake up X minutes before
                        wake_time = run_time - timedelta(minutes=task_pre_wake)
                        
                        # Ensure wake time is in the future
                        if wake_time > datetime.now(wake_time.tzinfo):
                            if next_wake_time is None or wake_time < next_wake_time:
                                next_wake_time = wake_time
                                next_wake_task = task
            
            # Remove existing pre-wake hold job
            if self.scheduler.get_job("system_prewake_hold"):
                self.scheduler.remove_job("system_prewake_hold")
            
            if next_wake_time:
                success = self.power_manager.set_wake_timer(next_wake_time)
                
                # Log WAKE_SCHEDULED event
                if next_wake_task and success:
                    task_id = next_wake_task.get('id', 0)
                    task_name = next_wake_task.get('name', 'Unknown')
                    self.execution_logger.log_event(
                        task_id, 
                        task_name, 
                        "WAKE_SCHEDULED", 
                        f"System will wake at {next_wake_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                
                # Schedule a job to start keeping awake at the wake time
                self.scheduler.add_job(
                    func=self._start_pre_wake,
                    trigger=DateTrigger(run_date=next_wake_time),
                    id="system_prewake_hold",
                    name="System Pre-wake Hold",
                    replace_existing=True
                )
                logger.info(f"Scheduled pre-wake hold for {next_wake_time}")
            else:
                self.power_manager.cancel_wake_timer()
                
        except Exception as e:
            logger.error(f"Error updating system wake timer: {e}")

    def stop_task(self, task_id: int) -> bool:
        """
        Stop a running task (recursively terminate process tree).
        This ensures that games/updates launched by a launcher are also killed.
        """
        if task_id in self.active_processes:
            process = self.active_processes[task_id]
            pid = process.pid
            logger.info(f"Attempting to stop Task ID {task_id} (PID {pid}) and its children...")
            
            try:
                # 1. Use psutil to find and kill children first
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    
                    if children:
                        logger.info(f"Found {len(children)} child processes. Terminating...")
                        for child in children:
                            try:
                                child.terminate()
                                logger.debug(f"Terminated child PID {child.pid} ({child.name()})")
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                        
                        # Wait briefly for children to die
                        gone, still_alive = psutil.wait_procs(children, timeout=3)
                        
                        # Force kill if still alive
                        for child in still_alive:
                            try:
                                child.kill()
                                logger.warning(f"Force killed stubborn child PID {child.pid} ({child.name()})")
                            except:
                                pass
                                
                except psutil.NoSuchProcess:
                    logger.warning(f"Parent process PID {pid} already gone during child lookup")
                except Exception as e:
                    logger.error(f"Error during child process termination: {e}")

                # 2. Terminate the main parent process (the one we launched)
                process.terminate()
                
                # Wait for it to exit
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Parent process PID {pid} did not exit gracefully. Force killing...")
                    process.kill()
                
                # 3. Clean up
                if task_id in self.active_processes:
                    del self.active_processes[task_id]
                    
                self.task_finished.emit(task_id)
                logger.info(f"Successfully stopped Task ID {task_id} and cleaned up process tree.")
                return True
                
            except Exception as e:
                logger.error(f"Critical error stopping task ID {task_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Force clean up dictionary even if error occurred
                if task_id in self.active_processes:
                    del self.active_processes[task_id]
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

    def get_next_run_time(self, task_id: int = None) -> Optional[datetime]:
        """
        Get the next run time.
        If task_id is provided, returns next run time for that task.
        If task_id is None, returns the earliest next run time of any job.
        """
        if task_id is not None:
            job_id = f"task_{task_id}"
            job = self.scheduler.get_job(job_id)
            return job.next_run_time if job else None
            
        jobs = self.scheduler.get_jobs()
        if not jobs:
            return None
            
        next_times = [job.next_run_time for job in jobs if job.next_run_time]
        if not next_times:
            return None
            
        return min(next_times)

    def _start_stuck_monitor(self, task_id: int, task_name: str, pid: int, task: Dict):
        """
        Start a background thread to monitor if the task gets stuck in an update/setup screen.
        Runs for 5 minutes after launch.
        """
        def monitor_thread():
            from process_tracker import get_spawned_processes
            
            logger.info(f"Stuck Monitor started for '{task_name}' (PID: {pid})")
            self.update_detector_started.emit(task_id, task_name)
            start_time = time.time()
            loop_count = 0
            
            # Initial wait for processes to spawn
            time.sleep(2)
            
            # Monitor for 5 minutes (300 seconds)
            while time.time() - start_time < 300:
                # Check if main process is still running
                if task_id not in self.active_processes:
                    break
                
                # Maintain a set of PIDs to check, starting with the initial PID
                # We need to dynamically update this list to handle launchers that exit
                if 'tracked_pids' not in locals():
                    tracked_pids = {pid}

                current_living_pids = []
                new_children_pids = set()

                # Check all tracked PIDs
                for t_pid in list(tracked_pids):
                    try:
                        proc = psutil.Process(t_pid)
                        if proc.is_running():
                            current_living_pids.append(t_pid)
                            
                            # Check for new children
                            try:
                                children = proc.children(recursive=True)
                                for child in children:
                                    if child.pid not in tracked_pids:
                                        logger.info(f"StuckMonitor: Adopting child process {child.name()} (PID: {child.pid})")
                                        new_children_pids.add(child.pid)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Add new children to tracking
                if new_children_pids:
                    tracked_pids.update(new_children_pids)
                    current_living_pids.extend(list(new_children_pids))
                
                # Update list for this iteration
                pids_to_check = current_living_pids
                
                # If NO processes are left alive, then we stop
                if not pids_to_check:
                    logger.info("StuckMonitor: All tracked processes finished. Stopping monitor.")
                    break
                
                # Check for stuck state (Title)
                stuck_title = self.stuck_detector.is_process_stuck(pids_to_check, STUCK_DETECTION_KEYWORDS)
                
                # Broad Search Fallback (Title) - If PID-based fails, look everywhere
                if not stuck_title:
                    all_titles = self.stuck_detector.get_all_window_titles()
                    for title in all_titles:
                        title_lower = title.lower()
                        for kw in STUCK_DETECTION_KEYWORDS:
                            if kw.lower() in title_lower:
                                stuck_title = title
                                logger.info(f"BROAD MATCH: Found stuck window title '{title}' globally")
                                break
                        if stuck_title: break
                
                # Check for stuck state (OCR) - Every 20 seconds (every 10th loop of 2s)
                stuck_ocr = False
                if not stuck_title and loop_count % 10 == 0:
                    # Try PID-based first
                    if self.stuck_detector.check_window_content(pids_to_check, STUCK_DETECTION_OCR_KEYWORDS):
                        stuck_ocr = True
                        logger.warning(f"STUCK DETECTED (UIA): Task '{task_name}' has error text in its windows")
                    
                    # Native OCR Fallback (If UIA fails)
                    if not stuck_ocr:
                         # Get HWNDs for tracked PIDs
                        win_info = self.stuck_detector.get_window_titles_and_pids()
                        tracked_hwnds = [hwnd for title, p, hwnd in win_info if p in pids_to_check]
                        
                        for hwnd in tracked_hwnds:
                            text = self.stuck_detector.check_window_content_ocr(hwnd)
                            if text:
                                text_lower = text.lower()
                                for kw in STUCK_DETECTION_OCR_KEYWORDS:
                                    if kw.lower() in text_lower:
                                        stuck_ocr = True
                                        logger.warning(f"STUCK DETECTED (NATIVE OCR): Found '{kw}' in window text: '{text[:50]}...'")
                                        break
                            if stuck_ocr: break
                    
                    # Fallback to Global OCR
                    if not stuck_ocr:
                         # Use existing UIA global check
                         if self.stuck_detector.check_global_window_content(STUCK_DETECTION_OCR_KEYWORDS):
                             stuck_ocr = True
                             logger.warning(f"STUCK DETECTED (GLOBAL UIA): Found update/error text in a visible window")

                if stuck_title or stuck_ocr:
                    reason = f"window '{stuck_title}'" if stuck_title else "error text (OCR)"
                    logger.warning(f"STUCK DETECTED: Task '{task_name}' is stuck on {reason}")
                    
                    # Kill and Restart Logic
                    # 1. Stop the task
                    self.stop_task(task_id)
                    
                    # 2. Wait a bit
                    time.sleep(5)
                    
                    # 3. Restart (Retry)
                    logger.info(f"Restarting stuck task '{task_name}'...")
                    
                    retry_key = f"retry_{task_id}"
                    retries = getattr(self, retry_key, 0)
                    
                    if retries < 3:
                        setattr(self, retry_key, retries + 1)
                        self.execute_immediately(task)
                    else:
                        logger.error(f"Task '{task_name}' stuck repeatedly. Giving up after 3 retries.")
                        setattr(self, retry_key, 0)
                    
                    return # Exit monitor thread
                
                # Check for confirmation dialogs that need a button click (e.g., "Patching complete")
                # This runs every 4 seconds (every 2nd loop of 2s)
                if loop_count % 2 == 0:
                    # Try PID-based first
                    found_dialog = self.stuck_detector.find_confirmation_dialog(pids_to_check, CONFIRMATION_DIALOG_KEYWORDS)
                    
                    # Fallback to Global search for dialogs
                    if not found_dialog:
                        found_dialog = self.stuck_detector.find_confirmation_dialog([None], CONFIRMATION_DIALOG_KEYWORDS)
                        if found_dialog:
                            logger.info(f"BROAD MATCH: Found confirmation dialog globally for '{task_name}'")

                    if found_dialog:
                        logger.info(f"CONFIRMATION DIALOG: Task '{task_name}' has a dialog waiting for input")
                        
                        # Increment persistent dialog counter
                        dlg_persist_attr = f"dlg_persist_{task_id}"
                        current_persist_count = getattr(self, dlg_persist_attr, 0) + 1
                        setattr(self, dlg_persist_attr, current_persist_count)
                        
                        # Try to auto-click the confirmation button
                        pids_for_click = pids_to_check + [None]
                        success = self.stuck_detector.click_confirmation_button(pids_for_click, CONFIRMATION_BUTTON_LABELS)
                        
                        if success:
                            # Reset persistence counter on success
                            setattr(self, dlg_persist_attr, 0)
                            
                            logger.info(f"AUTO-DISMISSED: Successfully clicked confirmation button for '{task_name}'")
                            
                            # Log to execution logger
                            self.execution_logger.log_event(
                                task_id,
                                task_name,
                                "AUTO_DISMISSED",
                                "Confirmation dialog auto-dismissed (update/patch complete)"
                            )
                            
                            # Update/Restart detection
                            logger.info(f"RESTART DETECTED: Scheduling task '{task_name}' to re-run in 30 seconds (post-update restart)")
                            
                            self.execution_logger.log_event(
                                task_id,
                                task_name,
                                "RESTART_SCHEDULED",
                                "Task will re-run in 30 seconds after update/restart completes"
                            )
                            
                            # Schedule re-run after 30 seconds
                            restart_time = datetime.now() + timedelta(seconds=30)
                            self.scheduler.add_job(
                                func=self._check_and_execute,
                                trigger=DateTrigger(run_date=restart_time),
                                args=[task],
                                name=f"restart_{task_name}_{restart_time.strftime('%H%M%S')}"
                            )
                            
                            # Exit monitor - the new job will have its own monitor
                            return
                        else:
                            # If click failed, check if we've reached the threshold for FORCE RESTART
                            if current_persist_count >= 3:
                                logger.error(f"PERSISTENT DIALOG: Task '{task_name}' has stuck dialog for ~12s. Forcing restart.")
                                setattr(self, dlg_persist_attr, 0) # Reset counter
                                
                                self.execution_logger.log_event(
                                    task_id,
                                    task_name,
                                    "STUCK_RESTART_DLG",
                                    "Persistent un-clickable dialog detected. Forcefully restarting task."
                                )
                                
                                # Use the existing kill-and-restart logic
                                # 1. Stop the task
                                self.stop_task(task_id)
                                
                                # 2. Wait a bit
                                time.sleep(5)
                                
                                # 3. Restart (Retry)
                                logger.info(f"Forcefully restarting stuck task '{task_name}'...")
                                
                                retry_key = f"retry_{task_id}"
                                retries = getattr(self, retry_key, 0)
                                if retries < 3:
                                    setattr(self, retry_key, retries + 1)
                                    self.execute_immediately(task)
                                else:
                                    logger.error(f"Task '{task_name}' stuck repeatedly on dialog. Giving up.")
                                    setattr(self, retry_key, 0)
                                
                                return # Exit monitor thread
                            else:
                                logger.warning(f"Click attempts failed. Dialog persistence: {current_persist_count}/3")
                    else:
                        # Reset counter if dialog disappears
                        dlg_persist_attr = f"dlg_persist_{task_id}"
                        if hasattr(self, dlg_persist_attr) and getattr(self, dlg_persist_attr, 0) > 0:
                             setattr(self, dlg_persist_attr, 0)
                
                time.sleep(2) # Check every 2 seconds (was 5s)
                loop_count += 1
            
            logger.debug(f"Stuck Monitor finished for '{task_name}'")
            self.update_detector_stopped.emit(task_id)

        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()

    def _cleanup_finished_processes(self):
        """
        Check for processes that have finished naturally and clean them up.
        Run periodically to prevent 'active_processes' from growing indefinitely.
        """
        finished_tasks = []
        
        # Check all active processes
        for task_id, process in list(self.active_processes.items()):
            try:
                # poll() returns None if running, exit code if finished
                exit_code = process.poll()
                if exit_code is not None:
                    finished_tasks.append((task_id, exit_code))
            except Exception as e:
                 logger.error(f"Error checking process status for task {task_id}: {e}")
        
        # Clean up finished ones
        for task_id, exit_code in finished_tasks:
            try:
                if task_id in self.active_processes:
                    del self.active_processes[task_id]
                    
                self.task_finished.emit(task_id)
                self.execution_logger.log_event(task_id, "Unknown", "FINISHED", f"Process exited naturally (Code {exit_code})")
                logger.debug(f"Task ID {task_id} finished naturally (Exit Code {exit_code}). Cleaned up.")
            except Exception as e:
                logger.error(f"Error cleaning up task {task_id}: {e}")
            
            logger.debug(f"Stuck Monitor finished for '{task_name}'")
            self.update_detector_stopped.emit(task_id)

        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()
