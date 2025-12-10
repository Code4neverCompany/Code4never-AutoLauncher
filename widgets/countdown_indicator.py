"""
CountdownIndicator Widget
Visual countdown display with circular progress or horizontal bar.
"""

from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QLinearGradient
from PyQt6.QtWidgets import QWidget
from datetime import timedelta


class CountdownIndicator(QWidget):
    """
    Visual countdown indicator with smooth animations.
    Displays time remaining with a progress bar.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._progress = 0.0  # 0.0 to 1.0
        self._total_seconds = 0
        self._remaining_seconds = 0
        
        # Animation
        self._animation = QPropertyAnimation(self, b"progress")
        self._animation.setDuration(500)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
    
    @pyqtProperty(float)
    def progress(self):
        return self._progress
    
    @progress.setter
    def progress(self, value):
        self._progress = max(0.0, min(1.0, value))
        self.update()
    
    def set_countdown(self, remaining_seconds, total_seconds):
        """Update countdown display."""
        self._remaining_seconds = remaining_seconds
        self._total_seconds = total_seconds
        
        if total_seconds > 0:
            target_progress = 1.0 - (remaining_seconds / total_seconds)
        else:
            target_progress = 0.0
        
        self._animation.setStartValue(self._progress)
        self._animation.setEndValue(target_progress)
        self._animation.start()
        
        self.update()
    
    def _format_time(self, seconds):
        """Format seconds to readable string."""
        if seconds <= 0:
            return "Starting soon..."
        
        td = timedelta(seconds=int(seconds))
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def paintEvent(self, event):
        """Custom paint for progress bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get theme-aware colors
        from qfluentwidgets import isDarkTheme
        if isDarkTheme():
            bg_color = QColor(45, 45, 48)
            text_color = QColor(255, 255, 255)
            progress_start = QColor(0, 122, 255)
            progress_end = QColor(0, 199, 190)
        else:
            bg_color = QColor(240, 240, 240)
            text_color = QColor(0, 0, 0)
            progress_start = QColor(0, 122, 255)
            progress_end = QColor(0, 199, 190)
        
        # Draw countdown text
        time_text = self._format_time(self._remaining_seconds)
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(0, 0, self.width(), 20, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"⏱ {time_text}")
        
        # Draw progress bar background
        bar_y = 22
        bar_height = 6
        bar_rect = QRectF(0, bar_y, self.width(), bar_height)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_rect, 3, 3)
        
        # Draw progress bar fill
        if self._progress > 0:
            fill_width = self.width() * self._progress
            fill_rect = QRectF(0, bar_y, fill_width, bar_height)
            
            # Gradient
            gradient = QLinearGradient(0, bar_y, fill_width, bar_y)
            gradient.setColorAt(0, progress_start)
            gradient.setColorAt(1, progress_end)
            
            painter.setBrush(gradient)
            painter.drawRoundedRect(fill_rect, 3, 3)
        
        # Draw percentage
        if self._total_seconds > 0:
            percent = int(self._progress * 100)
            painter.setPen(QPen(text_color.lighter(130), 1))
            painter.setFont(QFont("Segoe UI", 7))
            painter.drawText(self.width() - 35, 0, 35, 20, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{percent}%")
