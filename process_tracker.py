"""
Process Tracker Module for Autolauncher.
Tracks the actual launched process instead of just the shell process.
"""

import psutil
import time
from pathlib import Path
from logger import get_logger

logger = get_logger(__name__)


def get_spawned_processes(timeout: int = 5, target_process_name: str = None, search_start_time: float = None):
    """
    Find all processes spawned after a task launch.
    Prioritizes the target process name if provided.
    Filters out common system processes to avoid false positives.
    
    Args:
        timeout: How long to wait for processes to spawn (seconds)
        target_process_name: Optional name of the specific process to look for (e.g. "Raid.exe")
        search_start_time: Timestamp to start searching from. Defaults to now.
        
    Returns:
        List of psutil.Process objects created recently
    """
    start_time = time.time()
    # Use provided start time or default to slightly before now to catch fast processes
    search_time = search_start_time if search_start_time else (time.time() - 2.0)
    spawned_processes = []
    
    # Common system processes to ignore
    IGNORE_LIST = [
        'audiodg.exe', 'taskhostw.exe', 'dllhost.exe', 'conhost.exe', 
        'svchost.exe', 'explorer.exe', 'searchapp.exe', 'startmenuexperiencehost.exe',
        'runtimebroker.exe', 'backgroundtaskhost.exe', 'smartscreen.exe',
        'ctfmon.exe', 'wermgr.exe', 'csrss.exe', 'winlogon.exe'
    ]
    
    logger.info(f"Monitoring for newly spawned processes (timeout: {timeout}s)...")
    if target_process_name:
        logger.info(f"Prioritizing search for: {target_process_name}")
    
    target_found = False
    
    while time.time() - start_time < timeout:
        for proc in psutil.process_iter(['name', 'create_time', 'pid']):
            try:
                proc_name = proc.info['name']
                proc_name_lower = proc_name.lower()
                
                # 1. Check for target process match (priority)
                if target_process_name and target_process_name.lower() in proc_name_lower:
                    # Even if created slightly before, if it matches the name, we want it
                    # But ensure it's relatively new (e.g., within last 30 seconds)
                    if time.time() - proc.info['create_time'] < 30:
                        if proc.pid not in [p.pid for p in spawned_processes]:
                            spawned_processes.append(proc)
                            logger.info(f"🎯 Found TARGET process: {proc_name} (PID: {proc.pid})")
                            target_found = True
                
                # 2. Check for other spawned processes (only if we haven't found target yet?)
                # Actually, launchers might spawn the target later, so we keep looking.
                # But we filter out system noise.
                elif proc.info['create_time'] > search_time:
                    if proc_name_lower not in IGNORE_LIST:
                        if proc.pid not in [p.pid for p in spawned_processes]:
                            spawned_processes.append(proc)
                            logger.info(f"Detected new process: {proc_name} (PID: {proc.pid})")
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # If we found the target, we might not need to wait the full timeout?
        # But maybe the target spawns other things. Let's wait a bit but maybe reduce timeout?
        if target_found and time.time() - start_time > 3:
            break
            
        time.sleep(0.2)
    
    # If we found the target, filter out everything else to be safe?
    # No, sometimes the launcher stays open.
    # But if we found the target, we definitely want to monitor IT.
    # If we picked up random noise + target, the random noise might keep us awake forever.
    
    if target_found:
        # Filter to ONLY the target process(es) and maybe its children?
        # For now, let's just keep the target processes if found, to avoid the "audiodg" issue.
        logger.info("Target process found! Ignoring other detected processes to prevent false positives.")
        spawned_processes = [p for p in spawned_processes if target_process_name.lower() in p.name().lower()]
    
    if spawned_processes:
        logger.info(f"Monitoring {len(spawned_processes)} process(es)")
    else:
        logger.warning("No relevant processes detected")
    
    return spawned_processes


