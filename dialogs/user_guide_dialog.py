# dialogs/user_guide_dialog.py
# Copyright (c) 2025-2026 Mehdi Rajabi
# License: GNU General Public License v3.0 (See LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import wx
from i18n import _

class UserGuideDialog(wx.Dialog):
    """
    Displays the User Guide by loading content from a Markdown file
    based on the current language with a fallback to English.
    """

    def __init__(self, parent, lang_code="en"):
        super(UserGuideDialog, self).__init__(parent, title=_("User Guide"), size=(700, 600))
        self.panel = wx.Panel(self)
        
        # Load the content from help.txt based on localization
        guide_content = self._get_guide_content(lang_code)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl = wx.TextCtrl(
            self.panel, 
            value=guide_content, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.BORDER_SUNKEN | wx.TE_BESTWRAP
        )
        
        btn_sizer = wx.StdDialogButtonSizer()
        close_btn = wx.Button(self.panel, wx.ID_OK, _("&Close"))
        btn_sizer.AddButton(close_btn)
        btn_sizer.Realize()

        main_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT, 10)

        self.panel.SetSizer(main_sizer)
        self.CentreOnParent()
        
        self.text_ctrl.SetFocus() 
        self.text_ctrl.SetInsertionPoint(0)

    def _get_guide_content(self, lang_code):
        """
        Locates and reads the help.txt file for the specified language.
        Falls back to English if the localized file is missing.
        """
        base_dir = os.getcwd()
        help_file_name = "help.txt"
        
        # Define paths for localized and fallback (English) versions
        localized_path = os.path.join(base_dir, "locale", lang_code, help_file_name)
        fallback_path = os.path.join(base_dir, "locale", "en", help_file_name)

        # Fallback logic: check if localized file exists, otherwise use English
        target_path = localized_path if os.path.exists(localized_path) else fallback_path

        try:
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                return _("Error: User Guide file (help.txt) was not found in the locale directory.")
        except Exception as e:
            return f"{_('Error loading User Guide')}: {str(e)}"