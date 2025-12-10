"""
Power Manager Module for Autolauncher.
Handles Windows power management functions including setting wake timers and entering sleep mode.
"""

import ctypes
import time
from datetime import datetime
from ctypes import wintypes
from logger import get_logger

logger = get_logger(__name__)

# Constants
_kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
_powrprof = ctypes.WinDLL('powrprof', use_last_error=True)

class PowerManager:
    """
    Manages system power states and wake timers using Windows APIs.
    """
    
    def __init__(self):
        self._wake_timer_handle = None

    def set_wake_timer(self, wake_time: datetime) -> bool:
        """
        Set a waitable timer to wake the computer at the specified time.
        
        Args:
            wake_time: datetime object specifying when to wake up
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Cancel existing timer if any
            self.cancel_wake_timer()
            
            # Create a waitable timer
            # Manual reset=True, Name=None
            self._wake_timer_handle = _kernel32.CreateWaitableTimerW(None, True, None)
            
            if not self._wake_timer_handle:
                logger.error(f"Failed to create waitable timer. Error: {ctypes.get_last_error()}")
                return False
            
            # Convert datetime to Windows FileTime (100-nanosecond intervals since Jan 1, 1601)
            timestamp = wake_time.timestamp()
            # 11644473600 is the number of seconds between 1601-01-01 and 1970-01-01
            # 10000000 is the number of 100-nanosecond intervals in a second
            ft_value = int((timestamp + 11644473600) * 10000000)
            
            large_int = ctypes.c_int64(ft_value)
            
            # Set the timer
            # pDueTime: Negative values indicate relative time, positive values indicate absolute time.
            # We are calculating absolute time manually, but SetWaitableTimer expects a pointer to a LARGE_INTEGER.
            # Actually, for absolute time, we pass the positive value.
            
            # Period = 0 (signaled once)
            # pCompletionRoutine = None
            # pArgToCompletionRoutine = None
            # fResume = True (This is the key argument for waking the system)
            
            success = _kernel32.SetWaitableTimer(
                self._wake_timer_handle,
                ctypes.byref(large_int),
                0,
                None,
                None,
                True
            )
            
            if not success:
                logger.error(f"Failed to set wake timer. Error: {ctypes.get_last_error()}")
                self.cancel_wake_timer()
                return False
                
            logger.info(f"System wake timer set for {wake_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting wake timer: {e}")
            return False

    def cancel_wake_timer(self):
        """Cancel the current wake timer if it exists."""
        if self._wake_timer_handle:
            try:
                _kernel32.CancelWaitableTimer(self._wake_timer_handle)
                _kernel32.CloseHandle(self._wake_timer_handle)
                self._wake_timer_handle = None
                logger.debug("Wake timer cancelled")
            except Exception as e:
                logger.error(f"Error cancelling wake timer: {e}")

    def enter_sleep_mode(self, hibernate: bool = False, force: bool = False, disable_wake_events: bool = False) -> bool:
        """
        Put the system into sleep or hibernate mode.
        
        Args:
            hibernate: True for hibernate, False for sleep (suspend)
            force: True to force suspension immediately
            disable_wake_events: True to disable system wake events
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Initiating system {'hibernate' if hibernate else 'sleep'}...")
            # SetSuspendState(Hibernate, Force, WakeupEventsDisabled)
            success = _powrprof.SetSuspendState(hibernate, force, disable_wake_events)
            
            if not success:
                logger.error(f"Failed to enter sleep mode. Error: {ctypes.get_last_error()}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error entering sleep mode: {e}")
            return False

    def start_keep_awake(self) -> bool:
        """
        Prevent the system from entering sleep mode.
        Uses SetThreadExecutionState with ES_SYSTEM_REQUIRED | ES_CONTINUOUS.
        """
        try:
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED (optional)
            # We use ES_SYSTEM_REQUIRED to keep the system running.
            # ES_DISPLAY_REQUIRED would keep the screen on, which might be desired for "waking up".
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            
            # We want to keep system awake and maybe display too? 
            # Let's stick to system for now to avoid blinding user at night, 
            # unless they want to see the task running. 
            # Usually "Wake to run" implies running, so maybe display is good?
            # Let's use SYSTEM only for now, as the task itself might turn on display if it creates a window.
            # Actually, to be safe against "oversleeping", SYSTEM is enough.
            
            flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            
            previous_state = _kernel32.SetThreadExecutionState(flags)
            
            if previous_state == 0:
                logger.error("Failed to set thread execution state to keep awake.")
                return False
                
            logger.info("System keep-awake enabled.")
            return True
        except Exception as e:
            logger.error(f"Error starting keep awake: {e}")
            return False

    def stop_keep_awake(self) -> bool:
        """
        Allow the system to enter sleep mode normally again.
        Resets execution state to ES_CONTINUOUS.
        """
        try:
            ES_CONTINUOUS = 0x80000000
            
            # Reset to continuous only (clears specific requirements)
            previous_state = _kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            
            if previous_state == 0:
                logger.error("Failed to reset thread execution state.")
                return False
                
            logger.info("System keep-awake disabled.")
            return True
        except Exception as e:
            logger.error(f"Error stopping keep awake: {e}")
            return False

    def get_last_wake_info(self) -> dict:
        """
        Get information about the last system wake event.
        Returns a dict with 'wake_source' (str) and 'wake_time' (datetime).
        """
        try:
            # Use PowerShell to get the last wake event from the System event log
            # Event ID 1 from Microsoft-Windows-Power-Troubleshooter
            cmd = (
                "Get-WinEvent -LogName System -ProviderName Microsoft-Windows-Power-Troubleshooter "
                "-MaxEvents 1 | Select-Object -Property TimeCreated, @{N='WakeSource';E={$_.Properties[1].Value}} "
                "| ConvertTo-Json"
            )
            
            # Run PowerShell command
            import subprocess
            import json
            
            result = subprocess.run(
                ["powershell", "-Command", cmd], 
                capture_output=True, 
                text=True, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get wake info: {result.stderr}")
                return None
                
            data = json.loads(result.stdout)
            
            # Parse time
            # PowerShell JSON date format: "/Date(1733331234000)/" or ISO string depending on PS version
            # Usually ConvertTo-Json returns ISO-like string in newer PS, or the /Date/ format.
            # Let's handle the ISO format which is standard in modern PS Core, 
            # but Windows PowerShell 5.1 (default) might return /Date(...)/.
            
            time_str = data.get('TimeCreated')
            wake_source = data.get('WakeSource', 'Unknown')
            
            wake_time = None
            
            if time_str:
                if "/Date(" in time_str:
                    # Handle legacy format
                    import re
                    timestamp_ms = int(re.search(r'\d+', time_str).group())
                    wake_time = datetime.fromtimestamp(timestamp_ms / 1000.0)
                else:
                    # Handle ISO format
                    # Might need dateutil for robust parsing, but let's try standard
                    # Example: "2025-11-26T10:00:00"
                    try:
                        wake_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    except:
                        # Fallback
                        pass
            
            return {
                'wake_source': str(wake_source),
                'wake_time': wake_time
            }
            
        except Exception as e:
            logger.error(f"Error getting last wake info: {e}")
            return None
