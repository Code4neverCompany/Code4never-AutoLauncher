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

### ✅ Executable Downloads
- Downloads `.exe` files directly from GitHub releases
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
- `0.1.2` > `0.1.1` ✓
- `0.2.0` > `0.1.9` ✓
- Handles alpha/beta suffixes (e.g., `0.1.1-alpha`)

### 2. Update Detection

When an update is found, the manager checks:
1. Is there an `.exe` file in the release assets?
2. Is the app running as an executable?
3. If both yes → **enable automatic update**
4. If no → **manual download mode**

### 3. Download Process

For automatic updates:

```python
download_thread = UpdateDownloadThread(update_manager, exe_asset)
download_thread.progress.connect(on_progress)  # Progress updates
download_thread.finished.connect(on_complete)  # Download complete
download_thread.error.connect(on_error)        # Error handling
download_thread.start()
```

Progress callback receives:
- `downloaded`: Bytes downloaded so far
- `total`: Total file size in bytes

### 4. Installation Process

When installation starts:

1. Creates a batch script (`_update.bat`)
2. Batch script waits 2 seconds for app to close
3. Replaces old `.exe` with new `.exe`
4. Restarts the application
5. Self-deletes the batch script

**Batch Script** (auto-generated):
```batch
@echo off
timeout /t 2 /nobreak >nul
move /Y "<new_exe>" "<current_exe>"
start "" "<current_exe>"
exit
```

---

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
