# dialogs/settings/general.py
# Copyright (c) 2025-2026 Mehdi Rajabi
# License: GNU General Public License v3.0 (See LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import wx
from database import db_manager
from i18n import _, SUPPORTED_LANGUAGES
import sys
import os
import winreg

SETTING_LANGUAGE = 'language'
SETTING_CHECK_UPDATES = 'check_updates_on_startup'


class TabPanel(wx.Panel):
    """
    The "General" settings tab.
    Handles application language selection and startup update checks.
    """

    def __init__(self, parent):
        super(TabPanel, self).__init__(parent)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        lang_box = wx.StaticBox(self, label=_("Language"))
        lang_box_sizer = wx.StaticBoxSizer(lang_box, wx.VERTICAL)

        lang_label = wx.StaticText(self, label=_("Application Language:"))

        lang_choices = [
            _("English (en)"), 
            _("Italian (it)"), 
            _("Persian (fa)"), 
            _("Serbian (Latin) (sr_Latn)"), 
            _("Spanish (es)"), 
        ]
        lang_codes = SUPPORTED_LANGUAGES

        self.lang_map = dict(zip(lang_choices, lang_codes))
        self.lang_map_rev = dict(zip(lang_codes, lang_choices))

        self.lang_combo = wx.ComboBox(self, choices=lang_choices, style=wx.CB_READONLY)

        lang_box_sizer.Add(lang_label, 0, wx.ALL, 8)
        lang_box_sizer.Add(self.lang_combo, 0, wx.EXPAND | wx.ALL, 8)

        self.lang_restart_label = wx.StaticText(self, label=_("Language changes require an application restart."))
        lang_box_sizer.Add(self.lang_restart_label, 0, wx.ALL, 8)

        main_sizer.Add(lang_box_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.is_portable = self._check_is_portable()

        if sys.platform == "win32" and not self.is_portable:
            windows_box = wx.StaticBox(self, label=_("Windows Integration"))
            windows_box_sizer = wx.StaticBoxSizer(windows_box, wx.VERTICAL)

            self.context_menu_checkbox = wx.CheckBox(self, label=_("Add 'Add to AudioShelf Library' to Windows Explorer context menu"))
            windows_box_sizer.Add(self.context_menu_checkbox, 0, wx.ALL | wx.EXPAND, 8)

            main_sizer.Add(windows_box_sizer, 0, wx.EXPAND | wx.ALL, 10)
        else:
            self.context_menu_checkbox = None

        update_box = wx.StaticBox(self, label=_("Updates"))
        update_box_sizer = wx.StaticBoxSizer(update_box, wx.VERTICAL)

        self.update_checkbox = wx.CheckBox(self, label=_("Automatically check for updates on startup"))
        update_box_sizer.Add(self.update_checkbox, 0, wx.ALL | wx.EXPAND, 8)

        main_sizer.Add(update_box_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(main_sizer)

        self.current_lang_on_load = 'en'
        self.selected_lang_code = 'en'

        self._load_settings()

    def _load_settings(self):
        """Loads settings from the database."""
        current_lang = db_manager.get_setting(SETTING_LANGUAGE) or 'en'
        self.lang_combo.SetValue(self.lang_map_rev.get(current_lang, _("English (en)")))

        self.current_lang_on_load = current_lang
        self.selected_lang_code = current_lang

        check_updates = db_manager.get_setting(SETTING_CHECK_UPDATES)
        is_checked = (check_updates == 'True' or check_updates is None)
        self.update_checkbox.SetValue(is_checked)

        if self.context_menu_checkbox:
            is_installed = self._is_context_menu_installed()
            self.context_menu_checkbox.SetValue(is_installed)

    def save_settings(self):
        """Saves settings to the database."""
        selected_lang_display = self.lang_combo.GetValue()
        self.selected_lang_code = self.lang_map.get(selected_lang_display, 'en')
        db_manager.set_setting(SETTING_LANGUAGE, self.selected_lang_code)

        update_val = 'True' if self.update_checkbox.GetValue() else 'False'
        db_manager.set_setting(SETTING_CHECK_UPDATES, update_val)

        if self.context_menu_checkbox:
            want_installed = self.context_menu_checkbox.GetValue()
            is_installed = self._is_context_menu_installed()
            
            if want_installed and not is_installed:
                self._install_context_menu()
            elif not want_installed and is_installed:
                self._uninstall_context_menu()

    def _check_is_portable(self) -> bool:
        PORTABLE_MARKER_FILE = ".portable"
        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            app_path = os.path.dirname(sys.executable)
            internal_path = os.path.join(app_path, '_libs')
        else:
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            internal_path = app_path

        paths_to_check = [
            os.path.join(app_path, PORTABLE_MARKER_FILE),
            os.path.join(internal_path, PORTABLE_MARKER_FILE)
        ]
        
        for p in paths_to_check:
            if os.path.exists(p):
                return True
        return False

    def _is_context_menu_installed(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\AudioShelf"):
                return True
        except FileNotFoundError:
            return False

    def _install_context_menu(self):
        try:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            menu_text = _("Add to AudioShelf Library")
            
            key_dir = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\AudioShelf")
            winreg.SetValueEx(key_dir, "", 0, winreg.REG_SZ, menu_text)
            winreg.SetValueEx(key_dir, "Icon", 0, winreg.REG_SZ, f'"{exe_path}"')
            cmd_key_dir = winreg.CreateKey(key_dir, "command")
            winreg.SetValueEx(cmd_key_dir, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
            
            key_all = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\AudioShelf")
            winreg.SetValueEx(key_all, "", 0, winreg.REG_SZ, menu_text)
            winreg.SetValueEx(key_all, "Icon", 0, winreg.REG_SZ, f'"{exe_path}"')
            cmd_key_all = winreg.CreateKey(key_all, "command")
            winreg.SetValueEx(cmd_key_all, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        except Exception as e:
            print(f"Failed to install context menu: {e}")

    def _uninstall_context_menu(self):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\AudioShelf\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\AudioShelf")
        except FileNotFoundError:
            pass
            
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\AudioShelf\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\AudioShelf")
        except FileNotFoundError:
            pass

    def get_current_language_on_load(self) -> str:
        """Returns the language code that was active when the tab was initialized."""
        return self.current_lang_on_load

    def get_selected_language(self) -> str:
        """Returns the language code selected by the user."""
        return self.selected_lang_code