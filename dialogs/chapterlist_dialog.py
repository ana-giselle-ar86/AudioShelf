# dialogs/chapterlist_dialog.py
# Copyright (c) 2025-2026 Mehdi Rajabi
# License: GNU General Public License v3.0

import wx
import re
from typing import List, Dict
from i18n import _
from utils import format_time

class ChapterListDialog(wx.Dialog):
    """A dialog to display list of all chapters."""

    def __init__(self, parent, chapters: List[Dict], current_index: int):
        super(ChapterListDialog, self).__init__(parent, title=_("Chapter List"))

        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        list_label = wx.StaticText(self.panel, label=_("&Chapters:"))

        self.chapter_names = []
        for i, ch in enumerate(chapters):
            title = ch.get('title', _("Chapter {0}").format(i + 1))
            title = re.sub(r'^\d+[\s\-\.]*', '', title)
            title = re.sub(r'[\s\-\.]*\d+$', '', title)
            if not title.strip():
                title = _("Chapter {0}").format(i + 1)
            time_sec = ch.get('time', 0)
            time_str = format_time(int(time_sec * 1000))
            self.chapter_names.append(f"{title} - {time_str}")

        self.chapter_list_box = wx.ListBox(self.panel, choices=self.chapter_names, style=wx.LB_SINGLE)
        if 0 <= current_index < len(chapters):
            self.chapter_list_box.SetSelection(current_index)

        self.main_sizer.Add(list_label, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 10)
        self.main_sizer.Add(self.chapter_list_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        button_sizer = wx.StdDialogButtonSizer()
        self.go_button = wx.Button(self.panel, wx.ID_OK, _("&Go to Chapter"))
        self.cancel_button = wx.Button(self.panel, wx.ID_CANCEL, _("&Cancel"))

        button_sizer.AddButton(self.go_button)
        button_sizer.AddButton(self.cancel_button)
        button_sizer.Realize()

        self.main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.panel.SetSizer(self.main_sizer)
        self.SetSize((500, 350))
        self.CentreOnParent()

        self.chapter_list_box.SetFocus()

        self.go_button.Bind(wx.EVT_BUTTON, self.on_go)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.chapter_list_box.Bind(wx.EVT_LISTBOX_DCLICK, self.on_go)
        self.chapter_list_box.Bind(wx.EVT_KEY_DOWN, self.on_list_key)

        self.SetDefaultItem(self.go_button)

    def on_go(self, event):
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_list_key(self, event: wx.KeyEvent):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN:
            if self.chapter_list_box.GetSelection() != wx.NOT_FOUND:
                self.on_go(None)
            else:
                event.Skip()
        else:
            event.Skip()

    def get_selected_index(self) -> int:
        return self.chapter_list_box.GetSelection()