# i18n.py
# Copyright (c) 2025-2026 Mehdi Rajabi
# License: GNU General Public License v3.0 (See LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import gettext
import os
import logging

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(APP_DIR, 'locale')

SUPPORTED_LANGUAGES = ['en', 'it', 'fa', 'sr_Latn', 'es']
DEFAULT_LANGUAGE = 'en'

_ = None
ngettext = None


def set_language(lang_code: str = None):
    """
    Sets the application's active language.

    Args:
        lang_code: The language code (e.g., 'en', 'fa'). If None, loads from DB.
    """
    global _, ngettext

    if not lang_code:
        lang_code = DEFAULT_LANGUAGE

    try:
        t = gettext.translation('AudioShelf', localedir=LOCALE_DIR, languages=[lang_code], fallback=True)
        _ = t.gettext
        ngettext = t.ngettext
    except FileNotFoundError:
        logging.warning(f"Translation file not found for lang '{lang_code}'. Using default text.")
        _ = lambda s: s
        ngettext = lambda s, p, n: s if n == 1 else p


set_language()


def switch_language(lang_code: str):
    """
    Updates the language setting in the database and re-initializes the translator.

    Args:
        lang_code: The new language code to apply.
    """
    if lang_code in SUPPORTED_LANGUAGES:
        from database import db_manager
        db_manager.set_setting('language', lang_code)
        set_language(lang_code)
        logging.info(f"Language switched to {lang_code}. App restart may be required.")
    else:
        logging.error(f"Unsupported language code '{lang_code}'.")