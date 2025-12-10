## Changes for version 1.3.3
- FEATURE: Smart AFK Sleep - 'Sleep after completion' now activates if user was AFK (no input) during the entire task, even if system wasn't woken by the task

## Changes for version 1.3.2
- FIX: Log Dialog crash - Resolved 'Could not open execution log' error caused by incorrect QSize import (PyQt6 migration regression)

## Changes for version 1.3.1
- FIX: Dark Mode White UI Bug - Implemented auto-recovery timer (3s) to restore dark theme when corrupted
- NOTE: Root cause investigation pending - qfluentwidgets dark mode styling issue requires deeper analysis

## Changes for version 1.3.0
- FEATURE: Smart Auto Execution Mode - Intelligently postpones tasks when system is busy (CPU >50%, RAM >80%, user active, games/IDEs running)
- FEATURE: Dashboard Emoji Indicators - Visual emojis for Schedule (📅 Once, 🔄 Daily, 📆 Weekly), Countdown (⏱️ Normal, ⏳ Postponed, ⏸️ Paused, ❌ Expired)
- FEATURE: Color-coded Status Badges - Enabled (green), Disabled (blue), Postponed (orange), Running (purple pulse), Failed (red), Expired (gray)
- FEATURE: Enhanced Log Dialog - Shows blocker process icons for postponed tasks, EXECUTED events logged with reasons
- FEATURE: Postpone Timer - Countdown shows remaining time until retry with ⏳ indicator
- FIX: White UI Bug - Replaced timer workaround with proper qconfig.themeChanged signal handler
- FIX: Running status now clears when task finishes
- FIX: Settings sync - Scheduler now reloads settings before checking execution mode
- UX: Status badges centered in table cells
- UX: Wider countdown/schedule columns for emoji text

## Changes for version 1.2.3
- FIX: Resolved crashes when adding/editing tasks (Qt.Horizontal enum)
- FIX: Resolved crash on application exit (QSystemTrayIcon enum)

## Changes for version 1.2.2
- FIX: Resolved application crashes caused by missing translation keys (InfoBar NoneType error)
- FIX: Hardened language manager against null values

## Changes for version 1.2.1
- FIX: Migrated to PyQt6 to resolve DLL load failures
- FIX: Updated all UI components for PyQt6 compatibility

## Changes for version 1.2.0
- FEATURE: Visual Stuck Detection - Detects error dialogs and 'Update Required' windows using UI Automation
- FEATURE: Smart Sleep - Intelligent sleep management based on task completion
- IMPROVEMENT: Replaced unreliable OCR with robust pywinauto integration
- FIX: Enhanced task monitoring reliability

## Changes for version 1.1.0
- BETA RELEASE: Official Beta Launch!
- FEATURE: Wake from Sleep - System wakes up automatically for scheduled tasks
- FEATURE: Pre-wake Process - Configurable pre-wake duration (1-15 mins) to ensure system is ready
- FEATURE: Smart Process Tracking - Tracks actual game/app processes, including shortcuts (.lnk) and launchers
- FEATURE: Sleep after Completion - System sleeps only when the actual task finishes
- UX: Double-click task row to edit
- UX: Real-time clock display in Task Dialog

## Changes for version 1.0.13l
- TEST: Target release for verifying auto-update from v1.0.13k
- INFO: If you are seeing this, the auto-update worked!

## Changes for version 1.0.13k
- FIX: Resolved NameError regression in update manager
- FIX: Restored missing PowerShell download logic
- TEST: Final verification release for auto-update flow

## Changes for version 1.0.13j
- TEST: Target release for verifying auto-update from v1.0.13i
- INFO: If you are seeing this, the auto-update worked!

## Changes for version 1.0.13i
- FIX: Implemented robust PowerShell script-based download mechanism
- FIX: Resolved syntax error in update manager
- TEST: Final verification release for auto-update flow

## Changes for version 1.0.13h
- TEST: Final verification release for PowerShell update engine
- FIX: Confirmed robust download capability via Invoke-WebRequest

## Changes for version 1.0.13g
- FIX: Replaced Python downloader with robust Windows PowerShell downloader
- FIX: Solves persistent 0-byte download issues by using OS native networking
- FIX: Improved handling of SSL, redirects, and proxies

## Changes for version 1.0.13f
- TEST: Verification release to confirm auto-update functionality
- FIX: Confirmed fix for 0-byte downloads
- FIX: Confirmed fix for startup crashes

## Changes for version 1.0.13e
- FIX: Resolved application crash on startup due to missing UI method
- FIX: File logging now enabled in production builds (was DEBUG-only)
- FIX: Logs directory button now points to correct location

## Changes for version 1.0.13d
- FIX: File logging now enabled in production builds (was DEBUG-only)
- FIX: Logs directory button now points to correct location

## Changes for version 1.0.13c
- FIX: Application now properly loads saved language preference on startup
- FIX: Eliminated mixed language text on first launch

