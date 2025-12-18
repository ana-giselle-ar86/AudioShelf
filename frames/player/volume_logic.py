# frames/player/volume_logic.py
# Copyright (c) 2025 Mehdi Rajabi
# License: GNU General Public License v3.0

from i18n import _
from nvda_controller import speak, LEVEL_MINIMAL, LEVEL_FULL, LEVEL_CRITICAL

HAS_PYCAW = False
try:
    from comtypes import CoInitialize
    from pycaw.utils import AudioUtilities
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False
except Exception:
    HAS_PYCAW = False


def change_volume(frame, delta: int):
    current_vol = frame.engine.get_volume()
    new_vol = max(0, min(100, current_vol + delta))
    frame.engine.set_volume(new_vol)
    speak(f"{_('Volume')} {new_vol}%", LEVEL_FULL)


def change_system_volume(delta: int):
    if not HAS_PYCAW:
        speak(_("System volume control unavailable"), LEVEL_CRITICAL)
        return

    try:
        CoInitialize()
        device = AudioUtilities.GetSpeakers()
        interface = device.EndpointVolume
        
        current_vol = interface.GetMasterVolumeLevelScalar()
        new_vol = max(0.0, min(1.0, current_vol + (delta / 100.0)))
        
        interface.SetMasterVolumeLevelScalar(new_vol, None)
        
        final_vol = int(round(new_vol * 100))
        speak(f"{_('System Volume')} {final_vol}%", LEVEL_FULL)
        
    except Exception:
        speak("System Volume Error", LEVEL_CRITICAL)


def toggle_mute(frame):
    is_muted = frame.engine.get_mute()
    frame.engine.set_mute(not is_muted)
    speak(_("Mute On") if not is_muted else _("Mute Off"), LEVEL_MINIMAL)