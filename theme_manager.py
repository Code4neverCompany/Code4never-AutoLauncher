"""
Theme Manager Module for Autolauncher.
Handles application theme state, persistence, and transitions.
"""

from PyQt6.QtCore import QObject, QTimer, Qt
from qfluentwidgets import setTheme, Theme, qconfig, InfoBar, InfoBarPosition
from task_manager import SettingsManager
from logger import get_logger
from language_manager import get_text

logger = get_logger(__name__)

class ThemeManager(QObject):
    """
    Manages the application theme (Light/Dark).
    Handles persistence, toggling, and protection against external changes.
    """
    
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings = settings_manager
        self._expected_theme = self.settings.get('theme', 'Light')
        
    def apply_initial_theme(self):
        """Apply the saved theme during startup (before UI creation)."""
        # Apply theme based on saved preference
        if self._expected_theme == 'Dark':
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
        logger.info(f"ThemeManager: Applied initial theme: {self._expected_theme}")

    def setup_protection(self):
        """Connect signals to protect against unexpected theme changes."""
        # Listen for theme changes from qfluentwidgets system
        qconfig.themeChanged.connect(self._on_external_change)

    def _on_external_change(self, theme):
        """Protect against unexpected theme changes (e.g. system changes if not desired)."""
        current_expected = 'Dark' if theme == Theme.DARK else 'Light'
        saved_theme = self.settings.get('theme', 'Light')
        
        # If the change doesn't match our saved preference, revert it
        if current_expected != saved_theme:
            logger.warning(f"Unexpected theme change to {current_expected}, reverting to {saved_theme}")
            # Revert after short delay to ensure UI is ready
            QTimer.singleShot(50, lambda: self.apply_saved_theme())
        else:
            logger.debug(f"Theme change confirmed: {current_expected}")

    def apply_saved_theme(self):
        """Force apply the saved theme."""
        saved_theme = self.settings.get('theme', 'Light')
        if saved_theme == 'Dark':
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
            
    def toggle_theme(self, parent_window=None):
        """Toggle the current theme and save preference."""
        current = self.settings.get('theme', 'Light')
        new_theme = 'Dark' if current == 'Light' else 'Light'
        
        # Update settings
        self.settings.set('theme', new_theme)
        self._expected_theme = new_theme
        
        # Apply new theme
        if new_theme == 'Dark':
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
            
        logger.info(f"Theme toggled to {new_theme}")
        
        # Show notification if parent window provided
        if parent_window:
            InfoBar.success(
                title=get_text('main_window.theme_changed'),
                content=get_text('main_window.theme_switched', theme=new_theme),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=parent_window
            )
