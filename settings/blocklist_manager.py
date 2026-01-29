"""
Blocklist Manager Module for AutoLauncher.
Handles blocklist file operations, program list management, and scanning.

© 2026 4never Company. All rights reserved.
"""

import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from PyQt6.QtCore import QThread, pyqtSignal

from logger import get_logger
from config import DATA_DIR

logger = get_logger(__name__)

# Constants
GITHUB_PROGRAMS_URL = "https://raw.githubusercontent.com/Code4neverCompany/Code4never-AutoLauncher/main/known_programs.json"
APPDATA_DIR = Path(os.environ.get('APPDATA', '')) / 'c4n-AutoLauncher'


def load_known_programs() -> Dict[str, Tuple[str, str]]:
    """
    Load known programs from JSON file (local or bundled).
    
    Returns:
        Dictionary mapping exe_name -> (display_name, category)
    """
    # Try loading from AppData first (updated version)
    appdata_path = APPDATA_DIR / 'known_programs.json'
    
    if appdata_path.exists():
        try:
            with open(appdata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: tuple(v) for k, v in data.get('programs', {}).items()}
        except Exception as e:
            logger.warning(f"Failed to load AppData programs: {e}")
    
    # Fall back to bundled file
    bundled_path = Path(__file__).parent.parent / 'known_programs.json'
    
    if bundled_path.exists():
        try:
            with open(bundled_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: tuple(v) for k, v in data.get('programs', {}).items()}
        except Exception as e:
            logger.warning(f"Failed to load bundled programs: {e}")
    
    logger.warning("No known_programs.json found")
    return {}


def download_program_list() -> Tuple[bool, str, int]:
    """
    Download latest known_programs.json from GitHub.
    
    Returns:
        Tuple of (success: bool, version: str, program_count: int)
    """
    try:
        with urllib.request.urlopen(GITHUB_PROGRAMS_URL, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Save to AppData
        APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        appdata_path = APPDATA_DIR / 'known_programs.json'
        
        with open(appdata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        program_count = len(data.get('programs', {}))
        version = data.get('version', 'unknown')
        
        logger.info(f"Updated known_programs.json to v{version} ({program_count} programs)")
        return True, version, program_count
        
    except urllib.error.URLError as e:
        logger.error(f"Failed to download program list: {e}")
        return False, "", 0
    except Exception as e:
        logger.error(f"Failed to save program list: {e}")
        return False, "", 0


def get_available_drives() -> List[str]:
    """
    Get list of available drive letters on the system.
    
    Returns:
        List of uppercase drive letters (e.g., ['C', 'D', 'E'])
    """
    import string
    
    available = []
    for letter in string.ascii_uppercase:
        drive_path = Path(f"{letter}:\\")
        if drive_path.exists():
            try:
                next(drive_path.iterdir(), None)
                available.append(letter)
            except (PermissionError, OSError):
                pass
    return available


class ProgramScanner(QThread):
    """
    Background thread for scanning installed programs.
    
    Signals:
        progress(int, int, str): (current, total, current_exe_name)
        finished(list): List of (exe_name, (display_name, category)) tuples
    """
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    
    def __init__(self, known_programs: Dict[str, Tuple[str, str]], 
                 current_blocklist: List[str], 
                 drives: List[str]):
        super().__init__()
        self.known_programs = known_programs
        self.current_lower = [p.lower() for p in current_blocklist]
        self.drives = drives
    
    def run(self):
        found = []
        scan_dirs = []
        
        # Build list of directories to scan
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
            
            # Skip if already in blocklist
            if exe_name.lower() in self.current_lower:
                continue
            # Skip if already found
            if exe_name in [f[0] for f in found]:
                continue
            
            # Search for the executable
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


def categorize_found_programs(found_programs: List[Tuple[str, Tuple[str, str]]]) -> Dict[str, List[Tuple[str, str]]]:
    """
    Organize found programs by category.
    
    Args:
        found_programs: List of (exe_name, (display_name, category))
        
    Returns:
        Dict mapping category -> list of (exe_name, display_name)
    """
    by_category = {'Game': [], 'IDE': [], 'Productivity': []}
    
    for exe, (name, category) in found_programs:
        if category in by_category:
            by_category[category].append((exe, name))
    
    return by_category
