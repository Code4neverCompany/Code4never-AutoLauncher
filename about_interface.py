"""
About Interface Module
Displays application version information, changelog, and update controls.

© 2025 4never Company. All rights reserved.
"""

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from qfluentwidgets import (
    ScrollArea,
    SettingCardGroup,
    PrimaryPushSettingCard,
    HyperlinkCard,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    ExpandSettingCard,
    MessageBox,
    ProgressBar
)
from update_manager import UpdateManager
from logger import get_logger

logger = get_logger(__name__)


class UpdateDownloadThread(QThread):
    """Thread for downloading updates without blocking UI."""
    
    progress = Signal(int, int)  # downloaded, total
    finished = Signal(str)  # download_path
    error = Signal(str)  # error_message
    
    def __init__(self, update_manager, asset):
        super().__init__()
        self.update_manager = update_manager
        self.asset = asset
    
    def run(self):
        """Download the update."""
        try:
            def progress_callback(downloaded, total):
                self.progress.emit(downloaded, total)
            
            download_path = self.update_manager.download_update(
                self.asset,
                progress_callback
            )
            
            if download_path:
                self.finished.emit(download_path)
            else:
                self.error.emit("Download failed. Please try again.")
        except Exception as e:
            self.error.emit(f"Download error: {str(e)}")


class AboutInterface(ScrollArea):
    """
    About interface with version info and automatic update support.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.update_manager = UpdateManager()
        self.download_thread = None
        
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        
        # Set object name for styling
        self.setObjectName("aboutInterface")
        self.scrollWidget.setObjectName("scrollWidget")
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        
        # Configure layout
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # Set transparent background
        self.scrollWidget.setStyleSheet("QWidget{background-color: transparent;}")
        self.setStyleSheet("QScrollArea{background-color: transparent; border: none;}")
        
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        
        # --- About Group ---
        self.aboutGroup = SettingCardGroup("About", self.scrollWidget)
        
        # Version Card
        version = self.update_manager.get_current_version()
        mode = "Executable" if self.update_manager.is_executable else "Development Mode"
        
        self.checkUpdateCard = PrimaryPushSettingCard(
            "Check for Updates",
            FluentIcon.UPDATE,
            "Current Version",
            f"v{version} ({mode})",
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
        self.checkUpdateCard.button.setText("Checking...")
        
        # Check for updates
        update_info, error_msg = self.update_manager.check_for_updates()
        
        self.checkUpdateCard.setEnabled(True)
        self.checkUpdateCard.button.setText("Check for Updates")
        
        if error_msg:
            # Error occurred
            InfoBar.error(
                title="Update Check Failed",
                content=error_msg,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
        elif update_info:
            # Update available
            self._show_update_dialog(update_info)
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
    
    def _show_update_dialog(self, update_info):
        """Show dialog with update information and options."""
        version = update_info['version']
        can_auto_update = update_info.get('can_auto_update', False)
        
        if can_auto_update:
            # Can download and install automatically
            title = "Update Available"
            content = f"Version {version} is available!\n\nWould you like to download and install it now?\nThe application will restart after installation."
            
            w = MessageBox(title, content, self.window())
            w.yesButton.setText("Download & Install")
            w.cancelButton.setText("Later")
            
            if w.exec():
                self._download_and_install_update(update_info)
        else:
            # Manual download required (running as Python or no .exe asset)
            title = "Update Available"
            content = f"Version {version} is available!\n\nClick OK to visit the download page."
            
            w = MessageBox(title, content, self.window())
            w.cancelButton.hide()
            
            if w.exec():
                self.update_manager.open_download_page(update_info['url'])
    
    def _download_and_install_update(self, update_info):
        """Download and install an update."""
        exe_asset = update_info.get('exe_asset')
        if not exe_asset:
            InfoBar.error(
                title="Download Error",
                content="No executable found in release assets.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
            return
        
        # Show progress
        self.progress_bar = InfoBar.new(
            icon=FluentIcon.DOWNLOAD,
            title="Downloading Update",
            content="Preparing download...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=-1,  # Persistent
            parent=self.window()
        )
        
        # Start download in background thread
        self.download_thread = UpdateDownloadThread(self.update_manager, exe_asset)
        self.download_thread.progress.connect(self._on_download_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()
        
        logger.info("Starting update download...")
    
    def _on_download_progress(self, downloaded, total):
        """Update progress bar during download."""
        if total > 0:
            percent = int((downloaded / total) * 100)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            
            self.progress_bar.setContent(
                f"Downloaded {mb_downloaded:.1f} MB / {mb_total:.1f} MB ({percent}%)"
            )
    
    def _on_download_finished(self, download_path):
        """Handle successful download."""
        self.progress_bar.close()
        
        logger.info(f"Download complete: {download_path}")
        
        # Ask for confirmation to install
        w = MessageBox(
            "Ready to Install",
            "Update downloaded successfully!\n\nThe application will close and restart to install the update.\n\nContinue?",
            self.window()
        )
        w.yesButton.setText("Install Now")
        w.cancelButton.setText("Later")
        
        if w.exec():
            # Install and restart
            logger.info("Installing update...")
            if self.update_manager.install_update_and_restart(download_path):
                # Close the application (the batch script will restart it)
                QApplication.quit()
            else:
                InfoBar.error(
                    title="Installation Failed",
                    content="Could not install update. Please try manually.",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=5000,
                    parent=self
                )
    
    def _on_download_error(self, error_msg):
        """Handle download error."""
        self.progress_bar.close()
        
        logger.error(f"Download error: {error_msg}")
        
        InfoBar.error(
            title="Download Failed",
            content=error_msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000,
            parent=self
        )
