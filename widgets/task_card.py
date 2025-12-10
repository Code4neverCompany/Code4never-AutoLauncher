"""
TaskCard Widget
Modern card-based display for individual tasks.
Replaces the traditional table row with a premium card layout.
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, pyqtProperty, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from qfluentwidgets import CardWidget, isDarkTheme
from .countdown_indicator import CountdownIndicator
from .status_badge import StatusBadge
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_manager import get_text


class TaskCard(CardWidget):
    """
    Premium card widget for displaying task information.
    Features: Icon, name, schedule, countdown, status, hover effects.
    """
    
    # Signals
    clicked = pyqtSignal(str)  # task_id
    run_clicked = pyqtSignal(str)  # task_id
    edit_clicked = pyqtSignal(str)  # task_id
    
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.task_id = task_data.get('id', '')
        self._scale = 1.0
        self._setup_ui()
        self._setup_animations()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup card UI layout."""
        self.setFixedWidth(350)
        self.setMinimumHeight(120)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Top row: Icon + Name + Status
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setScaledContents(True)
        self._load_icon()
        
        # Name and schedule container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Task name
        self.name_label = QLabel(self.task_data.get('name', get_text('dialog.unknown')))
        self.name_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.name_label.setWordWrap(False)
        
        # Schedule info
        schedule_text = self._format_schedule()
        self.schedule_label = QLabel(schedule_text)
        self.schedule_label.setFont(QFont("Segoe UI", 9))
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.schedule_label)
        
        # Status badge
        self.status_badge = StatusBadge()
        status = get_text('dialog.active') if self.task_data.get('enabled', True) else get_text('dialog.paused')
        self.status_badge.set_status(status)
        
        top_layout.addWidget(self.icon_label)
        top_layout.addLayout(info_layout, 1)
        top_layout.addWidget(self.status_badge)
        
        # Countdown indicator
        self.countdown_indicator = CountdownIndicator()
        
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.countdown_indicator)
        main_layout.addStretch()
    
    def _load_icon(self):
        """Load and display task icon."""
        icon_path = self.task_data.get('icon_path')
        if icon_path:
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                self.icon_label.setPixmap(pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.icon_label.setText("📄")
        else:
            self.icon_label.setText("📄")
        
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def _format_schedule(self):
        """Format schedule information."""
        try:
            from datetime import datetime
            schedule_time = datetime.fromisoformat(self.task_data.get('schedule_time'))
            recurrence = self.task_data.get('recurrence', 'Once')
            recurrence_text = get_text(f'dialog.recurrence_{recurrence.lower()}')
            at_text = get_text('dialog.at')
            
            if recurrence == 'Once':
                return f"{recurrence_text} {at_text} {schedule_time.strftime('%H:%M')}"
            else:
                time_str = schedule_time.strftime('%H:%M')
                return f"{recurrence_text} {at_text} {time_str}"
        except:
            return get_text('dialog.invalid_schedule')
    
    def _setup_animations(self):
        """Setup hover and click animations."""
        self._scale_animation = QPropertyAnimation(self, b"scale")
        self._scale_animation.setDuration(150)
        self._scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 2)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)
    
    def _apply_styling(self):
        """Apply theme-aware styling."""
        if isDarkTheme():
            name_color = "#FFFFFF"
            schedule_color = "#B0B0B0"
        else:
            name_color = "#000000"
            schedule_color = "#666666"
        
        self.name_label.setStyleSheet(f"color: {name_color};")
        self.schedule_label.setStyleSheet(f"color: {schedule_color};")
    
    @pyqtProperty(float)
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        self._scale = value
        self.update()
    
    def update_countdown(self, remaining_seconds, total_seconds):
        """Update countdown display."""
        if self.task_data.get('enabled', True):
            self.countdown_indicator.set_countdown(remaining_seconds, total_seconds)
        else:
            # Paused tasks show no countdown
            self.countdown_indicator.set_countdown(0, 0)
    
    def update_status(self, is_active):
        """Update status badge."""
        status = get_text('dialog.active') if is_active else get_text('dialog.paused')
        self.status_badge.set_status(status)
        self.task_data['enabled'] = is_active
    
    def enterEvent(self, event):
        """Hover enter - scale up."""
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.02)
        self._scale_animation.start()
        
        # Increase shadow
        self.shadow.setBlurRadius(25)
        self.shadow.setOffset(0, 4)
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hover leave - scale down."""
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.0)
        self._scale_animation.start()
        
        # Decrease shadow
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 2)
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Click - quick scale down."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._scale_animation.stop()
            self._scale_animation.setDuration(100)
            self._scale_animation.setStartValue(self._scale)
            self._scale_animation.setEndValue(0.98)
            self._scale_animation.start()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Release - return to hover scale."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._scale_animation.stop()
            self._scale_animation.setDuration(150)
            self._scale_animation.setStartValue(self._scale)
            self._scale_animation.setEndValue(1.02 if self.underMouse() else 1.0)
            self._scale_animation.start()
            
            # Emit clicked signal
            self.clicked.emit(self.task_id)
        
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        """Override paint to apply scale transform."""
        super().paintEvent(event)
        
        if self._scale != 1.0:
            # This is handled by the graphics effect system
            # Scale is applied via transform
            pass
