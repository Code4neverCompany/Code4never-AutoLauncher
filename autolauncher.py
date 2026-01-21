"""
Autolauncher - Main Application Module
A desktop application for scheduling and automatically executing programs.
Features Fluent Design UI, theme switching, and countdown timers.
"""

import sys
import os
import ctypes
from ctypes import wintypes

from datetime import datetime
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QHeaderView, QSystemTrayIcon, QMenu, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QAbstractItemView
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QIcon, QAction

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
    NavigationItemPosition,
    qconfig
)

from task_manager import TaskManager, SettingsManager
from theme_manager import ThemeManager
from task_dialog import TaskDialog
from scheduler import TaskScheduler
from settings_interface import SettingsInterface
from addon_view import AddonView
from about_interface import AboutInterface
from update_manager import UpdateManager
from language_manager import get_text, get_language_manager
from widgets.status_badge import StatusBadge
from widgets.status_badge import StatusBadge
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
    

    def __init__(self, controller):
        """Initialize the Autolauncher application."""
        self.controller = controller
        
        # Alias managers from controller for compatibility
        self.settings_manager = controller.settings_manager
        self.theme_manager = controller.theme_manager
        self.task_manager = controller.task_manager
        self.scheduler = controller.scheduler
        self.update_manager = controller.update_manager
        
        # NOTE: Theme is already applied by MainController at this point
        
        # NOW call FluentWindow.__init__() 
        super().__init__()
        
        # Disable Windows 11 Mica effect for stability
        # Mica can fail and cause washed-out backgrounds - solid colors are more reliable
        self.setMicaEffectEnabled(False)
        
        # Connect to qconfig theme change signal for protection
        self.theme_manager.setup_protection()
        
        # Connect Controller Signals to View Slots
        self._connect_controller_signals()
        
        # Load saved language BEFORE creating UI
        saved_language = self.settings_manager.get('language', 'en')
        lang_manager = get_language_manager()
        lang_manager.set_language(saved_language)
        logger.info(f"Initialized language to: {saved_language}")
        
        # Load scheduled tasks into scheduler
        self._load_scheduled_tasks()
        
        # Connect scheduler signals
        self.scheduler.ask_user_permission.connect(self._handle_task_permission_request)
        self.scheduler.task_started.connect(self._handle_task_started)
        self.scheduler.task_finished.connect(self._handle_task_finished)
        self.scheduler.task_postponed.connect(self._handle_task_postponed)
        self.scheduler.task_finished.connect(self._handle_task_finished)
        self.scheduler.task_postponed.connect(self._handle_task_postponed)
        
        # Setup UI (now with correct theme already applied)
        self._init_ui()
        self._setup_system_tray()
        
        # Reload UI text after creation to ensure correct language
        QTimer.singleShot(100, self.reload_ui_text)
        
        # Setup countdown timer
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_countdowns)
        self.countdown_timer.start(TIMER_UPDATE_INTERVAL)
        
        logger.info("Autolauncher application initialized")
        
        QTimer.singleShot(100, self.controller.setup_auto_update)
        # Show addon startup toast
        QTimer.singleShot(2000, self._show_addon_startup_toast)

    def _connect_controller_signals(self):
        """Connect signals from Controller to View methods."""
        # Task Signals
        self.controller.task_added.connect(self._on_task_added_by_controller)
        self.controller.task_updated.connect(self._on_task_updated_by_controller)
        self.controller.task_deleted.connect(self._on_task_deleted_by_controller)
        
        # Update Signals
        self.controller.update_available.connect(self._handle_update_available)
        self.controller.no_update_available.connect(lambda: logger.info("View: No update available"))
        
        # Scheduler Signals (relayed by controller)
        self.controller.task_started.connect(self._handle_task_started)
        self.controller.task_finished.connect(self._handle_task_finished)
        self.controller.task_postponed.connect(self._handle_task_postponed)
        self.controller.ask_user_permission.connect(self._handle_task_permission_request)
        self.controller.ask_user_permission.connect(self._handle_task_permission_request)

    def _on_task_added_by_controller(self, task):
        """Handle task added signal."""
        self._refresh_task_table()
        
    def _on_task_updated_by_controller(self, task_id, task):
        """Handle task updated signal."""
        self._refresh_task_table()
        
    def _on_task_deleted_by_controller(self, task_id):
        """Handle task deleted signal."""
        self._refresh_task_table()

    
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
            
        # SPAM PREVENTION: Check if we already notified about this version
        if version in self.notified_versions:
            logger.debug(f"Already notified user about version {version}, skipping alert.")
            return

        # Mark as notified immediately
        self.notified_versions.add(version)
            
        # Smart Auto-Update Logic (only in Smart mode)
        frequency = self.settings_manager.get('auto_update_frequency', 'startup')
        if frequency == 'automatic' and self.update_manager.is_executable:
            smart_auto_install = self.settings_manager.get('smart_auto_install', False)
            
            if smart_auto_install:
                # Smart mode: Check task schedule
                next_run = self.scheduler.get_next_run_time()
                should_install = True
                
                if next_run:
                    now = datetime.now(next_run.tzinfo) if next_run.tzinfo else datetime.now()
                    delta = next_run - now
                    
                    if delta.total_seconds() < 1800: 
                        should_install = False
                        logger.info(f"Smart Update: Postponed. Next task in {delta.total_seconds()/60:.1f} mins")
                        
                        # Show notification that update is postponed
                        info_bar = InfoBar.info(
                            title=f"Update Available: v{version}",
                            content=f"Will install after tasks complete. Click to view details.",
                            orient=Qt.Orientation.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=-1,  # Persistent
                            parent=self
                        )
                        view_button = PushButton("View Details")
                        view_button.clicked.connect(lambda: self._navigate_to_about_for_update())
                        info_bar.addWidget(view_button)
                        return
                
                if should_install:
                    logger.info("Smart Update: Safe window detected. Starting automatic update...")
                    InfoBar.success(
                        title="Smart Update",
                        content="Installing update automatically (no conflicting tasks)...",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    self.aboutInterface._start_update_flow()
                    return
            else:
                # Immediate install mode
                logger.info("Auto-Update: Starting immediate update...")
                InfoBar.success(
                    title="Auto-Update",
                    content=f"Installing v{version} automatically...",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                self.aboutInterface._start_update_flow()
                return
        
        # For Python script mode, just show notification and open browser
        # For Python script mode, just show notification AND button to open browser
        if not self.update_manager.is_executable:
            info_bar = InfoBar.info(
                title=f"Update Available: v{version}",
                content="New version available. Click to view on GitHub.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000, # Show for 5 seconds as requested
                parent=self
            )
            
            # Create button to open link
            view_btn = PushButton("View Release")
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Use default webbrowser module directly or via update_manager helper
            view_btn.clicked.connect(lambda: self.update_manager.open_download_page(update_info['url']))
            
            info_bar.addWidget(view_btn)
            return
        
        # For executable mode (Manual/Startup modes), show notification with action to navigate to About page
        zip_asset = update_info.get('exe_asset') or update_info.get('zip_asset')
        if not zip_asset:
            logger.warning("No update package found in release")
            # Still show notification to inform user
            info_bar = InfoBar.info(
                title=f"Update Available: v{version}",
                content="Visit the About page to learn more",
                orient=Qt.Orientation.Horizontal,
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
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000, # Transient notification (5s) to avoid blocking screen
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
                orient=Qt.Orientation.Horizontal,
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
            orient=Qt.Orientation.Horizontal,
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
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def reload_ui_text(self):
        """Reload all UI text with current language."""
        # Window Title
        version = self.update_manager.get_current_version()
        self.setWindowTitle(f"{get_text('main_window.title')} (Beta v{version})")
        
        # Toolbar Buttons
        self.addButton.setText(get_text('main_window.add_task'))
        self.editButton.setText(get_text('main_window.edit_task'))
        self.deleteButton.setText(get_text('main_window.delete_task'))
        self.runNowButton.setText(get_text('main_window.run_now'))
        self.pauseResumeButton.setText(get_text('main_window.pause_resume'))
        self.viewLogButton.setText(get_text('main_window.view_log'))
        self.themeButton.setText(get_text('main_window.toggle_theme'))
        
        # Navigation Items
        if hasattr(self, 'tasksInterface'):
            self.tasksInterface.setText(get_text('main_window.tasks'))
        if hasattr(self, 'aboutItem'):
            self.aboutItem.setText(get_text('main_window.about'))
        if hasattr(self, 'settingsItem'):
            self.settingsItem.setText(get_text('main_window.settings'))

        # Table Headers
        self.columns = [
            get_text('main_window.col_name'),
            get_text('main_window.col_path'),
            get_text('main_window.col_schedule'),
            get_text('main_window.col_countdown'),
            get_text('main_window.col_status')
        ]
        self.taskTable.setHorizontalHeaderLabels(self.columns)
        
        # Refresh table content
        self._refresh_task_table()
        
        # Reload About Interface
        if hasattr(self, 'aboutInterface'):
            self.aboutInterface.reload_ui_text()
        
        logger.debug("Main window UI text reloaded")

    def _init_ui(self):
        """Initialize the user interface."""
        
        # Set window properties
        # Set window properties
        version = self.update_manager.get_current_version()
        self.setWindowTitle(f"{get_text('main_window.title')} (Beta v{version})")
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
        self.settingsInterface.language_changed.connect(self.reload_ui_text)
        
        # Create Addon View
        self.addonInterface = AddonView(self)
        
        # Create about interface
        self.aboutInterface = AboutInterface(self)
        
        self._create_navigation()
        
        logger.debug("UI initialized")
    
    def _create_navigation(self):
        """Create navigation interface with theme toggle."""
        
        # Set object name for the main widget
        self.mainWidget.setObjectName("mainWidget")
        
        # Add navigation items
        # Add navigation items
        self.tasksInterface = self.addSubInterface(
            self.mainWidget,
            FluentIcon.CALENDAR,
            get_text('main_window.tasks')
        )
        
        self.addonItem = self.addSubInterface(
            self.addonInterface,
            FluentIcon.TILES, # or PEOPLE
            "Addons" # TODO: Add to language manager
        )
        
        self.aboutItem = self.addSubInterface(
            self.aboutInterface,
            FluentIcon.INFO,
            get_text('main_window.about'),
            position=NavigationItemPosition.BOTTOM
        )
        
        self.settingsItem = self.addSubInterface(
            self.settingsInterface,
            FluentIcon.SETTING,
            get_text('main_window.settings'),
            position=NavigationItemPosition.BOTTOM
        )
        
        # Populate Addon View after controller is ready
        if hasattr(self, 'controller') and self.controller.addon_manager:
            self.addonInterface.populate_addons(self.controller.addon_manager)
    
    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        self.theme_manager.toggle_theme(self)
    
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
        # Create buttons
        self.addButton = PushButton(FluentIcon.ADD, get_text('main_window.add_task'), self)
        self.addButton.clicked.connect(self._add_task)
        
        self.editButton = PushButton(FluentIcon.EDIT, get_text('main_window.edit_task'), self)
        self.editButton.clicked.connect(self._edit_task)
        
        self.deleteButton = PushButton(FluentIcon.DELETE, get_text('main_window.delete_task'), self)
        self.deleteButton.clicked.connect(self._delete_task)
        
        self.runNowButton = PushButton(FluentIcon.PLAY, get_text('main_window.run_now'), self)
        self.runNowButton.clicked.connect(self._run_now)
        
        self.pauseResumeButton = PushButton(FluentIcon.PAUSE, get_text('main_window.pause_resume'), self)
        self.pauseResumeButton.clicked.connect(self._toggle_task_pause)
        
        self.viewLogButton = PushButton(FluentIcon.HISTORY, get_text('main_window.view_log'), self)
        self.viewLogButton.clicked.connect(self._show_execution_log)
        
        self.themeButton = PushButton(FluentIcon.CONSTRACT, get_text('main_window.toggle_theme'), self)
        self.themeButton.clicked.connect(self._toggle_theme)
        
        # Add buttons to toolbar
        self.toolbarLayout.addWidget(self.addButton)
        self.toolbarLayout.addWidget(self.editButton)
        self.toolbarLayout.addWidget(self.deleteButton)
        self.toolbarLayout.addWidget(self.runNowButton)
        self.toolbarLayout.addWidget(self.pauseResumeButton)
        self.toolbarLayout.addWidget(self.viewLogButton)
        self.toolbarLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.toolbarLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Addon Indicators Container
        self.addonContainer = QWidget()
        self.addonLayout = QHBoxLayout(self.addonContainer)
        self.addonLayout.setContentsMargins(0, 0, 0, 0)
        self.addonLayout.setSpacing(5)
        
        # Load indicators from AddonManager
        indicators = self.controller.addon_manager.get_all_indicators()
        if indicators:
            for widget in indicators:
                self.addonLayout.addWidget(widget)
                widget.hide() # Ensure initially hidden if handled by addon logic
            self.toolbarLayout.addWidget(self.addonContainer)
        
        self.toolbarLayout.addWidget(self.themeButton)
        
        # Create task table
        self.taskTable = TableWidget(self)
        
        # Define columns
        # Define columns
        self.columns = [
            get_text('main_window.col_name'),
            get_text('main_window.col_path'),
            get_text('main_window.col_schedule'),
            get_text('main_window.col_countdown'),
            get_text('main_window.col_status')
        ]
        self.taskTable.setColumnCount(len(self.columns))
        self.taskTable.setHorizontalHeaderLabels(self.columns)
        
        # Configure table properties
        self.taskTable.verticalHeader().setVisible(False)
        self.taskTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.taskTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.taskTable.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Set column resize modes
        header = self.taskTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Set default column widths
        self.taskTable.setColumnWidth(0, 150)  # Task Name
        self.taskTable.setColumnWidth(1, 300)  # Program Path
        self.taskTable.setColumnWidth(2, 200)  # Schedule (with emoji)
        self.taskTable.setColumnWidth(3, 160)  # Countdown (with emoji)
        self.taskTable.setColumnWidth(4, 120)  # Status (centered badge)
        
        header.setStretchLastSection(True)
        
        # Connect double-click to edit task
        self.taskTable.cellDoubleClicked.connect(self._on_task_double_clicked)
        
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
                
                # Emoji mapping for recurrence types
                recurrence_emojis = {
                    'Once': '📅',
                    'Daily': '🔄',
                    'Weekly': '📆',
                    'Monthly': '🗓️'
                }
                emoji = recurrence_emojis.get(recurrence, '📅')
                
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
                    
                    schedule_str = f"{emoji} {schedule_time.strftime(f'{date_fmt} %H:%M')}"
                else:
                    # For recurring tasks, show the pattern and time
                    time_str = schedule_time.strftime('%H:%M')
                    schedule_str = f"{emoji} {recurrence} @ {time_str}"
                    
            except:
                schedule_str = "Invalid"
            self.taskTable.setItem(row, 2, QTableWidgetItem(schedule_str))
            
            # Countdown (will be updated by timer)
            self.taskTable.setItem(row, 3, QTableWidgetItem(self._calculate_countdown(task)))
            
            # Status Badge - Color-coded status widget
            task_id = task.get('id')
            status_badge = StatusBadge()
            
            # Determine status
            # Determine status
            if not task.get('enabled', True):
                status_badge.set_status("Disabled")
            elif task_id in self.scheduler.active_processes:
                status_badge.set_status("Running")
            else:
                # Check for Expired first (for Once tasks that are done)
                expired = False
                try:
                    schedule_time = datetime.fromisoformat(task.get('schedule_time'))
                    recurrence = task.get('recurrence', 'Once')
                    if recurrence == 'Once' and schedule_time <= datetime.now():
                        status_badge.set_status("Expired")
                        expired = True
                except:
                    pass
                
                if not expired:
                    # Check if job is paused in scheduler
                    if self.scheduler.is_job_paused(task_id):
                        status_badge.set_status("Paused")
                    else:
                        # Check if there's a postponed retry scheduled
                        postponed_time = self._get_postponed_time(task_id)
                        if postponed_time:
                            status_badge.set_status("Postponed", f"@ {postponed_time}")
                        else:
                            status_badge.set_status("Enabled")
            
            # Wrap in container for centering
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(status_badge)
            self.taskTable.setCellWidget(row, 4, container)
            
            # Store task ID in row
            self.taskTable.item(row, 0).setData(Qt.ItemDataRole.UserRole, task_id)
        
        logger.debug(f"Refreshed task table with {len(tasks)} tasks")
    
    def _get_postponed_time(self, task_id: int) -> str:
        """Get the next retry time for a postponed task, if any."""
        try:
            for job in self.scheduler.scheduler.get_jobs():
                # Look for retry jobs for this task
                if job.name and f"retry_" in job.name:
                    # Check if job args contain this task
                    if job.args and len(job.args) > 0:
                        task = job.args[0]
                        if task.get('id') == task_id and job.next_run_time:
                            return job.next_run_time.strftime("%H:%M")
        except Exception as e:
            logger.debug(f"Error checking postponed time: {e}")
        return None
    
    def _calculate_countdown(self, task: dict) -> str:
        """
        Calculate countdown string for a task.
        
        Args:
            task: Task dictionary
            
        Returns:
            Formatted countdown string (with [Postponed] prefix if postponed)
        """
        try:
            task_id = task.get('id')
            
            # First check for postponed retry jobs
            postponed_time = self._get_postponed_time(task_id)
            if postponed_time:
                # Calculate countdown to postponed time
                from datetime import datetime as dt
                try:
                    # Parse the HH:MM time from postponed
                    today = dt.now()
                    hour, minute = map(int, postponed_time.split(':'))
                    next_run = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # If time is past, it might be tomorrow
                    if next_run < today:
                        from datetime import timedelta
                        next_run += timedelta(days=1)
                    
                    delta = next_run - today
                    hours, remainder = divmod(delta.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    # Show ⏳ emoji to indicate this is a postponed/retry timer
                    if hours > 0:
                        return f"⏳ {hours}h {minutes}m"
                    else:
                        return f"⏳ {minutes}m {seconds}s"
                except:
                    return f"⏳ @ {postponed_time}"
            
            # Get next run time from scheduler for accuracy (handles recurrence)
            next_run = self.scheduler.get_next_run_time(task_id)
            
            if not next_run:
                # Fallback for 'Once' tasks that might be in the past or not scheduled
                schedule_time = datetime.fromisoformat(task.get('schedule_time'))
                now = datetime.now()
                if schedule_time <= now and task.get('recurrence', 'Once') == 'Once':
                    return f"❌ {get_text('main_window.status_expired')}"
                return f"⏸️ {get_text('main_window.status_paused')}"
            
            # Calculate delta using timezone-naive datetimes if needed
            now = datetime.now(next_run.tzinfo)
            delta = next_run - now
            
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Show ⏱️ emoji for normal scheduled countdown
            if days > 0:
                return f"⏱️ {days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"⏱️ {hours}h {minutes}m {seconds}s"
            else:
                return f"⏱️ {minutes}m {seconds}s"
                
        except Exception as e:
            logger.error(f"Error calculating countdown: {e}")

            return get_text('main_window.status_error')
    
    def _update_countdowns(self):
        """Update countdown timers for all tasks."""
        
        for row in range(self.taskTable.rowCount()):
            task_id = self.taskTable.item(row, 0).data(Qt.ItemDataRole.UserRole)
            task = self.task_manager.get_task(task_id)
            
            if task:
                countdown = self._calculate_countdown(task)
                # Reuse existing item instead of creating new one (prevents style corruption)
                existing_item = self.taskTable.item(row, 3)
                if existing_item:
                    existing_item.setText(countdown)
                else:
                    self.taskTable.setItem(row, 3, QTableWidgetItem(countdown))
    
    def _run_now(self):
        """Execute the selected task immediately."""
        selected_rows = self.taskTable.selectedItems()
        if not selected_rows:
            InfoBar.warning(
                title=get_text('main_window.no_selection'),
                content=get_text('main_window.select_task_run'),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        task_id = self.taskTable.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        task = self.task_manager.get_task(task_id)
        
        if task:
            # Execute via controller
            if self.controller.execute_task_now(task_id):
                # Notification is handled by _handle_task_started signal
                logger.info(f"Manually executed task ID {task_id}")
            else:
                # Show error if execution failed immediately (e.g. invalid path)
                InfoBar.error(
                    title="Execution Failed",
                    content="Could not start the task. Check logs for details.",
                    orient=Qt.Orientation.Horizontal,
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
                name = task_data.get('name', 'Unknown')

                # Add task via controller
                if self.controller.add_task(task_data):
                    InfoBar.success(
                        title="Task Added",
                        content=f"Task '{name}' has been scheduled",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    logger.info(f"Added new task: {name}")
                    # Table refresh handled by task_added signal
                else:
                    InfoBar.error(
                        title="Error",
                        content="Failed to add task",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
            else:
                InfoBar.warning(
                    title=get_text('main_window.invalid_input'),
                    content=get_text('main_window.check_input'),
                    orient=Qt.Orientation.Horizontal,
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
                title=get_text('main_window.no_selection'),
                content=get_text('main_window.select_task_edit'),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        task_id = self.taskTable.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
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
                            title=get_text('main_window.task_updated'),
                            content=get_text('main_window.task_updated_msg', name=updated_task['name']),
                            orient=Qt.Orientation.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=2000,
                            parent=self
                        )
                        logger.info(f"Updated task ID {task_id}")
                else:
                    InfoBar.warning(
                        title=get_text('main_window.invalid_input'),
                        content=get_text('main_window.check_input'),
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
    
    def _on_task_double_clicked(self, row: int, column: int):
        """Handle double-click on task table - opens edit dialog."""
        # Select the row
        self.taskTable.selectRow(row)
        # Call edit task
        self._edit_task()
    
    def _delete_task(self):
        """Delete the selected task."""
        
        selected_rows = self.taskTable.selectedItems()
        if not selected_rows:
            InfoBar.warning(
                title="No Selection",
                content="Please select a task to delete",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        task_id = self.taskTable.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
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
                if self.controller.delete_task(task_id):
                    # Table refresh handled by task_deleted signal
                    
                    InfoBar.success(
                        title="Task Deleted",
                        content=f"Task '{task['name']}' has been deleted",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    logger.info(f"Deleted task ID {task_id}")
    
    def _load_scheduled_tasks(self):
        # Load all enabled tasks into the scheduler and restore postponed tasks
        
        enabled_tasks = self.task_manager.get_enabled_tasks()
        
        for task in enabled_tasks:
            # Check if task has a pending postponed schedule
            postponed_until = task.get('postponed_until')
            
            if postponed_until:
                try:
                    postponed_time = datetime.fromisoformat(postponed_until)
                    
                    if postponed_time > datetime.now():
                        # Still valid - schedule as retry job instead of normal schedule
                        from apscheduler.triggers.date import DateTrigger
                        task_name = task.get('name', 'Unknown')
                        
                        self.scheduler.scheduler.add_job(
                            func=self.scheduler._check_and_execute,
                            trigger=DateTrigger(run_date=postponed_time),
                            args=[task],
                            name=f"retry_{task_name}_{postponed_time.strftime('%H%M')}"
                        )
                        logger.info(f"Restored postponed task '{task_name}' - retry at {postponed_time.strftime('%H:%M')}")
                        continue  # Skip normal scheduling
                    else:
                        # Postponed time has passed - reschedule for soon (5 mins from now)
                        from datetime import timedelta
                        task_name = task.get('name', 'Unknown')
                        task_id = task.get('id', 0)
                        new_time = datetime.now() + timedelta(minutes=5)
                        self.task_manager.set_postponed_until(task_id, new_time.isoformat())
                        self.scheduler.scheduler.add_job(
                            func=self.scheduler._check_and_execute,
                            trigger=DateTrigger(run_date=new_time),
                            args=[task],
                            name=f"retry_{task_name}_{new_time.strftime('%H%M')}"
                        )
                        logger.info(f"Rescheduled expired postpone for task '{task_name}' - retry at {new_time.strftime('%H:%M')}")
                        continue  # Skip normal scheduling
                except Exception as e:
                    logger.warning(f"Error restoring postponed task: {e}")
            
            # Normal scheduling
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
        
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
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
    
    def _handle_task_permission_request(self, task: dict):
        """Handle permission request from scheduler when user is active."""
        dialog = MessageBox(
            get_text('main_window.task_started'),
            f"Task '{task['name']}' is ready to run.\nYou are currently active. Run now or postpone?",
            self
        )
        dialog.yesButton.setText("Run Now")
        dialog.cancelButton.setText("Postpone 10 min")
        
        result = dialog.exec()
        
        if result:  # Yes - Run Now
            self.scheduler.handle_user_response(task, 'Run')
        else:  # Cancel - Postpone
            self.scheduler.handle_user_response(task, 'Postpone')
    
    
    def _handle_task_started(self, task_id: int, task_name: str):
        """Handle task started event."""
        logger.info(f"Task started: {task_name} (ID: {task_id})")
        # Refresh table to show Running status
        self._refresh_task_table()
    
    def _handle_task_finished(self, task_id: int):
        """Handle task finished event."""
        logger.info(f"Task finished: ID {task_id}")
        self._refresh_task_table()
    
    def _handle_task_postponed(self, task_id: int, new_time_str: str):
        """Handle task postponed event."""
        task = self.task_manager.get_task(task_id)
        if task:
            InfoBar.info(
                title="Task Postponed",
                content=f"Task '{task['name']}' postponed to {new_time_str}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        # Refresh table to show Postponed status
        self._refresh_task_table()
    
    
    def changeEvent(self, event):
        """Handle system theme changes and enforce user preference."""
        super().changeEvent(event)
        
        # Check for theme change events or window activation
        # Adding ActivationChange to catch when window wakes up/gains focus
        # Guard against early calls before settings_manager is initialized
        if event.type() in [QEvent.Type.PaletteChange, QEvent.Type.ActivationChange]:
            if hasattr(self, 'settings_manager') and self.settings_manager:
                self.theme_manager.apply_saved_theme()
    
    def _toggle_task_pause(self):
        """Toggle pause/resume for the selected task."""
        selected_rows = self.taskTable.selectedItems()
        if not selected_rows:
            InfoBar.warning(
                title="No Selection",
                content="Please select a task to pause/resume",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        task_id = self.taskTable.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
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
                    orient=Qt.Orientation.Horizontal,
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
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def nativeEvent(self, eventType, message):
        """
        Handle native Windows events.
        Used to detect system power state changes (resume from sleep).
        This ensures wake timers are refreshed after the system wakes up.
        """
        # Windows power broadcast constants
        WM_POWERBROADCAST = 0x0218
        PBT_APMRESUMEAUTOMATIC = 0x0012
        PBT_APMRESUMESUSPEND = 0x0007
        
        try:
            if eventType == b'windows_generic_MSG':
                # Parse the Windows message structure
                msg = wintypes.MSG.from_address(int(message))
                
                if msg.message == WM_POWERBROADCAST:
                    # Check for resume events
                    if msg.wParam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND):
                        logger.info("System resumed from sleep - refreshing wake timer and re-syncing jobs")
                        # Refresh wake timer to ensure next scheduled task can wake the system
                        self.scheduler._update_system_wake_timer()
                        # Re-sync all jobs to capture any missed triggers during the transition
                        self.scheduler.resync_all_jobs()
        except Exception as e:
            logger.debug(f"Error in nativeEvent handler: {e}")
        
        return super().nativeEvent(eventType, message)

    def closeEvent(self, event):
        """Handle window close event (minimize to tray instead of closing)."""
        
        event.ignore()
        self.hide()
        
        # Show tray notification
        self.tray_icon.showMessage(
            APP_NAME,
            "Application minimized to system tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def _show_addon_startup_toast(self):
        """Show toast with enabled addons."""
        try:
            manager = self.controller.addon_manager
            enabled_addons = manager.get_enabled_addons()
            
            if enabled_addons:
                names = [addon.metadata.name for addon in enabled_addons]
                count = len(names)
                
                if count == 1:
                    title = "Addon Loaded"
                    content = f"{names[0]} is active."
                else:
                    title = f"{count} Addons Loaded"
                    content = ", ".join(names)
                
                InfoBar.success(
                    title=title,
                    content=content,
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000,
                    parent=self
                )
        except Exception as e:
            logger.error(f"Failed to show addon toast: {e}")

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

    # Ensure High DPI scaling support
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # ---------------------------------------------------------
    # SINGLE INSTANCE CHECK (Mutex + Window Restore)
    # ---------------------------------------------------------
    from ctypes import wintypes
    import win32gui
    import win32con
    
    MUTEX_NAME = "Global\\AutoLauncher_SingleInstance_Mutex_v6"
    
    # Try to create named mutex
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = kernel32.GetLastError()
    
    # ERROR_ALREADY_EXISTS = 183
    if last_error == 183:
        # App is already running
        logger.info("Another instance is already running. Focusing existing window...")
        
        # Find window by title partial match
        # Since we added version number, we search for prefix
        target_title_prefix = "AutoLauncher v"
        
        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title.startswith(target_title_prefix):
                    # Found it!
                    # Restore if minimized
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    # Bring to front
                    win32gui.SetForegroundWindow(hwnd)
                    return False # Stop enumeration
            return True

        try:
            win32gui.EnumWindows(enum_handler, None)
        except Exception:
            pass # EnumWindows stops by raising exception when we return False (sometimes)
            
        # Exit this instance
        sys.exit(0)
    
    # ---------------------------------------------------------
    
    # Create application
    app = QApplication(sys.argv)
    
    # Initialize Main Controller (Logic/Data)
    # This also initializes settings and applies theme immediately
    from main_controller import MainController
    controller = MainController()
    
    # Create main window (View) and inject controller
    window = AutolauncherApp(controller)
    window.show()
    
    # Start Application Logic
    controller.start()
    controller.setup_auto_update()
    
    # Execute application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
