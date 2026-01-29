"""
Test script for Language Manager
Verifies that translation files load correctly.
"""

import sys
sys.path.insert(0, r"f:\Python Coding Ground\FluentWidget_2")

from language_manager import LanguageManager

def test_language_manager():
    print("=" * 60)
    print("Language Manager Test")
    print("=" * 60)
    print()
    
    # Initialize manager
    lang_mgr = LanguageManager()
    
    # Test available languages
    available = lang_mgr.get_available_languages()
    print(f"Available languages: {available}")
    print()
    
    # Test English
    print("Testing English (en):")
    lang_mgr.set_language('en')
    print(f"  General: {lang_mgr.get_text('settings.general')}")
    print(f"  Execution Mode: {lang_mgr.get_text('settings.execution_mode')}")
    print(f"  Language: {lang_mgr.get_text('settings.language')}")
    print()
    
    # Test German
    print("Testing German (de):")
    lang_mgr.set_language('de')
    print(f"  General: {lang_mgr.get_text('settings.general')}")
    print(f"  Execution Mode: {lang_mgr.get_text('settings.execution_mode')}")
    print(f"  Language: {lang_mgr.get_text('settings.language')}")
    print()
    
    # Test formatting 
    print("Testing text formatting:")
    text = lang_mgr.format_text("settings.language_updated", language="Deutsch")
    print(f"  {text}")
    print()
    
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    test_language_manager()
