# AutoLauncher Release Notes

## v1.6.0 (2025-12-18) - Feature Update: Native OCR & Process Tracking
This major release transitions the "Stuck Detector" from unreliable pixel-matching to **Native Windows OCR (Optical Character Recognition)**, enabling the app to "read" game screens for update dialogs. It also includes critical fixes for game process tracking.

### New Features
*   **Native Windows OCR**: The AutoLauncher can now "see" text inside game windows that use custom UI engines (DirectX/OpenGL), such as **Wuthering Waves** or heavily skinned launchers.
*   **Universal Detection**: If standard detection fails, the system takes a micro-screenshot of the window and reads the pixels to find "Update" or "Maintenance" keywords.

### Critical Fixes
*   **v1.5.7 Hotfix Included**: Recursive process termination ensures zombie game clients are killed during a restart.

### Previous Releases

## v1.5.7 (2025-12-18)
**Hotfix: Recursive Process Termination**

### Critical Fixes
*   **FIX: Zombie Processes** - The "Smart Restart" feature previously failed to close game clients that were launched as child processes (e.g., the actual Wuthering Waves game window spawned by the launcher).
*   **CHANGE: Recursive Kill** - `stop_task` now forcefully terminates the entire process tree (Parent + All Children). This ensures that when a task is restarted, the stuck game window is actually closed first.

### Previous Releases

## v1.5.6 (2025-12-18)
**Smart Restart & Persistent Dialog Recovery**

### Changes
*   **FEATURE: Smart Restart** - Added a robust "trace back" mechanic for un-clickable update dialogs.
    *   If a confirmation dialog ("Notice", "Update", etc.) persists for 12 seconds despite auto-click attempts, the system now identifies it as "stuck".
    *   Stuck tasks are forcefully stopped and restarted to clear the blockage.
    *   This resolves issues with games like *Wuthering Waves* where custom UI rendering prevents standard button clicking.
*   **IMPROVEMENT: Enhanced Logging** - The `StuckDetector` now logs exactly which window and button it is interacting with, aiding in debugging.
*   **FIX: Dependency** - Explicitly included `pywinauto` in the production build to fix "module not found" errors in the detection subsystem.
*   **FIX: Persistent Dialog Logic** - Implemented a tracking counter in the scheduler to prevent infinite click loops on unresponsive windows.

### Previous Releases

## v1.5.5 (2025-12-18)
**Optimized Detection Speed & Depth**

### Changes
*   **PERFORMANCE: Multi-Pass Window Search** - Implemented a tiered search strategy:
    1.  **Fast Path (Win32 API)**: Scans all window titles instantly to filter candidates.
    2.  **Deep Path (UIA)**: Only inspects candidate windows with UI Automation, preventing system lag.
*   **PERFORMANCE: Broad Search Limit** - Increased global window search limit to 30 windows for thoroughness.
*   **FEATURE: Faster Reactions** - Confirmation dialog check frequency increased (10s -> 4s).
*   **FIX: Comtypes Caching** - Resolved `ImportError` issues by directing `comtypes` to a writable cache directory.

## v1.5.4 (2025-12-18)
**Broad Detection & Fixes**

### Changes
*   **FEATURE: Broad Update Detection** - StuckDetector now searches globally for independent launcher windows.
*   **FIX: Update Manager** - Fixed 403 Forbidden errors by adding User-Agent headers to GitHub requests.
*   **FIX: Update Manager** - Corrected repository target link.

