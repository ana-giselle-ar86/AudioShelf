# nvda_controller.py
# Copyright (c) 2025-2026 Mehdi Rajabi
# License: GNU General Public License v3.0 (See LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import sys
import logging
from database import db_manager
from i18n import _

try:
    # Import specific drivers to allow manual priority handling
    from accessible_output2.outputs import nvda, jaws
except ImportError:
    logging.critical("CRITICAL ERROR: accessible_output2 library is not installed.")
    sys.exit(1)

VERBOSITY_SILENT = 'silent'
VERBOSITY_MINIMAL = 'minimal'
VERBOSITY_FULL = 'full'

LEVEL_CRITICAL = 'critical'
LEVEL_MINIMAL = 'minimal'
LEVEL_FULL = 'full'

is_app_window_focussed = False


def set_app_focus_status(is_focussed: bool):
    """Updates the global focus state of the application."""
    global is_app_window_focussed
    is_app_window_focussed = is_focussed
    logging.debug(f"Application focus state set to: {is_focussed}")


_speaker = None
_current_driver_name = None  # To track which driver is active (nvda or jaws)

try:
    # 1. Try NVDA first
    _temp_nvda = nvda.NVDA()
    if _temp_nvda.is_active():
        _speaker = _temp_nvda
        _current_driver_name = 'nvda'
        logging.info("Screen reader detected: NVDA")
    
    # 2. Try JAWS if NVDA is not active
    if not _speaker:
        try:
            _temp_jaws = jaws.Jaws()
            if _temp_jaws.is_active():
                _speaker = _temp_jaws
                _current_driver_name = 'jaws'
                logging.info("Screen reader detected: JAWS")
        except Exception:
            pass

    if not _speaker:
        logging.info("No supported screen reader (NVDA/JAWS) detected. Speech output disabled.")

except Exception as e:
    logging.critical(f"CRITICAL ERROR: Could not initialize screen reader driver. Details: {e}")


def speak(text: str, level: str = LEVEL_MINIMAL, interrupt: bool = True):
    """
    Speaks text via the active screen reader.
    Includes specific logic for JAWS to ensure reliability.
    """
    if not _speaker:
        return

    try:
        # Check application focus logic
        if not is_app_window_focussed:
            ghf_setting = db_manager.get_setting('global_hotkey_feedback')
            is_ghf_enabled = (ghf_setting == 'True' or ghf_setting is None)
            if not is_ghf_enabled and level != LEVEL_CRITICAL:
                return

        # Check verbosity logic
        verbosity_setting = db_manager.get_setting('nvda_verbosity') or VERBOSITY_FULL
        is_allowed = False
        if verbosity_setting == VERBOSITY_FULL:
            is_allowed = True
        elif verbosity_setting == VERBOSITY_MINIMAL:
            is_allowed = (level == LEVEL_MINIMAL or level == LEVEL_CRITICAL)
        elif verbosity_setting == VERBOSITY_SILENT:
            is_allowed = (level == LEVEL_CRITICAL)

        if is_allowed:
            if _current_driver_name == 'jaws':
                # JAWS SPECIFIC FIX:
                # Sometimes JAWS generic wrapper fails to interrupt or speak properly in rapid succession.
                # We access the raw JAWS COM object to force 'SayString'.
                if interrupt:
                    # Manually stop speech first
                    _speaker.object.RunFunction("StopSpeech")
                _speaker.object.RunFunction("SayString", text)
            else:
                # NVDA (Standard behavior)
                _speaker.speak(text, interrupt=interrupt)

    except Exception as e:
        logging.error(f"Error in nvda_controller.speak(): {e}")


def cancel_speech():
    """Immediately silences screen reader speech."""
    if not _speaker:
        return
    try:
        if _current_driver_name == 'jaws':
            # JAWS SPECIFIC FIX:
            # JAWS driver in this library doesn't have .silence(), so we call StopSpeech directly.
            _speaker.object.RunFunction("StopSpeech")
        elif hasattr(_speaker, 'silence'):
            # NVDA has native silence method
            _speaker.silence()
            
    except Exception as e:
        logging.error(f"Error in nvda_controller.cancel_speech(): {e}")


def braille_message(text: str):
    """Sends a message to the connected Braille display."""
    if not _speaker:
        return
    try:
        if hasattr(_speaker, 'braille'):
            _speaker.braille(text)
    except Exception as e:
        logging.error(f"Error in nvda_controller.braille_message(): {e}")


def get_pause_on_dialog_setting() -> bool:
    """Retrieves the 'Pause on Dialog' user preference."""
    try:
        setting = db_manager.get_setting('pause_on_dialog')
        return setting == 'True'
    except Exception:
        return True


def cycle_verbosity():
    """Cycles the verbosity setting."""
    current = db_manager.get_setting('nvda_verbosity') or VERBOSITY_FULL
    
    if current == VERBOSITY_FULL:
        new_setting = VERBOSITY_MINIMAL
        display_text = _("Minimal")
    elif current == VERBOSITY_MINIMAL:
        new_setting = VERBOSITY_SILENT
        display_text = _("Silent")
    else:
        new_setting = VERBOSITY_FULL
        display_text = _("Full")

    db_manager.set_setting('nvda_verbosity', new_setting)
    speak(_("Verbosity: {0}").format(display_text), LEVEL_CRITICAL)