"""
Sentinel Addon
Main implementation of the Sentinel Addon.
"""

import threading
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal

from addon_interface import IAutolauncherAddon, AddonMetadata
from logger import get_logger
from config import STUCK_DETECTION_KEYWORDS, STUCK_DETECTION_OCR_KEYWORDS, CONFIRMATION_DIALOG_KEYWORDS, CONFIRMATION_BUTTON_LABELS
# TODO: Future Refactor - Move these keywords to per-addon configuration or per-game settings
# instead of global config.py constants to support dynamic game definitions.

from .logic import SentinelLogic
from .indicator import SentinelIndicator

logger = get_logger(__name__)

class SentinelAddon(IAutolauncherAddon):
    """
    Sentinel Addon: Watches for stuck updates/installers and auto-resolves them.
    Refactored from the original legacy StuckDetector.
    """

    def get_metadata(self) -> AddonMetadata:
        return AddonMetadata(
            name="Beacon Sentinel",  # Creative Name
            version="2.0.0",
            author="4Never Company",
            description="Advanced update detection and auto-resolution system.",
            id="c4n-ALSentinelAddon"
        )

    def __init__(self, manager):
        super().__init__(manager)
        self.logic = SentinelLogic()
        self.indicator = SentinelIndicator()
        
        # State tracking
        self.active_monitors: Dict[int, bool] = {} # task_id -> is_running
        self.retry_counts: Dict[int, int] = {} # task_id -> retries
        self.dialog_persistence: Dict[int, int] = {} # task_id -> persistence_count

    def get_indicator_widget(self) -> Optional[QWidget]:
        return self.indicator

    def on_task_start(self, task_data: Dict, process: Any):
        """Called when a task starts. We verify if monitoring is needed."""
        task_id = task_data.get('id')
        task_name = task_data.get('name', 'Unknown')
        
        # Check if we assume monitoring is wanted? 
        # For now, we enable it for all tasks that have a PID (which implies executable)
        if not process or not getattr(process, 'pid', None):
            return

        pid = process.pid
        
        # Start monitoring in a separate thread
        self.active_monitors[task_id] = True
        
        # Show indicator
        self.indicator.set_active(True, task_name)
        
        thread = threading.Thread(
            target=self._monitor_loop,
            args=(task_id, task_name, pid, task_data, process),
            daemon=True,
            name=f"SentinelMonitor-{task_id}"
        )
        thread.start()
        logger.info(f"Sentinel: Monitoring started for '{task_name}' (PID: {pid})")

    def on_task_end(self, task_id: int):
        """Stop monitoring when task ends."""
        if task_id in self.active_monitors:
            self.active_monitors[task_id] = False # Flag loop to stop
            logger.debug(f"Sentinel: Stopping monitor for task ID {task_id}")
            
        # Hide indicator if no more active monitors
        # We need to check if ANY monitor is true
        if not any(self.active_monitors.values()):
            self.indicator.set_active(False)

    def _monitor_loop(self, task_id: int, task_name: str, initial_pid: int, task_data: Dict, process_obj: Any):
        """
        Background monitoring loop.
        Runs for 5 minutes (300s).
        """
        start_time = time.time()
        loop_count = 0
        duration = 300 # 5 minutes
        
        # Initial wait
        time.sleep(2)
        
        tracked_pids = {initial_pid}
        
        while time.time() - start_time < duration:
            # Check stop flag
            if not self.active_monitors.get(task_id, False):
                break
                
            # Verify main process is still alive using the object if possible
            if process_obj.poll() is not None:
                # Process finished naturally
                break

            # --- PID Tracking (Spawned Children) ---
            current_living_pids = []
            new_children = set()
            
            for t_pid in list(tracked_pids):
                try:
                    proc = psutil.Process(t_pid)
                    if proc.is_running():
                        current_living_pids.append(t_pid)
                        try:
                            children = proc.children(recursive=True)
                            for child in children:
                                if child.pid not in tracked_pids:
                                    logger.debug(f"Sentinel: Tracking new child PID {child.pid}")
                                    new_children.add(child.pid)
                        except: pass
                except: pass
            
            if new_children:
                tracked_pids.update(new_children)
                current_living_pids.extend(list(new_children))
            
            if not current_living_pids:
                logger.debug(f"Sentinel: All tracked processes finished for '{task_name}'.")
                break
            
            pids_to_check = current_living_pids
            
            # --- Detection Logic ---
            stuck_reason = None
            
            # 1. Window Titles
            stuck_title = self.logic.is_process_stuck(pids_to_check, STUCK_DETECTION_KEYWORDS)
            if stuck_title:
                stuck_reason = f"Window Title: {stuck_title}"
            
            # 2. OCR (periodic)
            if not stuck_reason and loop_count % 10 == 0:
                if self.logic.check_window_content(pids_to_check, STUCK_DETECTION_OCR_KEYWORDS):
                    stuck_reason = "Window Content (UIA)"
                elif self.logic.check_window_content_ocr(list(tracked_pids)[0]): # Check one window effectively
                     # TODO: Logic check_window_content_ocr implementation above only took HWND, need to iterate
                     # Actually logic.py impl takes HWND. We need internal helper here?
                     # Let's just trust logic.check_window_content for now as primary.
                     pass 

            # --- Action: Stuck Detected -> Restart ---
            if stuck_reason:
                logger.warning(f"Sentinel: Task '{task_name}' STUCK on {stuck_reason}")
                self._handle_stuck_task(task_id, task_name, task_data)
                return # End thread

            # --- Action: Confirmation Dialog -> Click ---
            if loop_count % 2 == 0:
                # TODO: Future Refactor - Abstract this dialog detection. 
                # Currently relies on global CONFIRMATION_DIALOG_KEYWORDS which are tailored for specific games (e.g. WuWa).
                # Should be configurable per task/addon.
                if self.logic.find_confirmation_dialog(pids_to_check, CONFIRMATION_DIALOG_KEYWORDS):
                    logger.info(f"Sentinel: Confirmation dialog found for '{task_name}'")
                    
                    self.dialog_persistence[task_id] = self.dialog_persistence.get(task_id, 0) + 1
                    
                    # Try Click
                    if self.logic.click_confirmation_button(pids_to_check + [None], CONFIRMATION_BUTTON_LABELS):
                        logger.info(f"Sentinel: Successfully clicked button for '{task_name}'")
                        self.dialog_persistence[task_id] = 0
                        
                        # Assuming update/patch complete -> Schedule Restart
                        self._schedule_restart(task_id, task_name, task_data)
                        return
                    else:
                        # Failed to click
                        if self.dialog_persistence[task_id] >= 3:
                             logger.error(f"Sentinel: Persistent unclickable dialog for '{task_name}'. Forcing restart.")
                             self._handle_stuck_task(task_id, task_name, task_data)
                             return
                else:
                    self.dialog_persistence[task_id] = 0

            time.sleep(2)
            loop_count += 1
            
        # Cleanup
        if task_id in self.active_monitors:
            del self.active_monitors[task_id]
        
        # Determine if we should hide indicator
        if not any(self.active_monitors.values()):
            self.indicator.set_active(False)

    def _handle_stuck_task(self, task_id, task_name, task_data):
        """Stop and restart the stuck task."""
        scheduler = self.manager.context.scheduler # Access Scheduler via Context
        
        # 1. Stop
        scheduler.stop_task(task_id)
        
        time.sleep(5)
        
        # 2. Retry
        retries = self.retry_counts.get(task_id, 0)
        if retries < 3:
            self.retry_counts[task_id] = retries + 1
            logger.info(f"Sentinel: Restarting task '{task_name}' (Retry {retries + 1}/3)")
            scheduler.execute_immediately(task_data)
        else:
            logger.error(f"Sentinel: Task '{task_name}' stuck repeatedly. Giving up.")
            self.retry_counts[task_id] = 0

    def _schedule_restart(self, task_id, task_name, task_data):
        """Schedule a restart after a successful update click."""
        scheduler = self.manager.context.scheduler
        from apscheduler.triggers.date import DateTrigger # Need this? Or just us add_job helper
        
        restart_time = datetime.now() + timedelta(seconds=30)
        logger.info(f"Sentinel: Scheduling post-update restart for '{task_name}' at {restart_time}")
        
        # We need a function to call. scheduler._check_and_execute is internal.
        # But scheduler has check_and_execute? 
        # Using execute_immediately with a delay? Scheduler uses APScheduler.
        
        scheduler.scheduler.add_job(
             func=scheduler.execute_immediately, # execute_immediately usually runs ... immediately. 
             # Wait, execute_immediately calls _execute_task.
             # We can schedule _execute_task directly or execute_immediately.
             trigger=DateTrigger(run_date=restart_time),
             args=[task_data],
             name=f"sentinel_restart_{task_id}"
        )