## Changes for version 1.0.13b
- FIX: Auto-update downloads now properly follow GitHub CDN redirects
- FIX: Added comprehensive download logging with progress tracking
- FIX: Enhanced error detection for 0-byte file downloads
- FIX: Added ZIP file validation before installation

## Changes for version 1.0.13a
- FIX: Corrected translation JSON structure - separated 'about' section from 'dialog'
- FIX: Fixed translation key prefixes in task_card.py

## Changes for version 1.0.13
- FEATURE: Bilingual Support - English and German with dynamic language switching
- FEATURE: Comprehensive translations for all UI elements, dialogs, and messages
- UPDATE: Refactored UI components to support dynamic text reloading

## Changes for version 1.0.12
- FIX: Updated SettingsInterface docstrings to resolve import error
- FIX: Ensure module import works for packaged executable

## Changes for version 1.0.12
- FIX: Updated SettingsInterface docstrings to resolve import error
- FIX: Ensure module import works for packaged executable

## Changes for version 1.0.11
- FEATURE: Language Support - English and German
- FEATURE: Dynamic language switching without restart
- UPDATE: Translated Settings interface for bilingual support

## Changes for version 1.0.11
- FEATURE: Language Support - English and German
- FEATURE: Dynamic language switching without restart
- UPDATE: Translated Settings interface for bilingual support

## Changes for version 1.0.11
- FEATURE: Language Support - English and German
- FEATURE: Dynamic language switching without restart
- UPDATE: Translated Settings interface for bilingual support

## Changes for version 1.0.10
- FIX: Critical updater fix - supports renamed executables
- FIX: Improved update installation reliability

## Changes for version 1.0.4
- HOTFIX: Fixed crash on startup due to UI initialization error
- Restored missing method in About interface

## Changes for version 1.0.3
- Increased Auto-Update Check Frequency to 15 Minutes
- Translated About Page Disclaimer to English
- Added Current Version Changelog Display in About Page
- Improved Update Available UI Logic

## Changes for version 1.0.2
- Redesigned About Section with Update Dashboard
- Added Persistent 'Updating' Notification with Progress
- Improved Update Button Behavior (Always Visible)
- Streamlined Update Flow (Download -> Restart)

## Changes for version 1.0.2
- Redesigned About Section with Update Dashboard
- Added Persistent 'Updating' Notification with Progress
- Improved Update Button Behavior (Always Visible)
- Streamlined Update Flow (Download -> Restart)

## Changes for version 1.0.0
- Major Release: v1.0.0
- Implemented Directory-Based Update System
- Added Setup.exe Installer
- Improved Auto-Update Reliability (ZIP based)
- Fixed missing dependencies in updates

## Changes for version 1.0.0
- Major Release: v1.0.0
- Implemented Directory-Based Update System
- Added Setup.exe Installer
- Improved Auto-Update Reliability (ZIP based)
- Fixed missing dependencies in updates

# Auto-Update System - Documentation

This document explains the enhanced auto-update system for Autolauncher.

© 2025 4never Company. All rights reserved.

---

## Overview

The update manager now supports **automatic executable downloads and installations** when running as a standalone `.exe` file.

---

## Features

### ✅ Automatic Update Detection
- Checks GitHub releases for new versions
- Uses semantic versioning comparison
- Identifies pre-releases (Alpha/Beta versions)
- Detects executable assets in releases

### ✅ ZIP Package Downloads
- Downloads `.zip` release packages from GitHub
- Supports full directory updates (including assets/dependencies)
- Shows real-time download progress
- Non-blocking UI (download runs in background thread)
- Handles network errors gracefully

### ✅ Automatic Installation
- Replaces current executable with new version
- Uses batch script to handle file replacement
- Automatically restarts application after update
- Clean rollback on failure

### ✅ Smart Behavior
- **When running as .exe**: Offers automatic download/install
- **When running as Python**: Opens browser to download page
- Progress tracking with MB downloaded / total size
- User confirmation before installation

---

## How It Works

### 1. Version Checking

```python
update_info, error = update_manager.check_for_updates()
```

Returns:
- `update_info`: Dictionary with release details if update available
- `error`: Error message if check failed

The version comparison uses semantic versioning:

## Usage

### For Users

1. **Check for Updates**:
   - Go to Settings → About
   - Click "Check for Updates"

2. **If Update Available**:
   - **Running as .exe**: 
     - Click "Download & Install"
     - Wait for download progress
     - Confirm installation
     - App restarts automatically
   
   - **Running as Python**:
     - Click OK to open download page
     - Download manually

### For Developers

#### Adding to GitHub Release

For automatic updates to work, releases must include:

1. ✅ A version tag (e.g., `v0.1.2`)
2. ✅ An executable file (e.g., `Autolauncher.exe`)
3. ✅ Release notes in the body

**Example Release Process**:

```powershell
# Build the executable
python build_exe.py

# This creates:
# - dist\Autolauncher.exe (upload this to GitHub release)
# - release\Autolauncher_v*.zip (alternative distribution)
```

