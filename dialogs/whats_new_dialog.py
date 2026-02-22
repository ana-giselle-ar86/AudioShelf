# dialogs/whats_new_dialog.py
# Copyright (c) 2025 Mehdi Rajabi
# License: GNU General Public License v3.0 (See LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import wx
import os
import logging
from i18n import _
from dialogs.donate_dialog import DonateDialog


class WhatsNewDialog(wx.Dialog):
    def __init__(self, parent, show_donate=False):
        super(WhatsNewDialog, self).__init__(parent, title=_("What's New in AudioShelf"), size=(650, 550))
        self.show_donate = show_donate
        self._build_ui()
        self._load_changelog(latest_only=self.show_donate)

    def _build_ui(self):
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        info_lbl = wx.StaticText(self.panel, label=_("Release Notes:"))
        main_sizer.Add(info_lbl, 0, wx.ALL, 10)

        self.text_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        main_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self.show_donate:
            donate_btn = wx.Button(self.panel, wx.ID_ANY, _("&Donate..."))
            donate_btn.Bind(wx.EVT_BUTTON, self._on_donate)
            btn_sizer.Add(donate_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        btn_sizer.AddStretchSpacer(1)

        close_btn = wx.Button(self.panel, wx.ID_OK, _("&Close"))
        btn_sizer.Add(close_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.panel.SetSizer(main_sizer)
        self.CentreOnParent()

        self.SetDefaultItem(close_btn)
        self.text_ctrl.SetFocus()

    def _load_changelog(self, latest_only: bool):
        from database import db_manager
        
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        current_lang = db_manager.get_setting('language') or 'en'
        
        root_changelog = os.path.join(app_dir, 'CHANGELOG.md')
        localized_changelog = os.path.join(app_dir, 'locale', current_lang, 'CHANGELOG.md')
        
        if current_lang != 'en' and os.path.exists(localized_changelog):
            final_path = localized_changelog
        else:
            final_path = root_changelog

        if not os.path.exists(final_path):
            self.text_ctrl.SetValue(_("Changelog file not found."))
            return

        cleaned_lines = []
        capture = False

        try:
            with open(final_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    if line.startswith('## ['):
                        if capture and latest_only:
                            break
                        capture = True
                        version_text = line.replace('## ', '').replace('[', '').replace(']', '')
                        cleaned_lines.append(version_text)
                        cleaned_lines.append('')
                        continue

                    if capture:
                        if line.startswith('### '):
                            cleaned_lines.append('')
                            header_text = line.replace('### ', '').strip()
                            cleaned_lines.append(f"{header_text}:")
                        elif line:
                            cl = line.replace('**', '').replace('`', '')
                            if cl.startswith('- '):
                                cl = cl[2:]
                            
                            cl = cl.strip()
                            if cl or (cleaned_lines and cleaned_lines[-1] != ''):
                                cleaned_lines.append(cl)

            final_text = '\n'.join(cleaned_lines).strip()
            
            if current_lang in ['fa', 'ar']:
                self.text_ctrl.SetLayoutDirection(wx.Layout_RightToLeft)
                
            self.text_ctrl.SetValue(final_text)

        except Exception as e:
            logging.error(f"Error reading changelog from {final_path}: {e}", exc_info=True)
            self.text_ctrl.SetValue(_("Error loading changelog."))

    def _on_donate(self, event):
        dlg = DonateDialog(self)
        dlg.ShowModal()
        dlg.Destroy()