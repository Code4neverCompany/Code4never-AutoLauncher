
### 🛠️ Crash Fixes & Stability Improvements

This release addresses critical crashes reported when interacting with tasks (Add/Edit/Pause) and when closing the application to the system tray.

---

## 📥 Installation

### Option 1: Auto-Update (If You Have v1.2.0+)
1. App will detect v1.2.3 automatically
2. Click notification or go to About tab
3. Click "Update" button
4. Done! App restarts with new version

### Option 2: Fresh Install
1. Download `c4n-AutoLauncher_v1.2.3.zip` from GitHub Releases
2. Extract ZIP file
3. Run `Autolauncher.exe` inside the extracted folder
4. Enjoy!

---

## 🐛 Bug Fixes

### Critical Fixes
- **FIXED**: Application crash when clicking "Add Task", "Edit Task", or "Pause/Resume" (`AttributeError: type object 'Qt' has no attribute 'Horizontal'`).
- **FIXED**: Application crash when minimizing to system tray or exiting (`AttributeError: type object 'QSystemTrayIcon' has no attribute 'Information'`).
- **FIXED**: Resolved remaining PyQt6 enum compatibility issues.

---

## 📊 Performance Stats

- **Startup Time**: ~1.5 seconds
- **Memory Usage**: ~85MB
- **Update Check**: < 0.5 seconds (with ETag)

---

## 🎯 System Requirements

- **OS**: Windows 10 or Windows 11
- **RAM**: 200MB minimum
- **Disk Space**: 150MB
- **Internet**: Optional (only for updates)

---

## 📞 Support

- 🐛 **Report Bugs**: [GitHub Issues](https://github.com/Code4neverCompany/Code4never-AutoLauncher_AlphaVersion/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Code4neverCompany/Code4never-AutoLauncher_AlphaVersion/discussions)
- 📖 **Documentation**: See README.md

---

## 🙏 Credits

**Developed by**: 4never Company  
**UI Framework**: PyQt6 + PyQt6-Fluent-Widgets  
**Update System**: GitHub API + HTTP ETags  

---

**Thank you for using c4n-AutoLauncher!** 🚀

Your feedback drives continuous improvement.

---

**Release Date**: December 04, 2025  
**Version**: 1.2.3  
**Build**: Beta Release 1.2.3
