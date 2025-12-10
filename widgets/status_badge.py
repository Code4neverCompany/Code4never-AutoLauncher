"""
StatusBadge Widget
Colored badge indicating task status with multiple states.
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget


class StatusBadge(QWidget):
    """
    Visual status indicator with color and animation.
    Supports: Enabled, Disabled, Postponed, Failed, Running
    """
    
    # Status color mapping
    STATUS_COLORS = {
        'Enabled': ('#27AE60', '#FFFFFF'),      # Green
        'Active': ('#27AE60', '#FFFFFF'),       # Green (alias)
        'Disabled': ('#3498DB', '#FFFFFF'),     # Blue
        'Paused': ('#3498DB', '#FFFFFF'),       # Blue (alias)
        'Postponed': ('#F39C12', '#FFFFFF'),    # Orange
        'Failed': ('#E74C3C', '#FFFFFF'),       # Red
        'Running': ('#9B59B6', '#FFFFFF'),      # Purple
        'Expired': ('#7F8C8D', '#FFFFFF'),      # Gray
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 24)
        self._status = "Enabled"
        self._subtitle = ""  # For additional info like "@ 18:30"
        self._pulse_opacity = 1.0
        
        # Pulse animation for running status
        self._pulse_animation = QPropertyAnimation(self, b"pulseOpacity")
        self._pulse_animation.setDuration(1000)
        self._pulse_animation.setStartValue(1.0)
        self._pulse_animation.setEndValue(0.5)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop
    
    @pyqtProperty(float)
    def pulseOpacity(self):
        return self._pulse_opacity
    
    @pulseOpacity.setter
    def pulseOpacity(self, value):
        self._pulse_opacity = value
        self.update()
    
    def set_status(self, status: str, subtitle: str = ""):
        """
        Set status and optional subtitle.
        
        Args:
            status: One of 'Enabled', 'Disabled', 'Postponed', 'Failed', 'Running'
            subtitle: Optional text to show (e.g., '@ 18:30' for Postponed)
        """
        self._status = status
        self._subtitle = subtitle
        
        # Adjust width based on content
        if subtitle:
            self.setFixedWidth(120)
        else:
            self.setFixedWidth(80)
        
        # Only animate for Running status
        if status == "Running":
            self._pulse_animation.start()
        else:
            self._pulse_animation.stop()
            self._pulse_opacity = 1.0
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for status badge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get colors for status (default to gray if unknown)
        colors = self.STATUS_COLORS.get(self._status, ('#7F8C8D', '#FFFFFF'))
        bg_hex, text_hex = colors
        
        # Apply pulse opacity for animated statuses
        bg_color = QColor(bg_hex)
        if self._status == "Running":
            bg_color.setAlphaF(self._pulse_opacity)
        text_color = QColor(text_hex)
        
        # Draw rounded rectangle
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Draw text
        painter.setPen(text_color)
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Combine status and subtitle
        display_text = self._status
        if self._subtitle:
            display_text = f"{self._status} {self._subtitle}"
        
        painter.drawText(0, 0, self.width(), self.height(), Qt.AlignmentFlag.AlignCenter, display_text)