def resolve_shortcut(lnk_path: str) -> str:
    """
    Resolve a .lnk shortcut to get the target executable path.
    
    Args:
        lnk_path: Path to the .lnk file
        
    Returns:
        Tuple of (target_executable_path, arguments_string)
        If not a shortcut, returns (original_path, "")
    """
    if not lnk_path.endswith('.lnk'):
        return lnk_path, ""
    
    try:
        import pythoncom
        import win32com.client
        
        # Initialize COM for this thread
        pythoncom.CoInitialize()
        
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            target_path = shortcut.Targetpath
            arguments = shortcut.Arguments
            logger.info(f"Resolved shortcut: {lnk_path} -> {target_path} (Args: {arguments})")
            return target_path, arguments
        finally:
            # Uninitialize COM
            pythoncom.CoUninitialize()
            
    except Exception as e:
        logger.warning(f"Could not resolve shortcut {lnk_path}: {e}")
        # Fallback: try to extract executable name from .lnk file name
        # E.g., "Raid Shadow Legends.lnk" -> "Raid Shadow Legends.exe"
        lnk_name = Path(lnk_path).stem
        logger.info(f"Fallback: assuming executable name is '{lnk_name}.exe'")
        return lnk_name + ".exe", ""


def get_process_name_from_path(program_path: str) -> str:
    """
    Get the process name from a program path.
    Resolves shortcuts if needed.
    
    Args:
        program_path: Path to the program or shortcut
        
    Returns:
        Process name (e.g., "notepad.exe")
    """
    # Resolve shortcut if needed
    resolved_path, _ = resolve_shortcut(program_path)
    
    # Get the executable name
    path_obj = Path(resolved_path)
    process_name = path_obj.name
    
    logger.debug(f"Process name for {program_path}: {process_name}")
    return process_name


def wait_for_process_completion(process: psutil.Process, check_interval: float = 1.0):
    """
    Wait for a process to complete.
    
    Args:
        process: psutil.Process object to monitor
        check_interval: How often to check if process is still running (seconds)
    """
    try:
        logger.info(f"Monitoring process: {process.name()} (PID: {process.pid})")
        
        while process.is_running():
            time.sleep(check_interval)
        
        logger.info(f"Process {process.name()} (PID: {process.pid}) has finished")
    except psutil.NoSuchProcess:
        logger.info(f"Process no longer exists")
    except Exception as e:
        logger.error(f"Error monitoring process: {e}")


def wait_for_processes(processes: list, check_interval: float = 1.0):
    """
    Wait for all processes in a list to complete.
    Dynamically adopts child processes: if a monitored process spawns children,
    they are added to the wait list. This handles launchers that exit after starting the game.
    """
    if not processes:
        logger.warning("No processes to monitor")
        return
    
    # We work with a dynamic set of PIDs to avoid duplicating objects
    monitored_pids = {p.pid for p in processes}
    # Keep list of objects for polling
    active_procs = list(processes)
    
    logger.info(f"Monitoring {len(active_procs)} process(es) with child adoption")
    
    for proc in active_procs:
        try:
            logger.info(f"  - {proc.name()} (PID: {proc.pid})")
        except: pass
            
    while True:
        # 1. Check for new children from currently running processes
        new_children = []
        current_running = []
        
        for proc in list(active_procs): # Copy list to iterate safely
            try:
                if proc.is_running():
                    current_running.append(proc)
                    
                    # Look for children
                    try:
                        children = proc.children(recursive=True)
                        for child in children:
                            if child.pid not in monitored_pids:
                                try:
                                    child_name = child.name()
                                    # Filter out common noise? 
                                    # For now, adopting all children of specific user-launched tasks is strictly better
                                    # than losing the task.
                                    logger.info(f"🚀 Detected child process: {child_name} (PID: {child.pid}) - Adopting!")
                                    monitored_pids.add(child.pid)
                                    new_children.append(child)
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process died, that's fine, we just don't add it to current_running
                pass

        # Add new children to the main list
        if new_children:
            active_procs.extend(new_children)
            # Re-evaluate current_running to include new children immediately? 
            # Next loop will catch them as running.
            for child in new_children:
                current_running.append(child)

        # 2. Update active list
        active_procs = current_running
        
        if not active_procs:
            logger.info("All monitored processes (and children) have finished")
            break
            
        time.sleep(check_interval)
