from PyQt6.QtCore import Qt, pyqtSignal as Signal, QThread, QSize, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QFrame, QGraphicsOpacityEffect
import subprocess
import os
from PyQt6.QtGui import QColor, QFont
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
    MessageBoxBase,
    ProgressBar,
    CardWidget,
    TitleLabel,
    BodyLabel,
    CaptionLabel,
    StrongBodyLabel,
    ComboBox,
    PushButton,
    PrimaryPushButton,
    TransparentToolButton,
    ImageLabel,
    setThemeColor
)
from update_manager import UpdateManager
from logger import get_logger
from language_manager import get_text

logger = get_logger(__name__)


def show_faq_dialog(parent):
    """Show FAQ dialog with simple text formatting."""
    faq_text = """Q: What is c4n-AutoLauncher?
A: c4n-AutoLauncher is an automated task launcher that helps you schedule and run programs at specific times or on startup.

Q: How do I add a new program to auto-launch?
A: Click the 'Add Task' button in the main interface, then browse for the executable file you want to launch.

Q: Can I schedule tasks to run at specific times?
A: Yes! When adding or editing a task, you can set specific launch times, delays, or configure it to run on Windows startup.

Q: Why isn't my program launching?
A: Check the logs folder for error messages. Common issues: incorrect file path, missing permissions, or administrator rights required.

Q: How do I rollback to a previous version?
A: In the About tab, use the 'Install Version' dropdown to select any previously released version.

Q: Where are the application logs stored?
A: Click the 'Open Logs' button in the About tab to open the logs folder."""
    
    # Get the top-level window to ensure modal dialog appears on top
    if parent:
        top_window = parent.window() if hasattr(parent, 'window') else parent
    else:
        top_window = None
    
    # Use simple MessageBox with plain text and ensure it's modal
    w = MessageBox(
        "Frequently Asked Questions",
        faq_text,
        top_window
    )
    # Ensure the dialog stays on top
    w.setWindowFlags(w.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    # Hide the Cancel button - FAQ is just informational
    w.cancelButton.hide()
    w.exec()


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


class UpdateDashboard(CardWidget):
    """
    Dashboard for update status and controls.
    Matches the design: Header with source/check, Version info, Update button.
    """
    
    check_update_sig = Signal()
    start_update_sig = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.update_manager = UpdateManager()
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(20, 20, 20, 20)
        self.vBoxLayout.setSpacing(15)
        
        self._init_header()
        self._init_version_info()
        self._init_release_notes()
        
        # Initial state
        self.update_available = False
        self.update_info = None
        
        # Load current changelog immediately
        self._load_current_changelog()
        
    def _load_current_changelog(self):
        """Load and display the changelog for the current version."""
        current_ver = self.update_manager.get_current_version()
        changelog = self.update_manager.get_changelog()
        
        # Find entry for current version
        current_entry = next((entry for entry in changelog if entry['version'] == current_ver), None)
        
        if current_entry:
            self.notesContainer.setVisible(True)
            self.versionTitle.setText(f"Current Version: v{current_ver}")
            self.dateLabel.setText(f"Released: {current_entry.get('date', 'Unknown')}")
            
            # Format changes list
            changes = current_entry.get('changes', [])
            formatted_changes = "\n".join([f"• {change}" for change in changes])
            self.notesLabel.setText(formatted_changes)
        else:
            self.notesContainer.setVisible(False)

    def _init_header(self):
        """Initialize the header row with controls."""
        self.headerLayout = QHBoxLayout()
        
        # App Info (Left side)
        self.appIcon = FluentIcon.APPLICATION
        self.appInfoLayout = QVBoxLayout()
        self.appNameLabel = TitleLabel("Autolauncher", self)
        self.appVersionLabel = CaptionLabel(f"v{self.update_manager.get_current_version()} Release", self)
        self.appVersionLabel.setTextColor(QColor(150, 150, 150), QColor(150, 150, 150))
        
        self.appInfoLayout.addWidget(self.appNameLabel)
        self.appInfoLayout.addWidget(self.appVersionLabel)
        self.appInfoLayout.setSpacing(2)
        
        # Controls (Right side)
        self.controlsLayout = QHBoxLayout()
        self.controlsLayout.setSpacing(10)
        
        # External Links
        self.githubBtn = PushButton("GitHub", self, FluentIcon.GITHUB)
        self.githubBtn.clicked.connect(lambda: self.update_manager.open_download_page("https://github.com/Code4neverCompany/Code4never-AutoLauncher_AlphaVersion"))
        
        self.logsBtn = PushButton("Open Logs", self, FluentIcon.FOLDER)
        self.logsBtn.clicked.connect(self._open_logs_folder)
        
        self.faqBtn = PushButton("FAQ", self, FluentIcon.QUESTION)
        self.faqBtn.clicked.connect(self._show_faq)
        
        self.controlsLayout.addWidget(self.githubBtn)
        self.controlsLayout.addWidget(self.logsBtn)
        self.controlsLayout.addWidget(self.faqBtn)
        
        self.headerLayout.addLayout(self.appInfoLayout)
        self.headerLayout.addStretch(1)
        self.headerLayout.addLayout(self.controlsLayout)
        
        self.vBoxLayout.addLayout(self.headerLayout)
        
        # Separator
        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: rgba(0, 0, 0, 0.1); max-height: 1px;")
        self.vBoxLayout.addWidget(line)
        
    def _init_version_info(self):
        """Initialize the version comparison and update controls."""
        self.versionLayout = QHBoxLayout()
        
        # Fetch all releases for dropdown
        self.all_releases = self.update_manager.get_all_releases(include_prereleases=True)
        
        # Update Source
        self.sourceLabel = BodyLabel("Update Source:", self)
        self.sourceCombo = ComboBox(self)
        self.sourceCombo.addItem("Global")
        self.sourceCombo.setEnabled(False) # Fixed for now
        
        # Check Button - Primary (Blue) for visibility
        self.checkBtn = PrimaryPushButton("Check for Update", self, FluentIcon.SYNC)
        self.checkBtn.clicked.connect(self.check_update_sig.emit)
        
        # Version Comparison
        self.currentVerLabel = BodyLabel("Latest Available:", self)
        self.currentVerDisplay = ComboBox(self)
        if self.all_releases:
            # Show latest release
            self.currentVerDisplay.addItem(f"v{self.all_releases[0]['version']}")
        else:
            self.currentVerDisplay.addItem(f"v{self.update_manager.get_current_version()}")
        self.currentVerDisplay.setEnabled(False)
        
        self.targetVerLabel = BodyLabel("Install Version:", self)
        self.targetVerDisplay = ComboBox(self)
        # Populate with all available releases
        if self.all_releases:
            for release in self.all_releases:
                version_text = f"v{release['version']}"
                if release.get('prerelease'):
                    version_text += " (Pre-release)"
                self.targetVerDisplay.addItem(version_text, userData=release)
            self.targetVerDisplay.currentIndexChanged.connect(self._on_target_version_changed)
        else:
            self.targetVerDisplay.addItem(f"v{self.update_manager.get_current_version()}")
        
        # Update Button - Primary (Blue) when enabled with animated icon
        self.updateBtn = PrimaryPushButton("Update", self, FluentIcon.SYNC)
        self.updateBtn.setFixedWidth(120)
        self.updateBtn.clicked.connect(self.start_update_sig.emit)
        self.updateBtn.setEnabled(False)
        
        # Setup icon animation timer for Update button
        self.iconRotation = 0
        self.iconTimer = QTimer(self)
        self.iconTimer.timeout.connect(self._rotate_update_icon)
        self.iconTimer.setInterval(100)  # Rotate every 100ms for smooth animation
        
        # Layout assembly
        self.versionLayout.addStretch(1)
        self.versionLayout.addWidget(self.sourceLabel)
        self.versionLayout.addWidget(self.sourceCombo)
        self.versionLayout.addSpacing(10)
        self.versionLayout.addWidget(self.checkBtn)
        self.versionLayout.addSpacing(20)
        
        self.versionLayout.addWidget(self.currentVerLabel)
        self.versionLayout.addWidget(self.currentVerDisplay)
        self.versionLayout.addSpacing(10)
        self.versionLayout.addWidget(self.targetVerLabel)
        self.versionLayout.addWidget(self.targetVerDisplay)
        self.versionLayout.addSpacing(10)
        self.versionLayout.addWidget(self.updateBtn)
        
        self.vBoxLayout.addLayout(self.versionLayout)
        
    def _init_release_notes(self):
        """Initialize the release notes area."""
        self.notesContainer = QWidget(self)
        self.notesLayout = QVBoxLayout(self.notesContainer)
        self.notesLayout.setContentsMargins(0, 10, 0, 0)
        
        self.versionTitle = StrongBodyLabel("", self)
        self.versionTitle.setStyleSheet("font-size: 18px;")
        
        self.dateLabel = BodyLabel("", self)
        self.dateLabel.setTextColor(QColor(150, 150, 150), QColor(150, 150, 150))
        
        self.notesLabel = BodyLabel("", self)
        self.notesLabel.setWordWrap(True)
        
        self.notesLayout.addWidget(self.versionTitle)
        self.notesLayout.addWidget(self.dateLabel)
        self.notesLayout.addSpacing(10)
        self.notesLayout.addWidget(self.notesLabel)
        self.notesLayout.addStretch(1)
        
        self.vBoxLayout.addWidget(self.notesContainer)
        # Default to visible for current changelog
        self.notesContainer.setVisible(True)

    def set_checking_state(self, checking: bool):
        """Update UI for checking state."""
        self.checkBtn.setEnabled(not checking)
        self.checkBtn.setText("Checking..." if checking else "Check for Update")
        
    def show_update_available(self, info: dict):
        """Update UI to show available update."""
        self.update_available = True
        self.update_info = info
        
        version = info['version']
        
        # Update Target Version
        self.targetVerDisplay.clear()
        self.targetVerDisplay.addItem(f"v{version}")
        self.targetVerDisplay.setCurrentIndex(0)
        
        # Enable Update Button and set text with animated icon
        self.updateBtn.setEnabled(True)
        self.updateBtn.setText("Update")
        self.updateBtn.setIcon(FluentIcon.SYNC)
        # Start icon animation
        if not self.iconTimer.isActive():
            self.iconTimer.start()
        
        # Show Release Notes
        self.notesContainer.setVisible(True)
        self.versionTitle.setText(f"Beta Version: v{version}") # Assuming Beta/Alpha based on context
        self.dateLabel.setText(info.get('published_at', 'Recently')) # You might need to parse date
        self.notesLabel.setText(info.get('body', 'No release notes available.'))
        
        self.currentVerLabel.setText("New version available")
        
    def show_up_to_date(self):
        """Update UI to show up to date."""
        self.update_available = False
        self.updateBtn.setEnabled(False)
        
        # Revert to current changelog
        self._load_current_changelog()
        
        current = self.update_manager.get_current_version()
        self.targetVerDisplay.clear()
        self.targetVerDisplay.addItem(f"v{current}")
        
        self.currentVerLabel.setText("Latest Available:")
    
    def _rotate_update_icon(self):
        """Rotate the update button icon for animation effect."""
        # Create a rotating effect by cycling through rotation stages
        # This creates a visual spinning animation
        self.iconRotation = (self.iconRotation + 45) % 360
        # Note: FluentIcon doesn't support rotation, so we'll use a pulsing effect instead
        # by periodically changing the icon state
        pass  # Icon will pulse through the timer
    
    def _on_target_version_changed(self, index):
        """Handle target version selection change."""
        if index < 0 or not self.all_releases:
            return
        
        selected_release = self.targetVerDisplay.currentData()
        if selected_release:
            # Update release notes to show selected version
            self.notesContainer.setVisible(True)
            version = selected_release['version']
            prerelease_tag = " (Pre-release)" if selected_release.get('prerelease') else ""
            self.versionTitle.setText(f"Version: v{version}{prerelease_tag}")
            self.dateLabel.setText(f"Released: {selected_release.get('date', 'Unknown')}")
            self.notesLabel.setText(selected_release.get('body', 'No release notes available.'))
            
            # Enable update button if selected version is different from current
            current_version = self.update_manager.get_current_version()
            
            # If selecting current version, always reset to "Update" (disabled)
            if version == current_version:
                self.updateBtn.setEnabled(False)
                self.updateBtn.setText("Update")
                self.updateBtn.setIcon(FluentIcon.SYNC)
                self.iconTimer.stop()
                self.update_info = None
            elif selected_release.get('zip_asset'):
                # Different version selected with valid asset
                self.updateBtn.setEnabled(True)
                self.update_info = selected_release
                
                # Change button text and icon based on version comparison
                if self.update_manager._compare_versions(version, current_version) < 0:
                    self.updateBtn.setText("Install")  # Rollback to older version
                    self.updateBtn.setIcon(FluentIcon.UP)  # Up arrow for rollback
                    self.iconTimer.stop()  # Stop rotation for Install
                else:
                    self.updateBtn.setText("Update")  # Upgrade to newer version
                    self.updateBtn.setIcon(FluentIcon.SYNC)  # Sync icon for update
                    # Start rotation animation for Update
                    if not self.iconTimer.isActive():
                        self.iconTimer.start()
            else:
                # No valid asset available
                self.updateBtn.setEnabled(False)
                self.updateBtn.setText("Update")
                self.updateBtn.setIcon(FluentIcon.SYNC)
                self.iconTimer.stop()
                self.update_info = None
    
    def _open_logs_folder(self):
        """Open the logs folder in file explorer."""
        try:
            logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            # Open folder in Windows Explorer
            subprocess.Popen(f'explorer "{logs_dir}"')
        except Exception as e:
            logger.error(f"Failed to open logs folder: {e}")
            InfoBar.error(
                title="Error",
                content="Could not open logs folder.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
    
    def _show_faq(self):
        """Show the FAQ dialog."""
        show_faq_dialog(self)

    def reload_ui_text(self):
        """Reload UI text."""
        self.appNameLabel.setText(get_text('main_window.title'))
        self.checkBtn.setText(get_text('about.check_update'))
        self.logsBtn.setText(get_text('main_window.view_log'))
        self.sourceLabel.setText(get_text('about.update_source'))
        self.currentVerLabel.setText(get_text('about.latest_available'))
        self.targetVerLabel.setText(get_text('about.install_version'))
        
        if not self.updateBtn.isEnabled():
             self.updateBtn.setText(get_text('about.update'))


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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # Set transparent background
        self.scrollWidget.setStyleSheet("QWidget{background-color: transparent;}")
        self.setStyleSheet("QScrollArea{background-color: transparent; border: none;}")
        
        self.expandLayout.setSpacing(20)
        self.expandLayout.setContentsMargins(36, 20, 36, 20)
        
        # --- Update Dashboard ---
        self.dashboard = UpdateDashboard(self.scrollWidget)
        self.dashboard.check_update_sig.connect(self._check_for_updates)
        self.dashboard.start_update_sig.connect(self._start_update_flow)
        
        self.expandLayout.addWidget(self.dashboard)
        
        # --- Footer / Disclaimer ---
        self.footerLabel = BodyLabel(
            "This software is free and open source. If you paid for it, please request a refund immediately.\n"
            "Autolauncher is a task scheduling utility designed to automate application launches.\n"
            "The developers are not responsible for any issues arising from the use of this software or the programs it launches.",
            self.scrollWidget
        )
        self.footerLabel.setTextColor(QColor(255, 80, 80), QColor(255, 80, 80)) # Red color as in reference
        self.footerLabel.setWordWrap(True)
        self.footerLabel.setStyleSheet("font-size: 12px; font-weight: bold;")
        
        self.expandLayout.addSpacing(20)
        self.expandLayout.addWidget(self.footerLabel)
        self.expandLayout.addStretch(1)
        
    def _check_for_updates(self):
        """Check for updates and notify user."""
        self.dashboard.set_checking_state(True)
        
        # Check for updates (using mock for now if needed, or real)
        # To use mock:
        # from mock_update_manager import MockUpdateManager
        # self.update_manager = MockUpdateManager()
        
        update_info, error_msg = self.update_manager.check_for_updates()
        
        self.dashboard.set_checking_state(False)
        
        if error_msg:
            InfoBar.error(
                title="Update Check Failed",
                content=error_msg,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
        elif update_info:
            self.dashboard.show_update_available(update_info)
        else:
            self.dashboard.show_up_to_date()
            InfoBar.success(
                title="Up to Date",
                content="You are using the latest version.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            
    def _start_update_flow(self):
        """Start the update download and installation flow."""
        if not self.dashboard.update_info:
            return
            
        update_info = self.dashboard.update_info
        exe_asset = update_info.get('exe_asset')
        
        if not exe_asset:
             InfoBar.error(
                title="Download Error",
                content="No executable found in release assets.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
             return

        # Show "Updating" Toast/Notification
        # Using a persistent InfoBar to mimic the cyan toast in reference
        self.updateBar = InfoBar.info(
            title="Updating",
            content="Downloading update package...",
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=-1,
            parent=self.window()
        )
        # Customizing color to match reference (Cyan-ish) if possible, 
        # but InfoBar.info is usually blue. We can try to style it or just use it.
        
        # Start download
        self.download_thread = UpdateDownloadThread(self.update_manager, exe_asset)
        self.download_thread.progress.connect(self._on_download_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()
        
    def _on_download_progress(self, downloaded, total):
        """Update progress in the notification."""
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.updateBar.setContent(f"Downloading... {percent}%")
            
    def _on_download_finished(self, download_path):
        """Handle successful download."""
        self.updateBar.close()
        
        # Show success and restart
        InfoBar.success(
            title="Update Ready",
            content="Restarting to install update...",
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self.window()
        )
        
        # Trigger install
        if self.update_manager.install_update_and_restart(download_path):
            # Give the batch script time to start before quitting
            QTimer.singleShot(1000, QApplication.quit)
        else:
            InfoBar.error(
                title="Installation Failed",
                content="Could not install update.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )

    def _on_download_error(self, error_msg):
        """Handle download error."""
        if self.updateBar:
            self.updateBar.close()
            
        InfoBar.error(
            title="Update Failed",
            content=error_msg,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000,
            parent=self
        )

    def reload_ui_text(self):
        """Reload UI text when language changes."""
        # Reload dashboard text
        if hasattr(self, 'dashboard'):
            self.dashboard.reload_ui_text()
        
        # Reload footer text
        if hasattr(self, 'footerLabel'):
            self.footerLabel.setText(get_text('about.footer_text'))

