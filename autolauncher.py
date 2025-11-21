"""
Autolauncher - Main Application Module
A desktop application for scheduling and automatically executing programs.
Features Fluent Design UI, theme switching, and countdown timers.
"""

import sys
from datetime import datetime
from PySide6.QtWidgets import QApplication, QTableWidgetItem, QHeaderView, QSystemTrayIcon, QMenu, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QIcon, QAction
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
from update_manager import UpdateManager
from logger import get_logger
from config import (
    APP_NAME,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    TIMER_UPDATE_INTERVAL
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
    
    def _enforce_theme(self):
        """Periodically enforce the selected theme to prevent resets."""
        # Only re-apply if we are visible to avoid unnecessary work
        if self.isVisible():
            self._apply_saved_theme()
    
    def _init_ui(self):
        """Initialize the user interface."""
        
        # Set window properties
        version = self.update_manager.get_current_version()
        self.setWindowTitle(f"{APP_NAME} (Alpha v{version})")
        self.resize(
            self.settings_manager.get('window_width', DEFAULT_WINDOW_WIDTH),
            self.settings_manager.get('window_height', DEFAULT_WINDOW_HEIGHT)
        )
        
        # Create main interface
        self._create_main_widget()
        
        # Create settings interface
        self.settingsInterface = SettingsInterface(self)
        
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
        
        self.themeButton = PushButton(FluentIcon.CONSTRACT, "Toggle Theme", self)
        self.themeButton.clicked.connect(self._toggle_theme)
        
        # Add buttons to toolbar
        self.toolbarLayout.addWidget(self.addButton)
        self.toolbarLayout.addWidget(self.editButton)
        self.toolbarLayout.addWidget(self.deleteButton)
        self.toolbarLayout.addWidget(self.runNowButton)
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
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Task Name
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Program Path
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Schedule
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Countdown
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        
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
            # Task Name
            self.taskTable.setItem(row, 0, QTableWidgetItem(task.get('name', '')))
            
            # Program Path
            self.taskTable.setItem(row, 1, QTableWidgetItem(task.get('program_path', '')))
            
            # Schedule
            try:
                schedule_time = datetime.fromisoformat(task.get('schedule_time'))
                recurrence = task.get('recurrence', 'Once')
                
                if recurrence == 'Once':
                    schedule_str = schedule_time.strftime('%Y-%m-%d %H:%M')
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
                return "Not Scheduled"
            
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
        
        dialog = TaskDialog(self)
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
            dialog = TaskDialog(self, task_data=task)
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
        self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))  # Use default icon
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
        if event.type() in [QEvent.ThemeChange, QEvent.PaletteChange, QEvent.ActivationChange]:
            self._apply_saved_theme()

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
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # Create and show main window
    window = AutolauncherApp()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
