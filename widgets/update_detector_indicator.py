"""
Update Detector Indicator Widget
Blinking badge showing when the Auto Update Detector is actively monitoring a task.
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget


class UpdateDetectorIndicator(QWidget):
    """
    Visual indicator showing Update Detector status.
    Blinks when actively monitoring a task, hidden when inactive.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 28)
        self._active = False
        self._task_name = ""
        self._pulse_opacity = 1.0
        
        # Pulse animation for active state
        self._pulse_animation = QPropertyAnimation(self, b"pulseOpacity")
        self._pulse_animation.setDuration(800)
        self._pulse_animation.setStartValue(1.0)
        self._pulse_animation.setEndValue(0.4)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop
        
        # Start hidden
        self.hide()
    
    @pyqtProperty(float)
    def pulseOpacity(self):
        return self._pulse_opacity
    
    @pulseOpacity.setter
    def pulseOpacity(self, value):
        self._pulse_opacity = value
        self.update()
    
    def set_active(self, active: bool, task_name: str = ""):
        """
        Set the indicator active/inactive state.
        
        Args:
            active: True to show blinking indicator, False to hide
            task_name: Name of the task being monitored (for tooltip)
        """
        self._active = active
        self._task_name = task_name
        
        if active:
            self.setToolTip(f"Monitoring: {task_name}\nDetecting update dialogs for 5 minutes")
            self._pulse_animation.start()
            self.show()
        else:
            self._pulse_animation.stop()
            self._pulse_opacity = 1.0
            self.hide()
        
        self.update()
    
    def is_active(self) -> bool:
        """Check if the indicator is currently active."""
        return self._active
    
    def paintEvent(self, event):
        """Custom paint for the indicator."""
        if not self._active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Teal/Cyan color for Update Detector
        bg_color = QColor("#00ACC1")  # Cyan 600
        bg_color.setAlphaF(self._pulse_opacity)
        text_color = QColor("#FFFFFF")
        
        # Draw rounded rectangle background
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        
        # Draw text with icon
        painter.setPen(text_color)
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Draw magnifying glass icon and text
        text = "🔍 Update Detector"
        painter.drawText(0, 0, self.width(), self.height(), Qt.AlignmentFlag.AlignCenter, text)
