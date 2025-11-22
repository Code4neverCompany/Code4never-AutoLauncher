"""
Settings Interface Module
Displays application settings.

© 2025 4never Company. All rights reserved.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import (
    SettingCardGroup,
    SwitchSettingCard,
    FolderListSettingCard,
    OptionsSettingCard,
    PushSettingCard,
    HyperlinkCard,
    PrimaryPushSettingCard,
    ScrollArea,
    ComboBoxSettingCard,
    ExpandLayout,
    Theme,
    InfoBar,
    CustomColorSettingCard,
    setTheme,
    setThemeColor,
    RangeSettingCard,
    ColorDialog,
    SettingCard,
    ComboBox,
    FluentIcon,
    InfoBarPosition,
    IndeterminateProgressRing
)
from task_manager import SettingsManager
from logger import get_logger

logger = get_logger(__name__)


class SettingsInterface(ScrollArea):
    """
    Settings interface for application preferences.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_manager = SettingsManager()
        
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        
        # Set object name for styling
        self.setObjectName("settingsInterface")
        self.scrollWidget.setObjectName("scrollWidget")
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        
        # Configure layout
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # Set transparent background to fix Light mode issue
        self.scrollWidget.setStyleSheet("QWidget{background-color: transparent;}")
        self.setStyleSheet("QScrollArea{background-color: transparent; border: none;}")
        
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        
        # --- General Settings Group ---
        self.generalGroup = SettingCardGroup("General", self.scrollWidget)
        
        # Execution Mode Setting
        self.executionModeCard = SettingCard(
            FluentIcon.ROBOT,
            "Execution Mode",
            "Choose how tasks should behave when you are using the computer",
            parent=self.generalGroup
        )
        
        self.modeComboBox = ComboBox(self.executionModeCard)
        self.modeComboBox.addItems(["Automatic (Postpone if busy)", "Interactive (Ask if busy)", "Aggressive (Run always)"])
        self.executionModeCard.hBoxLayout.addWidget(self.modeComboBox, 0, Qt.AlignRight)
        self.executionModeCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        # Migrate old 'automode' bool if present
        mode = self.settings_manager.get('execution_mode', 'ask')
        if self.settings_manager.get('automode', False):
            mode = 'auto'
            
        # Map mode string to index
        mode_map = {'auto': 0, 'ask': 1, 'run': 2}
        self.modeComboBox.setCurrentIndex(mode_map.get(mode, 1))
        
        # Connect signal
        self.modeComboBox.currentIndexChanged.connect(self._on_execution_mode_changed)
        
        self.generalGroup.addSettingCard(self.executionModeCard)
        
        # --- Updates Settings Group ---
        self.updatesGroup = SettingCardGroup("Updates", self.scrollWidget)
        
        # Auto-Update Frequency Setting
        self.autoUpdateCard = SettingCard(
            FluentIcon.UPDATE,
            "Auto-Update Check",
            "Choose how often the app should check for updates",
            parent=self.updatesGroup
        )
        
        self.updateFrequencyComboBox = ComboBox(self.autoUpdateCard)
        self.updateFrequencyComboBox.addItems(["Disabled", "On Startup Only", "Daily", "Weekly"])
        self.autoUpdateCard.hBoxLayout.addWidget(self.updateFrequencyComboBox, 0, Qt.AlignRight)
        self.autoUpdateCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        frequency = self.settings_manager.get('auto_update_frequency', 'startup')
        frequency_map = {'disabled': 0, 'startup': 1, 'daily': 2, 'weekly': 3}
        self.updateFrequencyComboBox.setCurrentIndex(frequency_map.get(frequency, 1))
        
        # Connect signal
        self.updateFrequencyComboBox.currentIndexChanged.connect(self._on_update_frequency_changed)
        
        self.updatesGroup.addSettingCard(self.autoUpdateCard)
        
        # Check for Updates Now Button
        self.checkUpdateCard = PrimaryPushSettingCard(
            "Check Now",
            FluentIcon.SYNC,
            "Manual Update Check",
            "Check for the latest version immediately",
            parent=self.updatesGroup
        )
        self.checkUpdateCard.clicked.connect(self._on_check_updates_now)
        self.updatesGroup.addSettingCard(self.checkUpdateCard)


        
        # Add groups to layout
        self.expandLayout.addWidget(self.generalGroup)
        self.expandLayout.addWidget(self.updatesGroup)
        self.expandLayout.addStretch(1)
        
    def _on_execution_mode_changed(self, index: int):
        """Handle execution mode change."""
        modes = ['auto', 'ask', 'run']
        if 0 <= index < len(modes):
            mode = modes[index]
            self.settings_manager.set('execution_mode', mode)
            # Update legacy key for compatibility if needed, or just ignore it
            self.settings_manager.set('automode', mode == 'auto')
            
            logger.info(f"Execution mode set to: {mode}")
            
            InfoBar.success(
                title="Settings Saved",
                content=f"Execution Mode updated",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
    
    def _on_update_frequency_changed(self, index: int):
        """Handle update frequency change."""
        frequencies = ['disabled', 'startup', 'daily', 'weekly']
        if 0 <= index < len(frequencies):
            frequency = frequencies[index]
            self.settings_manager.set('auto_update_frequency', frequency)
            
            logger.info(f"Auto-update frequency set to: {frequency}")
            
            InfoBar.success(
                title="Settings Saved",
                content=f"Update check frequency updated",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
    
    def _on_check_updates_now(self):
        """Handle manual update check request."""
        # Import here to avoid circular dependency
        from update_manager import UpdateManager
        
        update_manager = UpdateManager()
        
        # Show checking status
        InfoBar.info(
            title="Checking for Updates",
            content="Please wait...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        
        # Perform the check
        update_info, error = update_manager.check_for_updates()
        update_manager.save_last_check_time(
            "update_available" if update_info else ("error" if error else "no_update"),
            update_info.get('version') if update_info else None
        )
        
        if error:
            InfoBar.error(
                title="Update Check Failed",
                content=f"{error}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
        elif update_info:
            # Notify parent window about available update
            if hasattr(self.parent(), '_handle_update_available'):
                self.parent()._handle_update_available(update_info)
            else:
                InfoBar.success(
                    title="Update Available",
                    content=f"Version {update_info['version']} is available!",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=5000,
                    parent=self
                )
        else:
            InfoBar.success(
                title="No Updates",
                content="You're running the latest version!",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
