# Building Autolauncher Executable - Quick Guide

This guide explains how to build a standalone Windows executable for Autolauncher.

© 2025 4never Company. All rights reserved.

---

## Prerequisites

1. Python 3.8 or newer installed
2. All dependencies from `requirements.txt` installed
3. Icon files in `assets/` directory

---

## Method 1: Using the Build Script (Recommended)

The easiest way to build the executable:

```powershell
# Navigate to project directory
cd "f:\Python Coding Ground\FluentWidget_2"

# Run the build script
python build_exe.py
```

### What the script does:
1. ✅ Checks for PyInstaller (installs if missing)
2. ✅ Verifies icon files exist
3. ✅ Cleans old build directories
4. ✅ Builds the executable using PyInstaller
5. ✅ Verifies the build was successful
6. ✅ Creates a release ZIP package

### Output:
- **Executable**: `dist/Autolauncher.exe`
- **Release Package**: `release/Autolauncher_v1.0.0_[timestamp].zip`

---

## Method 2: Manual Build

If you prefer to build manually:

```powershell
# 1. Install PyInstaller
pip install pyinstaller>=5.13.0

# 2. Clean old builds (optional)
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# 3. Run PyInstaller with spec file
pyinstaller autolauncher.spec --clean

# 4. Find your executable
ls dist/Autolauncher.exe
```

---

## Testing the Executable

After building:

```powershell
# Run the executable
.\dist\Autolauncher.exe
```

### Verify:
- [ ] Application window opens
- [ ] Custom icon appears in title bar and taskbar
- [ ] System tray icon displays correctly
- [ ] All features work (add/edit/delete tasks, scheduling, etc.)
- [ ] No console window appears

---

## Distributing the Executable

### Option 1: ZIP Package
The build script automatically creates a ZIP file in the `release/` directory.

### Option 2: Manual Distribution
Simply copy `dist/Autolauncher.exe` to the target system. No installation needed!

### System Requirements:
- Windows 10 or Windows 11
- No Python installation required
- Approximately 50-80 MB disk space

---

## Troubleshooting

### PyInstaller Not Found
```powershell
pip install --upgrade pyinstaller
```

### Missing Dependencies
```powershell
pip install -r requirements.txt
```

### Build Fails with Import Errors
Add missing modules to `hiddenimports` in `autolauncher.spec`:
```python
hiddenimports = [
    'PySide6.QtCore',
    'your_missing_module',  # Add here
]
```

### Executable Size Too Large
- Disable UPX compression in `autolauncher.spec` (set `upx=False`)
- Remove unused dependencies from your environment
- Use a virtual environment for building

### Icons Not Appearing
Verify files exist:
```powershell
ls assets/icon.ico
ls assets/icon.png
```

---

## Build Configuration

The PyInstaller configuration is in `autolauncher.spec`:

| Setting | Value | Purpose |
|---------|-------|---------|
| `console` | `False` | No console window (GUI app) |
| `icon` | `assets/icon.ico` | Application icon |
| `upx` | `True` | Enable compression |
| `onefile` | `True` | Single executable file |

---

## Advanced Options

### Custom Icon
Replace `assets/icon.ico` with your own icon file.

### Different Name
Edit `autolauncher.spec`:
```python
exe = EXE(
    ...
    name='MyCustomName',  # Change this
    ...
)
```

### Debug Build
For troubleshooting, enable debug mode:
```python
exe = EXE(
    ...
    console=True,  # Show console for debugging
    debug=True,    # Enable debug output
    ...
)
```

---

## Quick Reference

```powershell
# Complete build process (one command)
python build_exe.py

# Manual build
pyinstaller autolauncher.spec --clean

# Test executable
.\dist\Autolauncher.exe

# Package for distribution
Compress-Archive -Path dist/Autolauncher.exe -DestinationPath Autolauncher_v1.0.0.zip
```

---

## Support

For issues or questions:
- Check the walkthrough.md for detailed documentation
- Review PyInstaller logs in `build/` directory
- Verify all dependencies are installed
- Ensure virtual environment is activated

---

**Last Updated**: 2025-11-21  
**Compatible With**: Windows 10/11, Python 3.8+
