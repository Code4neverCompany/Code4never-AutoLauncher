"""
Addon Manager Module
Handles discovery, loading, and lifecycle management of Autolauncher Addons.
"""

import os
import importlib
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
from logger import get_logger
from addon_interface import IAutolauncherAddon

logger = get_logger(__name__)

class AddonManager:
    """
    Central manager for finding and running addons.
    Singleton-like access via MainController.
    """

    def __init__(self, context=None):
        self.context = context  # MainController reference
        self.addons: Dict[str, IAutolauncherAddon] = {}
        self.addon_dir = os.path.join(os.path.dirname(__file__), "addons")
        self._ensure_addon_dir()

    def _ensure_addon_dir(self):
        """Ensure the addons directory exists."""
        if not os.path.exists(self.addon_dir):
            try:
                os.makedirs(self.addon_dir)
                # Create __init__.py to make it a package
                with open(os.path.join(self.addon_dir, "__init__.py"), 'w') as f:
                    f.write("# Addons package\n")
            except Exception as e:
                logger.error(f"Failed to create addons directory: {e}")

    def discover_addons(self):
        """
        Scan the addons directory for valid addon packages.
        An addon is a subdirectory with an __init__.py and a main class implementing IAutolauncherAddon.
        """
        logger.info("Discovering addons...")
        if not os.path.exists(self.addon_dir):
            return

        # Add parent dir to sys.path to ensure imports work if needed
        parent_dir = os.path.dirname(self.addon_dir)
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)

        for item in os.listdir(self.addon_dir):
            item_path = os.path.join(self.addon_dir, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "__init__.py")):
                self._load_addon(item)

    def _load_addon(self, package_name: str):
        """
        Dynamically load an addon module.
        Assumes the addon has a specific entry point (e.g., 'main.py' or just exposes a class in __init__).
        We will look for a class that inherits from IAutolauncherAddon in the package.
        """
        try:
            # Import the package: addons.package_name
            module_name = f"addons.{package_name}"
            
            # Since we modify the directory structure, we might need to invalidate caches or re-import
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
            
            # Find the Addon class
            addon_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                try:
                    if (isinstance(attr, type) and 
                        issubclass(attr, IAutolauncherAddon) and 
                        attr is not IAutolauncherAddon):
                        addon_class = attr
                        break
                except TypeError:
                    continue
            
            if addon_class:
                # Instantiate
                addon_instance = addon_class(self)
                addon_id = addon_instance.metadata.id
                
                self.addons[addon_id] = addon_instance
                
                # Check persistence
                disabled_list = []
                if self.context and hasattr(self.context, 'settings_manager'):
                    disabled_list = self.context.settings_manager.get('disabled_addons', [])
                
                if addon_id not in disabled_list:
                    self.enable_addon(addon_id)
                else:
                    addon_instance._enabled = False
                    logger.info(f"Addon loaded (disabled): {addon_instance.metadata.name}")
            else:
                logger.warning(f"No IAutolauncherAddon implementation found in {package_name}")

        except Exception as e:
            logger.error(f"Failed to load addon '{package_name}': {e}")
            import traceback
            logger.debug(traceback.format_exc())

    def enable_addon(self, addon_id: str):
        """Enable an addon and persist state."""
        if addon_id in self.addons:
            addon = self.addons[addon_id]
            if getattr(addon, '_enabled', False):
                return # Already enabled

            try:
                addon.on_enable()
                addon._enabled = True
                logger.info(f"Enabled addon: {addon_id}")
                
                # Update settings
                if self.context and hasattr(self.context, 'settings_manager'):
                    sm = self.context.settings_manager
                    disabled = sm.get('disabled_addons', [])
                    if addon_id in disabled:
                        disabled.remove(addon_id)
                        sm.set('disabled_addons', disabled)
                        
            except Exception as e:
                logger.error(f"Error enabling addon {addon_id}: {e}")

    def disable_addon(self, addon_id: str):
        """Disable an addon and persist state."""
        if addon_id in self.addons:
            addon = self.addons[addon_id]
            if not getattr(addon, '_enabled', False):
                return # Already disabled

            try:
                addon.on_disable()
                addon._enabled = False
                logger.info(f"Disabled addon: {addon_id}")
                
                # Update settings
                if self.context and hasattr(self.context, 'settings_manager'):
                    sm = self.context.settings_manager
                    disabled = sm.get('disabled_addons', [])
                    if addon_id not in disabled:
                        disabled.append(addon_id)
                        sm.set('disabled_addons', disabled)
                        
            except Exception as e:
                logger.error(f"Error disabling addon {addon_id}: {e}")

    def get_enabled_addons(self) -> List[IAutolauncherAddon]:
        """Return list of enabled addon instances."""
        return [a for a in self.addons.values() if getattr(a, '_enabled', False)]
    
    def get_all_addons(self) -> List[IAutolauncherAddon]:
        """Return all loaded addon instances."""
        return list(self.addons.values())

    # --- Hooks ---

    def notify_app_start(self):
        for addon in self.addons.values():
            if addon._enabled:
                try: 
                    addon.on_app_start()
                except Exception as e:
                    logger.error(f"Error in addon {addon.metadata.id}.on_app_start: {e}")

    def notify_app_shutdown(self):
        for addon in self.addons.values():
            if addon._enabled:
                try:
                    addon.on_app_shutdown()
                except Exception as e:
                    logger.error(f"Error in addon {addon.metadata.id}.on_app_shutdown: {e}")

    def notify_task_start(self, task_data: Dict, process: Any):
        for addon in self.addons.values():
            if addon._enabled:
                try:
                    addon.on_task_start(task_data, process)
                except Exception as e:
                    logger.error(f"Error in addon {addon.metadata.id}.on_task_start: {e}")

    def notify_task_end(self, task_id: int):
        for addon in self.addons.values():
            if addon._enabled:
                try:
                    addon.on_task_end(task_id)
                except Exception as e:
                    logger.error(f"Error in addon {addon.metadata.id}.on_task_end: {e}")

    def get_all_indicators(self) -> List:
        """Get all UI indicators from enabled addons."""
        indicators = []
        for addon in self.addons.values():
            if addon._enabled:
                try:
                    widget = addon.get_indicator_widget()
                    if widget:
                        indicators.append(widget)
                except Exception as e:
                    logger.error(f"Error getting indicator from {addon.metadata.id}: {e}")
        return indicators
