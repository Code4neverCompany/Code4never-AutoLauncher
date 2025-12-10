"""
Settings Interface Module
Displays application settings.

© 2025 4never Company. All rights reserved.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
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
from language_manager import get_language_manager, set_language
from config import DEFAULT_LANGUAGE, DEFAULT_BLOCKLIST_PROCESSES

logger = get_logger(__name__)


class SettingsInterface(ScrollArea):
    """
    Settings interface for application preferences.
    """
    
    date_format_changed = pyqtSignal()
    language_changed = pyqtSignal()
    
    def __init__(self, settings_manager=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager if settings_manager else SettingsManager()
        
        # Initialize language manager
        self.lang_manager = get_language_manager()
        saved_language = self.settings_manager.get('language', DEFAULT_LANGUAGE)
        self.lang_manager.set_language(saved_language)
        
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        
        # Set object name for styling
        self.setObjectName("settingsInterface")
        self.scrollWidget.setObjectName("scrollWidget")
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        
        # Configure layout
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        self.executionModeCard.hBoxLayout.addWidget(self.modeComboBox, 0, Qt.AlignmentFlag.AlignRight)
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
        
        # Pre-wake Duration Setting
        self.preWakeCard = SettingCard(
            FluentIcon.POWER_BUTTON,
            "Pre-wake Duration",
            "How many minutes before a task to wake the computer",
            parent=self.generalGroup
        )
        
        self.preWakeComboBox = ComboBox(self.preWakeCard)
        self.preWakeComboBox.addItems(["1 minute", "3 minutes", "5 minutes", "10 minutes", "15 minutes"])
        self.preWakeCard.hBoxLayout.addWidget(self.preWakeComboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.preWakeCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        pre_wake = self.settings_manager.get('pre_wake_minutes', 5)
        pre_wake_map = {1: 0, 3: 1, 5: 2, 10: 3, 15: 4}
        self.preWakeComboBox.setCurrentIndex(pre_wake_map.get(pre_wake, 2))
        
        # Connect signal
        self.preWakeComboBox.currentIndexChanged.connect(self._on_pre_wake_changed)
        
        self.generalGroup.addSettingCard(self.preWakeCard)
        
        # Date Format Setting
        self.dateFormatCard = SettingCard(
            FluentIcon.CALENDAR,
            "Date Format",
            "Choose your preferred date display format",
            parent=self.generalGroup
        )
        
        self.dateFormatComboBox = ComboBox(self.dateFormatCard)
        self.dateFormatComboBox.addItems(["YYYY-MM-DD", "DD.MM.YYYY", "MM/DD/YYYY", "DD-MM-YYYY"])
        self.dateFormatCard.hBoxLayout.addWidget(self.dateFormatComboBox, 0, Qt.AlignmentFlag.AlignRight)
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
        self.timeFormatCard.hBoxLayout.addWidget(self.timeFormatComboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.timeFormatCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        time_format = self.settings_manager.get('time_format', '24h')
        format_map = {'24h': 0, '12h': 1}
        self.timeFormatComboBox.setCurrentIndex(format_map.get(time_format, 0))
        
        # Connect signal
        self.timeFormatComboBox.currentIndexChanged.connect(self._on_time_format_changed)
        
        self.generalGroup.addSettingCard(self.timeFormatCard)
        
        # Language Setting
        self.languageCard = SettingCard(
            FluentIcon.LANGUAGE,
            "Language",
            "Choose your preferred interface language",
            parent=self.generalGroup
        )
        
        self.languageComboBox = ComboBox(self.languageCard)
        # Get available languages from language manager
        available_languages = self.lang_manager.get_available_languages()
        self.language_codes = list(available_languages.keys())
        self.languageComboBox.addItems(list(available_languages.values()))
        self.languageCard.hBoxLayout.addWidget(self.languageComboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.languageCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        current_language = self.settings_manager.get('language', DEFAULT_LANGUAGE)
        if current_language in self.language_codes:
            self.languageComboBox.setCurrentIndex(self.language_codes.index(current_language))
        
        # Connect signal
        self.languageComboBox.currentIndexChanged.connect(self._on_language_changed)
        
        self.generalGroup.addSettingCard(self.languageCard)
        
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
        self.autoUpdateCard.hBoxLayout.addWidget(self.updateFrequencyComboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.autoUpdateCard.hBoxLayout.addSpacing(16)
        
        # Set initial state
        frequency = self.settings_manager.get('auto_update_frequency', 'startup')
        frequency_map = {'startup': 0, 'manual': 1, 'automatic': 2}
        self.updateFrequencyComboBox.setCurrentIndex(frequency_map.get(frequency, 0))
        
        # Connect signal
        self.updateFrequencyComboBox.currentIndexChanged.connect(self._on_update_frequency_changed)
        
        self.updatesGroup.addSettingCard(self.autoUpdateCard)

        # --- Blocklist Settings Group ---
        self.blocklistGroup = SettingCardGroup("Blocklist", self.scrollWidget)
        
        # Blocklist management card
        self.blocklistCard = SettingCard(
            FluentIcon.CANCEL,
            "Blocking Programs",
            "Tasks are postponed when these programs are running (in Auto mode)",
            parent=self.blocklistGroup
        )
        
        # Add button to open blocklist dialog
        from qfluentwidgets import PushButton
        self.editBlocklistButton = PushButton("Edit List", self.blocklistCard)
        self.editBlocklistButton.clicked.connect(self._open_blocklist_dialog)
        self.blocklistCard.hBoxLayout.addWidget(self.editBlocklistButton, 0, Qt.AlignmentFlag.AlignRight)
        self.blocklistCard.hBoxLayout.addSpacing(16)
        
        self.blocklistGroup.addSettingCard(self.blocklistCard)
        
        # Scan for programs button
        self.scanBlocklistCard = SettingCard(
            FluentIcon.SEARCH,
            "Scan for Programs",
            "Detect installed games and IDEs to add to blocklist",
            parent=self.blocklistGroup
        )
        
        self.scanBlocklistButton = PushButton("Scan", self.scanBlocklistCard)
        self.scanBlocklistButton.clicked.connect(self._scan_for_programs)
        self.scanBlocklistCard.hBoxLayout.addWidget(self.scanBlocklistButton, 0, Qt.AlignmentFlag.AlignRight)
        self.scanBlocklistCard.hBoxLayout.addSpacing(16)
        
        self.blocklistGroup.addSettingCard(self.scanBlocklistCard)
        
        # Update program list button
        self.updateProgramListCard = SettingCard(
            FluentIcon.SYNC,
            "Update Program List",
            "Download latest games and apps database from the web",
            parent=self.blocklistGroup
        )
        
        self.updateProgramListButton = PushButton("Update", self.updateProgramListCard)
        self.updateProgramListButton.clicked.connect(self._update_program_list)
        self.updateProgramListCard.hBoxLayout.addWidget(self.updateProgramListButton, 0, Qt.AlignmentFlag.AlignRight)
        self.updateProgramListCard.hBoxLayout.addSpacing(16)
        
        self.blocklistGroup.addSettingCard(self.updateProgramListCard)
        
        # Clear blocklist button
        self.resetBlocklistCard = SettingCard(
            FluentIcon.DELETE,
            "Clear Blocklist",
            "Remove all programs from the blocklist",
            parent=self.blocklistGroup
        )
        
        self.resetBlocklistButton = PushButton("Clear", self.resetBlocklistCard)
        self.resetBlocklistButton.clicked.connect(self._reset_blocklist)
        self.resetBlocklistCard.hBoxLayout.addWidget(self.resetBlocklistButton, 0, Qt.AlignmentFlag.AlignRight)
        self.resetBlocklistCard.hBoxLayout.addSpacing(16)
        
        self.blocklistGroup.addSettingCard(self.resetBlocklistCard)
        
        # Add groups to layout
        self.expandLayout.addWidget(self.generalGroup)
        self.expandLayout.addWidget(self.updatesGroup)
        self.expandLayout.addWidget(self.blocklistGroup)
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
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

    def _on_pre_wake_changed(self, index: int):
        """Handle pre-wake duration change."""
        durations = [1, 3, 5, 10, 15]
        if 0 <= index < len(durations):
            duration = durations[index]
            self.settings_manager.set('pre_wake_minutes', duration)
            
            logger.info(f"Pre-wake duration set to: {duration} minutes")
            
            InfoBar.success(
                title="Settings Saved",
                content=f"Pre-wake duration: {duration} min",
                orient=Qt.Orientation.Horizontal,
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
                orient=Qt.Orientation.Horizontal,
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
                orient=Qt.Orientation.Horizontal,
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
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

    
    def _on_language_changed(self, index: int):
        """Handle language change."""
        if 0 <= index < len(self.language_codes):
            language_code = self.language_codes[index]
            self.settings_manager.set('language', language_code)
            
            # Update language manager
            set_language(language_code)
            
            logger.info(f"Language set to: {language_code}")
            
            # Reload UI text
            self.reload_ui_text()
            
            # Emit signal for other components
            self.language_changed.emit()
            
            # Get language display name
            lang_display = self.languageComboBox.currentText()
            
            InfoBar.success(
                title=self.lang_manager.get_text("settings.settings_saved"),
                content=self.lang_manager.format_text("settings.language_updated", language=lang_display),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
    
    def _open_blocklist_dialog(self):
        """Open dialog to edit blocklist."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QFileDialog
        from qfluentwidgets import PrimaryPushButton, PushButton, SubtitleLabel, BodyLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Blocking Programs")
        dialog.setMinimumSize(500, 450)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = SubtitleLabel("Programs that postpone task execution:")
        layout.addWidget(title)
        
        # Help text
        helpText = BodyLabel("When these programs are running, tasks will be postponed (Auto mode only).\nClick 'Browse' to add executables from your computer.")
        helpText.setWordWrap(True)
        layout.addWidget(helpText)
        
        # List widget
        self._blocklistWidget = QListWidget()
        self._blocklistWidget.setAlternatingRowColors(True)
        self._blocklistWidget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        
        # Load current blocklist (starts empty if not configured)
        current_list = self.settings_manager.get('blocklist_processes', [])
        
        for proc in sorted(current_list):
            item = QListWidgetItem(proc)
            self._blocklistWidget.addItem(item)
        
        layout.addWidget(self._blocklistWidget)
        
        # Button row: Browse / Remove
        actionLayout = QHBoxLayout()
        
        browseButton = PrimaryPushButton("Browse...")
        browseButton.clicked.connect(lambda: self._browse_for_executable(dialog))
        actionLayout.addWidget(browseButton)
        
        removeButton = PushButton("Remove Selected")
        removeButton.clicked.connect(self._remove_selected_blocklist_items)
        actionLayout.addWidget(removeButton)
        
        actionLayout.addStretch()
        layout.addLayout(actionLayout)
        
        # Save/Cancel buttons
        buttonLayout = QHBoxLayout()
        cancelButton = PushButton("Cancel")
        cancelButton.clicked.connect(dialog.reject)
        saveButton = PrimaryPushButton("Save")
        saveButton.clicked.connect(lambda: self._save_blocklist(dialog))
        
        buttonLayout.addStretch()
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(saveButton)
        layout.addLayout(buttonLayout)
        
        dialog.exec()
    
    def _browse_for_executable(self, parent_dialog):
        """Open file browser to select an executable."""
        from PyQt6.QtWidgets import QFileDialog, QListWidgetItem
        from pathlib import Path
        
        file_path, _ = QFileDialog.getOpenFileName(
            parent_dialog,
            "Select Executable",
            "",
            "Executables (*.exe);;All Files (*)"
        )
        
        if file_path:
            # Extract just the filename
            exe_name = Path(file_path).name
            
            # Check for duplicates
            existing = [self._blocklistWidget.item(i).text().lower() for i in range(self._blocklistWidget.count())]
            if exe_name.lower() not in existing:
                self._blocklistWidget.addItem(QListWidgetItem(exe_name))
            else:
                InfoBar.warning(
                    title="Duplicate",
                    content=f"{exe_name} is already in the list",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
    
    def _remove_selected_blocklist_items(self):
        """Remove selected items from blocklist."""
        for item in self._blocklistWidget.selectedItems():
            self._blocklistWidget.takeItem(self._blocklistWidget.row(item))
    
    def _save_blocklist(self, dialog):
        """Save the blocklist to settings."""
        processes = [self._blocklistWidget.item(i).text() for i in range(self._blocklistWidget.count())]
        self.settings_manager.set('blocklist_processes', processes)
        
        logger.info(f"Blocklist updated: {len(processes)} processes")
        
        InfoBar.success(
            title="Blocklist Saved",
            content=f"{len(processes)} programs in blocklist",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        dialog.accept()
    
    def _reset_blocklist(self):
        """Reset blocklist to empty."""
        self.settings_manager.set('blocklist_processes', [])
        
        logger.info("Blocklist cleared")
        
        InfoBar.success(
            title="Blocklist Cleared",
            content="Blocklist is now empty",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
    
    def _load_known_programs(self) -> dict:
        """Load known programs from JSON file (local or bundled)."""
        import json
        from pathlib import Path
        
        # Try loading from AppData first (updated version)
        appdata_path = Path(os.environ.get('APPDATA', '')) / 'c4n-AutoLauncher' / 'known_programs.json'
        
        if appdata_path.exists():
            try:
                with open(appdata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert list format to tuple format
                    return {k: tuple(v) for k, v in data.get('programs', {}).items()}
            except Exception as e:
                logger.warning(f"Failed to load AppData programs: {e}")
        
        # Fall back to bundled file
        bundled_path = Path(__file__).parent / 'known_programs.json'
        
        if bundled_path.exists():
            try:
                with open(bundled_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {k: tuple(v) for k, v in data.get('programs', {}).items()}
            except Exception as e:
                logger.warning(f"Failed to load bundled programs: {e}")
        
        # Return empty dict if nothing found
        logger.warning("No known_programs.json found")
        return {}
    
    def _update_program_list(self):
        """Download latest known_programs.json from GitHub."""
        import json
        import urllib.request
        from pathlib import Path
        
        # GitHub raw URL for the file
        GITHUB_URL = "https://raw.githubusercontent.com/Code4neverCompany/Code4never-AutoLauncher/main/known_programs.json"
        
        try:
            InfoBar.info(
                title="Updating...",
                content="Downloading latest program list",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            
            # Download the file
            with urllib.request.urlopen(GITHUB_URL, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Save to AppData
            appdata_dir = Path(os.environ.get('APPDATA', '')) / 'c4n-AutoLauncher'
            appdata_dir.mkdir(parents=True, exist_ok=True)
            
            appdata_path = appdata_dir / 'known_programs.json'
            with open(appdata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            program_count = len(data.get('programs', {}))
            version = data.get('version', 'unknown')
            
            logger.info(f"Updated known_programs.json to v{version} ({program_count} programs)")
            
            InfoBar.success(
                title="Update Complete",
                content=f"Downloaded {program_count} programs (v{version})",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            
        except urllib.error.URLError as e:
            logger.error(f"Failed to download program list: {e}")
            InfoBar.error(
                title="Update Failed",
                content="Could not connect to server",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
        except Exception as e:
            logger.error(f"Failed to update program list: {e}")
            InfoBar.error(
                title="Update Failed",
                content=str(e)[:50],
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
    
    def _scan_for_programs(self):
        """Scan for installed games and IDEs to suggest for blocklist."""
        from PyQt6.QtCore import QThread, pyqtSignal
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout, QGroupBox, QProgressBar
        from qfluentwidgets import PrimaryPushButton, PushButton, SubtitleLabel, BodyLabel, CheckBox
        from pathlib import Path
        import os
        import string
        
        # Load programs from JSON file (dynamic, can be updated)
        KNOWN_PROGRAMS = self._load_known_programs()
        
        if not KNOWN_PROGRAMS:
            InfoBar.warning(
                title="No Program List",
                content="Click 'Update' to download the program list first",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
        
        # Step 1: Show drive selection dialog
        driveDialog = QDialog(self)
        driveDialog.setWindowTitle("Select Drives to Scan")
        driveDialog.setMinimumWidth(350)
        
        driveLayout = QVBoxLayout(driveDialog)
        driveLayout.setSpacing(12)
        driveLayout.setContentsMargins(20, 20, 20, 20)
        
        driveLayout.addWidget(SubtitleLabel("Where should we look?"))
        driveLayout.addWidget(BodyLabel("Select the drives to scan for installed programs:"))
        
        # Detect available drives
        available_drives = []
        for letter in string.ascii_uppercase:
            drive_path = Path(f"{letter}:\\")
            if drive_path.exists():
                try:
                    next(drive_path.iterdir(), None)
                    available_drives.append(letter)
                except (PermissionError, OSError):
                    pass
        
        driveCheckboxes = {}
        driveGroup = QGroupBox("Available Drives")
        driveGroupLayout = QVBoxLayout(driveGroup)
        
        for drive in available_drives:
            cb = CheckBox(f"{drive}:\\ drive")
            if drive == 'C':
                cb.setChecked(True)
            driveCheckboxes[drive] = cb
            driveGroupLayout.addWidget(cb)
        
        driveLayout.addWidget(driveGroup)
        
        driveButtonLayout = QHBoxLayout()
        driveCancelBtn = PushButton("Cancel")
        driveCancelBtn.clicked.connect(driveDialog.reject)
        driveScanBtn = PrimaryPushButton("Scan Selected Drives")
        
        driveButtonLayout.addStretch()
        driveButtonLayout.addWidget(driveCancelBtn)
        driveButtonLayout.addWidget(driveScanBtn)
        driveLayout.addLayout(driveButtonLayout)
        
        selected_drives = []
        
        def start_scan():
            nonlocal selected_drives
            selected_drives = [d for d, cb in driveCheckboxes.items() if cb.isChecked()]
            if selected_drives:
                driveDialog.accept()
            else:
                InfoBar.warning(
                    title="No Drives Selected",
                    content="Please select at least one drive",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=driveDialog
                )
        
        driveScanBtn.clicked.connect(start_scan)
        
        if driveDialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Step 2: Show progress dialog with real progress bar
        progressDialog = QDialog(self)
        progressDialog.setWindowTitle("Scanning...")
        progressDialog.setFixedSize(320, 130)
        progressLayout = QVBoxLayout(progressDialog)
        progressLayout.setContentsMargins(20, 20, 20, 20)
        
        self._progressLabel = BodyLabel(f"Scanning {', '.join(selected_drives)}:\\ drives...")
        progressLayout.addWidget(self._progressLabel)
        
        self._progressBar = QProgressBar()
        self._progressBar.setMinimum(0)
        self._progressBar.setMaximum(100)
        self._progressBar.setValue(0)
        self._progressBar.setTextVisible(True)
        self._progressBar.setFormat("%p% - %v of %m programs checked")
        progressLayout.addWidget(self._progressBar)
        
        # Scanner thread with progress reporting
        class ScannerThread(QThread):
            finished = pyqtSignal(list)
            progress = pyqtSignal(int, int, str)  # current, total, current_exe
            
            def __init__(self, known_progs, current_list, drives):
                super().__init__()
                self.known_programs = known_progs
                self.current_lower = [p.lower() for p in current_list]
                self.drives = drives
                
            def run(self):
                found = []
                scan_dirs = []
                
                for drive in self.drives:
                    scan_dirs.extend([
                        Path(f"{drive}:\\Program Files"),
                        Path(f"{drive}:\\Program Files (x86)"),
                        Path(f"{drive}:\\Games"),
                        Path(f"{drive}:\\SteamLibrary"),
                        Path(f"{drive}:\\Epic Games"),
                    ])
                
                local_appdata = os.environ.get('LOCALAPPDATA', '')
                if local_appdata:
                    scan_dirs.append(Path(local_appdata) / "Programs")
                
                # Filter to existing directories
                scan_dirs = [d for d in scan_dirs if d.exists()]
                
                exe_list = list(self.known_programs.keys())
                total = len(exe_list)
                
                for idx, exe_name in enumerate(exe_list):
                    self.progress.emit(idx + 1, total, exe_name)
                    
                    if exe_name.lower() in self.current_lower:
                        continue
                    if exe_name in [f[0] for f in found]:
                        continue
                    
                    for scan_dir in scan_dirs:
                        try:
                            # Quick search with limited depth
                            for depth in range(1, 4):
                                pattern = '/'.join(['*'] * depth) + '/' + exe_name
                                if list(scan_dir.glob(pattern)):
                                    found.append((exe_name, self.known_programs[exe_name]))
                                    break
                        except Exception:
                            pass
                
                self.finished.emit(found)
        
        current_blocklist = self.settings_manager.get('blocklist_processes', [])
        self._scanThread = ScannerThread(KNOWN_PROGRAMS, current_blocklist, selected_drives)
        
        def update_progress(current, total, exe_name):
            self._progressBar.setMaximum(total)
            self._progressBar.setValue(current)
            # Show short name
            short_name = exe_name[:20] + "..." if len(exe_name) > 20 else exe_name
            self._progressLabel.setText(f"Checking: {short_name}")
        
        def on_scan_complete(found_programs):
            progressDialog.close()
            
            if found_programs:
                by_category = {'Game': [], 'IDE': [], 'Productivity': []}
                for exe, (name, category) in found_programs:
                    by_category[category].append((exe, name))
                
                dialog = QDialog(self)
                dialog.setWindowTitle("Found Programs")
                dialog.setMinimumSize(450, 420)
                
                layout = QVBoxLayout(dialog)
                layout.setSpacing(12)
                layout.setContentsMargins(20, 20, 20, 20)
                
                title = SubtitleLabel(f"Found {len(found_programs)} programs")
                layout.addWidget(title)
                
                helpText = BodyLabel("These programs will postpone tasks when running.\nSelect which ones to add:")
                helpText.setWordWrap(True)
                layout.addWidget(helpText)
                
                listWidget = QListWidget()
                listWidget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
                
                category_icons = {'Game': '🎮', 'IDE': '💻', 'Productivity': '📊'}
                for category in ['Game', 'IDE', 'Productivity']:
                    if by_category[category]:
                        header = QListWidgetItem(f"─── {category_icons[category]} {category}s ({len(by_category[category])}) ───")
                        header.setFlags(header.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                        listWidget.addItem(header)
                        
                        for exe, name in sorted(by_category[category], key=lambda x: x[1]):
                            item = QListWidgetItem(f"    {name}")
                            item.setData(Qt.ItemDataRole.UserRole, exe)
                            item.setSelected(True)
                            listWidget.addItem(item)
                
                layout.addWidget(listWidget)
                
                buttonLayout = QHBoxLayout()
                cancelBtn = PushButton("Cancel")
                cancelBtn.clicked.connect(dialog.reject)
                addBtn = PrimaryPushButton("Add Selected")
                
                def add_selected():
                    selected = [item.data(Qt.ItemDataRole.UserRole) for item in listWidget.selectedItems() if item.data(Qt.ItemDataRole.UserRole)]
                    if selected:
                        updated_list = current_blocklist + selected
                        self.settings_manager.set('blocklist_processes', updated_list)
                        InfoBar.success(
                            title="Programs Added",
                            content=f"Added {len(selected)} programs",
                            orient=Qt.Orientation.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=2000,
                            parent=self
                        )
                    dialog.accept()
                
                addBtn.clicked.connect(add_selected)
                buttonLayout.addStretch()
                buttonLayout.addWidget(cancelBtn)
                buttonLayout.addWidget(addBtn)
                layout.addLayout(buttonLayout)
                
                dialog.exec()
            else:
                InfoBar.info(
                    title="No Programs Found",
                    content="No known games, IDEs, or productivity apps detected",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
        
        self._scanThread.progress.connect(update_progress)
        self._scanThread.finished.connect(on_scan_complete)
        self._scanThread.start()
        progressDialog.exec()
    
    def reload_ui_text(self):
        """Reload all UI text with current language."""
        lang = self.lang_manager
        
        # Update group titles
        self.generalGroup.titleLabel.setText(lang.get_text("settings.general"))
        self.updatesGroup.titleLabel.setText(lang.get_text("settings.updates"))
        
        # Update Execution Mode card
        self.executionModeCard.titleLabel.setText(lang.get_text("settings.execution_mode"))
        self.executionModeCard.contentLabel.setText(lang.get_text("settings.execution_mode_desc"))
        self.modeComboBox.clear()
        self.modeComboBox.addItems([
            lang.get_text("settings.execution_mode_auto"),
            lang.get_text("settings.execution_mode_ask"),
            lang.get_text("settings.execution_mode_run")
        ])
        # Restore selection
        mode = self.settings_manager.get('execution_mode', 'ask')
        mode_map = {'auto': 0, 'ask': 1, 'run': 2}
        self.modeComboBox.setCurrentIndex(mode_map.get(mode, 1))
        
        # Update Pre-wake card
        self.preWakeCard.titleLabel.setText(lang.get_text("settings.pre_wake"))
        self.preWakeCard.contentLabel.setText(lang.get_text("settings.pre_wake_desc"))
        # Note: ComboBox items are numbers, so translation might not be strictly needed unless we add "minutes" text dynamically
        # For now, we keep them hardcoded or we could rebuild the list.
        # Let's rebuild to be safe if we want to translate "minute(s)"
        self.preWakeComboBox.clear()
        self.preWakeComboBox.addItems([
            f"1 {lang.get_text('settings.minute')}",
            f"3 {lang.get_text('settings.minutes')}",
            f"5 {lang.get_text('settings.minutes')}",
            f"10 {lang.get_text('settings.minutes')}",
            f"15 {lang.get_text('settings.minutes')}"
        ])
        pre_wake = self.settings_manager.get('pre_wake_minutes', 5)
        pre_wake_map = {1: 0, 3: 1, 5: 2, 10: 3, 15: 4}
        self.preWakeComboBox.setCurrentIndex(pre_wake_map.get(pre_wake, 2))
        
        # Update Date Format card
        self.dateFormatCard.titleLabel.setText(lang.get_text("settings.date_format"))
        self.dateFormatCard.contentLabel.setText(lang.get_text("settings.date_format_desc"))
        
        # Update Time Format card
        self.timeFormatCard.titleLabel.setText(lang.get_text("settings.time_format"))
        self.timeFormatCard.contentLabel.setText(lang.get_text("settings.time_format_desc"))
        self.timeFormatComboBox.clear()
        self.timeFormatComboBox.addItems([
            lang.get_text("settings.time_format_24h"),
            lang.get_text("settings.time_format_12h")
        ])
        # Restore selection
        time_format = self.settings_manager.get('time_format', '24h')
        format_map = {'24h': 0, '12h': 1}
        self.timeFormatComboBox.setCurrentIndex(format_map.get(time_format, 0))
        
        # Update Language card
        self.languageCard.titleLabel.setText(lang.get_text("settings.language"))
        self.languageCard.contentLabel.setText(lang.get_text("settings.language_desc"))
        
        # Update Auto-Update card
        self.autoUpdateCard.titleLabel.setText(lang.get_text("settings.auto_update_mode"))
        self.autoUpdateCard.contentLabel.setText(lang.get_text("settings.auto_update_mode_desc"))
        self.updateFrequencyComboBox.clear()
        self.updateFrequencyComboBox.addItems([
            lang.get_text("settings.auto_update_startup"),
            lang.get_text("settings.auto_update_manual"),
            lang.get_text("settings.auto_update_automatic")
        ])
        # Restore selection
        frequency = self.settings_manager.get('auto_update_frequency', 'startup')
        frequency_map = {'startup': 0, 'manual': 1, 'automatic': 2}
        self.updateFrequencyComboBox.setCurrentIndex(frequency_map.get(frequency, 0))
        
        logger.debug("UI text reloaded for new language")
