# v1.9.0 (2026-02-05) - Feature Update: Visual Intelligence & Addons

This major update introduces the new Addon System and the first powerful addon: The Beacon Sentinel.

## New Features

* **Addon System**: A modular architecture allowing extensions to be added to AutoLauncher.
* **Beacon Sentinel (Visual Clicker)**: An intelligent addon that uses Computer Vision (OpenCV) to visually detect and click buttons on screen (e.g., "Confirm", "Launch").
* **Visual Debugging**: Integrated visual scanning logs to track what the Sentinel sees.

## Fixes & Improvements

* **Dependency Management**: Fixed critical issue where `cv2`, `numpy`, and `mss` were missing from the frozen executable.
* **Path Resolution**: Updated `addon_manager` to correctly locate resources when running as a compiled standalone executable.
* **Stability**: Enhanced error handling for addon initialization.
