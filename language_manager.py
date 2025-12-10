"""
Language Manager Module
Handles loading and retrieving translations for the application.

© 2025 4never Company. All rights reserved.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from logger import get_logger

logger = get_logger(__name__)


class LanguageManager:
    """
    Manages application translations and language switching.
    Supports dynamic language changes without restart.
    """

    def __init__(self, default_language: str = "en"):
        """
        Initialize the LanguageManager.

        Args:
            default_language: Default language code (e.g., 'en', 'de')
        """
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict] = {}
        self._load_translations()

    def _get_translations_dir(self) -> Path:
        """Get the translations directory path based on execution context."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            # PyInstaller 6.x puts resources in _internal folder
            exe_dir = Path(sys.executable).parent
            internal_dir = exe_dir / "_internal"

            # Check if _internal exists (PyInstaller 6.x)
            if internal_dir.exists() and (internal_dir / "translations").exists():
                return internal_dir / "translations"
            elif (exe_dir / "translations").exists():
                return exe_dir / "translations"
            else:
                logger.warning("Translations directory not found in executable location")
                return exe_dir / "translations"  # Return default even if doesn't exist
        else:
            # Running as Python script
            return Path(__file__).parent / "translations"

    def _load_translations(self):
        """Load all available translation files."""
        translations_dir = self._get_translations_dir()

        if not translations_dir.exists():
            logger.warning(f"Translations directory not found: {translations_dir}")
            return

        logger.info(f"Loading translations from: {translations_dir}")

        # Load all JSON files in the translations directory
        for lang_file in translations_dir.glob("*.json"):
            lang_code = lang_file.stem  # e.g., 'en' from 'en.json'
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"Loaded language: {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load translation file {lang_file}: {e}")

        if not self.translations:
            logger.warning("No translations loaded. Using fallback text.")

    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.

        Args:
            language_code: Language code (e.g., 'en', 'de')

        Returns:
            True if language was set successfully, False otherwise
        """
        if language_code in self.translations:
            self.current_language = language_code
            logger.info(f"Language set to: {language_code}")
            return True
        else:
            logger.warning(f"Language '{language_code}' not available. Available: {list(self.translations.keys())}")
            return False

    def get_text(self, key_path: str, language: Optional[str] = None) -> str:
        """
        Get translated text for a given key path.

        Args:
            key_path: Dot-separated key path (e.g., 'settings.general')
            language: Specific language code, or None to use current language

        Returns:
            Translated text, or key_path if translation not found
        """
        lang = language or self.current_language

        # If language not loaded, try default
        if lang not in self.translations:
            lang = self.default_language

        # If still not found, return key_path as fallback
        if lang not in self.translations:
            logger.debug(f"No translation for key '{key_path}' in language '{lang}'")
            return key_path

        # Navigate through nested dictionary
        keys = key_path.split('.')
        result = self.translations[lang]

        try:
            for key in keys:
                result = result[key]
            
            if result is None:
                return key_path
                
            return str(result)
        except (KeyError, TypeError):
            logger.debug(f"Translation key not found: {key_path}")
            return key_path

    def get_available_languages(self) -> Dict[str, str]:
        """
        Get available languages with their display names.

        Returns:
            Dictionary mapping language codes to display names
        """
        languages = {}
        for lang_code in self.translations.keys():
            # Get language display name from translation file
            display_name = self.get_text(f"settings.language_{lang_code}", lang_code)
            if display_name == f"settings.language_{lang_code}":
                # Fallback to code if no display name found
                display_name = lang_code.upper()
            languages[lang_code] = display_name

        return languages

    def format_text(self, key_path: str, **kwargs) -> str:
        """
        Get translated text and format it with provided arguments.

        Args:
            key_path: Dot-separated key path
            **kwargs: Format arguments

        Returns:
            Formatted translated text
        """
        text = self.get_text(key_path)
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to format text '{key_path}': {e}")
            return text


# Global instance for easy access
_language_manager: Optional[LanguageManager] = None


def get_language_manager() -> LanguageManager:
    """
    Get the global LanguageManager instance.

    Returns:
        LanguageManager instance
    """
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


def set_language(language_code: str) -> bool:
    """
    Set the global language.

    Args:
        language_code: Language code (e.g., 'en', 'de')

    Returns:
        True if successful, False otherwise
    """
    return get_language_manager().set_language(language_code)


def get_text(key_path: str, **kwargs) -> str:
    """
    Get translated text with optional formatting.

    Args:
        key_path: Dot-separated key path
        **kwargs: Format arguments

    Returns:
        Translated text
    """
    if kwargs:
        return get_language_manager().format_text(key_path, **kwargs)
    return get_language_manager().get_text(key_path)
