# v1.7.1 (2026-01-16) - UI, Permissions & Build Fixes
This patch release addresses critical UI status bugs, permission errors on restricted systems, and ensures all dependencies are correctly bundled.

### Critical Fixes
*   **FIX: UI Status Refresh** - Task icons now correctly reflect real-time status (Resolved "Paused" icon bug).
*   **FIX: Startup Crash (Permission Error)** - Logs and Data are now strictly stored in `%APPDATA%` to prevent "Access Denied" errors.
*   **FIX: Build System** - Resolved critical PyQt6 exclusion issue; UI libraries are now correctly bundled in the executable.
*   **FIX: Localization** - Enhanced German/English translation consistency.
