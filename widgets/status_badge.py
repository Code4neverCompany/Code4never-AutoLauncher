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
        self._status = "Enabled" # Internal state
        self._display_text = "Enabled" # Initial display text (will be localized)
        self._bg_color = QColor(16, 124, 16) # Default Green
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

    def start_pulse(self):
        if not self._pulse_animation.state() == QPropertyAnimation.State.Running:
            self._pulse_animation.start()

    def stop_pulse(self):
        if self._pulse_animation.state() == QPropertyAnimation.State.Running:
            self._pulse_animation.stop()
            self._pulse_opacity = 1.0 # Reset opacity when stopping
    
    def set_status(self, status: str, subtitle: str = ""):
        """
        Set status and optional subtitle.
        
        Args:
            status: One of 'Enabled', 'Disabled', 'Postponed', 'Failed', 'Running', 'Expired', 'Paused', 'Error'
            subtitle: Optional text to show (e.g., '@ 18:30' for Postponed)
        """
        self._status = status
        self._subtitle = subtitle
        
        # Get translator
        from language_manager import get_language_manager
        lang_mgr = get_language_manager()
        
        # Helper to translate
        def tr(key, default):
            return lang_mgr.get_text(f"widgets.{key}", default)
        
        if status == "Running":
            self._display_text = tr("status_running", "Running")
            self._bg_color = QColor(0, 120, 215)  # Fluent Blue
            self.start_pulse()
        elif status == "Enabled":
            self._display_text = tr("status_enabled", "Enabled")
            self._bg_color = QColor(16, 124, 16)  # Success Green
            self.stop_pulse()
        elif status == "Disabled":
            self._display_text = tr("status_disabled", "Disabled")
            self._bg_color = QColor(100, 100, 100) # Grey
            self.stop_pulse()
        elif status == "Expired":
            self._display_text = tr("status_expired", "Expired")
            self._bg_color = QColor(180, 100, 0)   # Orange
            self.stop_pulse()
        elif status == "Paused":
            self._display_text = tr("status_paused", "Paused")
            self._bg_color = QColor(140, 140, 40)  # Yellow-ish
            self.stop_pulse()
        elif status == "Error":
             self._display_text = tr("status_error", "Error")
             self._bg_color = QColor(200, 0, 0)     # Red
             self.stop_pulse()
        elif status == "Postponed": # Original status, not in the provided snippet, but should be handled
            self._display_text = tr("status_postponed", "Postponed")
            self._bg_color = QColor(243, 156, 18) # Orange
            self.stop_pulse()
        elif status == "Failed": # Original status, not in the provided snippet, but should be handled
            self._display_text = tr("status_failed", "Failed")
            self._bg_color = QColor(231, 76, 60) # Red
            self.stop_pulse()
        else: # Default for unknown statuses
            self._display_text = tr("status_unknown", status)
            self._bg_color = QColor(127, 140, 141) # Gray
            self.stop_pulse()
        
        # Adjust width based on content
        if subtitle:
            self.setFixedWidth(120)
        else:
            self.setFixedWidth(80)
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for status badge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Use localized bg_color
        bg_color = QColor(self._bg_color)
        if self.pulseOpacity != 1.0:
            bg_color.setAlphaF(self._pulse_opacity)
        
        # Draw rounded rectangle
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Draw Text
        painter.setPen(Qt.GlobalColor.white)
        text_rect = self.rect() # Use self.rect() for the bounding rectangle
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)

        if self._subtitle:
             # Draw main status slightly up
             painter.drawText(text_rect.adjusted(0, -6, 0, -6), Qt.AlignmentFlag.AlignCenter, self._display_text)
             # Draw subtitle slightly down and smaller
             font.setPointSize(7)
             font.setWeight(QFont.Weight.Normal)
             painter.setFont(font)
             painter.setPen(QColor(220, 220, 220))
             painter.drawText(text_rect.adjusted(0, 8, 0, 8), Qt.AlignmentFlag.AlignCenter, self._subtitle)
        else:
             painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._display_text)
