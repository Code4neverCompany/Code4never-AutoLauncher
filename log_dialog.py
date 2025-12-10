"""
Log Dialog Module
Displays the task execution log with detailed event information.
"""

import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableWidgetItem, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QIcon, QPixmap
from datetime import datetime
from qfluentwidgets import (
    MessageBoxBase,
    SubtitleLabel,
    TableWidget,
    PushButton,
    FluentIcon
)

from execution_logger import ExecutionLogger
from logger import get_logger

logger = get_logger(__name__)

class LogDialog(MessageBoxBase):
    """Dialog to display execution logs with color-coded events."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.execution_logger = ExecutionLogger()
        
        # UI Setup
        self.titleLabel = SubtitleLabel("Execution Log", self)
        self.viewLayout.addWidget(self.titleLabel)
        
        # Table with 5 columns
        self.logTable = TableWidget(self)
        self.logTable.setColumnCount(5)
        self.logTable.setHorizontalHeaderLabels(["Time", "Task", "Event", "Details", "Blockers"])
        self.logTable.verticalHeader().hide()
        self.logTable.setBorderVisible(True)
        self.logTable.setBorderRadius(8)
        self.logTable.setWordWrap(False)
        self.logTable.setMinimumHeight(450)
        self.logTable.setMinimumWidth(900)
        self.logTable.setIconSize(QSize(20, 20))
        
        # Resize columns
        self.logTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Time
        self.logTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Task
        self.logTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Event
        self.logTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          # Details
        self.logTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Blockers
        
        self.viewLayout.addWidget(self.logTable)
        
        # Buttons
        self.yesButton.setText("Refresh")
        self.yesButton.setIcon(FluentIcon.SYNC)
        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self._load_logs)
        
        self.cancelButton.setText("Close")
        self.cancelButton.clicked.disconnect()
        self.cancelButton.clicked.connect(self.accept) # Close dialog
        
        # Add a custom "Clear Log" button to the button layout
        self.clearButton = PushButton(FluentIcon.DELETE, "Clear Log", self.buttonGroup)
        self.clearButton.clicked.connect(self._clear_logs)
        self.buttonLayout.insertWidget(1, self.clearButton)
        
        # Load data
        self._load_logs()
        
        # Adjust dialog size
        self.widget.setMinimumWidth(950)
    
    def _extract_blockers_from_details(self, details: str) -> list:
        """Extract process names from details like 'Running: code.exe, Antigravity.exe'"""
        match = re.search(r'Running:\s*([^;]+)', details)
        if match:
            processes_str = match.group(1).strip()
            # Split by comma and clean up
            processes = [p.strip() for p in processes_str.split(',')]
            return processes
        return []
        
    def _load_logs(self):
        """Load logs into the table with color coding."""
        logs = self.execution_logger.get_logs(limit=100)
        self.logTable.setRowCount(len(logs))
        
        # Color mapping for event types
        event_colors = {
            'MISSED': '#E74C3C',        # Red
            'FAILED': '#E74C3C',        # Red
            'WAKE_SCHEDULED': '#3498DB', # Blue
            'WAKE_SUCCESS': '#2ECC71',   # Green
            'STARTED': '#27AE60',        # Green
            'EXECUTED': '#27AE60',       # Green - conditions met
            'FINISHED': '#7F8C8D',       # Gray
            'POSTPONED': '#F39C12',      # Orange
        }
        
        for i, entry in enumerate(logs):
            # Format timestamp
            try:
                dt = datetime.fromisoformat(entry['timestamp'])
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = entry.get('timestamp', '')
            
            event_type = str(entry.get('event_type', ''))
            details = str(entry.get('details', ''))
            
            # Extract blocker processes for POSTPONED events
            blockers = []
            blockers_text = ""
            if event_type == 'POSTPONED':
                blockers = self._extract_blockers_from_details(details)
                if blockers:
                    blockers_text = ", ".join(blockers)
            
            # Create items
            time_item = QTableWidgetItem(time_str)
            task_item = QTableWidgetItem(str(entry.get('task_name', '')))
            event_item = QTableWidgetItem(event_type)
            details_item = QTableWidgetItem(details)
            blockers_item = QTableWidgetItem(blockers_text)
            
            # Try to get icon for first blocker process
            if blockers:
                try:
                    from icon_extractor import get_process_icon
                    icon_path = get_process_icon(blockers[0])
                    if icon_path:
                        blockers_item.setIcon(QIcon(icon_path))
                except Exception as e:
                    logger.debug(f"Could not get blocker icon: {e}")
            
            # Apply color to event column
            if event_type in event_colors:
                color = QColor(event_colors[event_type])
                event_item.setForeground(color)
            
            self.logTable.setItem(i, 0, time_item)
            self.logTable.setItem(i, 1, task_item)
            self.logTable.setItem(i, 2, event_item)
            self.logTable.setItem(i, 3, details_item)
            self.logTable.setItem(i, 4, blockers_item)
            
    def _clear_logs(self):
        """Clear the logs."""
        self.execution_logger.clear_logs()
        self._load_logs()

