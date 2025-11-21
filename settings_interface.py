"""
Settings Interface Module
Displays application settings, version information, and update controls.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import (
    ScrollArea,
    SettingCardGroup,
    PrimaryPushSettingCard,
    HyperlinkCard,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    ExpandSettingCard
)
from update_manager import UpdateManager

class SettingsInterface(ScrollArea):
    """
    Settings interface with version info and update checking.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.update_manager = UpdateManager()
        
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
        
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        
        # --- About Group ---
        self.aboutGroup = SettingCardGroup("About", self.scrollWidget)
        
        # Version Card
        version = self.update_manager.get_current_version()
        self.checkUpdateCard = PrimaryPushSettingCard(
            "Check for Updates",
            FluentIcon.UPDATE,
            "Current Version",
            f"v{version}",
            self.aboutGroup
        )
        self.checkUpdateCard.clicked.connect(self._check_for_updates)
        
        # GitHub Link Card
        self.githubCard = HyperlinkCard(
            "https://github.com/Code4neverCompany/Code4never-AutoLauncher_AlphaVersion",
            "Open GitHub Repository",
            FluentIcon.GITHUB,
            "Source Code",
            "Report bugs or request features",
            self.aboutGroup
        )
        
        self.aboutGroup.addSettingCard(self.checkUpdateCard)
        self.aboutGroup.addSettingCard(self.githubCard)
        
        # --- Changelog Group ---
        self.changelogGroup = SettingCardGroup("What's New", self.scrollWidget)
        
        # Populate Changelog
        changelog = self.update_manager.get_changelog()
        for entry in changelog:
            version_num = entry.get('version', 'Unknown')
            date = entry.get('date', '')
            changes = entry.get('changes', [])
            
            # Create formatted text for changes
            changes_text = "\n".join([f"• {change}" for change in changes])
            
            card = ExpandSettingCard(
                FluentIcon.INFO,
                f"Version {version_num}",
                f"Released on {date}",
                self.changelogGroup
            )
            
            # Add a label with the changes inside the card
            label = QLabel(changes_text)
            label.setWordWrap(True)
            label.setContentsMargins(20, 10, 20, 10)
            # Basic styling to make it readable
            label.setStyleSheet("color: #666; font-size: 14px;") 
            
            card.viewLayout.addWidget(label)
            self.changelogGroup.addSettingCard(card)
            
        
        # Add groups to layout
        self.expandLayout.addWidget(self.aboutGroup)
        self.expandLayout.addWidget(self.changelogGroup)
        self.expandLayout.addStretch(1)
        
    def _check_for_updates(self):
        """Check for updates and notify user."""
        self.checkUpdateCard.setEnabled(False)
        self.checkUpdateCard.setText("Checking...")
        
        # Use a timer or thread in real app to avoid freezing, 
        # but for now we'll do it synchronously for simplicity as requested
        update_info = self.update_manager.check_for_updates()
        
        self.checkUpdateCard.setEnabled(True)
        self.checkUpdateCard.setText("Check for Updates")
        
        if update_info:
            # Update available
            InfoBar.success(
                title="Update Available",
                content=f"Version {update_info['version']} is available!",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
            # Open download link
            self.update_manager.open_download_page(update_info['url'])
        else:
            # Up to date
            InfoBar.info(
                title="Up to Date",
                content="You are using the latest version.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
