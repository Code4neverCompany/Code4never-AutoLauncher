"""
Icon Extractor Utility for c4n-AutoLauncher
Extracts icons from Windows executables and shortcuts for display in the task schedule.
"""

import os
import sys
import ctypes
from ctypes import windll, c_int, c_void_p, POINTER, byref
from typing import Optional
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

from logger import get_logger

logger = get_logger(__name__)

# Icon cache to avoid repeated extractions
_icon_cache = {}


def extract_icon_from_path(file_path: str) -> Optional[str]:
    """
    Extract icon from a file path (.exe or .lnk).
    
    Args:
        file_path: Path to the executable or shortcut file
        
    Returns:
        Path to the saved icon file, or None if extraction fails
    """
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"File path does not exist: {file_path}")
        return None
    
    # Check cache first
    cached_icon = get_cached_icon(file_path)
    if cached_icon:
        return cached_icon
    
    try:
        # Create icons directory if it doesn't exist
        icons_dir = os.path.join(os.getcwd(), 'data', 'icons')
        os.makedirs(icons_dir, exist_ok=True)
        
        # Generate a unique filename based on the file path hash
        import hashlib
        path_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()
        icon_save_path = os.path.join(icons_dir, f"{path_hash}.png")
        
        # Check if icon already exists on disk
        if os.path.exists(icon_save_path):
            return icon_save_path

        # Handle .lnk shortcuts
        icon = None
        if file_path.lower().endswith('.lnk'):
            # Try to get icon directly from shortcut properties first
            icon = get_shortcut_icon(file_path)
            
            # If that fails, try to resolve target and get icon from there
            if not icon:
                target_path = resolve_lnk_target(file_path)
                if target_path:
                    icon = get_exe_icon(target_path)
                else:
                    logger.warning(f"Could not resolve shortcut: {file_path}")
                    icon = get_default_icon()
        
        # Handle .exe files
        elif file_path.lower().endswith('.exe'):
            icon = get_exe_icon(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            icon = get_default_icon()
        
        # Save the icon to disk
        if icon and not icon.isNull():
            icon.save(icon_save_path, "PNG")
            return icon_save_path
            
        return None
        
    except Exception as e:
        logger.error(f"Error extracting icon from {file_path}: {e}")
        return None


def get_shortcut_icon(lnk_path: str) -> Optional[QPixmap]:
    """
    Try to extract the icon specified in the shortcut properties.
    
    Args:
        lnk_path: Path to the .lnk file
        
    Returns:
        QPixmap if a specific icon is set, None otherwise
    """
    try:
        import win32com.client
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        
        # IconLocation returns "path,index" (e.g. "C:\Program Files\App\app.exe,0")
        icon_location = shortcut.IconLocation
        
        if icon_location and "," in icon_location:
            path, index_str = icon_location.rsplit(",", 1)
            try:
                index = int(index_str)
                
                # If path is empty or just a comma, it might mean "use target"
                if not path.strip():
                    return None
                    
                # Expand environment variables if needed
                path = os.path.expandvars(path)
                
                if os.path.exists(path):
                    logger.debug(f"Extracting shortcut icon from {path}, index {index}")
                    return extract_icon_with_index(path, index)
            except ValueError:
                pass
                
        return None
        
    except Exception as e:
        logger.debug(f"Could not get shortcut icon for {lnk_path}: {e}")
        return None


def resolve_lnk_target(lnk_path: str) -> Optional[str]:
    """
    Resolve a .lnk shortcut to its target executable path.
    
    Args:
        lnk_path: Path to the .lnk file
        
    Returns:
        Path to the target executable, or None if resolution fails
    """
    try:
        import win32com.client
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        target = shortcut.TargetPath
        
        if target and os.path.exists(target):
            logger.debug(f"Resolved shortcut {lnk_path} -> {target}")
            return target
        else:
            logger.warning(f"Shortcut target does not exist: {target}")
            return None
            
    except Exception as e:
        logger.error(f"Error resolving shortcut {lnk_path}: {e}")
        return None


def get_exe_icon(exe_path: str) -> Optional[QPixmap]:
    """
    Extract icon from an executable file using Windows Shell API (default index 0).
    
    Args:
        exe_path: Path to the .exe file
        
    Returns:
        QPixmap containing the icon, or None if extraction fails
    """
    return extract_icon_with_index(exe_path, 0)


def extract_icon_with_index(path: str, index: int) -> Optional[QPixmap]:
    """
    Extract icon from a file at a specific index.
    
    Args:
        path: Path to the file (exe, dll, ico)
        index: Index of the icon to extract
        
    Returns:
        QPixmap containing the icon, or None if extraction fails
    """
    try:
        # Use Shell32.dll to extract icon
        shell32 = windll.shell32
        
        # ExtractIconEx returns the number of icons extracted
        large_icons = (c_void_p * 1)()
        small_icons = (c_void_p * 1)()
        
        # Note: ExtractIconExW can handle negative indices for specific resource IDs,
        # but WScript.Shell usually gives us a 0-based index.
        
        icon_count = shell32.ExtractIconExW(
            path,
            index,
            byref(large_icons),
            byref(small_icons),
            1   # Number of icons to extract
        )
        
        if icon_count > 0 and large_icons[0]:
            # Convert HICON to QPixmap
            icon_handle = large_icons[0]
            pixmap = hicon_to_pixmap(icon_handle)
            
            # Clean up icon handle
            windll.user32.DestroyIcon(icon_handle)
            if small_icons[0]:
                windll.user32.DestroyIcon(small_icons[0])
            
            if pixmap and not pixmap.isNull():
                return pixmap
            else:
                logger.warning(f"Failed to convert icon to pixmap: {path} index {index}")
                return None
        else:
            logger.warning(f"No icons found in {path} at index {index}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting icon from {path} index {index}: {e}")
        return None


def hicon_to_pixmap(hicon: int) -> Optional[QPixmap]:
    """
    Convert Windows HICON to QPixmap.
    
    Args:
        hicon: Handle to a Windows icon
        
    Returns:
        QPixmap representation of the icon, or None if conversion fails
    """
    try:
        # Get icon info
        # PyQt6 has QImage.fromHICON
        image = QImage.fromHICON(hicon)
        if not image.isNull():
            return QPixmap.fromImage(image)
        return None
        
    except ImportError:
        # QtWinExtras not available, use alternative method
        logger.warning("QtWinExtras not available, using alternative icon conversion")
        return get_default_icon()
    except Exception as e:
        logger.error(f"Error converting HICON to QPixmap: {e}")
        return get_default_icon()


def get_cached_icon(file_path: str) -> Optional[QPixmap]:
    """
    Retrieve a cached icon if available.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Cached QPixmap, or None if not in cache
    """
    return _icon_cache.get(file_path)


def cache_icon(file_path: str, pixmap: QPixmap):
    """
    Cache an extracted icon for future use.
    
    Args:
        file_path: Path to the file
        pixmap: The QPixmap to cache
    """
    _icon_cache[file_path] = pixmap
    logger.debug(f"Cached icon for {file_path}")


def get_default_icon() -> QPixmap:
    """
    Get a default fallback icon for when extraction fails.
    
    Returns:
        Default application icon as QPixmap
    """
    # Create a simple default icon (a colored square)
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.lightGray)
    return pixmap


def clear_icon_cache():
    """Clear all cached icons to free memory."""
    global _icon_cache
    _icon_cache.clear()
    logger.info("Icon cache cleared")


def get_process_icon(process_name: str) -> Optional[str]:
    """
    Get icon path for a running process by its name.
    
    Args:
        process_name: Name of the process (e.g., 'code.exe', 'Antigravity.exe')
        
    Returns:
        Path to the extracted icon file, or None if extraction fails
    """
    try:
        import psutil
        
        # Find the process and get its executable path
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                    exe_path = proc.info['exe']
                    if exe_path and os.path.exists(exe_path):
                        return extract_icon_from_path(exe_path)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        logger.debug(f"Process not found or no exe path: {process_name}")
        return None
        
    except Exception as e:
        logger.debug(f"Error getting process icon for {process_name}: {e}")
        return None

