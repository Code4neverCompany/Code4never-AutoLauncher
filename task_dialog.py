"""
Task Dialog Module for Autolauncher.
Provides a modern Fluent Design dialog for adding and editing scheduled tasks.
"""

from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import Qt, QDate, QTime, QPoint, QTimer
from PyQt6.QtWidgets import QFileDialog
from qfluentwidgets import (
    MessageBoxBase,
    SubtitleLabel,
    LineEdit,
    PushButton,
    CalendarPicker,
    TimePicker,
    AMTimePicker,
    BodyLabel,
    ComboBox,
    CheckBox
)
from task_manager import SettingsManager
from task_manager import SettingsManager
from logger import get_logger
from language_manager import get_text

logger = get_logger(__name__)


class TaskDialog(MessageBoxBase):
    """
    Dialog for creating and editing tasks with Fluent Design widgets.
    Supports dragging and mouse wheel time adjustment.
    """
    
    def __init__(self, parent=None, task_data=None, settings_manager=None):
        """
        Initialize the task dialog.
        
        Args:
            parent: Parent widget
            task_data: Optional dictionary with existing task data for editing
            settings_manager: SettingsManager instance for date format preferences
        """
        super().__init__(parent)
        self.task_data = task_data
        self.is_edit_mode = task_data is not None
        self.settings_manager = settings_manager if settings_manager else SettingsManager()
        
        # Variables for window dragging
        self.dragging = False
        self.drag_position = None
        
        # Set dialog title
        title = get_text('dialog.edit_title') if self.is_edit_mode else get_text('dialog.add_title')
        self.titleLabel = SubtitleLabel(title, self)
        
        # Initialize UI components
        self._init_ui()
        
        # Pre-fill data if editing
        if self.is_edit_mode:
            self._load_task_data()
        
        # Set widget properties
        self.widget.setMinimumWidth(500)
        
        # Enable mouse tracking for dragging
        self.titleLabel.setMouseTracking(True)
        self.titleLabel.setCursor(Qt.CursorShape.OpenHandCursor)
        
        logger.debug(f"TaskDialog initialized in {'edit' if self.is_edit_mode else 'add'} mode")
    
    def _init_ui(self):
        """Initialize the user interface components."""
        
        # Task Name
        self.nameLabel = BodyLabel(get_text('dialog.name_label'), self)
        self.nameInput = LineEdit(self)
        self.nameInput.setPlaceholderText(get_text('dialog.name_placeholder'))
        self.nameInput.setClearButtonEnabled(True)
        
        # Program Path
        self.pathLabel = BodyLabel(get_text('dialog.path_label'), self)
        self.pathInput = LineEdit(self)
        self.pathInput.setPlaceholderText(get_text('dialog.path_placeholder'))
        self.pathInput.setClearButtonEnabled(True)
        
        # Browse Button
        # Browse Button
        self.browseButton = PushButton(get_text('dialog.browse'), self)
        self.browseButton.clicked.connect(self._browse_program)
        
        # Recurrence
        self.recurrenceLabel = BodyLabel(get_text('dialog.recurrence_label'), self)
        self.recurrenceCombo = ComboBox(self)
        self.recurrenceCombo.addItems(["Once", "Daily", "Weekly", "Monthly"])
        self.recurrenceCombo.setCurrentIndex(0)
        self.recurrenceCombo.currentIndexChanged.connect(self._on_recurrence_changed)
        
        # Schedule Date
        self.dateLabel = BodyLabel(get_text('dialog.date_label'), self)
        self.datePicker = CalendarPicker(self)
        # Set to current date using QDate
        now = datetime.now()
        self.datePicker.setDate(QDate(now.year, now.month, now.day))
        
        # Apply date format from settings
        self._apply_date_format()
        
        # Schedule Time
        self.timeLabel = BodyLabel(get_text('dialog.time_label'), self)
        
        # Use appropriate time picker based on format preference
        time_format_setting = self.settings_manager.get('time_format', '24h')
        if time_format_setting == '12h':
            self.timePicker = AMTimePicker(self)
        else:
            self.timePicker = TimePicker(self)
        
        # Set to current time using QTime
        self.timePicker.setTime(QTime(now.hour, now.minute))
        # Enable wheel events on time picker
        self.timePicker.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.timePicker.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)  # Prioritize mouse wheel
        
        # Add widgets to layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(10)
        
        self.viewLayout.addWidget(self.nameLabel)
        self.viewLayout.addWidget(self.nameInput)
        self.viewLayout.addSpacing(10)
        
        self.viewLayout.addWidget(self.pathLabel)
        self.viewLayout.addWidget(self.pathInput)
        self.viewLayout.addWidget(self.browseButton)
        self.viewLayout.addSpacing(10)
        
        self.viewLayout.addWidget(self.recurrenceLabel)
        self.viewLayout.addWidget(self.recurrenceCombo)
        self.viewLayout.addSpacing(10)
        
        self.viewLayout.addWidget(self.dateLabel)
        self.viewLayout.addWidget(self.datePicker)
        self.viewLayout.addSpacing(10)
        
        self.viewLayout.addWidget(self.timeLabel)
        
        # Add current time reference label
        self.currentTimeLabel = BodyLabel(self)
        self._update_current_time_label()
        self.viewLayout.addWidget(self.currentTimeLabel)
        
        # Start timer to update current time label
        self.time_update_timer = QTimer(self)
        self.time_update_timer.timeout.connect(self._update_current_time_label)
        self.time_update_timer.start(1000)  # Update every second
        
        self.viewLayout.addWidget(self.timePicker)
        self.viewLayout.addSpacing(10)

        # Power Options
        self.wakeCheckBox = CheckBox(get_text('dialog.wake_option'), self)
        self.sleepCheckBox = CheckBox(get_text('dialog.sleep_option'), self)
        
        self.viewLayout.addWidget(self.wakeCheckBox)
        self.viewLayout.addWidget(self.sleepCheckBox)
        
        # Pre-wake duration (only shown when wake is enabled)
        self.preWakeLabel = BodyLabel("Pre-wake duration:", self)
        self.preWakeCombo = ComboBox(self)
        self.preWakeCombo.addItems(["1 minute", "3 minutes", "5 minutes", "10 minutes", "15 minutes"])
        
        # Default to global setting
        default_prewake = self.settings_manager.get('pre_wake_minutes', 5)
        prewake_map = {1: 0, 3: 1, 5: 2, 10: 3, 15: 4}
        self.preWakeCombo.setCurrentIndex(prewake_map.get(default_prewake, 2))
        
        self.viewLayout.addWidget(self.preWakeLabel)
        self.viewLayout.addWidget(self.preWakeCombo)
        self.viewLayout.addSpacing(10)
        
        # Connect wake checkbox to show/hide pre-wake options
        self.wakeCheckBox.stateChanged.connect(self._on_wake_checkbox_changed)
        self._on_wake_checkbox_changed()  # Initialize visibility
        
        # Configure buttons
        self.yesButton.setText(get_text('dialog.save') if self.is_edit_mode else get_text('dialog.add'))
        self.cancelButton.setText(get_text('dialog.cancel'))
        
        # Initialize date picker visibility based on default recurrence (Once)
        self._on_recurrence_changed(0)
    
    def _browse_program(self):
        """Open file browser to select an executable."""
        # Use QFileDialog instance instead of static method to set options
        dialog = QFileDialog(self, get_text('dialog.select_program'))
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Executable Files (*.exe *.lnk);;All Files (*.*)")
        
        # CRITICAL: Prevent automatic shortcut resolution
        # We want to select the .lnk file itself, not its target
        dialog.setOption(QFileDialog.Option.DontResolveSymlinks, True)
        
        if dialog.exec():  # PyQt6 uses exec()
            selected_files = dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                self.pathInput.setText(file_path)
                logger.debug(f"Selected program: {file_path}")
                
                # Auto-fill name if empty
                if not self.nameInput.text().strip():
                    name = Path(file_path).stem
                    # Capitalize first letter
                    name = name[0].upper() + name[1:] if name else name
                    self.nameInput.setText(name)
    
    def _load_task_data(self):
        """Load existing task data into the form fields."""
        if not self.task_data:
            return
            
        self.nameInput.setText(self.task_data.get('name', ''))
        self.pathInput.setText(self.task_data.get('program_path', ''))
        
        # Load recurrence
        recurrence = self.task_data.get('recurrence', 'Once')
        self.recurrenceCombo.setCurrentText(recurrence)
        
        try:
            schedule_time = datetime.fromisoformat(self.task_data.get('schedule_time'))
            # Convert to QDate and QTime
            self.datePicker.setDate(QDate(schedule_time.year, schedule_time.month, schedule_time.day))
            self.timePicker.setTime(QTime(schedule_time.hour, schedule_time.minute))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse schedule time: {e}")
            
        # Load power options
        self.wakeCheckBox.setChecked(self.task_data.get('wake_enabled', False))
        self.sleepCheckBox.setChecked(self.task_data.get('sleep_after', False))
        
        # Load per-task pre-wake duration
        task_prewake = self.task_data.get('pre_wake_minutes', self.settings_manager.get('pre_wake_minutes', 5))
        prewake_map = {1: 0, 3: 1, 5: 2, 10: 3, 15: 4}
        self.preWakeCombo.setCurrentIndex(prewake_map.get(task_prewake, 2))
    
    def _on_wake_checkbox_changed(self):
        """Show/hide pre-wake duration options based on wake checkbox."""
        is_wake_enabled = self.wakeCheckBox.isChecked()
        self.preWakeLabel.setVisible(is_wake_enabled)
        self.preWakeCombo.setVisible(is_wake_enabled)
    
    def validate_input(self) -> bool:
        """
        Validate user input.
        
        Returns:
            True if all inputs are valid, False otherwise
        """
        # Check task name
        if not self.nameInput.text().strip():
            logger.warning("Validation failed: Task name is empty")
            return False
        
        # Check program path
        program_path = self.pathInput.text().strip()
        if not program_path:
            logger.warning("Validation failed: Program path is empty")
            return False
        
        # Check if file exists
        if not Path(program_path).exists():
            logger.warning(f"Validation failed: Program file does not exist: {program_path}")
            return False
        
        # Check if scheduled time is in the future (only for 'Once' tasks)
        # For recurring tasks, the start date can be today/past as long as the time is valid
        recurrence = self.recurrenceCombo.currentText()
        scheduled_datetime = self.get_scheduled_datetime()
        
        if recurrence == 'Once' and scheduled_datetime <= datetime.now():
            logger.warning("Validation failed: Scheduled time is in the past")
            return False
        
        return True
    
    def get_scheduled_datetime(self) -> datetime:
        """
        Combine date and time pickers into a single datetime object.
        
        Returns:
            datetime object representing the scheduled time
        """
        # Get date from picker
        date = self.datePicker.getDate()
        
        # Get time from picker
        time = self.timePicker.getTime()
        
        return datetime(
            date.year(), date.month(), date.day(),
            time.hour(), time.minute(), time.second()
        )
    
    def get_task_data(self) -> dict:
        """
        Get the task data from the form fields.
        
        Returns:
            Dictionary with task data
        """
        # Map combo index to minutes
        prewake_values = [1, 3, 5, 10, 15]
        pre_wake_minutes = prewake_values[self.preWakeCombo.currentIndex()]
        
        task = {
            'name': self.nameInput.text().strip(),
            'program_path': self.pathInput.text().strip(),
            'schedule_time': self.get_scheduled_datetime().isoformat(),
            'recurrence': self.recurrenceCombo.currentText(),
            'enabled': True,
            'wake_enabled': self.wakeCheckBox.isChecked(),
            'sleep_after': self.sleepCheckBox.isChecked(),
            'pre_wake_minutes': pre_wake_minutes
        }
        
        if self.is_edit_mode:
            task['id'] = self.task_data['id']
            task['created_at'] = self.task_data['created_at']
        else:
            # ID and created_at will be handled by TaskManager
            pass
            
        return task
    
    def _apply_date_format(self):
        """Apply user's preferred date format to the date picker."""
        date_format_setting = self.settings_manager.get('date_format', 'YYYY-MM-DD')
        
        # Map setting to Qt date format
        format_map = {
            'YYYY-MM-DD': 'yyyy-MM-dd',
            'DD.MM.YYYY': 'dd.MM.yyyy',
            'MM/DD/YYYY': 'MM/dd/yyyy',
            'DD-MM-YYYY': 'dd-MM-yyyy'
        }
        
        qt_format = format_map.get(date_format_setting, 'yyyy-MM-dd')
        self.datePicker.setDateFormat(qt_format)
        logger.debug(f"Applied date format: {qt_format}")
    
    def _on_recurrence_changed(self, index):
        """Handle recurrence type change to show/hide date picker."""
        recurrence = self.recurrenceCombo.currentText()
        
        # Only show date picker for "Once" tasks
        # Recurring tasks start from current time
        show_date = (recurrence == "Once")
        
        self.dateLabel.setVisible(show_date)
        self.datePicker.setVisible(show_date)
        
        logger.debug(f"Recurrence changed to: {recurrence}, date picker visible: {show_date}")
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on title area (top 60 pixels)
            if event.pos().y() < 60:
                self.dragging = True
                # PyQt6 uses globalPosition().toPoint()
                global_pos = event.globalPosition().toPoint()
                self.drag_position = global_pos - self.frameGeometry().topLeft()
                self.titleLabel.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging."""
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            # PyQt6 uses globalPosition().toPoint()
            global_pos = event.globalPosition().toPoint()
            self.move(global_pos - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.titleLabel.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def _update_current_time_label(self):
        """Update the current time label with seconds."""
        now = datetime.now()
        time_format = self.settings_manager.get('time_format', '24h')
        
        if time_format == '12h':
            time_str = now.strftime('%I:%M:%S %p')
        else:
            time_str = now.strftime('%H:%M:%S')
        
        self.currentTimeLabel.setText(f"Current time: {time_str}")
    
    def wheelEvent(self, event):
        """Handle mouse wheel for time adjustment."""
        # Check if mouse is over the time picker
        time_picker_geometry = self.timePicker.geometry()
        # PyQt6 uses globalPosition().toPoint()
        global_pos = event.globalPosition().toPoint()
        mouse_pos = self.mapFromGlobal(global_pos)
        
        if time_picker_geometry.contains(mouse_pos):
            # Get current time
            current_time = self.timePicker.getTime()
            
            # Determine scroll direction (positive = up/forward, negative = down/backward)
            delta = event.angleDelta().y()
            
            if delta > 0:
                # Scroll up - add 1 minute
                new_time = current_time.addSecs(60)
            else:
                # Scroll down - subtract 1 minute
                new_time = current_time.addSecs(-60)
            
            # Update time picker
            self.timePicker.setTime(new_time)
            event.accept()
            logger.debug(f"Time adjusted via scroll wheel: {new_time.toString()}")
        else:
            super().wheelEvent(event)
