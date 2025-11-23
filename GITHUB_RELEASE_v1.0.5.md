# GitHub Release Instructions for v1.0.5

## Release Assets Created ✅

**ZIP Package**: `c4n-AutoLauncher_v1.0.5.zip`
- **Size**: 60.19 MB  
- **SHA256**: `21975F046D0156E5E7D4626080A22C5C61A8A02F7C66A3F20D10B4D28C3DF10D`
- **Location**: `f:\Python Coding Ground\FluentWidget_2\c4n-AutoLauncher_v1.0.5.zip`

---

## Steps to Create GitHub Release

### 1. Navigate to GitHub Releases
```
https://github.com/Code4neverCompany/Code4never-AutoLauncher_AlphaVersion/releases/new
```

### 2. Fill Release Information

**Tag**: `v1.0.5`  
**Release Title**: `c4n-AutoLauncher v1.0.5 - UI Polish & Efficient Updates`

**Description** (copy from RELEASE_NOTES.md):
```markdown
**UI Polishef & Efficient Updates** - Near RealTime Update Detection

© 2025 4never Company. All rights reserved.

---

## 🎉 What's New in v1.0.5

### ⚡ ETag-Based Update Checking
- **95% Bandwidth Reduction**: Uses HTTP ETags for conditional requests
- **Near Real-Time Detection**: Max 2-minute delay for new releases
- **Smart Caching**: Stores ETags in `etag_cache.json` for persistent efficiency

### 🎛️ Simplified Update Settings (3 Options)
- **On Startup**: Check only when app launches
- **Manual Only**: Check only when you click "Check for Updates"
- **Automatic (Recommended)**: Check every 2 minutes, prompt for install

### 🎨 UI Refinements
- Window size optimized to 1100×650
- FAQ dialog rebuilt for clarity
- Dynamic icons (UP arrow for rollback, SYNC for updates)
- Hidden Cancel button in FAQ

---

## 📥 Installation

### Auto-Update (If You Have v1.0.4)
1. App will detect v1.0.5 automatically within 2 minutes
2. Click notification or go to About tab
3. Click "Update" button
4. Done!

### Fresh Install
1. Download `c4n-AutoLauncher_v1.0.5.zip`
2. Extract ZIP file
3. Run `Autolauncher.exe`
4. Enjoy!

---

## 🔧 What Changed

- `update_manager.py` - ETag caching logic
- `autolauncher.py` - 3-option update system
- `settings_interface.py` - Simplified UI
- `about_interface.py` - FAQ fixes, dynamic icons
- `config.py` - Window size optimization
- **New**: `FUTURE_PLANS.md` - Roadmap

---

**SHA256**: `21975F046D0156E5E7D4626080A22C5C61A8A02F7C66A3F20D10B4D28C3DF10D`
```

### 3. Upload Assets

**Drag and drop** to GitHub:
- ✅ `c4n-AutoLauncher_v1.0.5.zip`

### 4. Mark as Pre-release
- ✅ Check "Set as a pre-release" (it's still alpha)

### 5. Publish
- Click **"Publish release"**

---

## Verification Steps

After publishing:
1. Download the ZIP from GitHub release
2. Extract and run `Autolauncher.exe`
3. Verify version shows `1.0.5` in About tab
4. Test "Check for Updates" (should say up to date)
5. Test Settings → Updates dropdown
6. Test FAQ button

---

## Git Commit & Push

Before creating release:
```powershell
git add .
git commit -m "Release v1.0.5 - UI polish, ETag updates, simplified settings"
git push origin main
git tag v1.0.5
git push origin v1.0.5
```

---

**Ready to publish!** 🚀
