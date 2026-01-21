"""
Main Controller Module for Autolauncher.
Handles business logic, manager coordination, and bridges the UI (View) with the Data/Logic (Model).
Implementation of the MVC pattern to decouple logic from the View.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QApplication

from task_manager import TaskManager, SettingsManager
from theme_manager import ThemeManager
from scheduler import TaskScheduler
from update_manager import UpdateManager
from language_manager import get_language_manager
from logger import get_logger
from config import TIMER_UPDATE_INTERVAL

from addon_manager import AddonManager

logger = get_logger(__name__)

class MainController(QObject):
    """
    Central controller for the Autolauncher application.
    Manages the lifecycle of sub-managers and handles business logic.
    """
    
    # Signals to update the UI
    search_text_changed = pyqtSignal(str)
    task_added = pyqtSignal(dict)
    task_updated = pyqtSignal(int, dict)
    task_deleted = pyqtSignal(int)
    
    # Scheduler signals relayed to UI
    task_started = pyqtSignal(int, str)
    task_finished = pyqtSignal(int)
    task_postponed = pyqtSignal(int, str)
    ask_user_permission = pyqtSignal(dict)
    update_detector_started = pyqtSignal(int, str)
    update_detector_stopped = pyqtSignal(int)
    
    # Update related signals
    update_available = pyqtSignal(dict)
    no_update_available = pyqtSignal()
    update_check_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # 1. Initialize Settings & Theme (Critical for UI init)
        self.settings_manager = SettingsManager()
        self.theme_manager = ThemeManager(self.settings_manager)
        
        # Apply initial theme immediately so it's ready before Window creation
        self.theme_manager.apply_initial_theme()
        self.theme_manager.setup_protection()
        
        # 2. Initialize Data & Logic Managers
        self.task_manager = TaskManager()
        self.scheduler = TaskScheduler()
        self.update_manager = UpdateManager()
        self.addon_manager = AddonManager(self)  # [NEW] Addon Manager with Context
        self.scheduler.addon_manager = self.addon_manager # Inject manager into scheduler
        
        # 3. Setup Internal State
        self.pending_update_info = None
        self.notified_versions = set()
        
        # 4. Initialize Language
        self._init_language()
        
        # 5. Connect Internal Signals
        self._connect_scheduler_signals()
        
        # 6. Discover Addons
        self.addon_manager.discover_addons()
        
        logger.info("MainController initialized successfully")

    def _init_language(self):
        """Initialize language from settings."""
        saved_language = self.settings_manager.get('language', 'en')
        lang_manager = get_language_manager()
        lang_manager.set_language(saved_language)
        logger.info(f"Initialized language to: {saved_language}")

    def _connect_scheduler_signals(self):
        """Connect scheduler signals to controller signals."""
        self.scheduler.task_started.connect(self.task_started.emit)
        self.scheduler.task_finished.connect(self.task_finished.emit)
        self.scheduler.task_postponed.connect(self.task_postponed.emit)
        self.scheduler.ask_user_permission.connect(self.ask_user_permission.emit)

    def start(self):
        """Start the application logic (load tasks, etc.)."""
        # Load tasks into scheduler
        self._load_scheduled_tasks()
        
        # Notify Addons
        self.addon_manager.notify_app_start()
        
        # Start startup tasks or logic here if needed
        pass

    def _load_scheduled_tasks(self):
        """Load enabled tasks from TaskManager into the Scheduler."""
        logger.info("Loading scheduled tasks into scheduler...")
        self.scheduler.clear_jobs()
        
        tasks = self.task_manager.get_enabled_tasks()
        for task in tasks:
            self.scheduler.add_job(task)
            
        logger.info(f"Loaded {len(tasks)} enabled tasks into scheduler")

    def shutdown(self):
        """Gracefully shutdown the application/controller."""
        logger.info("Shutting down MainController...")
        self.addon_manager.notify_app_shutdown()
        self.scheduler.shutdown()

        
    # --- Task Management Methods ---
    
    def add_task(self, task_data: dict) -> bool:
        """Add a new task."""
        new_task_id = self.task_manager.add_task(task_data)
        
        if new_task_id is not None:
            # Fetch the fully confirmed task from manager
            new_task = self.task_manager.get_task(new_task_id)
            
            if new_task:
                if new_task.get('enabled', True):
                    self.scheduler.add_job(new_task)
                self.task_added.emit(new_task)
                return True
                
        return False

    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        success = self.task_manager.delete_task(task_id)
        if success:
            self.scheduler.remove_job(task_id)
            self.task_deleted.emit(task_id)
        return success
        
    def execute_task_now(self, task_id: int) -> bool:
        """Force execute a task immediately."""
        task = self.task_manager.get_task(task_id)
        if task:
            return self.scheduler.execute_immediately(task)
        return False

    # --- Update Logic Methods ---
    
    def check_for_updates(self, silent=True):
        """Check for updates."""
        if silent:
            update_info, error = self.update_manager.check_for_updates_silent()
            if error:
                self.update_check_error.emit(error)
                return
            
            if update_info:
                version = update_info['version']
                
                # Check spam prevention
                if version in self.notified_versions:
                    logger.debug(f"Skipping duplicate update alert for {version}")
                    return
                
                self.notified_versions.add(version)
                self.update_available.emit(update_info)
            else:
                self.no_update_available.emit()
        else:
            # Interactive check (not implemented yet for controller, usually direct return)
            pass

    def setup_auto_update(self):
        """Setup automatic update checking based on user settings."""
        frequency = self.settings_manager.get('auto_update_frequency', 'startup')
        
        if frequency == 'manual':
            logger.info("Controller: Auto-update checks are disabled (manual mode)")
            return
            
        # Setup initial check on startup
        if frequency in ['startup', 'automatic']:
            self.initial_update_timer = QTimer(self)
            self.initial_update_timer.setSingleShot(True)
            self.initial_update_timer.timeout.connect(self._perform_startup_update_check)
            self.initial_update_timer.start(10000)  # 10 seconds after startup
            logger.info("Controller: Scheduled startup update check in 10 seconds")
        
        # Setup periodic check timer
        if frequency == 'automatic':
            self.periodic_update_timer = QTimer(self)
            self.periodic_update_timer.timeout.connect(self._perform_periodic_update_check)
            self.periodic_update_timer.start(120000)  # 2 minutes
            logger.info("Controller: Enabled automatic update checking every 2 minutes")

    def _perform_startup_update_check(self):
        """Perform update check on startup."""
        if self.update_manager.should_check_for_updates():
            logger.info("Controller: Performing startup update check...")
            self.check_for_updates(silent=True)
            
    def _perform_periodic_update_check(self):
        """Perform periodic update check."""
        logger.info("Controller: Performing periodic update check...")
        self.check_for_updates(silent=True)
