"""
Addon View Module
Displays and manages installed addons.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    ScrollArea, 
    SettingCardGroup, 
    SwitchSettingCard, 
    FluentIcon,
    InfoBar,
    InfoBarPosition
)
from logger import get_logger

logger = get_logger(__name__)

class AddonView(ScrollArea):
    """
    Dedicated view for managing Addons.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        
        # Set object name for styling
        self.setObjectName("addonView")
        self.scrollWidget.setObjectName("scrollWidget")
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 20, 36, 36)
        
        # Title
        from qfluentwidgets import TitleLabel
        self.titleLabel = TitleLabel("Extensions & Addons", self.scrollWidget)
        self.expandLayout.addWidget(self.titleLabel)
        
        # Group
        self.addonsGroup = SettingCardGroup("Installed Addons", self.scrollWidget)
        self.expandLayout.addWidget(self.addonsGroup)
        
        # We will populate this in a specialized method that can be called 
        # after the view is added to the window and has access to the controller
        
        self.expandLayout.addStretch(1)

    def populate_addons(self, addon_manager):
        """Populate the list of addons from the manager."""
        # Clear existing (if needed, simplified for now)
        # self.addonsGroup.removeAllWidgets() # Not easily available, assumes single call
        
        try:
            addons = addon_manager.get_all_addons()
            
            if not addons:
                # Placeholder for no addons
                from qfluentwidgets import BodyLabel
                self.addonsGroup.addSettingCard(
                    SwitchSettingCard(FluentIcon.INFO, "No Addons Found", "Check the addons folder.", configItem=None)
                )
                return

            for addon in addons:
                meta = addon.metadata
                is_enabled = getattr(addon, '_enabled', False)
                
                # Use PUZZLE or similar if EXTENSION is missing
                icon = FluentIcon.LEGO if hasattr(FluentIcon, 'LEGO') else FluentIcon.PEOPLE
                
                card = SwitchSettingCard(
                    icon,
                    meta.name,
                    f"{meta.description}\nVersion: {meta.version} | Author: {meta.author}",
                    configItem=None,
                    parent=self.addonsGroup
                )
                card.setChecked(is_enabled)
                
                # Connect signal
                card.checkedChanged.connect(
                    lambda checked, aid=meta.id: self._on_addon_toggled(addon_manager, aid, checked)
                )
                
                self.addonsGroup.addSettingCard(card)
        
        except Exception as e:
            logger.error(f"Failed to populate addon view: {e}")

    def _on_addon_toggled(self, manager, addon_id, is_checked):
        """Handle toggle."""
        try:
            if is_checked:
                manager.enable_addon(addon_id)
                status = "enabled"
            else:
                manager.disable_addon(addon_id)
                status = "disabled"
            
            InfoBar.success(
                title="Addon Updated",
                content=f"Addon {status}.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
        except Exception as e:
            logger.error(f"Error toggling addon: {e}")
