"""
Autolauncher - Main Application Module
A desktop application for scheduling and automatically executing programs.
Features Fluent Design UI, theme switching, and countdown timers.
"""

import sys
import os

from datetime import datetime
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QHeaderView, QSystemTrayIcon, QMenu, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QAction
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QIcon

# Ensure QApplication exists before importing qfluentwidgets
# This prevents "Must construct a QApplication before a QWidget" error
if not QApplication.instance():
    # Create a temporary QApplication for imports
    _temp_app = QApplication(sys.argv)

from qfluentwidgets import (
    FluentWindow,
    TableWidget,
    PushButton,
    setTheme,
    Theme,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    Action,
    TransparentToolButton,
    NavigationItemPosition
)

from task_manager import TaskManager, SettingsManager
from task_dialog import TaskDialog
from scheduler import TaskScheduler
from settings_interface import SettingsInterface
from about_interface import AboutInterface
from update_manager import UpdateManager
from logger import get_logger
from config import (
    APP_NAME,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    TIMER_UPDATE_INTERVAL,
    WINDOW_ICON_PATH,
    TRAY_ICON_PATH
)

logger = get_logger(__name__)


class AutolauncherApp(FluentWindow):
    """
    Main application window with Fluent Design theme.
    Displays scheduled tasks with countdown timers and provides task management.
    """
    
    def __init__(self):
        """Initialize the Autolauncher application."""
        super().__init__()
        
        # Initialize managers
        self.task_manager = TaskManager()
        self.settings_manager = SettingsManager()
        self.scheduler = TaskScheduler()
        self.update_manager = UpdateManager()
        
        # Load scheduled tasks into scheduler
        self._load_scheduled_tasks()
        
        # Setup UI
        self._init_ui()
        self._setup_system_tray()
        
        # Setup countdown timer
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_countdowns)
        self.countdown_timer.start(TIMER_UPDATE_INTERVAL)
        
        # Apply saved theme
        self._apply_saved_theme()
        
        # Setup theme enforcement timer (fix for "insane white" bug)
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self._enforce_theme)
        self.theme_timer.start(3000) # Check every 3 seconds
        
        logger.info("Autolauncher application initialized")
        
        # Setup auto-update after a short delay to ensure UI is fully ready
        QTimer.singleShot(100, self._setup_auto_update)
    
    def _enforce_theme(self):
        """Periodically enforce the selected theme to prevent resets."""
        # Only re-apply if we are visible to avoid unnecessary work
        if self.isVisible():
            self._apply_saved_theme()
    
    def _setup_auto_update(self):
        """Setup automatic update checking based on user settings."""
        frequency = self.settings_manager.get('auto_update_frequency', 'startup')
        
        if frequency == 'manual':
            logger.info("Auto-update checks are disabled (manual mode)")
            return
        
        # Store pending update info
        self.pending_update_info = None
        self.pending_update_path = None
        
        # Setup initial check on startup (for startup and automatic modes)
        if frequency in ['startup', 'automatic']:
            self.initial_update_timer = QTimer(self)
            self.initial_update_timer.setSingleShot(True)
            self.initial_update_timer.timeout.connect(self._perform_startup_update_check)
            self.initial_update_timer.start(10000)  # 10 seconds after startup
            logger.info("Scheduled startup update check in 10 seconds")
        
        # Setup periodic check timer for automatic mode only
        if frequency == 'automatic':
            self.periodic_update_timer = QTimer(self)
            self.periodic_update_timer.timeout.connect(self._perform_periodic_update_check)
            # Check every 2 minutes with ETag efficiency
            self.periodic_update_timer.start(120000)  # 2 minutes in milliseconds
            logger.info("Enabled automatic update checking every 2 minutes (ETag-based)")
    
    def _perform_startup_update_check(self):
        """Perform update check on startup."""
        if self.update_manager.should_check_for_updates():
            logger.info("Performing startup update check...")
            self._perform_update_check()
    
    def _perform_periodic_update_check(self):
        """Perform periodic update check (always checks, ignores frequency restrictions)."""
        logger.info("Performing periodic update check...")
        self._perform_update_check()
    
    def _perform_update_check(self):
        """Execute background update check."""
        update_info, error = self.update_manager.check_for_updates_silent()
        
        if error:
            # Silent failure for background checks
            self.update_manager.save_last_check_time("error", None)
            logger.debug(f"Update check failed: {error}")
            return
        
        if update_info:
            logger.info(f"Update available: {update_info['version']}")
            self.update_manager.save_last_check_time("update_available", update_info['version'])
            self._handle_update_available(update_info)
        else:
            logger.debug("No updates available")
            self.update_manager.save_last_check_time("no_update", None)
    
    def _handle_update_available(self, update_info: dict):
        """Handle when an update is available."""
        version = update_info['version']
        
        # Update the About interface dashboard
        if hasattr(self, 'aboutInterface') and hasattr(self.aboutInterface, 'dashboard'):
            self.aboutInterface.dashboard.show_update_available(update_info)
            
        # Smart Auto-Update Logic
        frequency = self.settings_manager.get('auto_update_frequency', 'startup')
        if frequency == 'automatic' and self.update_manager.is_executable:
            next_run = self.scheduler.get_next_run_time()
            should_install = True
            
            if next_run:
                now = datetime.now(next_run.tzinfo) if next_run.tzinfo else datetime.now()
                delta = next_run - now
                
                if delta.total_seconds() < 1800: 
                    should_install = False
                    logger.info(f"Smart Update: Postponed. Next task in {delta.total_seconds()/60:.1f} mins")
            
            if should_install:
                logger.info("Smart Update: Safe window detected. Starting automatic update...")
                InfoBar.success(
                    title="Smart Update",
                    content="Installing update automatically (no conflicting tasks)...",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                self.aboutInterface._start_update_flow()
                return
        
        # For Python script mode, just show notification and open browser
        if not self.update_manager.is_executable:
            InfoBar.info(
                title=f"Update Available: v{version}",
                content="Opening release page in browser...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            self.update_manager.open_download_page(update_info['url'])
            return
        
        # For executable mode, show notification with action to navigate to About page
        exe_asset = update_info.get('exe_asset')
        if not exe_asset:
            logger.warning("No .exe asset found in release")
            # Still show notification to inform user
            info_bar = InfoBar.info(
                title=f"Update Available: v{version}",
                content="Visit the About page to learn more",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=-1,  # Persistent
                parent=self
            )
            # Add action button to navigate to About page
            info_bar.addWidget(PushButton("View Details"))
            info_bar.widget.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.aboutInterface))
            return
        
        # Show prominent notification with action to view in About page
        info_bar = InfoBar.success(
            title=f"Update Available: v{version}",
            content="A new version is ready. Click 'View Details' to update.",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,  # Persistent until clicked
            parent=self
        )
        
        # Add action button to navigate to About page
        view_button = PushButton("View Details")
        view_button.clicked.connect(lambda: self._navigate_to_about_for_update())
        info_bar.addWidget(view_button)
        
        logger.info(f"Showed update notification for v{version}")
    
    def _navigate_to_about_for_update(self):
        """Navigate to the About page (helper for update notifications)."""
        self.stackedWidget.setCurrentWidget(self.aboutInterface)
        logger.debug("Navigated to About page for update")

    
    def _handle_download_complete(self, version: str):
        """Handle when update download completes."""
        logger.info("Update download completed")
        
        # Check if tasks are running
        if self.scheduler.has_running_tasks():
            # Defer installation
            logger.info("Tasks are running, deferring installation...")
            InfoBar.warning(
                title="Update Downloaded",
                content="Will install when tasks complete. Close this to cancel.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=-1,  # Persist until closed
                parent=self
            )
            
            # Setup monitor to check when tasks complete
            self.restart_check_timer = QTimer(self)
            self.restart_check_timer.timeout.connect(self._check_and_install_update)
            self.restart_check_timer.start(30000)  # Check every 30 seconds
        else:
            # No tasks running, install immediately with countdown
            self._install_update_with_countdown(version)
    
    def _check_and_install_update(self):
        """Check if tasks completed and install update."""
        if not self.scheduler.has_running_tasks():
            logger.info("Tasks completed, proceeding with update installation")
            self.restart_check_timer.stop()
            self._install_update_with_countdown(self.pending_update_info['version'])
    
    def _install_update_with_countdown(self, version: str):
        """Install update after showing countdown."""
        # Show countdown notification
        InfoBar.success(
            title="Installing Update",
            content=f"Restarting in 5 seconds to install v{version}...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        
        # Schedule installation after 5 seconds
        QTimer.singleShot(5000, self._install_and_restart)
    
    def _install_and_restart(self):
        """Install update and restart application."""
        if not self.pending_update_path:
            logger.error("No pending update path found")
            return
        
        logger.info("Installing update and restarting...")
        
        # Shutdown scheduler
        self.scheduler.shutdown()
        
        # Install and restart
        if self.update_manager.install_update_and_restart(self.pending_update_path):
            # Exit application (batch script will handle restart)
            QApplication.quit()
        else:
            InfoBar.error(
                title="Installation Failed",
                content="Could not install update. Please try manual installation.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def _init_ui(self):
        """Initialize the user interface."""
        
        # Set window properties
        version = self.update_manager.get_current_version()
        self.setWindowTitle(f"{APP_NAME} (Alpha v{version})")
        self.resize(
            self.settings_manager.get('window_width', DEFAULT_WINDOW_WIDTH),
            self.settings_manager.get('window_height', DEFAULT_WINDOW_HEIGHT)
        )
        
        # Set window icon
        try:
            if WINDOW_ICON_PATH.exists():
                self.setWindowIcon(QIcon(str(WINDOW_ICON_PATH)))
                logger.debug(f"Window icon set from {WINDOW_ICON_PATH}")
        except Exception as e:
            logger.warning(f"Failed to load window icon: {e}")
        
        # Create main interface
        self._create_main_widget()
        
        # Create settings interface
        self.settingsInterface = SettingsInterface(self.settings_manager, self)
        self.settingsInterface.date_format_changed.connect(self._refresh_task_table)
        
        # Create about interface
        self.aboutInterface = AboutInterface(self)
        
        self._create_navigation()
        
        logger.debug("UI initialized")
    
    def _create_navigation(self):
        """Create navigation interface with theme toggle."""
        
        # Set object name for the main widget
        self.mainWidget.setObjectName("mainWidget")
        
        # Add navigation items
        self.addSubInterface(
            self.mainWidget,
            FluentIcon.CALENDAR,
            "Tasks"
        )
        
        self.addSubInterface(
            self.aboutInterface,
            FluentIcon.INFO,
            "About",
            position=NavigationItemPosition.BOTTOM
        )
        
        self.addSubInterface(
            self.settingsInterface,
            FluentIcon.SETTING,
            "Settings",
            position=NavigationItemPosition.BOTTOM
        )
    
    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        current_theme = self.settings_manager.get('theme', 'Light')
        
        if current_theme == 'Light':
            new_theme = 'Dark'
            setTheme(Theme.DARK)
        else:
            new_theme = 'Light'
            setTheme(Theme.LIGHT)
        
        self.settings_manager.set('theme', new_theme)
        logger.info(f"Theme changed to {new_theme}")
        
        # Show notification
        InfoBar.success(
            title="Theme Changed",
            content=f"Switched to {new_theme} theme",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def _apply_saved_theme(self):
        """Apply the saved theme preference."""
        saved_theme = self.settings_manager.get('theme', 'Light')
        
        # Force re-application of theme
        if saved_theme == 'Dark':
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
            
        # Force repaint to ensure colors are correct
        self.repaint()
        
        logger.debug(f"Applied saved theme: {saved_theme}")
    
    def _create_main_widget(self):
        """Create the main widget with toolbar and task table."""
        
        # Create main container widget
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(10)
        
        # Create toolbar with buttons
        self.toolbar = QWidget()
        self.toolbarLayout = QHBoxLayout(self.toolbar)
        self.toolbarLayout.setContentsMargins(0, 0, 0, 0)
        self.toolbarLayout.setSpacing(10)
        
        
        # Create buttons
        self.addButton = PushButton(FluentIcon.ADD, "Add Task", self)
        self.addButton.clicked.connect(self._add_task)
        
        self.editButton = PushButton(FluentIcon.EDIT, "Edit Task", self)
        self.editButton.clicked.connect(self._edit_task)
        
        self.deleteButton = PushButton(FluentIcon.DELETE, "Delete Task", self)
        self.deleteButton.clicked.connect(self._delete_task)
        
        self.runNowButton = PushButton(FluentIcon.PLAY, "Run Now", self)
        self.runNowButton.clicked.connect(self._run_now)
        
        self.pauseResumeButton = PushButton(FluentIcon.PAUSE, "Pause/Resume", self)
        self.pauseResumeButton.clicked.connect(self._toggle_task_pause)
        
        self.viewLogButton = PushButton(FluentIcon.HISTORY, "View Log", self)
        self.viewLogButton.clicked.connect(self._show_execution_log)
        
        self.themeButton = PushButton(FluentIcon.CONSTRACT, "Toggle Theme", self)
        self.themeButton.clicked.connect(self._toggle_theme)
        
        # Add buttons to toolbar
        self.toolbarLayout.addWidget(self.addButton)
        self.toolbarLayout.addWidget(self.editButton)
        self.toolbarLayout.addWidget(self.deleteButton)
        self.toolbarLayout.addWidget(self.runNowButton)
        self.toolbarLayout.addWidget(self.pauseResumeButton)
        self.toolbarLayout.addWidget(self.viewLogButton)
        self.toolbarLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.toolbarLayout.addWidget(self.themeButton)
        
        # Create task table
        self.taskTable = TableWidget(self)
        
        # Define columns
        self.columns = ["Task Name", "Program Path", "Schedule", "Countdown", "Status"]
        self.taskTable.setColumnCount(len(self.columns))
        self.taskTable.setHorizontalHeaderLabels(self.columns)
        
        # Configure table properties
        self.taskTable.verticalHeader().setVisible(False)
        self.taskTable.setEditTriggers(TableWidget.NoEditTriggers)
        self.taskTable.setSelectionBehavior(TableWidget.SelectRows)
        self.taskTable.setSelectionMode(TableWidget.SingleSelection)
        
        # Set column resize modes
        header = self.taskTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Set default column widths
        self.taskTable.setColumnWidth(0, 150)  # Task Name
        self.taskTable.setColumnWidth(1, 300)  # Program Path
        self.taskTable.setColumnWidth(2, 180)  # Schedule
        self.taskTable.setColumnWidth(3, 120)  # Countdown
        self.taskTable.setColumnWidth(4, 100)  # Status
        
        header.setStretchLastSection(True)
        
        # Add toolbar and table to main layout
        self.mainLayout.addWidget(self.toolbar)
        self.mainLayout.addWidget(self.taskTable)
        
        # Load tasks into table
        self._refresh_task_table()
    
    def _refresh_task_table(self):
        """Refresh the task table with current data."""
        
        tasks = self.task_manager.get_all_tasks()
        self.taskTable.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # Task Name with Icon
            task_name = task.get('name', '')
            name_item = QTableWidgetItem(task_name)
            
            # Try to load and set icon
            try:
                from icon_extractor import extract_icon_from_path
                program_path = task.get('program_path', '')
                icon_path = extract_icon_from_path(program_path)
                if icon_path and os.path.exists(icon_path):
                    name_item.setIcon(QIcon(icon_path))
            except Exception as e:
                logger.debug(f"Could not load icon for task: {e}")
            
            self.taskTable.setItem(row, 0, name_item)
            
            # Program Path
            self.taskTable.setItem(row, 1, QTableWidgetItem(task.get('program_path', '')))
            
            # Schedule
            try:
                schedule_time = datetime.fromisoformat(task.get('schedule_time'))
                recurrence = task.get('recurrence', 'Once')
                
                if recurrence == 'Once':
                    # Get date format from settings
                    date_fmt_setting = self.settings_manager.get('date_format', 'YYYY-MM-DD')
                    
                    # Map setting to strftime format
                    fmt_map = {
                        'YYYY-MM-DD': '%Y-%m-%d',
                        'DD.MM.YYYY': '%d.%m.%Y',
                        'MM/DD/YYYY': '%m/%d/%Y',
                        'DD-MM-YYYY': '%d-%m-%Y'
                    }
                    date_fmt = fmt_map.get(date_fmt_setting, '%Y-%m-%d')
                    
                    schedule_str = schedule_time.strftime(f'{date_fmt} %H:%M')
                else:
                    # For recurring tasks, show the pattern and time
                    time_str = schedule_time.strftime('%H:%M')
                    schedule_str = f"{recurrence} at {time_str}"
                    
            except:
                schedule_str = "Invalid"
            self.taskTable.setItem(row, 2, QTableWidgetItem(schedule_str))
            
            # Countdown (will be updated by timer)
            self.taskTable.setItem(row, 3, QTableWidgetItem(self._calculate_countdown(task)))
            
            # Status
            status = "Enabled" if task.get('enabled', True) else "Disabled"
            self.taskTable.setItem(row, 4, QTableWidgetItem(status))
            
            # Store task ID in row
            self.taskTable.item(row, 0).setData(Qt.UserRole, task.get('id'))
        
        logger.debug(f"Refreshed task table with {len(tasks)} tasks")
    
    def _calculate_countdown(self, task: dict) -> str:
        """
        Calculate countdown string for a task.
        
        Args:
            task: Task dictionary
            
        Returns:
            Formatted countdown string
        """
        try:
            # Get next run time from scheduler for accuracy (handles recurrence)
            next_run = self.scheduler.get_next_run_time(task['id'])
            
            if not next_run:
                # Fallback for 'Once' tasks that might be in the past or not scheduled
                schedule_time = datetime.fromisoformat(task.get('schedule_time'))
                now = datetime.now()
                if schedule_time <= now and task.get('recurrence', 'Once') == 'Once':
                    return "Expired"
                return "Paused"
            
            # Calculate delta using timezone-naive datetimes if needed
            now = datetime.now(next_run.tzinfo)
            delta = next_run - now
            
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            else:
                return f"{minutes}m {seconds}s"
                
        except Exception as e:
            logger.error(f"Error calculating countdown: {e}")
            return "Error"
    
    def _update_countdowns(self):
        """Update countdown timers for all tasks."""
        
        for row in range(self.taskTable.rowCount()):
            task_id = self.taskTable.item(row, 0).data(Qt.UserRole)
            task = self.task_manager.get_task(task_id)
            
            if task:
                countdown = self._calculate_countdown(task)
                self.taskTable.setItem(row, 3, QTableWidgetItem(countdown))
    
    def _run_now(self):
        """Execute the selected task immediately."""
        selected_rows = self.taskTable.selectedItems()
        if not selected_rows:
            InfoBar.warning(
                title="No Selection",
                content="Please select a task to run",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        task_id = self.taskTable.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        task = self.task_manager.get_task(task_id)
        
        if task:
            if self.scheduler.execute_immediately(task):
                InfoBar.success(
                    title="Task Started",
                    content=f"Executing '{task['name']}' now...",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="Error",
                    content="Failed to start task",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _add_task(self):
        """Show dialog to add a new task."""
        
        dialog = TaskDialog(self, settings_manager=self.settings_manager)
        result = dialog.exec()
        
        # Reactivate main window to fix contrast/appearance issue
        self.raise_()
        self.activateWindow()
        self.repaint()
        
        if result:
            if dialog.validate_input():
                task_data = dialog.get_task_data()
                
                if self.task_manager.add_task(task_data):
                    self.scheduler.add_job(task_data)
                    self._refresh_task_table()
                    
                    InfoBar.success(
                        title="Task Added",
                        content=f"Task '{task_data['name']}' has been scheduled",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    logger.info(f"Added task: {task_data['name']}")
                else:
                    InfoBar.error(
                        title="Error",
                        content="Failed to save task",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
            else:
                InfoBar.warning(
                    title="Invalid Input",
                    content="Please check your input and try again",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def _edit_task(self):
        """Edit the selected task."""
        
        selected_rows = self.taskTable.selectedItems()
        if not selected_rows:
            InfoBar.warning(
                title="No Selection",
                content="Please select a task to edit",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        task_id = self.taskTable.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        task = self.task_manager.get_task(task_id)
        
        if task:
            dialog = TaskDialog(self, task_data=task, settings_manager=self.settings_manager)
            result = dialog.exec()
            
            # Reactivate main window to fix contrast/appearance issue
            self.raise_()
            self.activateWindow()
            self.repaint()
            
            if result:
                if dialog.validate_input():
                    updated_task = dialog.get_task_data()
                    
                    if self.task_manager.update_task(task_id, updated_task):
                        self.scheduler.update_job(updated_task)
                        self._refresh_task_table()
                        
                        InfoBar.success(
                            title="Task Updated",
                            content=f"Task '{updated_task['name']}' has been updated",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=2000,
                            parent=self
                        )
                        logger.info(f"Updated task ID {task_id}")
                else:
                    InfoBar.warning(
                        title="Invalid Input",
                        content="Please check your input and try again",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
    
    def _delete_task(self):
        """Delete the selected task."""
        
        selected_rows = self.taskTable.selectedItems()
        if not selected_rows:
            InfoBar.warning(
                title="No Selection",
                content="Please select a task to delete",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        task_id = self.taskTable.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        task = self.task_manager.get_task(task_id)
        
        if task:
            # Confirmation dialog
            w = MessageBox(
                "Confirm Delete",
                f"Are you sure you want to delete task '{task['name']}'?",
                self
            )
            result = w.exec()
            
            # Reactivate main window to fix contrast/appearance issue
            self.raise_()
            self.activateWindow()
            self.repaint()
            
            if result:
                if self.task_manager.delete_task(task_id):
                    self.scheduler.remove_job(task_id)
                    self._refresh_task_table()
                    
                    InfoBar.success(
                        title="Task Deleted",
                        content=f"Task '{task['name']}' has been deleted",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    logger.info(f"Deleted task ID {task_id}")
    
    def _load_scheduled_tasks(self):
        """Load all enabled tasks into the scheduler."""
        
        enabled_tasks = self.task_manager.get_enabled_tasks()
        
        for task in enabled_tasks:
            self.scheduler.add_job(task)
        
        logger.info(f"Loaded {len(enabled_tasks)} enabled tasks into scheduler")
    
    def _setup_system_tray(self):
        """Setup system tray icon and menu."""
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set custom icon with fallback
        try:
            if TRAY_ICON_PATH.exists():
                self.tray_icon.setIcon(QIcon(str(TRAY_ICON_PATH)))
                logger.debug(f"Tray icon set from {TRAY_ICON_PATH}")
            else:
                self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))
                logger.debug("Using fallback tray icon")
        except Exception as e:
            logger.warning(f"Failed to load tray icon: {e}")
            self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))
        
        self.tray_icon.setToolTip(APP_NAME)
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_icon_activated)
        
        # Show tray icon
        self.tray_icon.show()
        
        logger.debug("System tray icon initialized")
    
    def _tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def _quit_application(self):
        """Quit the application gracefully."""
        
        logger.info("Shutting down application")
        
        # Save window size
        self.settings_manager.set('window_width', self.width())
        self.settings_manager.set('window_height', self.height())
        
        # Shutdown scheduler
        self.scheduler.shutdown()
        
        # Quit
        QApplication.quit()
    
    def changeEvent(self, event):
        """Handle system theme changes and enforce user preference."""
        super().changeEvent(event)
        
        # Check for theme change events or window activation
        # Adding ActivationChange to catch when window wakes up/gains focus
        if event.type() in [QEvent.PaletteChange, QEvent.ActivationChange]:
            self._apply_saved_theme()
    
    def _toggle_task_pause(self):
        """Toggle pause/resume for the selected task."""
        selected_rows = self.taskTable.selectedItems()
        if not selected_rows:
            InfoBar.warning(
                title="No Selection",
                content="Please select a task to pause/resume",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        task_id = self.taskTable.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        task = self.task_manager.get_task(task_id)
        
        if task:
            new_enabled = not task.get('enabled', True)
            task['enabled'] = new_enabled
            
            if self.task_manager.update_task(task_id, task):
                if new_enabled:
                    self.scheduler.add_job(task)
                    status_msg = "Resumed"
                else:
                    self.scheduler.remove_job(task_id)
                    status_msg = "Paused"
                
                self._refresh_task_table()
                
                InfoBar.success(
                    title=f"Task {status_msg}",
                    content=f"Task '{task['name']}' has been {status_msg.lower()}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                logger.info(f"{status_msg} task ID {task_id}")
    
    def _show_execution_log(self):
        """Show the execution log dialog."""
        try:
            from log_dialog import LogDialog
            dialog = LogDialog(self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to open log dialog: {e}")
            InfoBar.error(
                title="Error",
                content="Could not open execution log",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def closeEvent(self, event):
        """Handle window close event (minimize to tray instead of closing)."""
        
        event.ignore()
        self.hide()
        
        # Show tray notification
        self.tray_icon.showMessage(
            APP_NAME,
            "Application minimized to system tray",
            QSystemTrayIcon.Information,
            2000
        )


def main():
    """Main entry point for the application."""
    
    # Windows-specific: Set App User Model ID
    # This ensures Windows shows our custom icon and name in taskbar/Task Manager
    # instead of grouping with Python
    try:
        import ctypes
        myappid = 'code4never.autolauncher.desktop.1.0'  # Unique app ID
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        logger.debug("Windows App User Model ID set")
    except Exception as e:
        logger.warning(f"Failed to set App User Model ID: {e}")
    
    # Create and show main window
    window = AutolauncherApp()
    window.show()
    
    # Run event loop
    app = QApplication.instance()
    sys.exit(app.exec_())  # PyQt5 uses exec_()


if __name__ == "__main__":
    main()
