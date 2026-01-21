"""
Addon Interface Module
Defines the contract for Autolauncher Addons.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import QWidget

@dataclass
class AddonMetadata:
    """Metadata for an addon."""
    name: str
    version: str
    author: str
    description: str
    id: str  # Unique identifier (e.g., "c4n-ALSentinelAddon")

class IAutolauncherAddon(ABC):
    """
    Abstract Base Class for all Autolauncher Addons.
    """

    def __init__(self, manager):
        """
        Initialize the addon.
        Args:
            manager: Reference to the AddonManager
        """
        self.manager = manager
        self.metadata = self.get_metadata()
        self._enabled = False

    @abstractmethod
    def get_metadata(self) -> AddonMetadata:
        """Return metadata about the addon."""
        pass

    def on_enable(self):
        """Called when the addon is enabled."""
        self._enabled = True

    def on_disable(self):
        """Called when the addon is disabled."""
        self._enabled = False

    def on_app_start(self):
        """Called when the main application finishes starting up."""
        pass

    def on_app_shutdown(self):
        """Called when the main application is shutting down."""
        pass

    def on_task_start(self, task_data: Dict, process: Any):
        """
        Called when a specific task is started.
        Args:
            task_data: Dictionary containing task configuration
            process: The subprocess object or process handle
        """
        pass

    def on_task_end(self, task_id: int):
        """
        Called when a task finishes.
        Args:
            task_id: The ID of the task
        """
        pass

    def get_indicator_widget(self) -> Optional[QWidget]:
        """
        Return a QWidget to be displayed in the main status bar/area.
        Return None if no indicator is needed.
        """
        return None
