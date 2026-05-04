# dialogs/goto_chapter_dialog.py
# Copyright (c) 2025-2026 Mehdi Rajabi
# License: GNU General Public License v3.0

import wx
import re
from i18n import _
from nvda_controller import speak, LEVEL_MINIMAL

NUMBER_PATTERN = re.compile(r'^\d+$')

class GoToChapterDialog(wx.Dialog):
    def __init__(self, parent, current_chapter_num: int, max_chapter_num: int):
        super(GoToChapterDialog, self).__init__(parent, title=_("Go to Chapter Number"))

        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.max_chapter_num = max_chapter_num
        self.target_chapter_index: int = -1

        instructions = _("Enter chapter number (1 to {0}):").format(self.max_chapter_num)
        instructions_label = wx.StaticText(self.panel, label=instructions)
        self.chapter_num_text = wx.TextCtrl(self.panel, value=str(current_chapter_num))

        self.main_sizer.Add(instructions_label, 0, wx.ALL | wx.EXPAND, 10)
        self.main_sizer.Add(self.chapter_num_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        button_sizer = wx.StdDialogButtonSizer()
        self.ok_button = wx.Button(self.panel, wx.ID_OK, _("&Go"))
        self.cancel_button = wx.Button(self.panel, wx.ID_CANCEL, _("&Cancel"))

        button_sizer.AddButton(self.ok_button)
        button_sizer.AddButton(self.cancel_button)
        button_sizer.Realize()

        self.main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.panel.SetSizer(self.main_sizer)
        self.main_sizer.Fit(self)
        self.CentreOnParent()

        self.chapter_num_text.SetFocus()
        self.chapter_num_text.SelectAll()
        self.SetDefaultItem(self.ok_button)

        self.ok_button.Bind(wx.EVT_BUTTON, self.on_go)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.chapter_num_text.Bind(wx.EVT_KEY_DOWN, self.on_text_key)

    def on_go(self, event):
        if self._validate_input():
            self.EndModal(wx.ID_OK)
        else:
            speak(_("Invalid number."), LEVEL_MINIMAL)
            wx.MessageBox(
                _("Invalid format. Please enter a number between 1 and {0}.").format(self.max_chapter_num),
                _("Invalid Input"), wx.OK | wx.ICON_ERROR
            )
            self.chapter_num_text.SetFocus()
            self.chapter_num_text.SelectAll()

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_text_key(self, event: wx.KeyEvent):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.on_go(None)
        else:
            event.Skip()

    def _validate_input(self) -> bool:
        input_str = self.chapter_num_text.GetValue().strip()
        if not NUMBER_PATTERN.match(input_str): return False
        try:
            target_num = int(input_str)
            if not (1 <= target_num <= self.max_chapter_num): return False
            self.target_chapter_index = target_num - 1
            return True
        except Exception:
            return False

    def get_selected_index(self) -> int:
        return self.target_chapter_index