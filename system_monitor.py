"""
System Monitor Module for Autolauncher.
Provides system busy detection based on CPU, RAM, GPU, idle time, and blocklist processes.

© 2026 4never Company. All rights reserved.
"""

import ctypes
import json
import psutil
from typing import Tuple, List, Set, Optional

from logger import get_logger
from config import DEFAULT_BLOCKLIST_PROCESSES, BLOCKLIST_FILE

logger = get_logger(__name__)


class LASTINPUTINFO(ctypes.Structure):
    """Windows structure for GetLastInputInfo."""
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]


# Default thresholds
CPU_THRESHOLD = 50  # percent
RAM_THRESHOLD = 80  # percent
GPU_THRESHOLD = 50  # percent
IDLE_THRESHOLD = 60  # seconds


def get_idle_time() -> float:
    """
    Get system idle time in seconds using Windows API.
    
    Returns:
        Idle time in seconds, or 0 if unable to determine.
    """
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
    
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo)):
        millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0
    else:
        return 0


def load_blocklist(settings_manager=None) -> Set[str]:
    """
    Load the user's blocklist from file, settings, or defaults.
    
    Args:
        settings_manager: Optional SettingsManager instance for legacy lookup.
        
    Returns:
        Set of lowercase process names to block.
    """
    user_blocklist = []
    
    # 1. Try to load from JSON file (Highest Priority)
    if BLOCKLIST_FILE.exists():
        try:
            with open(BLOCKLIST_FILE, 'r', encoding='utf-8') as f:
                user_blocklist = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load blocklist.json: {e}")
    
    # 2. If nothing in JSON, try settings (Legacy)
    if not user_blocklist and settings_manager:
        user_blocklist = settings_manager.get('blocklist_processes', None) or []
        
    # 3. Fallback to hardcoded defaults
    if not user_blocklist:
        user_blocklist = DEFAULT_BLOCKLIST_PROCESSES
    
    return set(p.lower() for p in user_blocklist)


def check_cpu_usage() -> Optional[str]:
    """Check CPU usage against threshold."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        if cpu_percent > CPU_THRESHOLD:
            return f"CPU at {cpu_percent:.0f}%"
    except Exception as e:
        logger.debug(f"CPU check failed: {e}")
    return None


def check_ram_usage() -> Optional[str]:
    """Check RAM usage against threshold."""
    try:
        ram = psutil.virtual_memory()
        if ram.percent > RAM_THRESHOLD:
            return f"RAM at {ram.percent:.0f}%"
    except Exception as e:
        logger.debug(f"RAM check failed: {e}")
    return None


def check_gpu_usage() -> Optional[str]:
    """Check GPU usage against threshold (requires GPUtil)."""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_load = max(gpu.load * 100 for gpu in gpus)
            if gpu_load > GPU_THRESHOLD:
                return f"GPU at {gpu_load:.0f}%"
    except ImportError:
        pass  # GPUtil not installed
    except Exception as e:
        logger.debug(f"GPU check failed: {e}")
    return None


def check_blocklist_processes(blocklist: Set[str]) -> Optional[str]:
    """
    Check if any blocklisted processes are running.
    
    Args:
        blocklist: Set of lowercase process names to check.
        
    Returns:
        String describing running blocklisted apps, or None.
    """
    try:
        running_blocklist = []
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                if proc_name in blocklist:
                    running_blocklist.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if running_blocklist:
            unique_apps = list(set(running_blocklist))[:3]  # Show max 3
            return f"Running: {', '.join(unique_apps)}"
    except Exception as e:
        logger.debug(f"Process check failed: {e}")
    return None


def is_system_busy(settings_manager=None) -> Tuple[bool, str]:
    """
    Check if the system is currently busy based on multiple factors.
    
    Args:
        settings_manager: Optional SettingsManager for blocklist lookup.
    
    Returns:
        Tuple of (is_busy: bool, reason: str)
    """
    reasons = []
    
    # Check CPU
    cpu_reason = check_cpu_usage()
    if cpu_reason:
        reasons.append(cpu_reason)
    
    # Check RAM
    ram_reason = check_ram_usage()
    if ram_reason:
        reasons.append(ram_reason)
    
    # Check GPU
    gpu_reason = check_gpu_usage()
    if gpu_reason:
        reasons.append(gpu_reason)
    
    # Check blocklist processes
    blocklist = load_blocklist(settings_manager)
    blocklist_reason = check_blocklist_processes(blocklist)
    if blocklist_reason:
        reasons.append(blocklist_reason)
    
    if reasons:
        return (True, "; ".join(reasons))
    else:
        return (False, "System is idle")