**GitHub Release Checklist**:
- [ ] Tag name: `v0.1.2` (or your version)
- [ ] Upload `Autolauncher.exe` as an asset
- [ ] Write release notes describing changes
- [ ] Mark as pre-release if Alpha/Beta

#### Version Info Structure

`version_info.json`:
```json
{
  "version": "0.1.1",
  "build_date": "2025-11-21",
  "changelog": [
    {
      "version": "0.1.1",
      "date": "2025-11-21",
      "changes": [
        "Added rounded corner icons",
        "Implemented auto-update system",
        "Fixed taskbar branding"
      ]
    }
  ]
}
```

---

## API Reference

### UpdateManager Class

#### Methods

**`check_for_updates() -> tuple[Optional[Dict], Optional[str]]`**
- Checks GitHub for latest release
- Returns: `(update_info, error_message)`

**`download_update(asset: Dict, progress_callback) -> Optional[str]`**
- Downloads an update asset
- `progress_callback(downloaded, total)`: Optional progress tracking
- Returns: Path to downloaded file

**`install_update_and_restart(exe_path: str) -> bool`**
- Installs update and restarts app
- Only works when running as executable
- Returns: `True` if installation started

**`get_current_version() -> str`**
- Returns current version string

**`get_changelog() -> List[Dict]`**
- Returns full changelog

#### Properties

**`is_executable: bool`**
- `True` if running as compiled executable
- `False` if running as Python script

---

## Update Info Dictionary

When an update is available, `update_info` contains:

```python
{
    "version": "0.1.2",           # New version number
    "url": "https://...",          # GitHub release URL
    "body": "Release notes...",    # Release description
    "assets": [...],               # List of all assets
    "exe_asset": {...},            # Executable asset details
    "can_auto_update": True        # Whether auto-update is possible
}
```

**exe_asset** structure:
```python
{
    "name": "Autolauncher.exe",
    "browser_download_url": "https://...",
    "size": 65234723,              # File size in bytes
    ...
}
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Update source unavailable" | GitHub returns 404 | Wait for release to be published |
| "No executable found" | Release has no .exe file | Upload .exe to GitHub release |
| "Download failed" | Network issue | Check internet connection |
| "Installation failed" | File permission issue | Run as administrator |

### Logging

All update operations are logged to `logs/autolauncher.log`:

```
INFO - UpdateManager initialized. Current Version: 0.1.1
INFO - Checking for updates...
DEBUG - Latest GitHub release: 0.1.2, Current: 0.1.1
INFO - New version found: 0.1.2
INFO - Downloading Autolauncher.exe (65234723 bytes)...
INFO - Download complete: C:\Temp\...
INFO - Installing update...
```

---

## Security Considerations

1. **HTTPS Only**: All downloads use HTTPS
2. **GitHub Verified**: Downloads only from official GitHub repository
3. **No Auto-Execute**: User must confirm installation
4. **Timeout Protection**: 30-second timeout on downloads
5. **Error Handling**: Graceful failure with user notification

---

## Testing Updates

### Local Testing

1. **Test Version Detection**:
   ```python
   manager = UpdateManager()
   update_info, error = manager.check_for_updates()
   ```

2. **Test with Mock Release**:
   - Create a GitHub release with higher version
   - Add a test `.exe` file
   - Run update check

3. **Test Download Progress**:
   ```python
   def progress(downloaded, total):
       print(f"{downloaded}/{total} bytes")
   
   path = manager.download_update(asset, progress)
   ```

### Production Testing

Before releasing to users:
- [ ] Create test release on GitHub
- [ ] Verify version comparison works
- [ ] Test download with slow connection
- [ ] Verify installation and restart works
- [ ] Test rollback on failure
- [ ] Verify app works after update

---

## Troubleshooting

### Update Check Fails

**Symptom**: "Failed to check updates"

**Solutions**:
1. Check internet connection
2. Verify GitHub repository is accessible
3. Check API rate limits (60 requests/hour)
4. Review logs for detailed error

### Download Stuck

**Symptom**: Progress bar doesn't move

**Solutions**:
1. Check firewall settings
2. Verify GitHub is not blocked
3. Try manual download from browser
4. Check available disk space

### Installation Fails

**Symptom**: "Installation failed" error

**Solutions**:
1. Close any antivirus temporarily
2. Run as administrator
3. Verify .exe is not in use by another process
4. Check file permissions on installation directory

---

## Future Enhancements

Potential improvements:

- [ ] Delta updates (only download changes)
- [ ] Update rollback feature
- [ ] Automatic background checks
- [ ] Update scheduling (install on next restart)
- [ ] Cryptographic signature verification
- [ ] Bandwidth throttling option
- [ ] Pause/resume downloads
- [ ] Update history tracking

---

**Last Updated**: 2025-11-21  
**Compatible With**: Autolauncher v0.1.1+
