"""
AutoLauncher Pre-Release Smoke Test
====================================
This script performs basic startup validation to catch critical import/init errors
before release. Run this after building the application to verify it will launch.

Run with: python tests/smoke_test.py
Expected: All checks pass before publishing a release.

History:
- Created after v1.8.x hotfix chain (v1.8.1-v1.8.4) revealed missing startup tests.
"""

import sys
import os

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_critical_imports():
    """Test 1: Verify all critical modules can be imported."""
    print("🔍 Test 1: Critical Imports...")
    
    critical_modules = [
        ("config", "Configuration module"),
        ("logger", "Logging module"),
        ("task_manager", "Task Manager"),
        ("scheduler", "Task Scheduler"),
        ("update_manager", "Update Manager"),
        ("theme_manager", "Theme Manager"),
        ("language_manager", "Language Manager"),
        ("addon_manager", "Addon Manager"),
        ("main_controller", "Main Controller"),
    ]
    
    failed = []
    for module_name, description in critical_modules:
        try:
            __import__(module_name)
            print(f"   ✅ {description} ({module_name})")
        except ImportError as e:
            print(f"   ❌ {description} ({module_name}): {e}")
            failed.append((module_name, str(e)))
    
    return len(failed) == 0, failed


def test_pyqt6_availability():
    """Test 2: Verify PyQt6 and FluentWidgets are available."""
    print("🔍 Test 2: PyQt6 & FluentWidgets Availability...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QObject
        print("   ✅ PyQt6.QtWidgets")
        print("   ✅ PyQt6.QtCore")
    except ImportError as e:
        print(f"   ❌ PyQt6: {e}")
        return False, str(e)
    
    try:
        from qfluentwidgets import FluentIcon, PushButton, setTheme, Theme
        print("   ✅ qfluentwidgets (FluentIcon, PushButton)")
    except ImportError as e:
        print(f"   ❌ qfluentwidgets: {e}")
        return False, str(e)
    
    # Verify FluentIcon has required icons (v1.8.1 crash was missing MOON)
    required_icons = ['HOME', 'SETTING', 'INFO', 'ADD', 'DELETE', 'EDIT']
    for icon_name in required_icons:
        if not hasattr(FluentIcon, icon_name):
            print(f"   ❌ FluentIcon missing: {icon_name}")
            return False, f"FluentIcon.{icon_name} not found"
        print(f"   ✅ FluentIcon.{icon_name}")
    
    return True, None


def test_controller_instantiation():
    """Test 3: Verify MainController can be instantiated."""
    print("🔍 Test 3: MainController Instantiation...")
    
    # QApplication is required before creating Qt widgets
    from PyQt6.QtWidgets import QApplication
    
    # Check if QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    try:
        from main_controller import MainController
        controller = MainController()
        print("   ✅ MainController instantiated")
        
        # Verify critical managers exist
        assert hasattr(controller, 'task_manager'), "Missing task_manager"
        assert hasattr(controller, 'scheduler'), "Missing scheduler"
        assert hasattr(controller, 'settings_manager'), "Missing settings_manager"
        assert hasattr(controller, 'addon_manager'), "Missing addon_manager"
        print("   ✅ All critical managers present")
        
        # Cleanup
        controller.shutdown()
        return True, None
        
    except Exception as e:
        print(f"   ❌ MainController failed: {e}")
        return False, str(e)


def test_settings_ui_components():
    """Test 4: Verify settings UI components can be imported."""
    print("🔍 Test 4: Settings UI Components...")
    
    try:
        from settings_interface import SettingsInterface
        print("   ✅ SettingsInterface importable")
    except ImportError as e:
        print(f"   ❌ SettingsInterface: {e}")
        return False, str(e)
    
    try:
        from about_interface import AboutInterface
        print("   ✅ AboutInterface importable")
    except ImportError as e:
        print(f"   ❌ AboutInterface: {e}")
        return False, str(e)
    
    try:
        from addon_view import AddonView
        print("   ✅ AddonView importable")
    except ImportError as e:
        print(f"   ❌ AddonView: {e}")
        return False, str(e)
    
    return True, None


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("🚀 AutoLauncher Pre-Release Smoke Test")
    print("=" * 60)
    print()
    
    all_passed = True
    results = []
    
    # Run tests
    tests = [
        ("Critical Imports", test_critical_imports),
        ("PyQt6 & FluentWidgets", test_pyqt6_availability),
        ("Controller Instantiation", test_controller_instantiation),
        ("Settings UI Components", test_settings_ui_components),
    ]
    
    for test_name, test_fn in tests:
        try:
            passed, error = test_fn()
            results.append((test_name, passed, error))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            results.append((test_name, False, str(e)))
            all_passed = False
        print()
    
    # Summary
    print("=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    for test_name, passed, error in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if error:
            print(f"           Error: {error}")
    
    print()
    if all_passed:
        print("🎉 All smoke tests PASSED! Safe to release.")
        sys.exit(0)
    else:
        print("🚨 Smoke tests FAILED! Do NOT release until fixed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
