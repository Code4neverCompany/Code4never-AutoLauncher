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
    
    date_format_changed = pyqtSignal()
    
    def __init__(self, settings_manager=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager if settings_manager else SettingsManager()
        
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
        
        # Date Format Setting
        self.dateFormatCard = SettingCard(
            FluentIcon.CALENDAR,
            "Date Format",
            "Choose your preferred date display format",
            parent=self.generalGroup
        )
        
        self.dateFormatComboBox = ComboBox(self.dateFormatCard)
        self.dateFormatComboBox.addItems(["YYYY-MM-DD", "DD.MM.YYYY", "MM/DD/YYYY", "DD-MM-YYYY"])
        self.dateFormatCard.hBoxLayout.addWidget(self.dateFormatComboBox, 0, Qt.AlignRight)
        self.dateFormatCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        date_format = self.settings_manager.get('date_format', 'YYYY-MM-DD')
        format_map = {'YYYY-MM-DD': 0, 'DD.MM.YYYY': 1, 'MM/DD/YYYY': 2, 'DD-MM-YYYY': 3}
        self.dateFormatComboBox.setCurrentIndex(format_map.get(date_format, 0))
        
        # Connect signal
        self.dateFormatComboBox.currentIndexChanged.connect(self._on_date_format_changed)
        
        self.generalGroup.addSettingCard(self.dateFormatCard)
        
        # Time Format Setting
        self.timeFormatCard = SettingCard(
            FluentIcon.HISTORY,
            "Time Format",
            "Choose between 12-hour and 24-hour time display",
            parent=self.generalGroup
        )
        
        self.timeFormatComboBox = ComboBox(self.timeFormatCard)
        self.timeFormatComboBox.addItems(["24-hour (14:30)", "12-hour (2:30 PM)"])
        self.timeFormatCard.hBoxLayout.addWidget(self.timeFormatComboBox, 0, Qt.AlignRight)
        self.timeFormatCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        time_format = self.settings_manager.get('time_format', '24h')
        format_map = {'24h': 0, '12h': 1}
        self.timeFormatComboBox.setCurrentIndex(format_map.get(time_format, 0))
        
        # Connect signal
        self.timeFormatComboBox.currentIndexChanged.connect(self._on_time_format_changed)
        
        self.generalGroup.addSettingCard(self.timeFormatCard)
        
        # --- Updates Settings Group ---
        self.updatesGroup = SettingCardGroup("Updates", self.scrollWidget)
        
        # Auto-Update Mode Setting
        self.autoUpdateCard = SettingCard(
            FluentIcon.UPDATE,
            "Auto-Update Mode",
            "Automatic: checks every 2 min, installs when next task is >30 min away",
            parent=self.updatesGroup
        )
        
        self.updateFrequencyComboBox = ComboBox(self.autoUpdateCard)
        self.updateFrequencyComboBox.addItems(["On Startup", "Manual Only", "Automatic (Smart)"])
        self.autoUpdateCard.hBoxLayout.addWidget(self.updateFrequencyComboBox, 0, Qt.AlignRight)
        self.autoUpdateCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        frequency = self.settings_manager.get('auto_update_frequency', 'startup')
        frequency_map = {'startup': 0, 'manual': 1, 'automatic': 2}
        self.updateFrequencyComboBox.setCurrentIndex(frequency_map.get(frequency, 0))
        
        # Connect signal
        self.updateFrequencyComboBox.currentIndexChanged.connect(self._on_update_frequency_changed)
        
        self.updatesGroup.addSettingCard(self.autoUpdateCard)

        
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
        frequencies = ['startup', 'manual', 'automatic']
        if 0 <= index < len(frequencies):
            frequency = frequencies[index]
            self.settings_manager.set('auto_update_frequency', frequency)
            
            logger.info(f"Auto-update mode set to: {frequency}")
            
            mode_names = ["On Startup", "Manual Only", "Automatic (Smart)"]
            
            InfoBar.success(
                title="Settings Saved",
                content=f"Update mode: {mode_names[index]}. Restart app to apply.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
    
    def _on_date_format_changed(self, index: int):
        """Handle date format change."""
        formats = ['YYYY-MM-DD', 'DD.MM.YYYY', 'MM/DD/YYYY', 'DD-MM-YYYY']
        if 0 <= index < len(formats):
            date_format = formats[index]
            self.settings_manager.set('date_format', date_format)
            
            logger.info(f"Date format set to: {date_format}")
            
            # Emit signal to update UI immediately
            self.date_format_changed.emit()
            
            InfoBar.success(
                title="Settings Saved",
                content=f"Date format: {date_format}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
    
    def _on_time_format_changed(self, index: int):
        """Handle time format change."""
        formats = ['24h', '12h']
        if 0 <= index < len(formats):
            time_format = formats[index]
            self.settings_manager.set('time_format', time_format)
            
            logger.info(f"Time format set to: {time_format}")
            
            InfoBar.success(
                title="Settings Saved",
                content=f"Time format: {'24-hour' if time_format == '24h' else '12-hour'}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
