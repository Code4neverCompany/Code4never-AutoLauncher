# AutoLauncher Release Notes

## v1.8.0 (2026-01-21) - The Addon System Update
This release introduces the **Addon System**, a major architectural upgrade that allows the Autolauncher to be successfully extended with new capabilities.

### 🧩 New Addon Architecture
*   **Foundational Plugin System**: Core support for discovering, loading, and managing external modules.
*   **c4n-ALSentinelAddon**: The powerful "Update Detector" has been migrated to this new system as the **"Beacon Sentinel"**.
*   **Dedicated UI**: A new "Addons" page in the navigation sidebar to manage your extensions.

### ✨ Improvements
*   **Startup Toast**: Get instant feedback on which addons are active when the app launches.
*   **Settings Persistence**: Your Addon enable/disable choices are saved permanently.
*   **Code Cleanup**: Removed legacy spaghetti code for a cleaner, more stable backend.

### 🛠️ Fixes
*   **UI Crash**: Fixed a crash in the Settings menu related to missing icon assets.
*   **WuWa Support**: Enhanced detection for "Wuthering Waves" update dialogs (via Sentinel Addon).

## v1.7.1 (2026-01-16) - UI, Permissions & Build Fixes
This patch release addresses critical UI status bugs, permission errors on restricted systems, and ensures all dependencies are correctly bundled.

### Critical Fixes
*   **FIX: UI Status Refresh** - Task icons now correctly reflect real-time status (Resolved "Paused" icon bug).
*   **FIX: Startup Crash (Permission Error)** - Logs and Data are now strictly stored in `%APPDATA%` to prevent "Access Denied" errors.
*   **FIX: Build System** - Resolved critical PyQt6 exclusion issue; UI libraries are now correctly bundled in the executable.
*   **FIX: Localization** - Enhanced German/English translation consistency.

## v1.7.0 (2026-01-15) - MVC Architecture & Backend Stability
This major release transforms the application architecture for long-term stability and introduces critical backend safeguards.

### Key Changes
*   **MVC Refactoring**: Complete architectural overhaul separating UI (View) from Logic (Controller). This makes the app more robust and easier to maintain.
*   **Atomic Writes**: "Safe Save" mechanism for `tasks.json` and `settings.json` prevents data corruption if the PC crashes during a save.
*   **Zombie Process Cleanup**: New background collector finds and kills processes that have finished but are still tracking as "Running".
*   **Blocklist Externalization**: Hardcoded game blocklists are now in `blocklist.json`, allowing you to add/remove games easily.
*   **Input Freeze Fix**: Resolved a critical bug where the keyboard/mouse would lock up on startup due to hook initialization order.

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

